"""
Service pour le traitement NLP et génération SQL
"""

import logging
from models.schema import ERP_SCHEMA, format_schema_detailed
from services.ollama_service import ollama_service
import re


logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        self.schema = ERP_SCHEMA
    
    def generate_nlp_prompt(self, question: str) -> str:
        """Génère le prompt pour l'extraction NLP"""
        return f"""
Tu es un moteur d'analyse linguistique expert intégré à un système ERP. Ta tâche est d'analyser la question ci-dessous et d'en extraire toutes les informations nécessaires à la génération d'une requête SQL. 

QUESTION UTILISATEUR :
"{question}"

SCHÉMA DE LA BASE DE DONNÉES :
{format_schema_detailed(self.schema)}

OBJECTIF :
Analyse la question et produis une sortie **au format texte structuré strict**, contenant toutes les sections obligatoires, même si certaines sont vides. N'invente jamais de table ou colonne non mentionnée dans le schéma.

FORMAT À RESPECTER :

INTENTION: ...
TABLES: [...]
COLONNES: [...]
FILTRES: [...] (si ils existent)
JOINTURES: [...] (si elles existent)
AGRÉGATION: ... (si elle existe)

RÈGLES :
- Ne saute **aucune section**
- Respecte **strictement** les noms du schéma
- Pour les dates : `EXTRACT(MONTH...)`, `EXTRACT(YEAR...)`
- Valeurs textuelles entourées de `'...'`

EXEMPLE :
INTENTION: SELECT  
TABLES: [commandes]  
COLONNES: [commandes.id, commandes.date_commande]  
FILTRES: [EXTRACT(MONTH FROM commandes.date_commande) BETWEEN 1 AND 3, EXTRACT(YEAR FROM commandes.date_commande) = 2024]  
JOINTURES: []  
AGRÉGATION:

Essaie d'utiliser beaucoup ton analyse tu as le schéma tu as tous analysé bien la requête et donne les meilleures extractions et les plus adéquates.
""".strip()
    
    def generate_sql_prompt(self, analysis_text: str) -> str:
        """Génère le prompt pour la génération SQL"""
        return f"""
Tu es un assistant SQL expert. Ton rôle est de transformer une analyse NLP structurée en requête SQL **exécutable et propre**, à partir du schéma ERP suivant :

📊 SCHÉMA :
{format_schema_detailed(self.schema)}

🧠 ANALYSE STRUCTURÉE :
{analysis_text}

🎯 OBJECTIF :
Génère la requête SQL correspondante, en respectant ces règles :

- Utilise SEULEMENT les colonnes mentionnées dans "COLONNES"
- Applique TOUS les filtres listés dans "FILTRES"
- Implémente toutes les jointures avec INNER JOIN
- Pour les dates, utilise EXTRACT(MONTH...) et EXTRACT(YEAR...) si mentionné
- Ne rajoute AUCUNE colonne ou table en plus
- Si AGRÉGATION est mentionnée, utilise COUNT/GROUP BY selon le cas
- Écris une requête SQL propre, indentée, sans explication
- N'ajoute pas d'agrégation s'il n'y en a pas dans la section AGRÉGATION 
- "Place TOUJOURS les conditions EXTRACT(...) dans une clause WHERE, jamais dans SELECT."

📦 Format de sortie :
```sql
-- requête SQL ici
```
Commence maintenant.
""".strip()
    
    def extract_information(self, question: str):
        """
        Extrait les informations d'une question en langage naturel
        
        Args:
            question (str): Question utilisateur
            
        Returns:
            dict: Informations extraites ou None en cas d'erreur
        """
        try:
            prompt = self.generate_nlp_prompt(question)
            response = ollama_service.generate_response(prompt)
            
            if response:
                parsed = self.parse_nlp_response(response)
                return {
                    'raw_response': response,
                    'parsed_analysis': parsed,
                    'success': True
                }
            else:
                return {
                    'error': 'Pas de réponse d\'Ollama',
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction NLP: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def generate_sql(self, analysis_text: str):
        """
        Génère une requête SQL depuis une analyse NLP
        
        Args:
            analysis_text (str): Texte d'analyse structurée
            
        Returns:
            dict: Requête SQL générée ou None en cas d'erreur
        """
        try:
            prompt = self.generate_sql_prompt(analysis_text)
            response = ollama_service.generate_response(prompt)
            
            if response:
                sql_query = self.extract_sql_from_response(response)
                return {
                    'raw_response': response,
                    'sql_query': sql_query,
                    'success': True
                }
            else:
                return {
                    'error': 'Pas de réponse d\'Ollama',
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération SQL: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def parse_nlp_response(self, response_text):
        """
        Parse une réponse NLP structurée (INTENTION, TABLES, COLONNES, etc.)
        et extrait les champs dans un dictionnaire.
        """
        try:
            result = {
                "INTENTION": "",
                "TABLES": "",
                "COLONNES": "",
                "FILTRES": "",
                "JOINTURES": "",
                "AGRÉGATION": ""
            }

            current_key = None
            for line in response_text.splitlines():
                line = line.strip()

                # 🔥 Nettoyer les **Markdown**
                line = re.sub(r"^\*\*(.*?)\*\*$", r"\1", line)
                line = re.sub(r"^\*\*(.*?)\*\*", r"\1", line)
                line = re.sub(r"\*\*", "", line)

                # 🔍 Détection d'une nouvelle section
                match = re.match(r"^(INTENTION|TABLES|COLONNES|FILTRES|JOINTURES|AGRÉGATION)\s*[:：]?\s*(.*)$", line, re.IGNORECASE)
                if match:
                    current_key = match.group(1).upper()
                    result[current_key] = match.group(2).strip()
                    continue

                # ⬇️ Ligne continue d'une section précédente
                if current_key and line:
                    result[current_key] += "\n" + line

            # Nettoyage final
            for key in result:
                result[key] = result[key].strip()

            return result

        except Exception as e:
            logger.error(f"Erreur lors du parsing NLP: {e}")
            return {
                "INTENTION": "",
                "TABLES": "",
                "COLONNES": "",
                "FILTRES": "",
                "JOINTURES": "",
                "AGRÉGATION": ""
            }

    
    def extract_sql_from_response(self, response_text):
        """Extrait le code SQL de la réponse"""
        try:
            # Cherche le bloc SQL entre ```sql et ```
            start_marker = "```sql"
            end_marker = "```"
            
            start_idx = response_text.find(start_marker)
            if start_idx == -1:
                return response_text.strip()
            
            start_idx += len(start_marker)
            end_idx = response_text.find(end_marker, start_idx)
            
            if end_idx == -1:
                return response_text[start_idx:].strip()
            
            return response_text[start_idx:end_idx].strip()
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction SQL: {e}")
            return response_text

# Instance globale du service
nlp_service = NLPService()