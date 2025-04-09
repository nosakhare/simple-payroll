from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, 
    SelectField, DateField, FloatField, TextAreaField, EmailField,
    IntegerField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, 
    Optional, ValidationError, NumberRange
)
from datetime import date

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

class EmployeeForm(FlaskForm):
    """Form for adding or editing employee information."""
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'), 
        ('Female', 'Female'), 
        ('Other', 'Other')
    ], validators=[DataRequired()])
    marital_status = SelectField('Marital Status', choices=[
        ('Single', 'Single'), 
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed')
    ], validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=256)])
    city = StringField('City', validators=[DataRequired(), Length(max=64)])
    state = SelectField('State', choices=[
        ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'),
        ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'),
        ('Benue', 'Benue'), ('Borno', 'Borno'), ('Cross River', 'Cross River'),
        ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('FCT Abuja', 'FCT Abuja'),
        ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
        ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'),
        ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara')
    ], validators=[DataRequired()])
    
    # Employment Details
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=16)])
    department = StringField('Department', validators=[DataRequired(), Length(max=64)])
    position = StringField('Position', validators=[DataRequired(), Length(max=64)])
    date_hired = DateField('Date Hired', validators=[DataRequired()])
    employment_status = SelectField('Employment Status', choices=[
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Suspended', 'Suspended'),
        ('Terminated', 'Terminated')
    ], validators=[DataRequired()])
    is_contract = BooleanField('Contract Employee')
    
    # Bank Details
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=64)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(max=20)])
    
    # Tax Information
    tax_id = StringField('Tax ID (TIN)', validators=[Optional(), Length(max=20)])
    pension_id = StringField('Pension ID', validators=[Optional(), Length(max=20)])
    nhf_id = StringField('NHF ID', validators=[Optional(), Length(max=20)])
    
    # Salary Information
    basic_salary = FloatField('Basic Salary (₦)', validators=[DataRequired(), NumberRange(min=0)])
    
    submit = SubmitField('Save Employee')
    
    def validate_date_of_birth(self, field):
        if field.data >= date.today():
            raise ValidationError('Date of birth must be in the past')
        
        # Check if employee is at least 18 years old
        today = date.today()
        age = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
        if age < 18:
            raise ValidationError('Employee must be at least 18 years old')

