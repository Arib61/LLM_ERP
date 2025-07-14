from llama_cpp import Llama

# Path to your GGUF model (change to your actual path)
MODEL_PATH = r"C:\Users\Administrateur\Documents\StageArib\projetERP\LLM_ERP-pre_phase1\Model\nsql-llama-2-7b.Q4_K_M.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_gpu_layers=40,    # Mieux si tu as un GPU, sinon mets 0 pour CPU only
    verbose=True
)

# === TEST: VALIDATION/CORRECTION PHASE ===

schema = """
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
"""

# ⚠️ 1. Traduire la question en anglais !
question = "Which are the 5 clients who ordered the most in total value? The result must be limited to 5 rows."


# ⚠️ 2. Mettre ici une requête SQL candidate (même fausse)
sql_candidate = """
SELECT clients.nom, COUNT(*) FROM clients;
"""

# === Prompt direct pour NSQL-Llama-2-7B (PAS D'INSTRUCTIONS) ===
prompt = f"""Schema:
{schema}

Question:
{question}

SQL Candidate:
{sql_candidate}

-- Correct SQL:
"""

output = llm(
    prompt,
    max_tokens=256,
    stop=["\n\n", "--", "```", "[/SQL]"],  # Stop à la fin de la requête
    temperature=0.1,
    echo=False
)

print("\n--- LLM OUTPUT ---\n")
print(output["choices"][0]["text"].strip())
