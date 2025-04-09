import json
import datetime
from datetime import datetime, date, timedelta
from models import TaxBracket, Employee, Payroll, PayrollItem, SalaryConfiguration

def calculate_age(birth_date):
    """Calculate age based on date of birth."""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def format_currency(amount):
    """Format a number as Nigerian Naira currency."""
    if amount is None:
        return "₦0.00"
    return f"₦{amount:,.2f}"

def calculate_paye_tax(annual_taxable_income):
    """
    Calculate PAYE (Pay As You Earn) tax based on Nigerian tax brackets.
    Returns the annual tax amount.
    
    Nigerian PAYE tax structure:
    - First ₦300,000: 7%
    - Next ₦300,000: 11%
    - Next ₦500,000: 15%
    - Next ₦500,000: 19%
    - Next ₦1,600,000: 21%
    - Above ₦3,200,000: 24%
    """
    tax_brackets = TaxBracket.query.order_by(TaxBracket.lower_limit).all()
    
    # If no tax brackets are defined in the database, use default Nigerian tax brackets
    if not tax_brackets:
        tax_brackets = [
            {'lower_limit': 0, 'upper_limit': 300000, 'rate': 7},
            {'lower_limit': 300000, 'upper_limit': 600000, 'rate': 11},
            {'lower_limit': 600000, 'upper_limit': 1100000, 'rate': 15},
            {'lower_limit': 1100000, 'upper_limit': 1600000, 'rate': 19},
            {'lower_limit': 1600000, 'upper_limit': 3200000, 'rate': 21},
            {'lower_limit': 3200000, 'upper_limit': None, 'rate': 24}
        ]
    
    total_tax = 0
    remaining_income = annual_taxable_income
    tax_details = []
    
    for bracket in tax_brackets:
        lower = bracket.lower_limit if hasattr(bracket, 'lower_limit') else bracket['lower_limit']
        upper = bracket.upper_limit if hasattr(bracket, 'upper_limit') else bracket['upper_limit']
        rate = bracket.rate if hasattr(bracket, 'rate') else bracket['rate']
        
        if remaining_income <= 0:
            break
            
        if upper is None:  # Highest bracket
            taxable_in_bracket = remaining_income
        else:
            taxable_in_bracket = min(remaining_income, upper - lower)
            
        tax_in_bracket = taxable_in_bracket * (rate / 100)
        total_tax += tax_in_bracket
        
        tax_details.append({
            'bracket': f"{format_currency(lower)} - {format_currency(upper) if upper else 'above'}",
            'rate': f"{rate}%",
            'taxable_amount': format_currency(taxable_in_bracket),
            'tax': format_currency(tax_in_bracket)
        })
        
        remaining_income -= taxable_in_bracket
    
    return total_tax, tax_details

def calculate_pension(basic_salary, transport_allowance=0, housing_allowance=0, is_contract=False, pension_rate=8.0):
    """
    Calculate pension contribution according to Nigerian regulations.
    
    Pension is calculated as 8% of (basic + transport + housing) for eligible employees.
    Contract employees and those earning below ₦30,000 are exempt from pension contributions.
    """
    monthly_salary = basic_salary + transport_allowance + housing_allowance
    
    # Contract employees are exempt from pension
    if is_contract:
        return 0.0
    
    # Employees earning below ₦30,000 are exempt from pension
    if monthly_salary < 30000:
        return 0.0
    
    # Calculate pension contribution
    return monthly_salary * (pension_rate / 100)

def calculate_employer_pension(basic_salary, transport_allowance=0, housing_allowance=0, is_contract=False, pension_rate=10.0):
    """
    Calculate employer pension contribution according to Nigerian regulations.
    
    Employer pension is calculated as 10% of (basic + transport + housing) for eligible employees.
    """
    monthly_salary = basic_salary + transport_allowance + housing_allowance
    
    # Contract employees are exempt from pension
    if is_contract:
        return 0.0
    
    # Employees earning below ₦30,000 are exempt from pension
    if monthly_salary < 30000:
        return 0.0
    
    # Calculate employer pension contribution
    return monthly_salary * (pension_rate / 100)

