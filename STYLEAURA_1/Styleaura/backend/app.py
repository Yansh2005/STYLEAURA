from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database import create_indexes
from routes.auth import auth_bp
from routes.images import images_bp
from routes.analysis import analysis_bp
from routes.recommendations import recommendations_bp
from routes.users import users_bp
from routes.chat import chat_bp
from routes.cart import cart_bp
from routes.contact import contact_bp
from routes.ml_analysis import ml_analysis_bp
from routes.outfit_images import outfit_images_bp
from dotenv import load_dotenv

def create_app():
    # Load environment variables from .env if present
    load_dotenv()
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    # Restrict CORS to known frontend origins
    CORS(app, origins=Config.CORS_ORIGINS)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(contact_bp, url_prefix='/api/contact')
    app.register_blueprint(ml_analysis_bp, url_prefix='/api/ml')
    app.register_blueprint(outfit_images_bp, url_prefix='/api/ml')
    
    # Create database indexes
    create_indexes()
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'StyleAura API is running'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Run without debug/reloader to avoid Windows WinError 10038
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
