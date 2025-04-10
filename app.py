import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create declarative base for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

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
    mail.init_app(app)
    
    # Configure login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register a function to update mail config after db has been initialized
    @app.before_request
    def before_request():
        try:
            # Only try to update mail config if db is initialized and not in a db migration
            if 'migrate' not in sys.argv[0] and db.get_engine(app) is not None:
                from email_config import update_mail_config
                # Update mail configuration from database
                update_mail_config()
        except Exception as e:
            app.logger.error(f"Error loading company settings: {str(e)}")
    
    # Register blueprints
    from routes.main import main as main_bp
    from routes.auth import auth as auth_bp
    from routes.employees import employees as employees_bp
    from routes.payroll import payroll as payroll_bp
    from routes.configuration import configuration as configuration_bp
    from routes.calculator import calculator as calculator_bp
    from routes.test import test as test_bp
    from routes.payslips import payslips as payslips_bp
    from routes.settings import settings as settings_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(payroll_bp, url_prefix='/payroll')
    app.register_blueprint(configuration_bp, url_prefix='/configuration')
    app.register_blueprint(calculator_bp, url_prefix='/calculator')
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(payslips_bp, url_prefix='/payslips')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Add custom Jinja filters
    import json
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Convert a JSON string to a Python dictionary."""
        return json.loads(value) if value else {}
        
    # Add company settings to all templates
    @app.context_processor
    def inject_company_settings():
        from models import CompanySettings
        """Make company settings available to all templates."""
        try:
            settings = CompanySettings.get_settings()
            # Update app config with company settings so they're available through config object
            app.config['COMPANY_NAME'] = settings.company_name
            app.config['COMPANY_ADDRESS'] = settings.company_address
            app.config['COMPANY_CITY'] = settings.company_city
            app.config['COMPANY_COUNTRY'] = settings.company_country
            app.config['COMPANY_EMAIL'] = settings.company_email
            app.config['COMPANY_PHONE'] = settings.company_phone
            app.config['COMPANY_WEBSITE'] = settings.company_website
            app.config['COMPANY_LOGO'] = settings.company_logo
            
            return {
                'company_settings': settings
            }
        except Exception as e:
            # In case of error, return empty dict
            print(f"Error loading company settings: {e}")
            return {'company_settings': None}
    
    return app

# Create app instance
app = create_app()

# Initialize database within app context
with app.app_context():
    # Import models for database creation
    from models import (
        User, Employee, Payroll, PayrollItem, TaxBracket, AllowanceType, 
        DeductionType, SalaryConfiguration, PayrollAdjustment, Payslip, EmailLog,
        CompanySettings
    )
    
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