class PayrollForm(FlaskForm):
    """Form for creating a new payroll run."""
    name = StringField('Payroll Name', validators=[DataRequired(), Length(max=64)])
    period_start = DateField('Period Start Date', validators=[DataRequired()])
    period_end = DateField('Period End Date', validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    submit = SubmitField('Create Payroll')
    
    def validate_period_end(self, field):
        if field.data < self.period_start.data:
            raise ValidationError('End date must be after start date')
            
    def validate_payment_date(self, field):
        if field.data < self.period_end.data:
            raise ValidationError('Payment date must be after end date')
            
    def validate(self, extra_validators=None):
        """Custom validation to check for payroll period overlaps."""
        from models import Payroll
        
        if not super().validate(extra_validators=extra_validators):
            return False
            
        # Check for overlapping payroll periods
        if Payroll.check_for_overlap(self.period_start.data, self.period_end.data):
            self.period_start.errors.append("This period overlaps with an existing payroll period.")
            return False
            
        return True

class PayrollStatusForm(FlaskForm):
    """Form for changing the status of a payroll period."""
    payroll_id = HiddenField('Payroll ID', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'),
        ('Active', 'Active'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Closed', 'Closed'),
        ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    confirm = BooleanField('I confirm this status change', validators=[DataRequired()])
    submit = SubmitField('Update Status')

class PayrollProcessForm(FlaskForm):
    """Form for processing a payroll."""
    payroll_id = HiddenField('Payroll ID', validators=[DataRequired()])
    confirm = BooleanField('I confirm that all the information is correct', validators=[DataRequired()])
    submit = SubmitField('Process Payroll')
    
class PayrollAdjustmentForm(FlaskForm):
    """Form for adding adjustments to a payroll item."""
    payroll_id = HiddenField('Payroll ID', validators=[DataRequired()])
    payroll_item_id = HiddenField('Payroll Item ID', validators=[DataRequired()])
    adjustment_type = SelectField('Adjustment Type', choices=[
        ('bonus', 'Bonus'),
        ('reimbursement', 'Reimbursement'),
        ('deduction', 'Deduction')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=256)])
    amount = FloatField('Amount (₦)', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Add Adjustment')

class TaxBracketForm(FlaskForm):
    """Form for adding or editing tax brackets."""
    lower_limit = FloatField('Lower Limit (₦)', validators=[DataRequired(), NumberRange(min=0)])
    upper_limit = FloatField('Upper Limit (₦)', validators=[Optional(), NumberRange(min=0)])
    rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Tax Bracket')
    
    def validate_upper_limit(self, field):
        if field.data and field.data <= self.lower_limit.data:
            raise ValidationError('Upper limit must be greater than lower limit')

class AllowanceTypeForm(FlaskForm):
    """Form for adding or editing allowance types."""
    name = StringField('Allowance Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=256)])
    is_taxable = BooleanField('Taxable')
    is_percentage = BooleanField('Calculate as Percentage of Basic Salary')
    default_value = FloatField('Default Value', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Allowance Type')

class DeductionTypeForm(FlaskForm):
    """Form for adding or editing deduction types."""
    name = StringField('Deduction Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=256)])
    is_percentage = BooleanField('Calculate as Percentage of Basic Salary')
    default_value = FloatField('Default Value', validators=[DataRequired(), NumberRange(min=0)])
    is_tax_deductible = BooleanField('Tax Deductible')
    submit = SubmitField('Save Deduction Type')

class CompensationChangeForm(FlaskForm):
    """Form for updating employee compensation."""
    basic_salary = FloatField('New Basic Salary (₦)', validators=[DataRequired(), NumberRange(min=0)])
    effective_date = DateField('Effective Date', validators=[DataRequired()])
    change_reason = TextAreaField('Reason for Change', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Update Compensation')
    
    def validate_effective_date(self, field):
        """Validate the effective date."""
        if field.data < date.today():
            raise ValidationError('Effective date must be today or in the future')


class SalaryConfigurationForm(FlaskForm):
    """Form for setting up salary component percentages."""
    name = StringField('Configuration Name', validators=[DataRequired(), Length(max=64)])
    basic_salary_percentage = FloatField('Basic Salary (%)', validators=[DataRequired(), NumberRange(min=1, max=100)])
    transport_allowance_percentage = FloatField('Transport Allowance (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    housing_allowance_percentage = FloatField('Housing Allowance (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    utility_allowance_percentage = FloatField('Utility Allowance (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    meal_allowance_percentage = FloatField('Meal Allowance (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    clothing_allowance_percentage = FloatField('Clothing Allowance (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Configuration')
    
    def validate(self, extra_validators=None):
        """Custom validation to ensure all percentages add up to 100%."""
        if not super().validate(extra_validators=extra_validators):
            return False
            
        total = (
            self.basic_salary_percentage.data +
            self.transport_allowance_percentage.data +
            self.housing_allowance_percentage.data +
            self.utility_allowance_percentage.data +
            self.meal_allowance_percentage.data +
            self.clothing_allowance_percentage.data
        )
        
        if abs(total - 100.0) > 0.01:  # Allow a small floating-point error
            self.basic_salary_percentage.errors.append(f'Total percentage must be exactly 100%. Current total: {total:.2f}%')
            return False
            
        return True

class SearchForm(FlaskForm):
    """Form for searching employees."""
    query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')

class StatutoryCalculatorForm(FlaskForm):
    """Form for statutory deductions test calculator."""
    basic_salary = FloatField('Basic Salary (₦)', validators=[DataRequired(), NumberRange(min=0)])
    transport_allowance = FloatField('Transport Allowance (₦)', validators=[Optional(), NumberRange(min=0)])
    housing_allowance = FloatField('Housing Allowance (₦)', validators=[Optional(), NumberRange(min=0)])
    other_allowances = FloatField('Other Allowances (₦)', validators=[Optional(), NumberRange(min=0)])
    is_contract = BooleanField('Is Contract Employee', default=False)
    submit = SubmitField('Calculate Statutory Deductions')
    
class ProrationCalculatorForm(FlaskForm):
    """Form for salary proration calculator."""
    amount = FloatField('Amount to Prorate (₦)', validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    month = SelectField('Month', choices=[
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'), (5, 'May'), (6, 'June'),
        (7, 'July'), (8, 'August'), (9, 'September'),
        (10, 'October'), (11, 'November'), (12, 'December')
    ], coerce=int, validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    submit = SubmitField('Calculate Prorated Amount')
    
    def validate_end_date(self, field):
        """Validate end date if provided."""
        if field.data and field.data < self.start_date.data:
            raise ValidationError('End date must be after start date')


class CompanySettingsForm(FlaskForm):
    """Form for editing company settings."""
    # Company Information
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    company_address = TextAreaField('Address', validators=[DataRequired(), Length(max=256)])
    company_city = StringField('City', validators=[DataRequired(), Length(max=64)])
    company_state = SelectField('State', choices=[
        ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'),
        ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'),
        ('Benue', 'Benue'), ('Borno', 'Borno'), ('Cross River', 'Cross River'),
        ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('FCT Abuja', 'FCT Abuja'),
        ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
        ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'),
        ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara')
    ], validators=[DataRequired()])
    company_country = StringField('Country', validators=[DataRequired(), Length(max=64)], default='Nigeria')
    company_postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    company_phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    company_email = EmailField('Email', validators=[DataRequired(), Email()])
    company_website = StringField('Website', validators=[Optional(), Length(max=120)])
    company_registration_number = StringField('Registration Number', validators=[Optional(), Length(max=50)])
    company_tax_id = StringField('Tax ID', validators=[Optional(), Length(max=50)])
    
    # Banking Information fields removed as requested
    
    # Logo (handled separately)
    submit = SubmitField('Save Settings')