def calculate_consolidated_relief(annual_gross_income, annual_pension=0, annual_nhf=0):
    """
    Calculate Consolidated Relief Allowance (CRA) according to Nigerian regulations.
    
    CRA is the higher of ₦200,000 or 1% of gross income, plus pension and NHF contributions.
    """
    base_relief = max(200000, annual_gross_income * 0.01)
    return base_relief + annual_pension + annual_nhf

def calculate_nhf(basic_salary, nhf_rate=2.5):
    """Calculate National Housing Fund contribution (default 2.5% of basic salary)."""
    return basic_salary * (nhf_rate / 100)

def process_payroll(payroll_id):
    """
    Process a payroll run by calculating pay for all employees.
    
    This will:
    1. Get all active employees
    2. Calculate their gross pay, deductions, and net pay
    3. Create payroll items for each employee
    4. Update the payroll totals
    """
    payroll = Payroll.query.get(payroll_id)
    if not payroll or payroll.status != 'Draft':
        return False, "Invalid payroll or payroll is not in draft status"
    
    # Get all active employees
    employees = Employee.query.filter_by(employment_status='Active').all()
    
    # Initialize payroll totals
    total_basic = 0
    total_allowances = 0
    total_deductions = 0
    total_tax = 0
    total_net = 0
    
    # Get active salary configuration
    salary_config = SalaryConfiguration.query.filter_by(is_active=True).first()
    
    # If no active configuration, use default percentages
    if not salary_config:
        basic_percentage = 60.0
        transport_percentage = 10.0
        housing_percentage = 15.0
        utility_percentage = 5.0
        meal_percentage = 5.0
        clothing_percentage = 5.0
    else:
        basic_percentage = salary_config.basic_salary_percentage
        transport_percentage = salary_config.transport_allowance_percentage
        housing_percentage = salary_config.housing_allowance_percentage
        utility_percentage = salary_config.utility_allowance_percentage
        meal_percentage = salary_config.meal_allowance_percentage
        clothing_percentage = salary_config.clothing_allowance_percentage
    
    # Process each employee
    for employee in employees:
        # Calculate total monthly compensation
        total_compensation = employee.basic_salary * (100.0 / basic_percentage)
        
        # Calculate salary components based on configuration percentages
        monthly_basic_salary = total_compensation * (basic_percentage / 100.0)
        transport_allowance = total_compensation * (transport_percentage / 100.0)
        housing_allowance = total_compensation * (housing_percentage / 100.0)
        utility_allowance = total_compensation * (utility_percentage / 100.0)
        meal_allowance = total_compensation * (meal_percentage / 100.0)
        clothing_allowance = total_compensation * (clothing_percentage / 100.0)
        
        # Calculate gross pay (sum of all components)
        monthly_gross_pay = (
            monthly_basic_salary + 
            transport_allowance + 
            housing_allowance + 
            utility_allowance +
            meal_allowance +
            clothing_allowance
        )
        
        # Calculate deductions - use contract status (assume regular employees)
        is_contract = employee.employment_status == 'Contract'
        monthly_pension = calculate_pension(
            monthly_basic_salary, 
            transport_allowance, 
            housing_allowance, 
            is_contract
        )
        monthly_nhf = calculate_nhf(monthly_basic_salary)
        
        # Calculate employer contributions (for reporting purposes)
        monthly_employer_pension = calculate_employer_pension(
            monthly_basic_salary, 
            transport_allowance, 
            housing_allowance, 
            is_contract
        )
        
        # Calculate taxable income (annual)
        annual_basic = monthly_basic_salary * 12
        annual_gross = monthly_gross_pay * 12
        annual_pension = monthly_pension * 12
        annual_nhf = monthly_nhf * 12
        
        # Calculate consolidated relief allowance
        consolidated_relief = calculate_consolidated_relief(annual_gross, annual_pension, annual_nhf)
        
        annual_taxable_income = max(0, annual_gross - consolidated_relief)
        
        # Calculate PAYE tax
        annual_tax, tax_details = calculate_paye_tax(annual_taxable_income)
        monthly_tax = annual_tax / 12
        
        # Calculate net pay
        total_monthly_deductions = monthly_pension + monthly_nhf + monthly_tax
        monthly_net_pay = monthly_gross_pay - total_monthly_deductions
        
        # Create payroll item for this employee
        payroll_item = PayrollItem(
            payroll_id=payroll.id,
            employee_id=employee.id,
            basic_salary=monthly_basic_salary,
            gross_pay=monthly_gross_pay,
            taxable_income=annual_taxable_income / 12,  # Monthly taxable income
            tax_amount=monthly_tax,
            pension_amount=monthly_pension,
            nhf_amount=monthly_nhf,
            other_deductions=0.0,
            net_pay=monthly_net_pay,
            allowances=json.dumps({
                'Housing Allowance': housing_allowance,
                'Transport Allowance': transport_allowance,
                'Utility Allowance': utility_allowance,
                'Meal Allowance': meal_allowance,
                'Clothing Allowance': clothing_allowance
            }),
            deductions=json.dumps({
                'Pension': monthly_pension,
                'NHF': monthly_nhf,
                'PAYE Tax': monthly_tax
            }),
            tax_details=json.dumps({
                'Annual Basic Salary': annual_basic,
                'Annual Gross Income': annual_gross,
                'Consolidated Relief': consolidated_relief,
                'Annual Taxable Income': annual_taxable_income,
                'Annual Tax': annual_tax,
                'Monthly Tax': monthly_tax,
                'Tax Brackets': tax_details
            })
        )
        
        # Add to database
        from app import db
        db.session.add(payroll_item)
        
        # Update payroll totals
        total_basic += monthly_basic_salary
        total_allowances += (
            housing_allowance + 
            transport_allowance + 
            utility_allowance + 
            meal_allowance + 
            clothing_allowance
        )
        total_deductions += (monthly_pension + monthly_nhf)
        total_tax += monthly_tax
        total_net += monthly_net_pay
    
    # Update payroll record
    payroll.total_basic_salary = total_basic
    payroll.total_allowances = total_allowances
    payroll.total_deductions = total_deductions
    payroll.total_tax = total_tax
    payroll.total_net_pay = total_net
    payroll.status = 'Completed'
    payroll.date_updated = datetime.utcnow()
    
    # Commit changes to database
    db.session.commit()
    
    return True, f"Successfully processed payroll for {len(employees)} employees"

