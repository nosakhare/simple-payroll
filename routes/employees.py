from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import date, datetime
import csv, io, codecs
from werkzeug.utils import secure_filename

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


@employees.route('/download-csv-template')
@login_required
def download_csv_template():
    """Download a CSV template for bulk employee upload."""
    # Create a CSV template with field headers
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    
    # Write headers based on employee model fields
    headers = [
        # Personal Information
        'employee_id', 'first_name', 'last_name', 'email', 'phone_number', 
        'date_of_birth (YYYY-MM-DD)', 'gender (Male/Female/Other)', 
        'marital_status (Single/Married/Divorced/Widowed)', 
        'address', 'city', 'state',
        
        # Employment Details
        'department', 'position', 'date_hired (YYYY-MM-DD)', 
        'employment_status (Active/On Leave/Suspended/Terminated)',
        
        # Bank Details
        'bank_name', 'account_number',
        
        # Tax Information (Optional)
        'tax_id', 'pension_id', 'nhf_id',
        
        # Salary Information
        'basic_salary',
    ]
    writer.writerow(headers)
    
    # Create CSV response
    csv_data.seek(0)
    
    # Create the response with the CSV data
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=employee_upload_template_{timestamp}.csv'
        }
    )


@employees.route('/bulk-upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    """Upload employees in bulk using a CSV file."""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if the file was selected
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        # Check if the file is a CSV
        if not file.filename.endswith('.csv'):
            flash('Only CSV files are allowed', 'danger')
            return redirect(request.url)
            
        try:
            # Read the CSV file
            stream = codecs.iterdecode(file.stream, 'utf-8')
            reader = csv.DictReader(stream)
            
            # Track success, errors and duplicates
            success_count = 0
            error_count = 0
            duplicate_count = 0
            errors = []
            
            # Process each row in the CSV
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
                try:
                    # Check required fields
                    required_fields = ['employee_id', 'first_name', 'last_name', 'email', 'phone_number', 
                                      'date_of_birth (YYYY-MM-DD)', 'gender (Male/Female/Other)', 
                                      'marital_status (Single/Married/Divorced/Widowed)', 
                                      'address', 'city', 'state', 'department', 'position', 
                                      'date_hired (YYYY-MM-DD)', 'employment_status (Active/On Leave/Suspended/Terminated)',
                                      'bank_name', 'account_number', 'basic_salary']
                    
                    missing_fields = [field for field in required_fields if field not in row or not row[field]]
                    if missing_fields:
                        errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                        error_count += 1
                        continue
                    
                    # Check for duplicate employee ID
                    if Employee.query.filter_by(employee_id=row['employee_id']).first():
                        errors.append(f"Row {row_num}: Employee ID already exists: {row['employee_id']}")
                        duplicate_count += 1
                        continue
                        
                    # Check for duplicate email
                    if Employee.query.filter_by(email=row['email']).first():
                        errors.append(f"Row {row_num}: Email already exists: {row['email']}")
                        duplicate_count += 1
                        continue
                        
                    # Validate and parse dates
                    try:
                        date_of_birth = datetime.strptime(row['date_of_birth (YYYY-MM-DD)'], '%Y-%m-%d').date()
                        date_hired = datetime.strptime(row['date_hired (YYYY-MM-DD)'], '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid date format. Use YYYY-MM-DD format.")
                        error_count += 1
                        continue
                        
                    # Validate age (must be at least 18)
                    today = date.today()
                    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                    if age < 18:
                        errors.append(f"Row {row_num}: Employee must be at least 18 years old.")
                        error_count += 1
                        continue
                        
                    # Validate gender
                    gender = row['gender (Male/Female/Other)']
                    if gender not in ['Male', 'Female', 'Other']:
                        errors.append(f"Row {row_num}: Invalid gender. Must be Male, Female, or Other.")
                        error_count += 1
                        continue
                        
                    # Validate marital status
                    marital_status = row['marital_status (Single/Married/Divorced/Widowed)']
                    if marital_status not in ['Single', 'Married', 'Divorced', 'Widowed']:
                        errors.append(f"Row {row_num}: Invalid marital status. Must be Single, Married, Divorced, or Widowed.")
                        error_count += 1
                        continue
                        
                    # Validate employment status
                    employment_status = row['employment_status (Active/On Leave/Suspended/Terminated)']
                    if employment_status not in ['Active', 'On Leave', 'Suspended', 'Terminated']:
                        errors.append(f"Row {row_num}: Invalid employment status. Must be Active, On Leave, Suspended, or Terminated.")
                        error_count += 1
                        continue
                        
                    # Validate state
                    valid_states = ['Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 
                                   'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 
                                   'FCT Abuja', 'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 
                                   'Kebbi', 'Kogi', 'Kwara', 'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 
                                   'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara']
                    if row['state'] not in valid_states:
                        errors.append(f"Row {row_num}: Invalid state. Must be one of the 36 Nigerian states or FCT Abuja.")
                        error_count += 1
                        continue
                        
                    # Validate basic salary
                    try:
                        basic_salary = float(row['basic_salary'])
                        if basic_salary <= 0:
                            errors.append(f"Row {row_num}: Basic salary must be greater than 0.")
                            error_count += 1
                            continue
                    except ValueError:
                        errors.append(f"Row {row_num}: Basic salary must be a valid number.")
                        error_count += 1
                        continue
                        
                    # Create new employee
                    employee = Employee(
                        employee_id=row['employee_id'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=row['email'],
                        phone_number=row['phone_number'],
                        date_of_birth=date_of_birth,
                        gender=gender,
                        marital_status=marital_status,
                        address=row['address'],
                        city=row['city'],
                        state=row['state'],
                        department=row['department'],
                        position=row['position'],
                        date_hired=date_hired,
                        employment_status=employment_status,
                        bank_name=row['bank_name'],
                        account_number=row['account_number'],
                        tax_id=row.get('tax_id', ''),
                        pension_id=row.get('pension_id', ''),
                        nhf_id=row.get('nhf_id', ''),
                        basic_salary=basic_salary
                    )
                    
                    db.session.add(employee)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
                    
            # Commit to database if there were successful entries
            if success_count > 0:
                db.session.commit()
                
            # Display results
            if success_count > 0:
                flash(f'Successfully added {success_count} employees.', 'success')
            if error_count > 0 or duplicate_count > 0:
                flash(f'Encountered {error_count} errors and {duplicate_count} duplicates.', 'warning')
                return render_template('employees/bulk_upload.html', errors=errors)
                
            return redirect(url_for('employees.index'))
                
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('employees/bulk_upload.html')
