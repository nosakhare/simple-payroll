from flask import Blueprint, render_template, jsonify
from app import db
from models import User, Employee, Payroll, PayrollItem, PayrollAdjustment
from utils import format_currency, process_payroll, generate_payslip_data
from datetime import datetime, date, timedelta
import json

test = Blueprint('test', __name__)

@test.route('/')
def index():
    """Test page for the payroll system."""
    return render_template('test/index.html')

@test.route('/create-test-data')
def create_test_data():
    """Create test data for the payroll system."""
    # Check if tables exist and create them if not
    try:
        db.create_all()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'})
    
    # Create a test user if none exists
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        user.set_password('password')
        db.session.add(user)
    
    # Create test employees if none exist
    if Employee.query.count() == 0:
        employees = [
            Employee(
                employee_id='EMP001',
                first_name='John',
                last_name='Doe',
                email='john.doe@example.com',
                phone_number='08012345678',
                date_of_birth=date(1985, 5, 15),
                gender='Male',
                marital_status='Married',
                address='123 Lagos Street',
                city='Lagos',
                state='Lagos',
                department='Engineering',
                position='Senior Engineer',
                date_hired=date(2020, 1, 15),
                employment_status='Active',
                bank_name='First Bank',
                account_number='1234567890',
                tax_id='TAX12345',
                pension_id='PEN12345',
                nhf_id='NHF12345',
                basic_salary=150000.0
            ),
            Employee(
                employee_id='EMP002',
                first_name='Jane',
                last_name='Smith',
                email='jane.smith@example.com',
                phone_number='08098765432',
                date_of_birth=date(1990, 8, 20),
                gender='Female',
                marital_status='Single',
                address='456 Abuja Road',
                city='Abuja',
                state='FCT Abuja',
                department='Finance',
                position='Accountant',
                date_hired=date(2021, 3, 10),
                employment_status='Active',
                bank_name='GTBank',
                account_number='0987654321',
                tax_id='TAX54321',
                pension_id='PEN54321',
                nhf_id='NHF54321',
                basic_salary=120000.0
            )
        ]
        for emp in employees:
            db.session.add(emp)
    
    # Create a test payroll if none exists
    if Payroll.query.count() == 0:
        # Current month payroll
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        if today.month == 12:
            end_of_month = date(today.year, 12, 31)
        else:
            end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        payroll = Payroll(
            name=f'Payroll for {start_of_month.strftime("%B %Y")}',
            period_start=start_of_month,
            period_end=end_of_month,
            payment_date=end_of_month,
            status='Draft',
            is_active=False,
            created_by_id=user.id
        )
        db.session.add(payroll)
    
    # Commit changes
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'message': 'Test data created successfully',
        'data': {
            'users': User.query.count(),
            'employees': Employee.query.count(),
            'payrolls': Payroll.query.count()
        }
    })

@test.route('/process-test-payroll')
def process_test_payroll():
    """Process the test payroll."""
    # Get the first payroll in draft status
    payroll = Payroll.query.filter_by(status='Draft').first()
    
    if not payroll:
        return jsonify({'status': 'error', 'message': 'No draft payroll found'})
    
    # Process the payroll
    success, message = process_payroll(payroll.id)
    
    if success:
        return jsonify({'status': 'success', 'message': message, 'payroll_id': payroll.id})
    else:
        return jsonify({'status': 'error', 'message': message})

@test.route('/add-test-adjustment/<int:payroll_id>')
def add_test_adjustment(payroll_id):
    """Add a test adjustment to a payroll item."""
    # Get the first payroll item
    payroll_item = PayrollItem.query.filter_by(payroll_id=payroll_id).first()
    
    if not payroll_item:
        return jsonify({'status': 'error', 'message': 'No payroll items found'})
    
    # Create a test adjustment
    adjustment = PayrollAdjustment(
        payroll_id=payroll_id,
        payroll_item_id=payroll_item.id,
        adjustment_type='bonus',
        description='Year-end bonus',
        amount=10000.0, 
        created_by_id=User.query.first().id
    )
    
    # Mark the payroll item as adjusted
    payroll_item.is_adjusted = True
    
    # Recalculate net pay
    payroll_item.recalculate_net_pay()
    
    db.session.add(adjustment)
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'message': 'Adjustment added successfully',
        'adjustment': {
            'type': adjustment.adjustment_type,
            'amount': adjustment.amount,
            'payroll_item_id': payroll_item.id
        }
    })

@test.route('/view-test-payslip/<int:payroll_id>')
def view_test_payslip(payroll_id):
    """View a test payslip."""
    # Get the first payroll item
    payroll_item = PayrollItem.query.filter_by(payroll_id=payroll_id).first()
    
    if not payroll_item:
        return jsonify({'status': 'error', 'message': 'No payroll items found'})
    
    # Generate payslip data
    payslip_data = generate_payslip_data(payroll_item.id)
    
    # Render the payslip template
    return render_template('payroll/payslip.html', payslip=payslip_data, format_currency=format_currency)