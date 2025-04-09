from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

def load_user(user_id):
    """User loader function for Flask-Login."""
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """User model for authentication and system access."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """Set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check user password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Employee(db.Model):
    """Employee model for storing employee information."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(16), unique=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(64), nullable=False)
    
    # Employment details
    department = db.Column(db.String(64), nullable=False)
    position = db.Column(db.String(64), nullable=False)
    date_hired = db.Column(db.Date, nullable=False)
    employment_status = db.Column(db.String(20), nullable=False, default='Active')
    
    # Bank details
    bank_name = db.Column(db.String(64), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    
    # Tax information
    tax_id = db.Column(db.String(20), nullable=True)
    pension_id = db.Column(db.String(20), nullable=True)
    nhf_id = db.Column(db.String(20), nullable=True)  # National Housing Fund
    
    # Salary information
    basic_salary = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payroll_items = db.relationship('PayrollItem', backref='employee', lazy=True)
    compensation_history = db.relationship('CompensationHistory', backref='employee', lazy=True, order_by='CompensationHistory.effective_date.desc()')
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.first_name} {self.last_name}>'
    
    def full_name(self):
        """Get employee's full name."""
        return f"{self.first_name} {self.last_name}"

class TaxBracket(db.Model):
    """Tax bracket model for Nigeria's PAYE tax system."""
    id = db.Column(db.Integer, primary_key=True)
    lower_limit = db.Column(db.Float, nullable=False)
    upper_limit = db.Column(db.Float, nullable=True)  # Null for the highest bracket
    rate = db.Column(db.Float, nullable=False)  # Percentage (e.g., 7.0 for 7%)
    
    def __repr__(self):
        if self.upper_limit:
            return f'<TaxBracket {self.lower_limit} - {self.upper_limit} @ {self.rate}%>'
        else:
            return f'<TaxBracket {self.lower_limit}+ @ {self.rate}%>'

class AllowanceType(db.Model):
    """Model for types of allowances available in the system."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    is_taxable = db.Column(db.Boolean, default=True)
    is_percentage = db.Column(db.Boolean, default=False)  # If True, calculated as % of basic salary
    default_value = db.Column(db.Float, default=0.0)  # Default amount or percentage
    
    def __repr__(self):
        return f'<AllowanceType {self.name}>'

class DeductionType(db.Model):
    """Model for types of deductions available in the system."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    is_percentage = db.Column(db.Boolean, default=False)  # If True, calculated as % of basic salary
    default_value = db.Column(db.Float, default=0.0)  # Default amount or percentage
    is_tax_deductible = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<DeductionType {self.name}>'

class Payroll(db.Model):
    """Payroll model representing a payroll run for a specific period."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Draft')  # Draft, Processing, Completed, Cancelled
    total_basic_salary = db.Column(db.Float, default=0.0)
    total_allowances = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    total_tax = db.Column(db.Float, default=0.0)
    total_net_pay = db.Column(db.Float, default=0.0)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='payrolls')
    payroll_items = db.relationship('PayrollItem', backref='payroll', lazy=True)
    
    def __repr__(self):
        return f'<Payroll {self.name} [{self.status}]>'

class CompensationHistory(db.Model):
    """Model for tracking employee compensation history and changes."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    basic_salary = db.Column(db.Float, nullable=False)
    
    # Record who made the change and when
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    change_reason = db.Column(db.String(256), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    changed_by = db.relationship('User', backref='compensation_changes')
    
    def __repr__(self):
        return f'<CompensationHistory {self.id} for Employee #{self.employee_id} @{self.effective_date}>'


class SalaryConfiguration(db.Model):
    """Model for storing salary component configuration percentages."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    basic_salary_percentage = db.Column(db.Float, nullable=False)
    transport_allowance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    housing_allowance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    utility_allowance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    meal_allowance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    clothing_allowance_percentage = db.Column(db.Float, nullable=False, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='salary_configurations')
    
    def __repr__(self):
        return f'<SalaryConfiguration {self.id}: {self.name}>'
    
    @property
    def total_percentage(self):
        """Get the sum of all percentage allocations."""
        return (
            self.basic_salary_percentage +
            self.transport_allowance_percentage +
            self.housing_allowance_percentage +
            self.utility_allowance_percentage +
            self.meal_allowance_percentage +
            self.clothing_allowance_percentage
        )

class PayrollItem(db.Model):
    """Model for individual employee payroll records within a payroll run."""
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    basic_salary = db.Column(db.Float, nullable=False)
    
    # Computed amounts
    gross_pay = db.Column(db.Float, nullable=False)
    taxable_income = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    pension_amount = db.Column(db.Float, nullable=False)
    nhf_amount = db.Column(db.Float, nullable=False)  # National Housing Fund
    other_deductions = db.Column(db.Float, nullable=False, default=0.0)
    net_pay = db.Column(db.Float, nullable=False)
    
    # JSON fields for detailed breakdown
    allowances = db.Column(db.JSON, nullable=False, default=dict)
    deductions = db.Column(db.JSON, nullable=False, default=dict)
    tax_details = db.Column(db.JSON, nullable=False, default=dict)
    
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PayrollItem {self.id} for Employee #{self.employee_id}>'
