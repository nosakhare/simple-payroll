from app import app, db
from sqlalchemy import text

def add_bank_id_column():
    """Add the bank_id column to the Employee table."""
    with app.app_context():
        # Check if the column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('employee')]
        
        if 'bank_id' not in columns:
            # Add the column
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE employee ADD COLUMN bank_id INTEGER'))
                conn.commit()
            print("Added bank_id column to employee table")
            
            # Add the foreign key constraint
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE employee ADD CONSTRAINT fk_employee_bank_id FOREIGN KEY (bank_id) REFERENCES bank (id)'))
                conn.commit()
            print("Added foreign key constraint")
        else:
            print("bank_id column already exists")

if __name__ == "__main__":
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        print("Created all tables")
        
        # Add bank_id column to Employee table
        add_bank_id_column()