from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Employee, Payroll
from utils import format_currency

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page with summary statistics."""
    # Get summary statistics
    employee_count = Employee.query.filter_by(employment_status='Active').count()
    total_employees = Employee.query.count()
    
    # Get the latest payrolls
    recent_payrolls = Payroll.query.order_by(Payroll.date_created.desc()).limit(5).all()
    
    # Calculate total payroll amount from completed payrolls
    total_payroll = sum(payroll.total_net_pay for payroll in 
                        Payroll.query.filter_by(status='Completed').all())
    
    # Get payroll status counts
    draft_count = Payroll.query.filter_by(status='Draft').count()
    completed_count = Payroll.query.filter_by(status='Completed').count()
    
    return render_template(
        'dashboard.html',
        employee_count=employee_count,
        total_employees=total_employees,
        recent_payrolls=recent_payrolls,
        total_payroll=total_payroll,
        draft_count=draft_count,
        completed_count=completed_count,
        format_currency=format_currency
    )
