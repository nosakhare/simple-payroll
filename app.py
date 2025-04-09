import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create declarative base for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create application factory
def create_app(config_class=Config):
    # Create the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set secret key
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-development")
    
    # Configure proxy settings for URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from routes.main import main as main_bp
    from routes.auth import auth as auth_bp
    from routes.employees import employees as employees_bp
    from routes.payroll import payroll as payroll_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(payroll_bp, url_prefix='/payroll')
    
    return app

# Create app instance
app = create_app()

# Initialize database within app context
with app.app_context():
    # Import models for database creation
    from models import User, Employee, Payroll, PayrollItem, TaxBracket, AllowanceType, DeductionType
    
    # Create all tables
    db.create_all()
    
    # Import the user loader from models
    from models import load_user
    login_manager.user_loader(load_user)
