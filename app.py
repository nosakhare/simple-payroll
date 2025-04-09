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
    from routes.configuration import configuration as configuration_bp
    from routes.calculator import calculator as calculator_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(payroll_bp, url_prefix='/payroll')
    app.register_blueprint(configuration_bp, url_prefix='/configuration')
    app.register_blueprint(calculator_bp, url_prefix='/calculator')
    
    return app

# Create app instance
app = create_app()

# Initialize database within app context
with app.app_context():
    # Import models for database creation
    from models import User, Employee, Payroll, PayrollItem, TaxBracket, AllowanceType, DeductionType, SalaryConfiguration
    
    # Create all tables
    db.create_all()
    
    # Import the user loader from models
    from models import load_user
    login_manager.user_loader(load_user)
    
    # Create default salary configuration if none exists
    if not SalaryConfiguration.query.first():
        # Find an admin user to be the creator
        admin_user = User.query.filter_by(is_admin=True).first()
        
        # If no admin user, use the first user
        if not admin_user:
            admin_user = User.query.first()
        
        # Only create if we have a user
        if admin_user:
            default_config = SalaryConfiguration(
                name="Default Configuration",
                basic_salary_percentage=60.0,
                transport_allowance_percentage=10.0,
                housing_allowance_percentage=15.0,
                utility_allowance_percentage=5.0,
                meal_allowance_percentage=5.0,
                clothing_allowance_percentage=5.0,
                is_active=True,
                created_by_id=admin_user.id
            )
            db.session.add(default_config)
            db.session.commit()
            print("Created default salary configuration.")