def generate_payslip_data(payroll_item_id):
    """Generate data for a payslip based on a payroll item."""
    from app import db
    
    # Get the payroll item
    payroll_item = PayrollItem.query.get(payroll_item_id)
    if not payroll_item:
        return None
    
    # Get related data
    employee = Employee.query.get(payroll_item.employee_id)
    payroll = Payroll.query.get(payroll_item.payroll_id)
    
    # Parse JSON fields
    allowances = json.loads(payroll_item.allowances)
    deductions = json.loads(payroll_item.deductions)
    tax_details = json.loads(payroll_item.tax_details)
    
    # Build payslip data
    payslip = {
        'payroll_item': payroll_item,
        'employee': employee,
        'payroll': payroll,
        'allowances': allowances,
        'deductions': deductions,
        'tax_details': tax_details,
        'generated_on': datetime.utcnow().strftime('%d %B, %Y'),
        'payment_method': 'Bank Transfer',
    }
    
    return payslip

def count_working_days(start_date, end_date):
    """
    Count working days (Monday-Friday) between two dates, inclusive.
    
    Args:
        start_date: datetime.date object representing the start date
        end_date: datetime.date object representing the end date
        
    Returns:
        Number of working days between start_date and end_date, inclusive
    """
    # Ensure start_date is before or equal to end_date
    if start_date > end_date:
        return 0
    
    # Initialize counter
    working_days = 0
    
    # Iterate through each day
    current_date = start_date
    while current_date <= end_date:
        # Weekday returns 0 (Monday) through 6 (Sunday)
        if current_date.weekday() < 5:  # 0-4 are Monday to Friday
            working_days += 1
        
        # Move to next day
        current_date += datetime.timedelta(days=1)
    
    return working_days

