# RAG.py

from sentence_transformers import SentenceTransformer
import faiss

# ========= SCHEMA GLOBAL ERP (exemple) =========
erp_schema = {
    "tables": {
        "clients": {
            "description": "Table des clients",
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "secteur": "VARCHAR(50)",
                "ville": "VARCHAR(50)"
            }
        },
        "commandes": {
            "description": "Table des commandes",
            "columns": {
                "id": "INT PRIMARY KEY",
                "date_commande": "DATE",
                "montant": "DECIMAL(10,2)",
                "client_id": "INT",
                "produit_id": "INT"
            }
        },
        "produits": {
            "description": "Table des produits",
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "categorie": "VARCHAR(50)",
                "prix_unitaire": "DECIMAL(10,2)"
            }
        },
        "fournisseurs": {
            "description": "Table des fournisseurs",
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "pays": "VARCHAR(50)",
                "categorie_fournisseur": "VARCHAR(50)"
            }
        }
    },
    "relations": {
        "commandes.client_id": "clients.id",
        "commandes.produit_id": "produits.id",
        # "produits.fournisseur_id": "fournisseurs.id"  # si tu ajoutes ce champ !
    }
}

# ========= INITIALISATION DU RAG (à faire une fois) =========
embedder = SentenceTransformer(r'C:\Users\Administrateur\Documents\StageArib\projetERP\LLM_ERP-pre_phase1\Model\all-MiniLM-L6-v2')
schema_texts = []
table_names = list(erp_schema["tables"].keys())
for table in table_names:
    desc = f"Table {table}: {erp_schema['tables'][table]['description']}. Colonnes: {', '.join(erp_schema['tables'][table]['columns'].keys())}"
    schema_texts.append(desc)

embeddings = embedder.encode(schema_texts, convert_to_tensor=True).cpu().numpy()
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# ========= RAG FUNCTIONS =========

def retrieve_relevant_schema(question, k=8):
    """Retourne le sous-schéma SQL pertinent pour la question."""
    question_embed = embedder.encode([question], convert_to_tensor=True).cpu().numpy()
    distances, indices = index.search(question_embed, k)
    relevant_tables = [table_names[i] for i in indices[0]]

    sub_schema = {
        "tables": {t: erp_schema["tables"][t] for t in relevant_tables},
        "relations": {}
    }
    for src_col, dst_col in erp_schema.get("relations", {}).items():
        src_table = src_col.split(".")[0]
        dst_table = dst_col.split(".")[0]
        if src_table in relevant_tables and dst_table in relevant_tables:
            sub_schema["relations"][src_col] = dst_col
    return sub_schema

def sub_schema_to_sql(sub_schema):
    """Transforme le sous-schéma en string SQL pour le prompt LLM."""
    sql = ""
    for table, meta in sub_schema["tables"].items():
        columns = [f"{col} {type_}" for col, type_ in meta["columns"].items()]
        sql += f"CREATE TABLE {table} (\n  " + ",\n  ".join(columns) + "\n);\n"
    if sub_schema.get("relations"):
        sql += "\n-- Relations :\n"
        for src, dst in sub_schema["relations"].items():
            sql += f"-- {src} can be joined with {dst}\n"
    return sql

# # ========== EXEMPLE D'UTILISATION ==========
# if __name__ == "__main__":
#     question = "Quels sont les clients ayant passé une commande en 2024 ?"
#     sub_schema = retrieve_relevant_schema(question, k=3)
#     print("=== Sous-schéma pertinent ===")
#     print(sub_schema_to_sql(sub_schema))
