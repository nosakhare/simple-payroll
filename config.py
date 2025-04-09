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
