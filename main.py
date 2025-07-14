from pathlib import Path
import time
from llm_session import LLMChatSession
from prompt import (
    build_sql_prompt,
    build_sql_correction_prompt,
    build_sql_validator_prompt
)
from RAG import retrieve_relevant_schema, sub_schema_to_sql
import re
from translatepy import Translator
from questions import questions


def translate_fr_to_en(text):
    t = Translator()
    return t.translate(text, "English").result


SQL_STARTERS = ("SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP")

def clean_llm_sql_output(output: str) -> str:
    output = re.sub(r"\[/?SQL\]", "", output, flags=re.IGNORECASE)
    output = re.sub(r"```sql|```", "", output, flags=re.IGNORECASE)
    lines = output.splitlines()
    sql_started = False
    sql_lines = []
    for line in lines:
        stripped = line.strip()
        if any(txt in stripped.lower() for txt in [
            "your answer", "voici", "final answer", "réponse", "answer:"
        ]):
            continue
        if not sql_started and any(stripped.upper().startswith(starter) for starter in SQL_STARTERS):
            sql_started = True
        if sql_started:
            if (
                not stripped
                or stripped.startswith("--")
                or re.match(r"^#|^//|^NOTE\b|^\[", stripped, re.IGNORECASE)
            ):
                break
            sql_lines.append(line)
    sql_code = "\n".join(sql_lines).strip()
    if ";" in sql_code:
        sql_code = sql_code.split(";")[0] + ";"
    return sql_code

def assert_sql_basic_validity(sql: str):
    if not sql:
        raise ValueError("SQL query is empty")
    if not any(sql.upper().startswith(s) for s in SQL_STARTERS):
        raise ValueError(f"Unexpected SQL output:\n{sql[:80]}...")
    if "note" in sql.lower() or "explanation" in sql.lower():
        raise ValueError(f"Chatter detected in SQL:\n{sql[:80]}...")

# === Model paths & schema ===
MODEL_PATH_PREM = Path(r"C:\Users\Administrateur\Documents\StageArib\projetERP\LLM_ERP-pre_phase1\Model\prem-1B-SQL.Q8_0.gguf")       
MODEL_PATH_LLAMA = Path(r"C:\Users\Administrateur\Documents\StageArib\projetERP\LLM_ERP-pre_phase1\Model\Meta-Llama-3-8B-Instruct-Q6_K.gguf")
MODEL_PATH_VALIDATOR = Path(r"C:\Users\Administrateur\Documents\StageArib\projetERP\LLM_ERP-pre_phase1\Model\nsql-llama-2-7b.Q4_K_M.gguf")
N_CTX = 2048

SCHEMA_SQL = """
CREATE TABLE commandes (
  id INT PRIMARY KEY,
  date_commande DATE,
  montant DECIMAL(10,2),
  client_id INT,
  produit_id INT
);
CREATE TABLE clients (
  id INT PRIMARY KEY,
  nom VARCHAR(100),
  secteur VARCHAR(50),
  ville VARCHAR(50)
);
CREATE TABLE produits (
  id INT PRIMARY KEY,
  nom VARCHAR(100),
  categorie VARCHAR(50),
  prix_unitaire DECIMAL(10,2)
);
CREATE TABLE fournisseurs (
  id INT PRIMARY KEY,
  nom VARCHAR(100),
  pays VARCHAR(50),
  categorie_fournisseur VARCHAR(50)
);
-- commandes.client_id can be joined with clients.id
-- commandes.produit_id can be joined with produits.id
-- produits.id can (optionally) be linked to fournisseurs.id if you add a 'fournisseur_id'
"""





results = []

with LLMChatSession(MODEL_PATH_PREM, n_ctx=N_CTX, n_gpu_layers=100) as prem, \
     LLMChatSession(MODEL_PATH_LLAMA, n_ctx=N_CTX, n_gpu_layers=100) as llama, \
     LLMChatSession(MODEL_PATH_VALIDATOR, n_ctx=N_CTX, n_gpu_layers=100) as nsql:

    for idx, question in enumerate(questions):
        print(f"\nQuestion {idx+1}/{len(questions)}: {question}")

        # 1. Génération brute
        sql_prompt = build_sql_prompt(question, SCHEMA_SQL)
        raw_sql = prem.generate(sql_prompt)
        sql_code = clean_llm_sql_output(raw_sql.strip().replace("[SQL]", "").strip())

        # 2. Correction
        sub_schema = retrieve_relevant_schema(question, k=3)
        schema_str = sub_schema_to_sql(sub_schema)
        correction_prompt = build_sql_correction_prompt(
            question=question,
            sql_code=sql_code,
            schema=schema_str
        )
        t0 = time.perf_counter()
        corrected_output = llama.generate(correction_prompt, stop_tag=None, max_tokens=256)
        t1 = time.perf_counter()
        sql_corrigee = clean_llm_sql_output(corrected_output)

        # 3. Correction invalid fallback
        if (
            sql_corrigee.strip().lower() in ["select 'not possible';", "select 'not possible'", "not possible", ""] or
            "???" in sql_corrigee or "?" in sql_corrigee or
            not any(sql_corrigee.upper().startswith(s) for s in SQL_STARTERS)
        ):
            try:
                assert_sql_basic_validity(sql_code)
                print(f"💡 Fallback: Correction impossible, fallback to raw brute version!")
                sql_corrigee = sql_code
            except Exception as e:
                print(f"[FALLBACK ERROR]: {e}")
                sql_corrigee = "SELECT 'Not possible';"

        # 4. Validation stricte logique
        validator_prompt = build_sql_validator_prompt(translate_fr_to_en(question), sql_corrigee, SCHEMA_SQL)
        validation_output = nsql.generate(validator_prompt, stop_tag=None, max_tokens=256)
        validation_sql = clean_llm_sql_output(validation_output)
        try:
            assert_sql_basic_validity(validation_sql)
            final_sql = validation_sql
        except Exception as e:
            print(f"[VALIDATION FALLBACK ERROR] : {e}")
            final_sql = "SELECT 'Not possible';"

        results.append({
            "question": question,
            "sql_brute": sql_code,
            "sql_corrigee": sql_corrigee,
            "sql_finale": final_sql,
            "correction_raw": corrected_output,
            "validator_raw": validation_output,
            "duration_s": round(t1 - t0, 2)
        })

        print(f"Requête finale:\n{final_sql}\n---")

# Save to file
with open("resultat.txt", "w", encoding="utf-8") as f:
    for idx, r in enumerate(results):
        f.write(f"--- Question {idx+1:02d} ---\n")
        f.write(f"Question : {r['question']}\n")
        f.write(f"--- SQL brute ---\n{r['sql_brute']}\n")
        f.write(f"--- SQL corrigée ---\n{r['sql_corrigee']}\n")
        f.write(f"--- SQL validée ---\n{r['sql_finale']}\n")
        f.write(f"Temps (s) : {r['duration_s']}\n\n")

print("✅ Robust results saved in llama3_sql_benchmark.txt")
