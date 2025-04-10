"""
Email configuration utility to update Flask-Mail settings from database.
"""
from flask import current_app
from flask_mail import Mail

def update_mail_config():
    """
    Update the Flask-Mail configuration from the database settings.
    
    This function should be called after the application and database 
    are fully initialized to update the mail configuration with the 
    values stored in the CompanySettings table.
    """
    try:
        # Import here to avoid circular imports
        from models import CompanySettings
        
        # Get company settings
        settings = CompanySettings.get_settings()
        
        if settings:
            # Update only if values are not None
            if settings.mail_server:
                current_app.config['MAIL_SERVER'] = settings.mail_server
            
            if settings.mail_port:
                current_app.config['MAIL_PORT'] = settings.mail_port
            
            if settings.mail_use_tls is not None:
                current_app.config['MAIL_USE_TLS'] = settings.mail_use_tls
            
            if settings.mail_use_ssl is not None:
                current_app.config['MAIL_USE_SSL'] = settings.mail_use_ssl
            
            if settings.mail_username:
                current_app.config['MAIL_USERNAME'] = settings.mail_username
            
            # Try environment variable first, fall back to database
            mail_password = os.environ.get('MAIL_PASSWORD')
            if mail_password:
                current_app.config['MAIL_PASSWORD'] = mail_password
            elif settings.mail_password:
                current_app.config['MAIL_PASSWORD'] = settings.mail_password
            
            if settings.mail_default_sender:
                current_app.config['MAIL_DEFAULT_SENDER'] = settings.mail_default_sender
            else:
                # Use company email as default sender if no specific sender is set
                current_app.config['MAIL_DEFAULT_SENDER'] = settings.company_email
            
            # Get the mail extension and update it
            mail = current_app.extensions.get('mail')
            if mail and isinstance(mail, Mail):
                # Reinitialize the mail extension with the new configuration
                mail.init_app(current_app)
                
            return True, "Mail configuration updated successfully"
        
        return False, "Company settings not found"
        
    except Exception as e:
        print(f"Error updating mail configuration: {str(e)}")
        return False, f"Error updating mail configuration: {str(e)}"