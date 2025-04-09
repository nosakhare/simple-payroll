from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import date

from app import db
from models import Employee, CompensationHistory
from forms import EmployeeForm, SearchForm, CompensationChangeForm
from utils import format_currency

employees = Blueprint('employees', __name__)

@employees.route('/')
@login_required
def index():
    """Display list of employees."""
    search_form = SearchForm(request.args, meta={'csrf': False})
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Search query
    query = Employee.query
    if search_form.query.data:
        search_term = f"%{search_form.query.data}%"
        query = query.filter(
            or_(
                Employee.first_name.like(search_term),
                Employee.last_name.like(search_term),
                Employee.employee_id.like(search_term),
                Employee.department.like(search_term),
                Employee.position.like(search_term),
                Employee.email.like(search_term)
            )
        )
    
    # Get paginated list of employees
    employees_list = query.order_by(Employee.date_created.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'employees/index.html', 
        employees=employees_list,
        search_form=search_form,
        format_currency=format_currency
    )

@employees.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new employee."""
    form = EmployeeForm()
    
    if form.validate_on_submit():
        # Check if employee ID already exists
        existing_employee = Employee.query.filter_by(employee_id=form.employee_id.data).first()
        if existing_employee:
            flash('Employee ID already exists. Please use a different ID.', 'danger')
            return render_template('employees/create.html', form=form)
            
        # Check if email already exists
        existing_email = Employee.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already exists. Please use a different email address.', 'danger')
            return render_template('employees/create.html', form=form)
        
        # Create new employee
        employee = Employee(
            employee_id=form.employee_id.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            marital_status=form.marital_status.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            department=form.department.data,
            position=form.position.data,
            date_hired=form.date_hired.data,
            employment_status=form.employment_status.data,
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            tax_id=form.tax_id.data,
            pension_id=form.pension_id.data,
            nhf_id=form.nhf_id.data,
            basic_salary=form.basic_salary.data
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash(f'Employee {employee.full_name()} added successfully.', 'success')
        return redirect(url_for('employees.index'))
        
    return render_template('employees/create.html', form=form)

@employees.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing employee."""
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # Check if employee ID already exists and is not this employee
        existing_employee = Employee.query.filter_by(employee_id=form.employee_id.data).first()
        if existing_employee and existing_employee.id != employee.id:
            flash('Employee ID already exists. Please use a different ID.', 'danger')
            return render_template('employees/edit.html', form=form, employee=employee)
            
        # Check if email already exists and is not this employee
        existing_email = Employee.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != employee.id:
            flash('Email already exists. Please use a different email address.', 'danger')
            return render_template('employees/edit.html', form=form, employee=employee)
        
        # Check if salary changed, if so, record in compensation history
        if employee.basic_salary != form.basic_salary.data:
            # Create compensation history record
            compensation_history = CompensationHistory(
                employee_id=employee.id,
                effective_date=date.today(),  # Default to today, can be changed via compensation form
                basic_salary=form.basic_salary.data,
                changed_by_id=current_user.id,
                change_reason="Updated during employee edit"
            )
            db.session.add(compensation_history)
        
        # Update employee
        employee.employee_id = form.employee_id.data
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.email = form.email.data
        employee.phone_number = form.phone_number.data
        employee.date_of_birth = form.date_of_birth.data
        employee.gender = form.gender.data
        employee.marital_status = form.marital_status.data
        employee.address = form.address.data
        employee.city = form.city.data
        employee.state = form.state.data
        employee.department = form.department.data
        employee.position = form.position.data
        employee.date_hired = form.date_hired.data
        employee.employment_status = form.employment_status.data
        employee.bank_name = form.bank_name.data
        employee.account_number = form.account_number.data
        employee.tax_id = form.tax_id.data
        employee.pension_id = form.pension_id.data
        employee.nhf_id = form.nhf_id.data
        employee.basic_salary = form.basic_salary.data
        
        db.session.commit()
        
        flash(f'Employee {employee.full_name()} updated successfully.', 'success')
        return redirect(url_for('employees.view', id=employee.id))
        
    return render_template('employees/edit.html', form=form, employee=employee)

@employees.route('/view/<int:id>')
@login_required
def view(id):
    """View employee details."""
    employee = Employee.query.get_or_404(id)
    return render_template('employees/view.html', employee=employee, format_currency=format_currency)

@employees.route('/compensation/<int:id>', methods=['GET', 'POST'])
@login_required
def compensation(id):
    """View and update employee compensation history."""
    employee = Employee.query.get_or_404(id)
    form = CompensationChangeForm()
    
    if form.validate_on_submit():
        # Create new compensation history record
        compensation_history = CompensationHistory(
            employee_id=employee.id,
            effective_date=form.effective_date.data,
            basic_salary=form.basic_salary.data,
            changed_by_id=current_user.id,
            change_reason=form.change_reason.data
        )
        
        # Update employee's current salary if effective date is today
        if form.effective_date.data <= date.today():
            employee.basic_salary = form.basic_salary.data
        
        db.session.add(compensation_history)
        db.session.commit()
        
        flash(f'Compensation updated for {employee.full_name()}. New salary: {format_currency(form.basic_salary.data)} effective {form.effective_date.data.strftime("%d-%m-%Y")}.', 'success')
        return redirect(url_for('employees.compensation', id=employee.id))
    
    # Pre-fill current salary
    if not form.basic_salary.data:
        form.basic_salary.data = employee.basic_salary
        form.effective_date.data = date.today()
    
    # Get compensation history
    compensation_history = CompensationHistory.query.filter_by(employee_id=employee.id).order_by(
        CompensationHistory.effective_date.desc()
    ).all()
    
    return render_template(
        'employees/compensation.html', 
        employee=employee, 
        form=form, 
        compensation_history=compensation_history,
        format_currency=format_currency
    )


@employees.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete an employee."""
    employee = Employee.query.get_or_404(id)
    
    # Store name before deletion for flash message
    employee_name = employee.full_name()
    
    db.session.delete(employee)
    db.session.commit()
    
    flash(f'Employee {employee_name} deleted successfully.', 'success')
    return redirect(url_for('employees.index'))
