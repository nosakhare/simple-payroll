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
    is_contract = db.Column(db.Boolean, default=False, nullable=False)
    
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
    status = db.Column(db.String(20), nullable=False, default='Draft')  # Draft, Active, Processing, Completed, Closed, Cancelled
    is_active = db.Column(db.Boolean, default=False)  # Flag to indicate active payroll period
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
    adjustment_items = db.relationship('PayrollAdjustment', backref='payroll', lazy=True)
    
    def __repr__(self):
        return f'<Payroll {self.name} [{self.status}]>'
        
    @staticmethod
    def check_for_overlap(start_date, end_date, exclude_id=None):
        """
        Check if there's any overlap with existing payroll periods.
        Returns True if overlap exists, False otherwise.
        """
        query = Payroll.query.filter(
            db.or_(
                # New period starts during an existing period
                db.and_(
                    Payroll.period_start <= start_date,
                    Payroll.period_end >= start_date
                ),
                # New period ends during an existing period
                db.and_(
                    Payroll.period_start <= end_date,
                    Payroll.period_end >= end_date
                ),
                # New period completely contains an existing period
                db.and_(
                    Payroll.period_start >= start_date,
                    Payroll.period_end <= end_date
                )
            )
        )
        
        # Exclude the current payroll if updating
        if exclude_id:
            query = query.filter(Payroll.id != exclude_id)
            
        return query.first() is not None
        
    def get_payroll_status_display(self):
        """Get a human-readable status for display purposes."""
        status_map = {
            'Draft': 'Draft',
            'Active': 'Active (In Progress)',
            'Processing': 'Processing',
            'Completed': 'Completed',
            'Closed': 'Closed',
            'Cancelled': 'Cancelled'
        }
        return status_map.get(self.status, self.status)

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
    
    # Flag to indicate if this item has been adjusted
    is_adjusted = db.Column(db.Boolean, default=False)
    
    # JSON fields for detailed breakdown
    allowances = db.Column(db.JSON, nullable=False, default=dict)
    deductions = db.Column(db.JSON, nullable=False, default=dict)
    tax_details = db.Column(db.JSON, nullable=False, default=dict)
    
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    adjustments = db.relationship('PayrollAdjustment', backref='payroll_item', lazy=True)
    
    def __repr__(self):
        return f'<PayrollItem {self.id} for Employee #{self.employee_id}>'
        
    def recalculate_net_pay(self):
        """Recalculate net pay after adjustments."""
        # Calculate total positive adjustments (bonuses and reimbursements)
        positive_adjustments = sum(adj.amount for adj in self.adjustments 
                                if adj.adjustment_type in ['bonus', 'reimbursement'])
        
        # Calculate total negative adjustments (deductions)
        negative_adjustments = sum(adj.amount for adj in self.adjustments 
                                if adj.adjustment_type == 'deduction')
        
        # Calculate total deductions
        total_deductions = (self.tax_amount + self.pension_amount + 
                            self.nhf_amount + self.other_deductions - negative_adjustments)
        
        # Net Pay = Gross Pay + Positive Adjustments - Total Deductions
        self.net_pay = self.gross_pay + positive_adjustments - total_deductions
        
        return self.net_pay


class PayrollAdjustment(db.Model):
    """Model for payroll adjustments (reimbursements, bonuses, or additional deductions)."""
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=False)
    payroll_item_id = db.Column(db.Integer, db.ForeignKey('payroll_item.id'), nullable=False)
    adjustment_type = db.Column(db.String(20), nullable=False)  # 'bonus', 'reimbursement', 'deduction'
    description = db.Column(db.String(256), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Positive for additions, negative for deductions
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='payroll_adjustments')
    
    def __repr__(self):
        return f'<PayrollAdjustment {self.id}: {self.adjustment_type} ₦{self.amount:,.2f}>'


class Payslip(db.Model):
    """Model for storing generated payslips."""
    id = db.Column(db.Integer, primary_key=True)
    payroll_item_id = db.Column(db.Integer, db.ForeignKey('payroll_item.id'), nullable=False)
    pdf_data = db.Column(db.LargeBinary, nullable=False)  # Store the PDF binary data
    filename = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    is_emailed = db.Column(db.Boolean, default=False)
    email_date = db.Column(db.DateTime, nullable=True)
    email_status = db.Column(db.String(20), nullable=True)  # 'sent', 'failed', 'pending'
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payroll_item = db.relationship('PayrollItem', backref='payslip')
    created_by = db.relationship('User', backref='generated_payslips')
    
    def __repr__(self):
        return f'<Payslip {self.id} for PayrollItem #{self.payroll_item_id}>'


class EmailLog(db.Model):
    """Model for tracking email deliveries."""
    id = db.Column(db.Integer, primary_key=True)
    payslip_id = db.Column(db.Integer, db.ForeignKey('payslip.id'), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'sent', 'failed', 'pending'
    error_message = db.Column(db.Text, nullable=True)
    send_date = db.Column(db.DateTime, default=datetime.utcnow)
    retry_count = db.Column(db.Integer, default=0)
    
    # Relationship
    payslip = db.relationship('Payslip', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.id} for Payslip #{self.payslip_id}>'


class CompanySettings(db.Model):
    """Model for storing company information that appears on payslips and reports."""
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False, default='Nigerian Payroll System')
    company_address = db.Column(db.String(256), nullable=False, default='123 Lagos Business District')
    company_city = db.Column(db.String(64), nullable=False, default='Lagos')
    company_state = db.Column(db.String(64), nullable=False, default='Lagos')
    company_country = db.Column(db.String(64), nullable=False, default='Nigeria')
    company_postal_code = db.Column(db.String(20), nullable=True)
    company_phone = db.Column(db.String(20), nullable=False, default='+234 123 456 7890')
    company_email = db.Column(db.String(120), nullable=False, default='payroll@nigerianpayroll.com')
    company_website = db.Column(db.String(120), nullable=True, default='www.nigerianpayroll.com')
    company_registration_number = db.Column(db.String(50), nullable=True)
    company_tax_id = db.Column(db.String(50), nullable=True)
    company_logo = db.Column(db.String(256), nullable=True, default='static/img/company_logo.svg')
    
    # Banking information removed as requested
    
    # Timestamps
    last_updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    last_updated_by = db.relationship('User', backref='company_settings_updates')
    
    def __repr__(self):
        return f'<CompanySettings {self.id}: {self.company_name}>'
    
    @classmethod
    def get_settings(cls):
        """Get the company settings or create default if none exists."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
