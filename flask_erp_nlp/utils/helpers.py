"""
Fonctions utilitaires pour l'application
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_error_response(error_type, message, details=None):
    """
    Formate une réponse d'erreur standardisée
    
    Args:
        error_type (str): Type d'erreur
        message (str): Message d'erreur
        details (dict, optional): Détails additionnels
        
    Returns:
        dict: Réponse d'erreur formatée
    """
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    if details:
        response['error']['details'] = details
    
    return response

def format_success_response(data, message=None):
    """
    Formate une réponse de succès standardisée
    
    Args:
        data (dict): Données à retourner
        message (str, optional): Message de succès
        
    Returns:
        dict: Réponse de succès formatée
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    if message:
        response['message'] = message
    
    return response

def log_request(endpoint, data, user_ip=None):
    """
    Log une requête entrante
    
    Args:
        endpoint (str): Endpoint appelé
        data (dict): Données de la requête
        user_ip (str, optional): IP de l'utilisateur
    """
    log_msg = f"API {endpoint} appelée"
    
    if user_ip:
        log_msg += f" depuis {user_ip}"
    
    # Log les données sensibles de manière sécurisée
    if 'question' in data:
        log_msg += f" - Question: {data['question'][:50]}..."
    
    logger.info(log_msg)

def sanitize_input(text):
    """
    Nettoie et sanitise une entrée texte
    
    Args:
        text (str): Texte à nettoyer
        
    Returns:
        str: Texte nettoyé
    """
    if not isinstance(text, str):
        return ""
    
    # Supprime les caractères de contrôle dangereux
    cleaned = text.replace('\x00', '').replace('\r', '').strip()
    
    return cleaned

def extract_keywords(text, max_keywords=10):
    """
    Extrait les mots-clés principaux d'un texte
    
    Args:
        text (str): Texte à analyser
        max_keywords (int): Nombre maximum de mots-clés
        
    Returns:
        list: Liste des mots-clés
    """
    if not text:
        return []
    
    # Mots-clés SQL/ERP communs
    sql_keywords = [
        'select', 'where', 'from', 'join', 'group', 'order', 'count', 
        'sum', 'avg', 'max', 'min', 'having', 'distinct'
    ]
    
    erp_keywords = [
        'client', 'commande', 'produit', 'fournisseur', 'montant', 
        'date', 'prix', 'secteur', 'ville', 'categorie'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    # Recherche des mots-clés SQL
    for keyword in sql_keywords:
        if keyword in text_lower:
            found_keywords.append(f"sql:{keyword}")
    
    # Recherche des mots-clés ERP
    for keyword in erp_keywords:
        if keyword in text_lower:
            found_keywords.append(f"erp:{keyword}")
    
    return found_keywords[:max_keywords]

def validate_sql_query(sql_query):
    """
    Valide basiquement une requête SQL
    
    Args:
        sql_query (str): Requête SQL à valider
        
    Returns:
        dict: Résultat de validation
    """
    if not sql_query:
        return {
            'valid': False,
            'error': 'Requête vide'
        }
    
    sql_lower = sql_query.lower().strip()
    
    # Vérifications de sécurité basiques
    dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'create', 'alter', 'truncate']
    
    for keyword in dangerous_keywords:
        if keyword in sql_lower:
            return {
                'valid': False,
                'error': f'Mot-clé dangereux détecté: {keyword}'
            }
    
    # Vérification de la structure basique
    if not sql_lower.startswith('select'):
        return {
            'valid': False,
            'error': 'Seules les requêtes SELECT sont autorisées'
        }
    
    return {
        'valid': True,
        'error': None
    }

def format_sql_query(sql_query):
    """
    Formate une requête SQL pour l'affichage
    
    Args:
        sql_query (str): Requête SQL à formater
        
    Returns:
        str: Requête SQL formatée
    """
    if not sql_query:
        return ""
    
    # Supprime les espaces multiples et les sauts de ligne excessifs
    formatted = ' '.join(sql_query.split())
    
    # Ajoute des sauts de ligne pour la lisibilité
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'HAVING']
    
    for keyword in keywords:
        formatted = formatted.replace(keyword, f'\n{keyword}')
    
    return formatted.strip()

def get_table_info(table_name):
    """
    Récupère les informations d'une table du schéma
    
    Args:
        table_name (str): Nom de la table
        
    Returns:
        dict: Informations de la table ou None
    """
    from models.schema import ERP_SCHEMA
    
    return ERP_SCHEMA.get('tables', {}).get(table_name, None)

def estimate_query_complexity(sql_query):
    """
    Estime la complexité d'une requête SQL
    
    Args:
        sql_query (str): Requête SQL
        
    Returns:
        dict: Estimation de complexité
    """
    if not sql_query:
        return {'level': 'unknown', 'score': 0}
    
    sql_lower = sql_query.lower()
    complexity_score = 0
    
    # Facteurs de complexité
    if 'join' in sql_lower:
        complexity_score += 2
    if 'group by' in sql_lower:
        complexity_score += 2
    if 'having' in sql_lower:
        complexity_score += 1
    if 'order by' in sql_lower:
        complexity_score += 1
    if 'extract(' in sql_lower:
        complexity_score += 1
    if 'count(' in sql_lower or 'sum(' in sql_lower:
        complexity_score += 1
    
    # Nombre de tables (approximatif)
    table_count = sql_lower.count('from') + sql_lower.count('join')
    complexity_score += table_count
    
    # Détermination du niveau
    if complexity_score <= 2:
        level = 'simple'
    elif complexity_score <= 5:
        level = 'moderate'
    else:
        level = 'complex'
    
    return {
        'level': level,
        'score': complexity_score,
        'factors': {
            'joins': sql_lower.count('join'),
            'aggregations': sql_lower.count('group by'),
            'table_count': table_count
        }
    }