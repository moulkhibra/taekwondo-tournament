from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

def create_app():
    # Set correct template and static folders
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tournament.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_tournaments():
        from app.models import Tournament
        tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
        return dict(tournaments=[{'id': t.id, 'name': t.name} for t in tournaments])
    
    # Import routes after app creation to avoid circular imports
    from app.routes import main
    from app.auth_routes import auth
    from app.scoring_routes import scoring
    from app.scheduling_routes import scheduling
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(scoring)
    app.register_blueprint(scheduling)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app