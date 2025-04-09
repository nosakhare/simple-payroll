from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from models import Payroll, PayrollItem, Employee, PayrollAdjustment
from forms import (
    PayrollForm, PayrollProcessForm, PayrollStatusForm, 
    PayrollAdjustmentForm
)
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
    
    # Initialize forms based on payroll status
    process_form = None
    status_form = None
    
    # Display different forms based on payroll status
    if payroll.status == 'Draft':
        process_form = PayrollProcessForm()
        process_form.payroll_id.data = payroll.id
    
    # Status form for changing payroll status
    status_form = PayrollStatusForm()
    status_form.payroll_id.data = payroll.id
    status_form.status.data = payroll.status
    
    return render_template(
        'payroll/view.html', 
        payroll=payroll,
        payroll_items=payroll_items,
        process_form=process_form,
        status_form=status_form,
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

@payroll.route('/update-status', methods=['POST'])
@login_required
def update_status():
    """Update payroll status."""
    form = PayrollStatusForm()
    
    if form.validate_on_submit():
        payroll_id = int(form.payroll_id.data)
        payroll = Payroll.query.get_or_404(payroll_id)
        
        # Store the old status for messaging
        old_status = payroll.status
        new_status = form.status.data
        
        # Validate status transitions
        valid_transition = True
        error_message = ""
        
        # Define allowed status transitions based on current status
        if old_status == 'Draft' and new_status not in ['Draft', 'Active', 'Cancelled']:
            valid_transition = False
            error_message = "A draft payroll can only be marked as Active or Cancelled"
        elif old_status == 'Active' and new_status not in ['Active', 'Processing', 'Closed']:
            valid_transition = False
            error_message = "An active payroll can only be moved to Processing or Closed status"
        elif old_status == 'Processing' and new_status not in ['Processing', 'Completed']:
            valid_transition = False
            error_message = "A processing payroll can only be moved to Completed status"
        elif old_status == 'Completed' and new_status not in ['Completed', 'Closed']:
            valid_transition = False
            error_message = "A completed payroll can only be moved to Closed status"
        elif old_status in ['Closed', 'Cancelled'] and new_status != old_status:
            valid_transition = False
            error_message = f"A {old_status.lower()} payroll cannot change status"
            
        if not valid_transition:
            flash(error_message, 'danger')
            return redirect(url_for('payroll.view', id=payroll_id))
            
        # Handle the is_active flag specially
        if new_status == 'Active':
            # First, deactivate all other active payrolls
            Payroll.query.filter_by(is_active=True).update({'is_active': False})
            payroll.is_active = True
        elif old_status == 'Active' and new_status != 'Active':
            payroll.is_active = False
            
        # Update the payroll status
        payroll.status = new_status
        payroll.date_updated = datetime.utcnow()
        db.session.commit()
        
        flash(f'Payroll status updated from {old_status} to {new_status}.', 'success')
        return redirect(url_for('payroll.view', id=payroll_id))
    
    flash('Invalid form submission.', 'danger')
    return redirect(url_for('payroll.index'))

@payroll.route('/payroll-item/<int:id>')
@login_required
def view_payroll_item(id):
    """View and manage a specific payroll item."""
    import json
    payroll_item = PayrollItem.query.get_or_404(id)
    payroll = Payroll.query.get_or_404(payroll_item.payroll_id)
    employee = Employee.query.get_or_404(payroll_item.employee_id)
    
    # Get all adjustments for this payroll item
    adjustments = PayrollAdjustment.query.filter_by(payroll_item_id=id).order_by(PayrollAdjustment.date_created.desc()).all()
    
    # Parse JSON fields from the payroll item
    allowances_dict = json.loads(payroll_item.allowances) if payroll_item.allowances else {}
    deductions_dict = json.loads(payroll_item.deductions) if payroll_item.deductions else {}
    tax_details_dict = json.loads(payroll_item.tax_details) if payroll_item.tax_details else {}
    
    # Create a new adjustment form if the payroll is in an editable state
    adjustment_form = None
    if payroll.status in ['Active', 'Processing']:
        adjustment_form = PayrollAdjustmentForm()
        adjustment_form.payroll_id.data = payroll.id
        adjustment_form.payroll_item_id.data = id
    
    return render_template(
        'payroll/payroll_item.html',
        payroll_item=payroll_item,
        payroll=payroll,
        employee=employee,
        adjustments=adjustments,
        adjustment_form=adjustment_form,
        allowances=allowances_dict,
        deductions=deductions_dict,
        tax_details=tax_details_dict,
        format_currency=format_currency
    )

@payroll.route('/add-adjustment', methods=['POST'])
@login_required
def add_adjustment():
    """Add an adjustment to a payroll item."""
    form = PayrollAdjustmentForm()
    
    if form.validate_on_submit():
        payroll_id = int(form.payroll_id.data)
        payroll_item_id = int(form.payroll_item_id.data)
        
        # Verify the payroll item exists
        payroll_item = PayrollItem.query.get_or_404(payroll_item_id)
        payroll = Payroll.query.get_or_404(payroll_id)
        
        # Verify the payroll is in a state that allows adjustments
        if payroll.status not in ['Active', 'Processing']:
            flash('Adjustments can only be made to active or processing payrolls.', 'danger')
            return redirect(url_for('payroll.view_payroll_item', id=payroll_item_id))
        
        # Create the adjustment with positive or negative amount based on type
        amount = form.amount.data
        if form.adjustment_type.data == 'deduction':
            amount = -amount  # Make deductions negative
            
        # Create and save the adjustment
        adjustment = PayrollAdjustment(
            payroll_id=payroll_id,
            payroll_item_id=payroll_item_id,
            adjustment_type=form.adjustment_type.data,
            description=form.description.data,
            amount=amount,
            created_by_id=current_user.id
        )
        
        db.session.add(adjustment)
        
        # Mark the payroll item as adjusted
        payroll_item.is_adjusted = True
        
        # Recalculate net pay
        payroll_item.recalculate_net_pay()
        
        db.session.commit()
        
        flash(f'Adjustment added successfully. Net pay updated to {format_currency(payroll_item.net_pay)}.', 'success')
        return redirect(url_for('payroll.view_payroll_item', id=payroll_item_id))
    
    flash('Invalid form submission.', 'danger')
    return redirect(url_for('payroll.index'))

@payroll.route('/payslip/<int:id>')
@login_required
def payslip(id):
    """View a payslip for a specific payroll item."""
    payroll_item = PayrollItem.query.get_or_404(id)
    
    # Check if a PDF payslip already exists for this item
    from models import Payslip
    existing_payslip = Payslip.query.filter_by(payroll_item_id=id).first()
    
    if existing_payslip:
        # Redirect to payslip view
        flash('A PDF payslip already exists for this item.', 'info')
        return redirect(url_for('payslips.view', id=existing_payslip.id))
    
    # Generate payslip data for the HTML view
    payslip_data = generate_payslip_data(id)
    if not payslip_data:
        flash('Error generating payslip.', 'danger')
        return redirect(url_for('payroll.view', id=payroll_item.payroll_id))
    
    return render_template(
        'payroll/payslip.html',
        payslip=payslip_data,
        format_currency=format_currency
    )
