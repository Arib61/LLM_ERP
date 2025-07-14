import streamlit as st
from pathlib import Path
import re
import time
from translatepy import Translator
from llm_session2 import LLMChatSession
from prompt import (
    build_sql_prompt,
    build_sql_correction_prompt,
    build_sql_validator_prompt
)
from RAG import retrieve_relevant_schema, sub_schema_to_sql
from questions import questions  # Ton fichier questions.py

# ========= CONFIG MODEL ET SCHÉMA =========
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

SQL_STARTERS = ("SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP")

# ========== UTILITAIRES PIPELINE ==========

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

def translate_fr_to_en(text):
    t = Translator()
    return t.translate(text, "English").result

# ========== CACHE DES MODELS ==========

@st.cache_resource(show_spinner="Chargement des modèles LLM... (peut prendre 1-2 min la 1ère fois)")
def get_llm_sessions():
    prem = LLMChatSession(MODEL_PATH_PREM, n_ctx=N_CTX, n_gpu_layers=100)
    llama = LLMChatSession(MODEL_PATH_LLAMA, n_ctx=N_CTX, n_gpu_layers=100)
    nsql = LLMChatSession(MODEL_PATH_VALIDATOR, n_ctx=N_CTX, n_gpu_layers=100)
    return prem, llama, nsql

prem, llama, nsql = get_llm_sessions()

# ========== PIPELINE PRINCIPAL ==========

def process_question(question, prem, llama, nsql, schema_sql):
    # 1. Génération brute
    sql_prompt = build_sql_prompt(question, schema_sql)
    raw_sql = prem.generate(sql_prompt)
    sql_code = clean_llm_sql_output(raw_sql.strip().replace("[SQL]", "").strip())

    # Correction
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

    # Fallback
    if (
        sql_corrigee.strip().lower() in ["select 'not possible';", "select 'not possible'", "not possible", ""] or
        "???" in sql_corrigee or "?" in sql_corrigee or
        not any(sql_corrigee.upper().startswith(s) for s in SQL_STARTERS)
    ):
        try:
            assert_sql_basic_validity(sql_code)
            sql_corrigee = sql_code
        except Exception as e:
            sql_corrigee = "SELECT 'Not possible';"

    # Validation
    validator_prompt = build_sql_validator_prompt(translate_fr_to_en(question), sql_corrigee, schema_sql)
    validation_output = nsql.generate(validator_prompt, stop_tag=None, max_tokens=256)
    validation_sql = clean_llm_sql_output(validation_output)
    try:
        assert_sql_basic_validity(validation_sql)
        final_sql = validation_sql
    except Exception as e:
        final_sql = "SELECT 'Not possible';"

    return {
        "sql_code": sql_code,
        "sql_corrigee": sql_corrigee,
        "final_sql": final_sql,
        "duration": round(t1-t0,2)
    }

# ========== INTERFACE STREAMLIT ==========

st.set_page_config(page_title="NLP2SQL Pipeline Test", layout="centered")
st.title("🧠 NLP → SQL pipeline (offline)")

tab1, tab2 = st.tabs(["Question libre", "Test multi-question"])

# ---- 1. Test manuel : une question ----
with tab1:
    st.header("Testez votre question (Français ou Anglais)")
    user_question = st.text_area("Question", value="Quel est le montant total des commandes par client ?", height=80)
    if st.button("Générer SQL !") and user_question.strip():
        with st.spinner("Génération, correction et validation SQL..."):
            result = process_question(user_question, prem, llama, nsql, SCHEMA_SQL)
            st.success("✅ Pipeline terminé")
            st.markdown("### SQL brut")
            st.code(result["sql_code"], language="sql")
            st.markdown("### SQL corrigée")
            st.code(result["sql_corrigee"], language="sql")
            st.markdown("### SQL validée (finale)")
            st.code(result["final_sql"], language="sql")
            st.info(f"Temps pipeline : {result['duration']} sec")

# ---- 2. Test sur liste complète (batch) ----
with tab2:
    st.header("Tester sur la liste complète de questions")
    if st.button("Exécuter sur toutes les questions"):
        with st.spinner("Boucle sur toutes les questions (patientez un peu)"):
            for idx, question in enumerate(questions):
                result = process_question(question, prem, llama, nsql, SCHEMA_SQL)
                st.write(f"**{question}**")
                st.code(result["final_sql"], language="sql")
                st.divider()
        st.success("🚀 Batch terminé ! (voir logs ci-dessus)")