def calculate_proration_factor(start_date, end_date, month=None, year=None):
    """
    Calculate proration factor based on working days.
    
    Args:
        start_date: datetime.date object of the employee's start date
        end_date: datetime.date object of the employee's end date or None
        month: Month for which to calculate the proration (1-12)
        year: Year for which to calculate the proration
        
    Returns:
        Float between 0 and 1 representing the proration factor
    """
    # Use current month and year if not specified
    today = datetime.date.today()
    if month is None:
        month = today.month
    if year is None:
        year = today.year
    
    # Get the first and last day of the specified month
    first_day = datetime.date(year, month, 1)
    if month == 12:
        last_day = datetime.date(year, 12, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    # Count total working days in the month
    total_working_days = count_working_days(first_day, last_day)
    
    # Adjust start and end dates to be within the month
    if start_date and start_date > first_day:
        period_start = start_date
    else:
        period_start = first_day
    
    if end_date and end_date < last_day:
        period_end = end_date
    else:
        period_end = last_day
    
    # Count working days in the period
    period_working_days = count_working_days(period_start, period_end)
    
    # Calculate proration factor
    if total_working_days == 0:  # Avoid division by zero
        return 0.0
    
    return period_working_days / total_working_days

def prorate_amount(amount, start_date=None, end_date=None, month=None, year=None):
    """
    Prorate an amount based on working days.
    
    Args:
        amount: The amount to be prorated
        start_date: Employee's start date (or None if not applicable)
        end_date: Employee's end date (or None if not applicable)
        month: Month for which to calculate the proration (1-12)
        year: Year for which to calculate the proration
        
    Returns:
        Prorated amount
    """
    # If no start or end date, return the full amount
    if not start_date and not end_date:
        return amount
    
    # Calculate proration factor
    factor = calculate_proration_factor(start_date, end_date, month, year)
    
    # Apply proration
    return amount * factor
    
def calculate_statutory_deductions(basic_salary, transport_allowance=0, housing_allowance=0, other_allowances=0, is_contract=False):
    """
    Calculator function for statutory deductions.
    
    Args:
        basic_salary: Monthly basic salary
        transport_allowance: Monthly transport allowance
        housing_allowance: Monthly housing allowance
        other_allowances: Monthly other allowances
        is_contract: Whether employee is on contract
        
    Returns:
        Dictionary with all calculated values
    """
    # Calculate monthly values
    monthly_gross = basic_salary + transport_allowance + housing_allowance + other_allowances
    
    # Calculate pension (employee and employer)
    monthly_pension = calculate_pension(
        basic_salary, 
        transport_allowance, 
        housing_allowance, 
        is_contract
    )
    
    monthly_employer_pension = calculate_employer_pension(
        basic_salary, 
        transport_allowance, 
        housing_allowance, 
        is_contract
    )
    
    # Calculate NHF
    monthly_nhf = calculate_nhf(basic_salary)
    
    # Calculate annualized values
    annual_gross = monthly_gross * 12
    annual_pension = monthly_pension * 12
    annual_nhf = monthly_nhf * 12
    
    # Calculate consolidated relief allowance
    consolidated_relief = calculate_consolidated_relief(annual_gross, annual_pension, annual_nhf)
    
    # Calculate taxable income
    annual_taxable_income = max(0, annual_gross - consolidated_relief)
    
    # Calculate PAYE tax
    annual_tax, tax_details = calculate_paye_tax(annual_taxable_income)
    monthly_tax = annual_tax / 12
    
    # Calculate total deductions and net pay
    total_monthly_deductions = monthly_pension + monthly_nhf + monthly_tax
    monthly_net_pay = monthly_gross - total_monthly_deductions
    
    # Build result dictionary
    return {
        # Monthly values
        'monthly_basic': basic_salary,
        'monthly_transport': transport_allowance,
        'monthly_housing': housing_allowance,
        'monthly_other': other_allowances,
        'monthly_gross': monthly_gross,
        'monthly_pension': monthly_pension,
        'monthly_employer_pension': monthly_employer_pension,
        'monthly_nhf': monthly_nhf,
        'monthly_tax': monthly_tax,
        'total_monthly_deductions': total_monthly_deductions,
        'monthly_net_pay': monthly_net_pay,
        
        # Annual values
        'annual_gross': annual_gross,
        'consolidated_relief': consolidated_relief,
        'annual_taxable_income': annual_taxable_income,
        'annual_tax': annual_tax,
        'tax_details': tax_details,
        
        # Status
        'is_contract': is_contract,
        'is_pension_exempt': is_contract or monthly_gross < 30000
    }
