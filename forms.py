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

class PayrollProcessForm(FlaskForm):
    """Form for processing a payroll."""
    payroll_id = HiddenField('Payroll ID', validators=[DataRequired()])
    confirm = BooleanField('I confirm that all the information is correct', validators=[DataRequired()])
    submit = SubmitField('Process Payroll')

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

class SearchForm(FlaskForm):
    """Form for searching employees."""
    query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')
