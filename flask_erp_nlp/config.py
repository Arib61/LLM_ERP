import os

class Config:
    """Configuration de l'application"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuration Ollama
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST') or 'http://localhost:11434'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'llama3.2'
    
    # Configuration API
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Debug
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'