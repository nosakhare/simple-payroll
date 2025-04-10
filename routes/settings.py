from flask import (
    Blueprint, render_template, flash, redirect, 
    url_for, request, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from sqlalchemy import desc

from app import db
from models import CompanySettings, EmailLog, Payslip, Payroll
from forms import CompanySettingsForm
from email_utils import send_payslip_email, retry_failed_emails

# Create blueprint
settings = Blueprint('settings', __name__)


@settings.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    """View and edit company settings."""
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get existing settings or create default
    company_settings = CompanySettings.get_settings()
    
    # Create form and populate with existing data
    form = CompanySettingsForm(obj=company_settings)
    
    # Process form submission
    if form.validate_on_submit():
        # Check if email settings are being updated
        email_updated = (
            form.mail_server.data != company_settings.mail_server or
            form.mail_port.data != company_settings.mail_port or
            form.mail_use_tls.data != company_settings.mail_use_tls or
            form.mail_use_ssl.data != company_settings.mail_use_ssl or
            form.mail_username.data != company_settings.mail_username or
            form.mail_password.data != company_settings.mail_password or
            form.mail_default_sender.data != company_settings.mail_default_sender
        )
        
        # Update settings with form data
        form.populate_obj(company_settings)
        
        # Set the user who updated the settings
        company_settings.last_updated_by_id = current_user.id
        
        # Save changes
        db.session.commit()
        
        # Update email configuration immediately
        if email_updated:
            try:
                from email_config import update_mail_config
                success, message = update_mail_config()
                if success:
                    flash('Company settings and email configuration updated successfully.', 'success')
                else:
                    flash(f'Company settings updated, but email configuration update failed: {message}', 'warning')
            except Exception as e:
                flash(f'Company settings updated, but email configuration update failed: {str(e)}', 'warning')
        else:
            flash('Company settings updated successfully.', 'success')
            
        return redirect(url_for('settings.company'))
        
    return render_template(
        'settings/company.html', 
        form=form, 
        company_settings=company_settings
    )


@settings.route('/company/logo', methods=['POST'])
@login_required
def upload_logo():
    """Upload a company logo."""
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get existing settings
    company_settings = CompanySettings.get_settings()
    
    # Check if a file was uploaded
    if 'logo' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('settings.company'))
    
    file = request.files['logo']
    
    # Check if file is empty
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('settings.company'))
    
    # Check if file extension is allowed
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
        flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, SVG.', 'danger')
        return redirect(url_for('settings.company'))
    
    # Create a unique filename
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"company_logo_{uuid.uuid4().hex}.{extension}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static', 'img', 'company')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # Update the database
    relative_path = os.path.join('static', 'img', 'company', unique_filename)
    
    # Delete old logo if it exists and is not the default
    if (company_settings.company_logo and 
        company_settings.company_logo != 'static/img/company_logo.svg' and
        os.path.exists(os.path.join(current_app.root_path, company_settings.company_logo))):
        try:
            os.remove(os.path.join(current_app.root_path, company_settings.company_logo))
        except Exception as e:
            # Log the error but continue
            print(f"Error removing old logo: {e}")
    
    # Update settings
    company_settings.company_logo = relative_path
    company_settings.last_updated_by_id = current_user.id
    db.session.commit()
    
    flash('Company logo updated successfully.', 'success')
    return redirect(url_for('settings.company'))


@settings.route('/email-logs', methods=['GET'])
@login_required
def email_logs():
    """View email logs."""
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get page number and filters from query string
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    payroll_id = request.args.get('payroll_id', type=int)
    
    # Number of logs per page
    per_page = 20
    
    # Query logs
    query = EmailLog.query.order_by(desc(EmailLog.send_date))
    
    # Filter by status if provided
    if status:
        query = query.filter_by(status=status)
    
    # Filter by payroll if provided
    if payroll_id:
        query = query.filter_by(payroll_id=payroll_id)
    
    # Get paginated results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    email_logs = pagination.items
    
    # Get count of failed emails for the retry all button
    failed_count = EmailLog.query.filter_by(status='failed').filter(EmailLog.retry_count < 3).count()
    
    # Get all payrolls for the dropdown filter
    payrolls = Payroll.query.order_by(desc(Payroll.period_end)).all()
    
    return render_template(
        'settings/email_logs.html',
        email_logs=email_logs,
        page=page,
        pages=pagination.pages,
        status=status,
        payroll_id=payroll_id,
        payrolls=payrolls,
        has_failed_emails=failed_count > 0,
        failed_count=failed_count
    )


@settings.route('/retry-email/<int:log_id>', methods=['POST'])
@login_required
def retry_email(log_id):
    """Retry sending a failed email."""
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the email log
    email_log = EmailLog.query.get_or_404(log_id)
    
    # Check if it's a failed email
    if email_log.status != 'failed':
        flash('Only failed emails can be retried.', 'warning')
        return redirect(url_for('settings.email_logs'))
    
    # Get the associated payslip
    payslip = Payslip.query.get(email_log.payslip_id)
    if not payslip:
        flash('Payslip not found for this email.', 'danger')
        return redirect(url_for('settings.email_logs'))
    
    # Try to resend the email, passing the payroll_id if it exists
    success, message = send_payslip_email(email_log.payslip_id, email_log.payroll_id)
    
    if success:
        flash(f'Email resent successfully: {message}', 'success')
    else:
        flash(f'Failed to resend email: {message}', 'danger')
    
    return redirect(url_for('settings.email_logs'))


@settings.route('/retry-all-emails', methods=['POST'])
@login_required
def retry_all_emails():
    """Retry all failed emails."""
    # Only admin users can access this page
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Retry failed emails
    success, message, retried, succeeded = retry_failed_emails()
    
    if success:
        flash(f'{message}', 'success')
    else:
        flash(f'Error: {message}', 'danger')
    
    return redirect(url_for('settings.email_logs'))