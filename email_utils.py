import os
from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message
from threading import Thread

from app import db, mail
from models import Payslip, EmailLog, Employee, PayrollItem

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            # Log the error but don't raise it to prevent thread crashes
            print(f"Error sending email: {str(e)}")

def send_email(subject, recipients, text_body, html_body, attachments=None, sender=None):
    """
    Send an email with optional attachments.
    
    Args:
        subject: Email subject
        recipients: List of email recipients
        text_body: Plain text email body
        html_body: HTML email body
        attachments: List of tuples (filename, content_type, data)
        sender: The email sender address, if None, will use Flask-Mail's default sender
        
    Returns:
        Tuple of (success, server_response) where:
        - success: True if email was sent successfully, False otherwise
        - server_response: The response from the mail server or error message
    """
    # If no sender is provided, try to get it from config (which is updated from the database)
    if sender is None:
        # Try to get from the configuration which is populated from the database
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        # If still None, try to get the company email
        if not sender:
            sender = current_app.config.get('COMPANY_EMAIL')
    
    try:
        msg = Message(subject, recipients=recipients, sender=sender)
        msg.body = text_body
        msg.html = html_body
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                filename, content_type, data = attachment
                msg.attach(filename, content_type, data)
        
        # Send the email directly to capture any immediate errors
        mail.send(msg)
        
        print(f"Email sent successfully from: {sender} to: {recipients}")
        return True, "Message accepted by mail server for delivery"
        
    except Exception as e:
        error_message = str(e)
        print(f"Failed to send email: {error_message}")
        return False, error_message

def send_payslip_email(payslip_id):
    """
    Send a payslip as an email attachment.
    
    Args:
        payslip_id: ID of the payslip to send
        
    Returns:
        A tuple of (success, message)
    """
    # Get the payslip
    payslip = Payslip.query.get(payslip_id)
    
    if not payslip:
        return False, "Payslip not found"
    
    # Get the employee
    employee = Employee.query.join(PayrollItem).filter(PayrollItem.id == payslip.payroll_item_id).first()
    
    if not employee:
        return False, "Employee not found"
    
    # Check if email has already been sent successfully
    if payslip.is_emailed and payslip.email_status == 'sent':
        return True, "Payslip has already been emailed"
    
    subject = f"Your Payslip - {employee.first_name} {employee.last_name}"
    
    # Get company information from config
    company_name = current_app.config.get('COMPANY_NAME', 'Nigerian Payroll System')
    company_email = current_app.config.get('COMPANY_EMAIL', 'payroll@nigerianpayroll.com')
    
    # Render email templates
    text_body = render_template(
        'email/payslip.txt',
        employee=employee,
        company_name=company_name
    )
    
    html_body = render_template(
        'email/payslip.html',
        employee=employee,
        company_name=company_name
    )
    
    # Create attachment
    attachments = [(payslip.filename, 'application/pdf', payslip.pdf_data)]
    
    # Send the email and get the server response
    success, server_response = send_email(
        subject=subject,
        recipients=[employee.email],
        text_body=text_body,
        html_body=html_body,
        attachments=attachments,
        sender=company_email
    )
    
    if success:
        # Update payslip record
        payslip.is_emailed = True
        payslip.email_date = datetime.utcnow()
        payslip.email_status = 'sent'
        
        # Create email log with server response
        email_log = EmailLog(
            payslip_id=payslip.id,
            recipient=employee.email,
            subject=subject,
            status='sent',
            send_date=datetime.utcnow(),
            server_response=server_response
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        return True, f"Payslip emailed to {employee.email}"
    
    else:
        # Update payslip record
        payslip.email_status = 'failed'
        
        # Create email log with error
        email_log = EmailLog(
            payslip_id=payslip.id,
            recipient=employee.email,
            subject=subject,
            status='failed',
            error_message=server_response,
            send_date=datetime.utcnow()
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        return False, f"Failed to send email: {server_response}"

def send_all_payslips(payroll_id):
    """
    Send payslips to all employees in a payroll run.
    
    Args:
        payroll_id: ID of the payroll to send payslips for
        
    Returns:
        A tuple of (success, message, sent_count, failed_count)
    """
    # Get all payslips for this payroll
    payslips = Payslip.query.join(PayrollItem).filter(PayrollItem.payroll_id == payroll_id).all()
    
    if not payslips:
        return False, "No payslips found for this payroll", 0, 0
    
    # Send payslips
    sent_count = 0
    failed_count = 0
    
    for payslip in payslips:
        success, _ = send_payslip_email(payslip.id)
        if success:
            sent_count += 1
        else:
            failed_count += 1
    
    return True, f"Sent {sent_count} payslips, {failed_count} failed", sent_count, failed_count

def retry_failed_emails():
    """
    Retry sending failed emails.
    
    Returns:
        A tuple of (success, message, retried_count, success_count)
    """
    # Get all failed emails with less than 3 retry attempts
    failed_logs = EmailLog.query.filter_by(status='failed').filter(EmailLog.retry_count < 3).all()
    
    if not failed_logs:
        return True, "No failed emails to retry", 0, 0
    
    retried_count = 0
    success_count = 0
    
    for log in failed_logs:
        # Retry sending the email
        success, _ = send_payslip_email(log.payslip_id)
        
        # Update retry count
        log.retry_count += 1
        db.session.commit()
        
        retried_count += 1
        if success:
            success_count += 1
    
    return True, f"Retried {retried_count} emails, {success_count} succeeded", retried_count, success_count