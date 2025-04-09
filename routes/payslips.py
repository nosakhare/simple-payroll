from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app, Response
from flask_login import login_required, current_user
from werkzeug.exceptions import NotFound
import io

from app import db
from models import Payslip, PayrollItem, Payroll, Employee, EmailLog
from utils import format_currency
from payslip_utils import create_payslip_pdf, generate_all_payslips, download_payslip
from email_utils import send_payslip_email, send_all_payslips, retry_failed_emails

payslips = Blueprint('payslips', __name__)

@payslips.route('/')
@login_required
def index():
    """Display list of payslips."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get all payslips with their related payroll items, payrolls, and employees
    query = Payslip.query.join(PayrollItem).join(
        Employee, Employee.id == PayrollItem.employee_id
    ).join(
        Payroll, Payroll.id == PayrollItem.payroll_id
    ).order_by(Payslip.date_created.desc())
    
    # Apply search filters if provided
    employee_search = request.args.get('employee', '')
    payroll_search = request.args.get('payroll', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    email_status = request.args.get('email_status', '')
    
    if employee_search:
        query = query.filter(
            (Employee.first_name.ilike(f'%{employee_search}%')) | 
            (Employee.last_name.ilike(f'%{employee_search}%')) |
            (Employee.employee_id.ilike(f'%{employee_search}%'))
        )
    
    if payroll_search:
        query = query.filter(Payroll.name.ilike(f'%{payroll_search}%'))
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payslip.date_created >= date_from)
        except:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Payslip.date_created <= date_to)
        except:
            pass
    
    if email_status:
        if email_status == 'sent':
            query = query.filter(Payslip.email_status == 'sent')
        elif email_status == 'failed':
            query = query.filter(Payslip.email_status == 'failed')
        elif email_status == 'pending':
            query = query.filter(Payslip.is_emailed == False)
    
    payslips_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'payslips/index.html',
        payslips=payslips_paginated,
        format_currency=format_currency,
        employee_search=employee_search,
        payroll_search=payroll_search,
        date_from=date_from if isinstance(date_from, str) else date_from.strftime('%Y-%m-%d') if date_from else '',
        date_to=date_to if isinstance(date_to, str) else date_to.strftime('%Y-%m-%d') if date_to else '',
        email_status=email_status
    )

@payslips.route('/view/<int:id>')
@login_required
def view(id):
    """View a payslip."""
    payslip = Payslip.query.get_or_404(id)
    payroll_item = PayrollItem.query.get_or_404(payslip.payroll_item_id)
    employee = Employee.query.get_or_404(payroll_item.employee_id)
    payroll = Payroll.query.get_or_404(payroll_item.payroll_id)
    
    # Get email logs for this payslip
    email_logs = EmailLog.query.filter_by(payslip_id=id).order_by(EmailLog.send_date.desc()).all()
    
    # Get company information from config
    company_info = {
        'name': current_app.config.get('COMPANY_NAME', 'Nigerian Payroll System'),
        'address': current_app.config.get('COMPANY_ADDRESS', '123 Lagos Business District'),
        'city': current_app.config.get('COMPANY_CITY', 'Lagos'),
        'country': current_app.config.get('COMPANY_COUNTRY', 'Nigeria'),
        'email': current_app.config.get('COMPANY_EMAIL', 'payroll@nigerianpayroll.com'),
        'phone': current_app.config.get('COMPANY_PHONE', '+234 123 456 7890')
    }
    
    return render_template(
        'payslips/view.html',
        payslip=payslip,
        payroll_item=payroll_item,
        employee=employee,
        payroll=payroll,
        email_logs=email_logs,
        format_currency=format_currency,
        company_info=company_info
    )

@payslips.route('/download/<int:id>')
@login_required
def download(id):
    """Download a payslip PDF."""
    success, data, filename = download_payslip(id)
    
    if not success:
        flash(data, 'danger')
        return redirect(url_for('payslips.index'))
    
    return send_file(
        io.BytesIO(data),
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )

@payslips.route('/generate/<int:payroll_item_id>', methods=['POST'])
@login_required
def generate(payroll_item_id):
    """Generate a payslip for a specific payroll item."""
    payroll_item = PayrollItem.query.get_or_404(payroll_item_id)
    
    # Generate the payslip
    success, message, payslip_id = create_payslip_pdf(payroll_item_id, current_user.id)
    
    if success:
        flash(message, 'success')
        if payslip_id:
            return redirect(url_for('payslips.view', id=payslip_id))
    else:
        flash(message, 'danger')
    
    return redirect(url_for('payroll.view_payroll_item', id=payroll_item_id))

@payslips.route('/generate-all/<int:payroll_id>', methods=['POST'])
@login_required
def generate_all(payroll_id):
    """Generate payslips for all employees in a payroll run."""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Generate payslips
    success, message, count = generate_all_payslips(payroll_id, current_user.id)
    
    if success:
        flash(f"{message}", 'success')
    else:
        flash(f"Error: {message}", 'danger')
    
    return redirect(url_for('payroll.view', id=payroll_id))

@payslips.route('/send/<int:id>', methods=['POST'])
@login_required
def send(id):
    """Send a payslip as an email attachment."""
    payslip = Payslip.query.get_or_404(id)
    
    # Send the email
    success, message = send_payslip_email(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(f"Error: {message}", 'danger')
    
    return redirect(url_for('payslips.view', id=id))

@payslips.route('/send-all/<int:payroll_id>', methods=['POST'])
@login_required
def send_all(payroll_id):
    """Send payslips to all employees in a payroll run."""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Send payslips
    success, message, sent, failed = send_all_payslips(payroll_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(f"Error: {message}", 'danger')
    
    return redirect(url_for('payroll.view', id=payroll_id))

@payslips.route('/retry-failed', methods=['POST'])
@login_required
def retry_failed():
    """Retry sending failed emails."""
    # Only allow admins to retry failed emails
    if not current_user.is_admin:
        flash("Only administrators can retry failed emails.", 'danger')
        return redirect(url_for('payslips.index'))
    
    # Retry failed emails
    success, message, retried, succeeded = retry_failed_emails()
    
    if success:
        flash(message, 'success')
    else:
        flash(f"Error: {message}", 'danger')
    
    return redirect(url_for('payslips.index'))

@payslips.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a payslip."""
    # Only allow admins to delete payslips
    if not current_user.is_admin:
        flash("Only administrators can delete payslips.", 'danger')
        return redirect(url_for('payslips.index'))
    
    payslip = Payslip.query.get_or_404(id)
    
    # Get related info for redirect
    payroll_item = PayrollItem.query.get(payslip.payroll_item_id)
    payroll_id = payroll_item.payroll_id if payroll_item else None
    
    # Delete email logs first (maintain referential integrity)
    EmailLog.query.filter_by(payslip_id=id).delete()
    
    # Delete the payslip
    db.session.delete(payslip)
    db.session.commit()
    
    flash("Payslip deleted successfully.", 'success')
    
    # Redirect to appropriate page
    if payroll_id:
        return redirect(url_for('payroll.view', id=payroll_id))
    else:
        return redirect(url_for('payslips.index'))