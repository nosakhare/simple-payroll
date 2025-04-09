from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from models import Payroll, PayrollItem, Employee
from forms import PayrollForm, PayrollProcessForm
from utils import format_currency, process_payroll, generate_payslip_data

payroll = Blueprint('payroll', __name__)

@payroll.route('/')
@login_required
def index():
    """Display list of payrolls."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get paginated list of payrolls
    payrolls = Payroll.query.order_by(Payroll.date_created.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'payroll/index.html', 
        payrolls=payrolls,
        format_currency=format_currency
    )

@payroll.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new payroll."""
    form = PayrollForm()
    
    if form.validate_on_submit():
        # Create new payroll
        payroll = Payroll(
            name=form.name.data,
            period_start=form.period_start.data,
            period_end=form.period_end.data,
            payment_date=form.payment_date.data,
            status='Draft',
            created_by_id=current_user.id
        )
        
        db.session.add(payroll)
        db.session.commit()
        
        flash(f'Payroll "{payroll.name}" created successfully.', 'success')
        return redirect(url_for('payroll.view', id=payroll.id))
        
    return render_template('payroll/process.html', form=form, creating=True)

@payroll.route('/view/<int:id>')
@login_required
def view(id):
    """View payroll details."""
    payroll = Payroll.query.get_or_404(id)
    
    # Get employees in this payroll
    payroll_items = PayrollItem.query.filter_by(payroll_id=payroll.id).all()
    
    # Get process form if payroll is in draft status
    process_form = None
    if payroll.status == 'Draft':
        process_form = PayrollProcessForm()
        process_form.payroll_id.data = payroll.id
    
    return render_template(
        'payroll/view.html', 
        payroll=payroll,
        payroll_items=payroll_items,
        process_form=process_form,
        format_currency=format_currency
    )

@payroll.route('/process', methods=['POST'])
@login_required
def process():
    """Process a payroll."""
    form = PayrollProcessForm()
    
    if form.validate_on_submit():
        payroll_id = int(form.payroll_id.data)
        
        # Process the payroll
        success, message = process_payroll(payroll_id)
        
        if success:
            flash(message, 'success')
        else:
            flash(f'Error processing payroll: {message}', 'danger')
            
        return redirect(url_for('payroll.view', id=payroll_id))
    
    flash('Invalid form submission.', 'danger')
    return redirect(url_for('payroll.index'))

@payroll.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a payroll."""
    payroll = Payroll.query.get_or_404(id)
    
    # Check if payroll can be deleted
    if payroll.status != 'Draft':
        flash('Only draft payrolls can be deleted.', 'danger')
        return redirect(url_for('payroll.view', id=payroll.id))
    
    # Store name before deletion for flash message
    payroll_name = payroll.name
    
    # Delete all associated payroll items
    PayrollItem.query.filter_by(payroll_id=payroll.id).delete()
    
    # Delete the payroll
    db.session.delete(payroll)
    db.session.commit()
    
    flash(f'Payroll "{payroll_name}" deleted successfully.', 'success')
    return redirect(url_for('payroll.index'))

@payroll.route('/payslip/<int:id>')
@login_required
def payslip(id):
    """View a payslip for a specific payroll item."""
    payroll_item = PayrollItem.query.get_or_404(id)
    
    # Generate payslip data
    payslip_data = generate_payslip_data(id)
    if not payslip_data:
        flash('Error generating payslip.', 'danger')
        return redirect(url_for('payroll.view', id=payroll_item.payroll_id))
    
    return render_template(
        'payroll/payslip.html',
        payslip=payslip_data,
        format_currency=format_currency
    )
