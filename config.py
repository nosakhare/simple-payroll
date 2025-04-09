import os

class Config:
    """Configuration settings for the application."""
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-key-for-development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///nigerian_payroll.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    DEBUG = True
    
    # Flask-Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'payroll@nigerianpayroll.com')
    
    # Company information for payslips
    COMPANY_NAME = 'Nigerian Payroll System'
    COMPANY_ADDRESS = '123 Lagos Business District'
    COMPANY_CITY = 'Lagos'
    COMPANY_COUNTRY = 'Nigeria'
    COMPANY_EMAIL = 'payroll@nigerianpayroll.com'
    COMPANY_PHONE = '+234 123 456 7890'
    COMPANY_WEBSITE = 'www.nigerianpayroll.com'
    COMPANY_LOGO = 'static/img/company_logo.svg'  # Path to company logo
