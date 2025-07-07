from flask import Flask
from flask_cors import CORS
import logging
from config import Config
from routes.api_routes import api_bp

def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(Config)
    
    # CORS
    CORS(app)
    
    # Logging
    logging.basicConfig(level=logging.INFO)
    
    # Enregistrement des blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)