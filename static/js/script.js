/**
 * Nigerian Payroll System - Main JavaScript file
 * 
 * This file contains common functionality used across the application.
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize popovers if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        
        alerts.forEach(function(alert) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 5000);

    // Enable form validation styles
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function(e) {
            const value = parseFloat(this.value.replace(/[^0-9.-]+/g, ''));
            
            if (!isNaN(value)) {
                this.value = value.toLocaleString('en-NG', {
                    style: 'currency',
                    currency: 'NGN'
                });
            }
        });

        input.addEventListener('focus', function(e) {
            this.value = this.value.replace(/[^0-9.-]+/g, '');
        });
    });

    // Set up datepickers if available
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.date-picker', {
            dateFormat: 'Y-m-d',
            allowInput: true
        });
    }

    // Add confirm dialog to delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm:not([data-bs-toggle="modal"])');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});

/**
 * Format a number as Nigerian Naira
 * @param {number} amount - The amount to format
 * @returns {string} - Formatted currency string
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN'
    }).format(amount);
}

/**
 * Format a date string to a more readable format
 * @param {string} dateString - The date string to format
 * @returns {string} - Formatted date string
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-NG', options);
}

/**
 * Calculate age from date of birth
 * @param {string} dateOfBirth - The date of birth string
 * @returns {number} - Age in years
 */
function calculateAge(dateOfBirth) {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    return age;
}

/**
 * Calculate PAYE tax based on annual income
 * @param {number} annualIncome - Annual taxable income
 * @returns {number} - Annual tax amount
 */
function calculatePAYETax(annualIncome) {
    // Nigerian tax brackets (as of 2023)
    const taxBrackets = [
        { min: 0, max: 300000, rate: 0.07 },
        { min: 300000, max: 600000, rate: 0.11 },
        { min: 600000, max: 1100000, rate: 0.15 },
        { min: 1100000, max: 1600000, rate: 0.19 },
        { min: 1600000, max: 3200000, rate: 0.21 },
        { min: 3200000, max: Infinity, rate: 0.24 }
    ];
    
    let totalTax = 0;
    let remainingIncome = annualIncome;
    
    for (const bracket of taxBrackets) {
        if (remainingIncome <= 0) break;
        
        const taxableInBracket = Math.min(remainingIncome, bracket.max - bracket.min);
        const taxInBracket = taxableInBracket * bracket.rate;
        
        totalTax += taxInBracket;
        remainingIncome -= taxableInBracket;
    }
    
    return totalTax;
}
