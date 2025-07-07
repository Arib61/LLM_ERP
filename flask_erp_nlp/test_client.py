"""
Client de test pour les APIs Flask
"""

import requests
import json
from datetime import datetime

class APIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_health(self):
        """Test de l'API de santé"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def extract_information(self, question):
        """Test de l'API d'extraction"""
        try:
            data = {"question": question}
            response = self.session.post(
                f"{self.base_url}/api/extract",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def generate_sql(self, analysis):
        """Test de l'API de génération SQL"""
        try:
            data = {"analysis": analysis}
            response = self.session.post(
                f"{self.base_url}/api/generate-sql",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def process_complete(self, question):
        """Test de l'API complète"""
        try:
            data = {"question": question}
            response = self.session.post(
                f"{self.base_url}/api/process",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_ollama(self):
        """Test de la connexion Ollama"""
        try:
            response = self.session.post(f"{self.base_url}/api/test-ollama")
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """Fonction principale de test"""
    client = APIClient()
    
    print("🚀 Tests des APIs Flask ERP NLP-SQL\n")
    
    # Test 1: Santé
    print("1. Test de santé...")
    health = client.test_health()
    print(f"   Résultat: {health}")
    print()
    
    # Test 2: Connexion Ollama
    print("2. Test connexion Ollama...")
    ollama_test = client.test_ollama()
    print(f"   Résultat: {ollama_test}")
    print()
    
    # Test 3: Extraction d'informations
    print("3. Test extraction d'informations...")
    test_questions = [
        "Quels clients ont commandé des produits en avril 2024?",
        "Combien de commandes ont été passées par secteur?",
        "Quel est le montant total des commandes par client?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"   Question {i}: {question}")
        result = client.extract_information(question)
        
        if result.get('success'):
            print(f"   ✅ Extraction réussie")
            if 'data' in result and 'parsed_analysis' in result['data']:
                parsed = result['data']['parsed_analysis']
                print(f"   📊 Analyse: {parsed}")
        else:
            print(f"   ❌ Échec: {result.get('error', 'Erreur inconnue')}")
        print()
    
    # Test 4: Génération SQL
    print("4. Test génération SQL...")
    sample_analysis = """
INTENTION: SELECT
TABLES: [commandes, clients]
COLONNES: [clients.nom, commandes.montant]
FILTRES: [EXTRACT(MONTH FROM commandes.date_commande) = 4, EXTRACT(YEAR FROM commandes.date_commande) = 2024]
JOINTURES: [commandes.client_id = clients.id]
AGRÉGATION:
    """.strip()
    
    sql_result = client.generate_sql(sample_analysis)
    if sql_result.get('success'):
        print("   ✅ Génération SQL réussie")
        if 'data' in sql_result and 'sql_query' in sql_result['data']:
            sql_query = sql_result['data']['sql_query']
            print(f"   🔍 SQL généré:\n{sql_query}")
    else:
        print(f"   ❌ Échec: {sql_result.get('error', 'Erreur inconnue')}")
    print()
    
    # Test 5: Processus complet
    print("5. Test processus complet...")
    complete_question = "Quels sont les clients qui ont commandé des produits en mars 2024?"
    
    complete_result = client.process_complete(complete_question)
    if complete_result.get('success'):
        print("   ✅ Processus complet réussi")
        if 'data' in complete_result:
            data = complete_result['data']
            print(f"   📝 Question: {data.get('question', 'N/A')}")
            print(f"   🔍 SQL: {data.get('sql_query', 'N/A')}")
            print(f"   ⏱️  Temps: {data.get('processing_time_seconds', 'N/A')}s")
    else:
        print(f"   ❌ Échec: {complete_result.get('error', 'Erreur inconnue')}")
    
    print("\n🏁 Tests terminés!")

if __name__ == "__main__":
    main()