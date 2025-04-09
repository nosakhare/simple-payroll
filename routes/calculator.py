from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from datetime import date

from forms import StatutoryCalculatorForm, ProrationCalculatorForm
from utils import calculate_statutory_deductions, format_currency, prorate_amount

calculator = Blueprint('calculator', __name__)

@calculator.route('/', methods=['GET', 'POST'])
@login_required
def statutory():
    """Statutory deductions calculator."""
    form = StatutoryCalculatorForm()
    
    # Initialize results
    results = None
    
    if form.validate_on_submit():
        # Get form data
        basic_salary = form.basic_salary.data
        transport_allowance = form.transport_allowance.data if form.transport_allowance.data is not None else 0
        housing_allowance = form.housing_allowance.data if form.housing_allowance.data is not None else 0
        other_allowances = form.other_allowances.data if form.other_allowances.data is not None else 0
        is_contract = form.is_contract.data
        
        # Calculate statutory deductions
        results = calculate_statutory_deductions(
            basic_salary, 
            transport_allowance, 
            housing_allowance, 
            other_allowances, 
            is_contract
        )
        
        # Flash a message
        flash('Statutory deductions calculated successfully.', 'success')
    
    return render_template(
        'calculator/statutory.html',
        form=form,
        results=results,
        format_currency=format_currency
    )

@calculator.route('/api/calculate', methods=['POST'])
@login_required
def api_calculate():
    """API endpoint for calculating statutory deductions."""
    # Get form data
    data = request.json
    
    # Validate inputs
    if not data or 'basic_salary' not in data:
        return jsonify({'error': 'Basic salary is required'}), 400
    
    # Get values with defaults
    basic_salary = float(data.get('basic_salary', 0))
    transport_allowance = float(data.get('transport_allowance', 0))
    housing_allowance = float(data.get('housing_allowance', 0))
    other_allowances = float(data.get('other_allowances', 0))
    is_contract = bool(data.get('is_contract', False))
    
    # Calculate statutory deductions
    results = calculate_statutory_deductions(
        basic_salary, 
        transport_allowance, 
        housing_allowance, 
        other_allowances, 
        is_contract
    )
    
    # Format currency values for API response
    formatted_results = {
        'monthly_basic': format_currency(results['monthly_basic']),
        'monthly_transport': format_currency(results['monthly_transport']),
        'monthly_housing': format_currency(results['monthly_housing']),
        'monthly_other': format_currency(results['monthly_other']),
        'monthly_gross': format_currency(results['monthly_gross']),
        'monthly_pension': format_currency(results['monthly_pension']),
        'monthly_employer_pension': format_currency(results['monthly_employer_pension']),
        'monthly_nhf': format_currency(results['monthly_nhf']),
        'monthly_tax': format_currency(results['monthly_tax']),
        'total_monthly_deductions': format_currency(results['total_monthly_deductions']),
        'monthly_net_pay': format_currency(results['monthly_net_pay']),
        'annual_gross': format_currency(results['annual_gross']),
        'consolidated_relief': format_currency(results['consolidated_relief']),
        'annual_taxable_income': format_currency(results['annual_taxable_income']),
        'annual_tax': format_currency(results['annual_tax']),
        'is_contract': results['is_contract'],
        'is_pension_exempt': results['is_pension_exempt']
    }
    
    return jsonify(formatted_results)
    
@calculator.route('/proration', methods=['GET', 'POST'])
@login_required
def proration():
    """Salary proration calculator."""
    form = ProrationCalculatorForm()
    
    # Set default month and year to current
    if not form.is_submitted():
        today = date.today()
        form.month.data = today.month
        form.year.data = today.year
    
    # Initialize results
    results = None
    
    if form.validate_on_submit():
        # Get form data
        amount = form.amount.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        month = form.month.data
        year = form.year.data
        
        # Calculate prorated amount
        prorated_amount = prorate_amount(amount, start_date, end_date, month, year)
        
        # Get the original amount and prorated amount
        results = {
            'original_amount': amount,
            'prorated_amount': prorated_amount,
            'start_date': start_date,
            'end_date': end_date,
            'month': month,
            'year': year,
            'month_name': form.month.choices[month-1][1],
            'proration_factor': prorated_amount / amount if amount else 0
        }
        
        # Flash a message
        flash('Amount prorated successfully.', 'success')
    
    return render_template(
        'calculator/proration.html',
        form=form,
        results=results,
        format_currency=format_currency,
        current_year=date.today().year
    )