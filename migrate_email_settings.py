import sys
from app import create_app, db
from sqlalchemy import text

def add_email_config_columns():
    """Add email configuration columns to the CompanySettings table."""
    try:
        # Connect to the database
        app = create_app()
        with app.app_context():
            # Check if columns already exist to avoid errors
            columns_to_add = [
                {
                    "name": "mail_server",
                    "type": "VARCHAR(120)",
                    "default": "'smtp.gmail.com'"
                },
                {
                    "name": "mail_port",
                    "type": "INTEGER",
                    "default": "587"
                },
                {
                    "name": "mail_use_tls",
                    "type": "BOOLEAN",
                    "default": "TRUE"
                },
                {
                    "name": "mail_use_ssl",
                    "type": "BOOLEAN",
                    "default": "FALSE"
                },
                {
                    "name": "mail_username",
                    "type": "VARCHAR(120)",
                    "default": "NULL"
                },
                {
                    "name": "mail_password",
                    "type": "VARCHAR(120)",
                    "default": "NULL"
                },
                {
                    "name": "mail_default_sender",
                    "type": "VARCHAR(120)",
                    "default": "NULL"
                }
            ]
            
            # Execute the alter table statements
            for column in columns_to_add:
                try:
                    sql = text(f"ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS {column['name']} {column['type']} DEFAULT {column['default']}")
                    db.session.execute(sql)
                    print(f"Added column {column['name']} to company_settings table")
                except Exception as e:
                    print(f"Error adding column {column['name']}: {str(e)}")
            
            # Commit the changes
            db.session.commit()
            print("Migration completed successfully")
            return True, "Migration completed successfully"
            
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False, f"Migration failed: {str(e)}"

if __name__ == "__main__":
    success, message = add_email_config_columns()
    if not success:
        sys.exit(1)