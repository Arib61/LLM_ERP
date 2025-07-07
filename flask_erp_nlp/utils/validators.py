"""
Validateurs pour les données d'entrée
"""

def validate_question(data):
    """
    Valide les données pour l'API d'extraction
    
    Args:
        data (dict): Données à valider
        
    Returns:
        dict: Résultat de validation
    """
    if not data:
        return {
            'valid': False,
            'error': 'Données manquantes',
            'message': 'Aucune donnée reçue'
        }
    
    if 'question' not in data:
        return {
            'valid': False,
            'error': 'Question manquante',
            'message': 'Le champ "question" est requis'
        }
    
    question = data['question']
    
    if not isinstance(question, str):
        return {
            'valid': False,
            'error': 'Type invalide',
            'message': 'La question doit être une chaîne de caractères'
        }
    
    if len(question.strip()) == 0:
        return {
            'valid': False,
            'error': 'Question vide',
            'message': 'La question ne peut pas être vide'
        }
    
    if len(question) > 1000:
        return {
            'valid': False,
            'error': 'Question trop longue',
            'message': 'La question ne peut pas dépasser 1000 caractères'
        }
    
    return {
        'valid': True,
        'error': None,
        'message': 'Question valide'
    }

def validate_analysis(data):
    """
    Valide les données pour l'API de génération SQL
    
    Args:
        data (dict): Données à valider
        
    Returns:
        dict: Résultat de validation
    """
    if not data:
        return {
            'valid': False,
            'error': 'Données manquantes',
            'message': 'Aucune donnée reçue'
        }
    
    if 'analysis' not in data:
        return {
            'valid': False,
            'error': 'Analyse manquante',
            'message': 'Le champ "analysis" est requis'
        }
    
    analysis = data['analysis']
    
    if not isinstance(analysis, str):
        return {
            'valid': False,
            'error': 'Type invalide',
            'message': 'L\'analyse doit être une chaîne de caractères'
        }
    
    if len(analysis.strip()) == 0:
        return {
            'valid': False,
            'error': 'Analyse vide',
            'message': 'L\'analyse ne peut pas être vide'
        }
    
    if len(analysis) > 5000:
        return {
            'valid': False,
            'error': 'Analyse trop longue',
            'message': 'L\'analyse ne peut pas dépasser 5000 caractères'
        }
    
    # Vérification de la structure minimale
    required_sections = ['INTENTION:', 'TABLES:', 'COLONNES:']
    missing_sections = []
    
    for section in required_sections:
        if section not in analysis:
            missing_sections.append(section)
    
    if missing_sections:
        return {
            'valid': False,
            'error': 'Structure d\'analyse invalide',
            'message': f'Sections manquantes: {", ".join(missing_sections)}'
        }
    
    return {
        'valid': True,
        'error': None,
        'message': 'Analyse valide'
    }