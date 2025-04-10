"""
Migration script to add server_response field to the EmailLog model.
Run this once to update the database.
"""
import os
import sys
from sqlalchemy import create_engine, Column, Text, text

# Get the database URI from environment or use default
DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///nigerian_payroll.db')

# Create the engine
engine = create_engine(DATABASE_URI)
connection = engine.connect()

# Add the new column
try:
    print("Adding server_response column to email_log table...")
    if 'sqlite' in DATABASE_URI:
        # SQLite doesn't support adding columns with ALTER directly
        connection.execute(text("ALTER TABLE email_log ADD COLUMN server_response TEXT"))
    else:
        # PostgreSQL and others
        connection.execute(text("ALTER TABLE email_log ADD COLUMN IF NOT EXISTS server_response TEXT"))
    
    connection.commit()
    print("Migration completed successfully.")
except Exception as e:
    connection.rollback()
    print(f"Error during migration: {e}")
    sys.exit(1)
finally:
    connection.close()