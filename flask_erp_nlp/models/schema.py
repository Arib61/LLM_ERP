"""
Schéma de base de données ERP
"""

ERP_SCHEMA = {
    "tables": {
        "commandes": {
            "columns": {
                "id": "INT PRIMARY KEY",
                "date_commande": "DATE",
                "montant": "DECIMAL(10,2)",
                "client_id": "INT FOREIGN KEY",
                "produit_id": "INT FOREIGN KEY"
            },
            "description": "Commandes passées par les clients"
        },
        "clients": {
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "secteur": "VARCHAR(50)",
                "ville": "VARCHAR(50)"
            },
            "description": "Informations clients"
        },
        "produits": {
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "categorie": "VARCHAR(50)",
                "prix_unitaire": "DECIMAL(10,2)"
            },
            "description": "Catalogue produits"
        },
        "fournisseurs": {
            "columns": {
                "id": "INT PRIMARY KEY",
                "nom": "VARCHAR(100)",
                "pays": "VARCHAR(50)",
                "categorie_fournisseur": "VARCHAR(50)"
            },
            "description": "Fournisseurs disponibles"
        }
    },
    "relations": {
        "commandes.client_id": "clients.id",
        "commandes.produit_id": "produits.id"
    }
}

def format_schema_detailed(schema):
    """Formate le schéma pour les prompts"""
    tables_desc = []
    for table, info in schema["tables"].items():
        cols = ", ".join([f"{col} ({type_col})" for col, type_col in info["columns"].items()])
        tables_desc.append(f"Table {table}: {cols} - {info['description']}")
    
    relations = "\nRelations:\n" + "\n".join([f"- {rel}" for rel in schema["relations"]])
    return "\n".join(tables_desc) + relations