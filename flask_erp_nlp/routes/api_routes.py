"""
Routes API pour le service NLP-SQL
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from services.ollama_service import ollama_service
from services.nlp_service import nlp_service
from utils.validators import validate_question, validate_analysis
from utils.helpers import format_error_response, format_success_response

logger = logging.getLogger(__name__)

# Création du blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Vérification de l'état de l'API"""
    ollama_connected = ollama_service.is_connected()
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'ollama_connected': ollama_connected,
        'services': {
            'ollama': 'connected' if ollama_connected else 'disconnected',
            'nlp': 'ready'
        }
    })

@api_bp.route('/extract', methods=['POST'])
def extract_information():
    """
    API 1: Extraction d'informations depuis une question
    
    Input: 
    {
        "question": "Quels clients ont commandé en avril 2024?"
    }
    
    Output: 
    {
        "success": true,
        "data": {
            "raw_response": "...",
            "parsed_analysis": {...},
            "question": "..."
        }
    }
    """
    try:
        # Validation de l'entrée
        data = request.get_json()
        validation_result = validate_question(data)
        
        if not validation_result['valid']:
            return format_error_response(
                validation_result['error'],
                validation_result['message']
            ), 400
        
        question = data['question'].strip()
        
        # Vérification de la connexion Ollama
        if not ollama_service.is_connected():
            return format_error_response(
                'Service indisponible',
                'Connexion à Ollama indisponible'
            ), 503
        
        # Extraction des informations
        logger.info(f"Extraction pour la question: {question}")
        result = nlp_service.extract_information(question)
        
        if result['success']:
            return format_success_response({
                'sql_query': result['sql_query'],
                'generation_timestamp': datetime.now().isoformat()
            })
        else:
            return format_error_response(
                'Erreur d\'extraction',
                result.get('error', 'Erreur inconnue')
            ), 500
            
    except Exception as e:
        logger.error(f"Erreur dans extract_information: {e}")
        return format_error_response(
            'Erreur interne',
            'Une erreur inattendue s\'est produite'
        ), 500

@api_bp.route('/generate-sql', methods=['POST'])
def generate_sql():
    """
    API 2: Génération SQL depuis une analyse NLP
    
    Input:
    {
        "analysis": "INTENTION: SELECT\nTABLES: [commandes]\n..."
    }
    
    Output:
    {
        "success": true,
        "data": {
            "sql_query": "SELECT ...",
            "raw_response": "...",
            "analysis": "..."
        }
    }
    """
    try:
        # Validation de l'entrée
        data = request.get_json()
        validation_result = validate_analysis(data)
        
        if not validation_result['valid']:
            return format_error_response(
                validation_result['error'],
                validation_result['message']
            ), 400
        
        analysis = data['analysis'].strip()
        
        # Vérification de la connexion Ollama
        if not ollama_service.is_connected():
            return format_error_response(
                'Service indisponible',
                'Connexion à Ollama indisponible'
            ), 503
        
        # Génération SQL
        logger.info(f"Génération SQL pour l'analyse: {analysis[:100]}...")
        result = nlp_service.generate_sql(analysis)
        
        if result['success']:
            return format_success_response({
            'sql_query': result['sql_query'],
            'generation_timestamp': datetime.now().isoformat()
        })
        else:
            return format_error_response(
                'Erreur de génération SQL',
                result.get('error', 'Erreur inconnue')
            ), 500
            
    except Exception as e:
        logger.error(f"Erreur dans generate_sql: {e}")
        return format_error_response(
            'Erreur interne',
            'Une erreur inattendue s\'est produite'
        ), 500

@api_bp.route('/process', methods=['POST'])
def process_complete():
    """
    API combinée: Question -> Analyse -> SQL
    
    Input:
    {
        "question": "Quels clients ont commandé en avril 2024?"
    }
    
    Output:
    {
        "success": true,
        "data": {
            "question": "...",
            "analysis": {...},
            "sql_query": "...",
            "processing_time": "..."
        }
    }
    """
    try:
        start_time = datetime.now()
        
        # Validation de l'entrée
        data = request.get_json()
        validation_result = validate_question(data)
        
        if not validation_result['valid']:
            return format_error_response(
                validation_result['error'],
                validation_result['message']
            ), 400
        
        question = data['question'].strip()
        
        # Vérification de la connexion Ollama
        if not ollama_service.is_connected():
            return format_error_response(
                'Service indisponible',
                'Connexion à Ollama indisponible'
            ), 503
        
        # Étape 1: Extraction
        logger.info(f"Processus complet pour: {question}")
        extraction_result = nlp_service.extract_information(question)
        
        if not extraction_result['success']:
            return format_error_response(
                'Erreur d\'extraction',
                extraction_result.get('error', 'Erreur inconnue')
            ), 500
        
        # Étape 2: Génération SQL
        sql_result = nlp_service.generate_sql(extraction_result['raw_response'])
        
        if not sql_result['success']:
            return format_error_response(
                'Erreur de génération SQL',
                sql_result.get('error', 'Erreur inconnue')
            ), 500
        
        # Temps de traitement
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return format_success_response({
            'question': question,
            'analysis': {
                'raw_response': extraction_result['raw_response'],
                'parsed': extraction_result['parsed_analysis']
            },
            'sql_query': sql_result['sql_query'],
            'processing_time_seconds': processing_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur dans process_complete: {e}")
        return format_error_response(
            'Erreur interne',
            'Une erreur inattendue s\'est produite'
        ), 500

@api_bp.route('/test-ollama', methods=['POST'])
def test_ollama():
    """Test de connexion et fonctionnement d'Ollama"""
    try:
        if not ollama_service.is_connected():
            return format_error_response(
                'Ollama déconnecté',
                'Impossible de se connecter à Ollama'
            ), 503
        
        # Test avec une question simple
        test_success = ollama_service.test_connection()
        
        return format_success_response({
            'ollama_connected': True,
            'test_passed': test_success,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur dans test_ollama: {e}")
        return format_error_response(
            'Erreur de test',
            str(e)
        ), 500