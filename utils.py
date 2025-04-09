import json
from datetime import datetime, date
from models import TaxBracket, Employee, Payroll, PayrollItem

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

def calculate_pension(basic_salary, pension_rate=8.0):
    """Calculate pension contribution (default 8% of basic salary in Nigeria)."""
    return basic_salary * (pension_rate / 100)

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
    
    # Process each employee
    for employee in employees:
        # Calculate monthly values
        monthly_basic_salary = employee.basic_salary
        
        # For demo purposes, we'll add some standard allowances
        # In a real system, these would be configured per employee
        housing_allowance = monthly_basic_salary * 0.1  # 10% of basic
        transport_allowance = monthly_basic_salary * 0.05  # 5% of basic
        
        # Calculate gross pay
        monthly_gross_pay = monthly_basic_salary + housing_allowance + transport_allowance
        
        # Calculate deductions
        monthly_pension = calculate_pension(monthly_basic_salary)
        monthly_nhf = calculate_nhf(monthly_basic_salary)
        
        # Calculate taxable income (annual)
        annual_basic = monthly_basic_salary * 12
        annual_gross = monthly_gross_pay * 12
        annual_pension = monthly_pension * 12
        annual_nhf = monthly_nhf * 12
        
        # In Nigeria, the first ₦200,000 or 1% of gross income (whichever is higher) is tax-exempt
        tax_relief = max(200000, annual_gross * 0.01)
        consolidated_relief = tax_relief + annual_pension + annual_nhf
        
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
                'Transport Allowance': transport_allowance
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
        total_allowances += (housing_allowance + transport_allowance)
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
