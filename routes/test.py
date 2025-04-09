from flask import Blueprint, render_template, jsonify, redirect, url_for
from datetime import datetime, timedelta
from app import db
from models import User, Employee, Payroll, PayrollItem, PayrollAdjustment
import json

# Create test blueprint
test = Blueprint('test', __name__)

@test.route('/')
def index():
    """Render the test page."""
    return render_template('test/index.html')

@test.route('/create-test-data')
def create_test_data():
    """Create test data for demonstration purposes."""
    try:
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            # Create a test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                is_admin=True
            )
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        
        # Check if test employee exists
        test_employee = Employee.query.filter_by(email='employee@example.com').first()
        if not test_employee:
            # Create a test employee
            test_employee = Employee(
                first_name='John',
                last_name='Doe',
                email='employee@example.com',
                phone_number='1234567890',
                date_of_birth=datetime(1990, 1, 1),
                gender='Male',
                marital_status='Single',
                address='123 Test Street',
                city='Lagos',
                state='Lagos',
                employee_id='EMP001',
                department='IT',
                position='Software Developer',
                date_hired=datetime(2020, 1, 1),
                employment_status='Active',
                bank_name='First Bank',
                account_number='1234567890',
                tax_id='12345',
                pension_id='67890',
                nhf_id='54321',
                basic_salary=500000.00,  # 500,000 Naira
                created_by_id=test_user.id
            )
            db.session.add(test_employee)
            
            # Create a second test employee
            test_employee2 = Employee(
                first_name='Jane',
                last_name='Smith',
                email='jane@example.com',
                phone_number='0987654321',
                date_of_birth=datetime(1992, 5, 15),
                gender='Female',
                marital_status='Married',
                address='456 Sample Avenue',
                city='Abuja',
                state='FCT Abuja',
                employee_id='EMP002',
                department='Finance',
                position='Accountant',
                date_hired=datetime(2019, 6, 15),
                employment_status='Active',
                bank_name='UBA',
                account_number='0987654321',
                tax_id='54321',
                pension_id='09876',
                nhf_id='12345',
                basic_salary=450000.00,  # 450,000 Naira
                created_by_id=test_user.id
            )
            db.session.add(test_employee2)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Test data created successfully',
            'data': {
                'user_id': test_user.id,
                'employees': ['EMP001', 'EMP002']
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@test.route('/process-test-payroll')
def process_test_payroll():
    """Process a test payroll for the current month."""
    try:
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            return jsonify({
                'status': 'error',
                'message': 'Test user not found. Please create test data first.'
            })
        
        # Get current month dates
        today = datetime.today()
        month_start = datetime(today.year, today.month, 1)
        if today.month == 12:
            month_end = datetime(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
        
        # Check if a payroll already exists for this period
        existing_payroll = Payroll.query.filter(
            Payroll.period_start == month_start,
            Payroll.period_end == month_end
        ).first()
        
        if existing_payroll:
            payroll = existing_payroll
        else:
            # Create a new payroll
            payroll = Payroll(
                name=f"Payroll for {today.strftime('%B %Y')}",
                period_start=month_start,
                period_end=month_end,
                payment_date=month_end,
                status='Processing',
                created_by_id=test_user.id
            )
            db.session.add(payroll)
            db.session.commit()
        
        # Get all active employees
        employees = Employee.query.filter_by(employment_status='Active').all()
        
        # Create payroll items for each employee
        for employee in employees:
            # Check if payroll item already exists
            existing_item = PayrollItem.query.filter_by(
                payroll_id=payroll.id,
                employee_id=employee.id
            ).first()
            
            if not existing_item:
                # Use a simplified approach for test data
                basic_salary = employee.basic_salary
                
                # Calculate allowances (60% basic salary, 40% allowances)
                transport_allowance = basic_salary * 0.1
                housing_allowance = basic_salary * 0.15
                utility_allowance = basic_salary * 0.05
                meal_allowance = basic_salary * 0.05
                clothing_allowance = basic_salary * 0.05
                
                # Calculate gross pay
                gross_pay = (
                    basic_salary + 
                    transport_allowance + 
                    housing_allowance + 
                    utility_allowance + 
                    meal_allowance + 
                    clothing_allowance
                )
                
                # Calculate deductions
                pension = basic_salary * 0.08
                nhf = basic_salary * 0.025
                
                # Calculate tax (simplified at 10% of gross)
                tax = gross_pay * 0.1
                
                # Calculate net pay
                net_pay = gross_pay - (pension + nhf + tax)
                
                # Create payroll item
                payroll_item = PayrollItem(
                    payroll_id=payroll.id,
                    employee_id=employee.id,
                    basic_salary=basic_salary,
                    transport_allowance=transport_allowance,
                    housing_allowance=housing_allowance,
                    utility_allowance=utility_allowance,
                    meal_allowance=meal_allowance,
                    clothing_allowance=clothing_allowance,
                    gross_pay=gross_pay,
                    pension=pension,
                    nhf=nhf,
                    tax=tax,
                    net_pay=net_pay,
                    is_adjusted=False,
                    created_by_id=test_user.id
                )
                db.session.add(payroll_item)
        
        # Update payroll with total amounts
        payroll_items = PayrollItem.query.filter_by(payroll_id=payroll.id).all()
        payroll.total_basic_salary = sum(item.basic_salary for item in payroll_items)
        payroll.total_allowances = sum(
            item.transport_allowance + item.housing_allowance + 
            item.utility_allowance + item.meal_allowance + 
            item.clothing_allowance for item in payroll_items
        )
        payroll.total_deductions = sum(item.pension + item.nhf for item in payroll_items)
        payroll.total_tax = sum(item.tax for item in payroll_items)
        payroll.total_net_pay = sum(item.net_pay for item in payroll_items)
        
        # Update payroll status
        payroll.status = 'Completed'
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Payroll processed successfully',
            'payroll_id': payroll.id
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@test.route('/add-test-adjustment/<int:payroll_id>')
def add_test_adjustment(payroll_id):
    """Add a test adjustment to a payroll item."""
    try:
        # Check if payroll exists
        payroll = Payroll.query.get(payroll_id)
        if not payroll:
            return jsonify({
                'status': 'error',
                'message': 'Payroll not found'
            })
        
        # Get the first payroll item
        payroll_item = PayrollItem.query.filter_by(payroll_id=payroll_id).first()
        if not payroll_item:
            return jsonify({
                'status': 'error',
                'message': 'No payroll items found for this payroll'
            })
        
        # Create test user if needed
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            return jsonify({
                'status': 'error',
                'message': 'Test user not found. Please create test data first.'
            })
        
        # Create a bonus adjustment
        adjustment = PayrollAdjustment(
            payroll_item_id=payroll_item.id,
            adjustment_type='bonus',
            description='Performance bonus',
            amount=50000.00,  # 50,000 Naira bonus
            created_by_id=test_user.id
        )
        db.session.add(adjustment)
        
        # Mark payroll item as adjusted
        payroll_item.is_adjusted = True
        
        # Update net pay
        payroll_item.net_pay += adjustment.amount
        
        # Update payroll total
        payroll.total_net_pay += adjustment.amount
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Adjustment added successfully',
            'adjustment': {
                'id': adjustment.id,
                'type': adjustment.adjustment_type,
                'amount': adjustment.amount,
                'description': adjustment.description
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@test.route('/view-test-payslip/<int:payroll_id>')
def view_test_payslip(payroll_id):
    """View a test payslip."""
    try:
        # Check if payroll exists
        payroll = Payroll.query.get(payroll_id)
        if not payroll:
            return render_template('error.html', message='Payroll not found')
        
        # Get the first payroll item
        payroll_item = PayrollItem.query.filter_by(payroll_id=payroll_id).first()
        if not payroll_item:
            return render_template('error.html', message='No payroll items found for this payroll')
        
        # Get employee
        employee = Employee.query.get(payroll_item.employee_id)
        
        # Get adjustments
        adjustments = PayrollAdjustment.query.filter_by(payroll_item_id=payroll_item.id).all()
        
        # Render payslip
        return render_template(
            'payroll/payslip.html',
            payroll=payroll,
            payroll_item=payroll_item,
            employee=employee,
            adjustments=adjustments
        )
    
    except Exception as e:
        return render_template('error.html', message=str(e))