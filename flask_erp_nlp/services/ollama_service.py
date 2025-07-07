"""
Service pour la communication avec Ollama
"""

from ollama import Client
import logging
from config import Config

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.client = None
        self.model = Config.OLLAMA_MODEL
        self.connect()
    
    def connect(self):
        """Établit la connexion avec Ollama"""
        try:
            self.client = Client(host=Config.OLLAMA_HOST)
            logger.info("✅ Connexion à Ollama établie")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à Ollama: {e}")
            self.client = None
            return False
    
    def is_connected(self):
        """Vérifie si la connexion est établie"""
        return self.client is not None
    
    def generate_response(self, prompt, max_retries=3):
        """
        Génère une réponse via Ollama
        
        Args:
            prompt (str): Le prompt à envoyer
            max_retries (int): Nombre de tentatives en cas d'échec
            
        Returns:
            str: La réponse générée ou None en cas d'erreur
        """
        if not self.is_connected():
            logger.error("Ollama n'est pas connecté")
            return None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if response and 'message' in response:
                    return response['message']['content']
                else:
                    logger.warning(f"Réponse Ollama invalide: {response}")
                    
            except Exception as e:
                logger.error(f"Erreur Ollama (tentative {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # Tentative de reconnexion
                    logger.info("Tentative de reconnexion...")
                    self.connect()
        
        return None
    
    def test_connection(self):
        """Test la connexion avec une requête simple"""
        try:
            response = self.generate_response("Dis juste 'OK' pour tester la connexion")
            return response is not None
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion: {e}")
            return False

# Instance globale du service
ollama_service = OllamaService()