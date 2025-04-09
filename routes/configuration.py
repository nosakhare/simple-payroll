from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from models import SalaryConfiguration
from forms import SalaryConfigurationForm

configuration = Blueprint('configuration', __name__)

@configuration.route('/')
@login_required
def index():
    """Display list of salary configurations."""
    # Get active configuration first
    active_config = SalaryConfiguration.query.filter_by(is_active=True).first()
    
    # Get all configurations
    configs = SalaryConfiguration.query.order_by(SalaryConfiguration.date_created.desc()).all()
    
    return render_template(
        'configuration/index.html',
        configs=configs,
        active_config=active_config
    )

@configuration.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new salary configuration."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Only administrators can create salary configurations.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get form
    form = SalaryConfigurationForm()
    
    if form.validate_on_submit():
        # Create new salary configuration
        config = SalaryConfiguration(
            name=form.name.data,
            basic_salary_percentage=form.basic_salary_percentage.data,
            transport_allowance_percentage=form.transport_allowance_percentage.data,
            housing_allowance_percentage=form.housing_allowance_percentage.data,
            utility_allowance_percentage=form.utility_allowance_percentage.data,
            meal_allowance_percentage=form.meal_allowance_percentage.data,
            clothing_allowance_percentage=form.clothing_allowance_percentage.data,
            created_by_id=current_user.id,
            is_active=False
        )
        
        db.session.add(config)
        db.session.commit()
        
        flash(f'Salary configuration "{config.name}" created successfully.', 'success')
        return redirect(url_for('configuration.index'))
    
    return render_template('configuration/form.html', form=form, creating=True)

@configuration.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a salary configuration."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Only administrators can edit salary configurations.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the configuration
    config = SalaryConfiguration.query.get_or_404(id)
    
    # Get form
    form = SalaryConfigurationForm(obj=config)
    
    if form.validate_on_submit():
        # Update the configuration
        config.name = form.name.data
        config.basic_salary_percentage = form.basic_salary_percentage.data
        config.transport_allowance_percentage = form.transport_allowance_percentage.data
        config.housing_allowance_percentage = form.housing_allowance_percentage.data
        config.utility_allowance_percentage = form.utility_allowance_percentage.data
        config.meal_allowance_percentage = form.meal_allowance_percentage.data
        config.clothing_allowance_percentage = form.clothing_allowance_percentage.data
        
        db.session.commit()
        
        flash(f'Salary configuration "{config.name}" updated successfully.', 'success')
        return redirect(url_for('configuration.index'))
    
    return render_template('configuration/form.html', form=form, creating=False, config=config)

@configuration.route('/activate/<int:id>', methods=['POST'])
@login_required
def activate(id):
    """Activate a salary configuration (and deactivate all others)."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Only administrators can activate salary configurations.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Deactivate all configurations
    SalaryConfiguration.query.update({SalaryConfiguration.is_active: False})
    
    # Activate the selected configuration
    config = SalaryConfiguration.query.get_or_404(id)
    config.is_active = True
    
    db.session.commit()
    
    flash(f'Salary configuration "{config.name}" is now active.', 'success')
    return redirect(url_for('configuration.index'))

@configuration.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a salary configuration."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Only administrators can delete salary configurations.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the configuration
    config = SalaryConfiguration.query.get_or_404(id)
    
    # Don't allow deletion of active configuration
    if config.is_active:
        flash('You cannot delete the active salary configuration.', 'danger')
        return redirect(url_for('configuration.index'))
    
    # Store name for flash message
    config_name = config.name
    
    # Delete the configuration
    db.session.delete(config)
    db.session.commit()
    
    flash(f'Salary configuration "{config_name}" deleted successfully.', 'success')
    return redirect(url_for('configuration.index'))