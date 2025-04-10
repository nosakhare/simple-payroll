"""
Migration script to add payroll_id field to the EmailLog model.
Run this once to update the database.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get the database URI from environment or use default
DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///nigerian_payroll.db')

# Create the engine
engine = create_engine(DATABASE_URI)
connection = engine.connect()

# Add the new column
try:
    print("Adding payroll_id column to email_log table...")
    if 'sqlite' in DATABASE_URI:
        # SQLite doesn't support adding columns with ALTER directly
        connection.execute(text("ALTER TABLE email_log ADD COLUMN payroll_id INTEGER"))
    else:
        # PostgreSQL and others
        connection.execute(text("ALTER TABLE email_log ADD COLUMN IF NOT EXISTS payroll_id INTEGER"))
    
    # Add the foreign key relationship in a separate step if needed
    # This isn't directly supported in SQLite, but works for other databases
    if 'sqlite' not in DATABASE_URI:
        connection.execute(text("ALTER TABLE email_log ADD CONSTRAINT fk_email_log_payroll "
                            "FOREIGN KEY (payroll_id) REFERENCES payroll (id)"))
    
    connection.commit()
    print("Migration completed successfully.")
except Exception as e:
    connection.rollback()
    print(f"Error during migration: {e}")
    sys.exit(1)
finally:
    connection.close()