from app import app, db
from models import User, Employee, Payroll, PayrollItem, PayrollAdjustment, TaxBracket, AllowanceType, DeductionType, SalaryConfiguration, CompensationHistory
import sqlalchemy as sa
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.sql import text

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)

def drop_column(table_name, column_name):
    """Drop a column from a table."""
    if check_column_exists(table_name, column_name):
        print(f"Dropping column {column_name} from {table_name}")
        
        if db.engine.name == 'postgresql':
            # PostgreSQL supports ALTER TABLE DROP COLUMN directly
            stmt = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            db.session.execute(text(stmt))
            db.session.commit()
            return True
        else:
            # SQLite doesn't support dropping columns directly.
            # For SQLite, we'd need to recreate the table without the column,
            # which is more complex and not implemented here.
            print(f"Dropping columns in SQLite is not supported. Skipping {column_name}.")
            return False
    return False

def add_column(table_name, column):
    """Add a column to a table."""
    if not check_column_exists(table_name, column.name):
        print(f"Adding column {column.name} to {table_name}")
        column_name = column.name
        column_type = column.type
        
        # Add default value if specified
        default_value = ""
        if column.default is not None:
            # Get the default value
            if column.default.is_scalar:
                if isinstance(column.default.arg, bool):
                    default_value = f" DEFAULT {str(column.default.arg).lower()}"
                elif isinstance(column.default.arg, (int, float)):
                    default_value = f" DEFAULT {column.default.arg}"
                else:
                    default_value = f" DEFAULT '{column.default.arg}'"
        
        # Add nullable constraint
        nullable = ""
        if not column.nullable:
            nullable = " NOT NULL"
            
        # Create the ALTER TABLE statement
        if isinstance(column_type, sa.Boolean):
            # PostgreSQL uses boolean type
            if db.engine.name == 'postgresql':
                stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} BOOLEAN{default_value}{nullable}"
            else:
                # SQLite uses INTEGER for boolean
                stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER{default_value}{nullable}"
        else:
            stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_value}{nullable}"
        
        # Execute the statement
        db.session.execute(sa.text(stmt))
        db.session.commit()
        return True
    return False

# Migrate database schema
def migrate_database():
    """Run database migrations."""
    with app.app_context():
        print("Starting database migration...")
        
        # Ensure all tables exist
        db.create_all()
        
        # Check and add PayrollItem.is_adjusted column
        add_column('payroll_item', PayrollItem.__table__.c.is_adjusted)
        
        # Check and add Payroll.is_active column
        add_column('payroll', Payroll.__table__.c.is_active)
        
        # Check and add Employee.is_contract column
        add_column('employee', Employee.__table__.c.is_contract)
        
        # Drop banking information columns from CompanySettings as requested
        drop_column('company_settings', 'bank_name')
        drop_column('company_settings', 'bank_account_number')
        drop_column('company_settings', 'bank_account_name')
        drop_column('company_settings', 'bank_branch')
        drop_column('company_settings', 'bank_sort_code')
        
        print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate_database()