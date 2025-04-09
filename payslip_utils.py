import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, 
    PageBreak, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line
from flask import current_app
import cairosvg
from PIL import Image as PILImage
import tempfile

from app import db
from models import Payslip, Employee, Payroll, PayrollItem, EmailLog, User
from utils import format_currency, generate_payslip_data

def convert_svg_to_png(svg_path):
    """
    Convert SVG file to PNG format for use with ReportLab.
    
    Args:
        svg_path: Path to SVG file
        
    Returns:
        Path to temporary PNG file
    """
    try:
        # Create a temporary file for the PNG output
        fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
        # Convert SVG to PNG
        cairosvg.svg2png(url=svg_path, write_to=temp_path)
        
        return temp_path
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return None

def create_payslip_pdf(payroll_item_id, user_id):
    """
    Generate a PDF payslip for a specific payroll item.
    
    Args:
        payroll_item_id: ID of the PayrollItem to generate payslip for
        user_id: ID of the user generating the payslip
        
    Returns:
        A tuple of (success, message, payslip_id)
    """
    # Get the payslip data
    payslip_data = generate_payslip_data(payroll_item_id)
    if not payslip_data:
        return False, "Failed to generate payslip data", None
    
    # Check if a payslip already exists for this payroll item
    existing_payslip = Payslip.query.filter_by(payroll_item_id=payroll_item_id).first()
    if existing_payslip:
        return True, "Payslip already exists", existing_payslip.id
    
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    
    # Get payslip data
    employee = payslip_data['employee']
    payroll = payslip_data['payroll']
    payroll_item = payslip_data['payroll_item']
    
    # Set up the document
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=2*cm, 
        leftMargin=2*cm,
        topMargin=2*cm, 
        bottomMargin=2*cm,
        title=f"Payslip - {employee.full_name()} - {payroll.name}"
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CompanyName', 
        fontName='Helvetica-Bold', 
        fontSize=16, 
        alignment=1,  # Center alignment
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='PayslipTitle', 
        fontName='Helvetica-Bold', 
        fontSize=14, 
        alignment=1,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle', 
        fontName='Helvetica-Bold', 
        fontSize=12, 
        spaceBefore=10, 
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='EmployeeInfo', 
        fontName='Helvetica', 
        fontSize=10, 
        spaceBefore=0, 
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='TableHeader', 
        fontName='Helvetica-Bold', 
        fontSize=9, 
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name='TableCell', 
        fontName='Helvetica', 
        fontSize=9,
        alignment=0
    ))
    styles.add(ParagraphStyle(
        name='FooterText', 
        fontName='Helvetica', 
        fontSize=8, 
        alignment=1,
        textColor=colors.gray,
        # Use italic parameter instead of Helvetica-Italic font name
        italic=True
    ))
    
    # Build the PDF content
    elements = []
    
    # Company header
    company_name = current_app.config.get('COMPANY_NAME')
    company_address = current_app.config.get('COMPANY_ADDRESS')
    company_city = current_app.config.get('COMPANY_CITY')
    company_country = current_app.config.get('COMPANY_COUNTRY')
    company_email = current_app.config.get('COMPANY_EMAIL')
    company_phone = current_app.config.get('COMPANY_PHONE')
    
    # Try to add company logo if it exists
    logo_path = current_app.config.get('COMPANY_LOGO')
    full_logo_path = os.path.join(current_app.root_path, logo_path)
    if logo_path and os.path.exists(full_logo_path):
        # Check if it's an SVG file
        if logo_path.lower().endswith('.svg'):
            # Convert SVG to PNG
            temp_png_path = convert_svg_to_png(full_logo_path)
            if temp_png_path:
                try:
                    logo = Image(temp_png_path)
                    logo.drawWidth = 2.5*cm
                    logo.drawHeight = 2.5*cm
                    elements.append(logo)
                    
                    # Schedule the temporary file for deletion
                    # We don't remove it immediately because ReportLab needs it during PDF generation
                    @current_app.teardown_appcontext
                    def remove_temp_file(exception=None):
                        try:
                            if os.path.exists(temp_png_path):
                                os.remove(temp_png_path)
                        except Exception as e:
                            print(f"Error removing temporary file: {e}")
                except Exception as e:
                    print(f"Error adding logo to PDF: {e}")
        else:
            # Use the image directly
            try:
                logo = Image(full_logo_path)
                logo.drawWidth = 2.5*cm
                logo.drawHeight = 2.5*cm
                elements.append(logo)
            except Exception as e:
                print(f"Error adding logo to PDF: {e}")
    
    # Company header
    elements.append(Paragraph(company_name, styles['CompanyName']))
    elements.append(Paragraph(f"{company_address}, {company_city}, {company_country}", styles['EmployeeInfo']))
    elements.append(Paragraph(f"Email: {company_email} | Phone: {company_phone}", styles['EmployeeInfo']))
    
    # Divider line
    elements.append(Spacer(1, 0.5*cm))
    
    # Payslip title with period
    elements.append(Paragraph("PAYSLIP", styles['PayslipTitle']))
    elements.append(Paragraph(
        f"Period: {payroll.period_start.strftime('%d %B, %Y')} to {payroll.period_end.strftime('%d %B, %Y')}",
        styles['EmployeeInfo']
    ))
    elements.append(Paragraph(f"Payment Date: {payroll.payment_date.strftime('%d %B, %Y')}", styles['EmployeeInfo']))
    elements.append(Paragraph(f"Generated On: {payslip_data['generated_on']}", styles['EmployeeInfo']))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Employee information
    elements.append(Paragraph("EMPLOYEE INFORMATION", styles['SectionTitle']))
    
    employee_data = [
        ["Employee Name:", f"{employee.first_name} {employee.last_name}", "Employee ID:", employee.employee_id],
        ["Department:", employee.department, "Position:", employee.position],
        ["Bank Name:", employee.bank_name, "Account Number:", employee.account_number],
        ["Payment Method:", payslip_data['payment_method'], "", ""]
    ]
    
    employee_table = Table(employee_data, colWidths=[4*cm, 5*cm, 3*cm, 4*cm])
    employee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
    ]))
    elements.append(employee_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Earnings section
    elements.append(Paragraph("EARNINGS", styles['SectionTitle']))
    
    earnings_data = [["Description", "Amount"]]
    earnings_data.append(["Basic Salary", format_currency(payroll_item.basic_salary)])
    
    # Add allowances
    for allowance_name, amount in payslip_data['allowances'].items():
        earnings_data.append([allowance_name, format_currency(amount)])
    
    # Add bonuses and reimbursements if any
    if payslip_data['has_adjustments']:
        if payslip_data['adjustment_totals']['bonuses'] > 0:
            earnings_data.append(["Bonuses", format_currency(payslip_data['adjustment_totals']['bonuses'])])
        if payslip_data['adjustment_totals']['reimbursements'] > 0:
            earnings_data.append(["Reimbursements", format_currency(payslip_data['adjustment_totals']['reimbursements'])])
    
    # Calculate total earnings
    total_earnings = payroll_item.gross_pay
    if payslip_data['has_adjustments']:
        total_earnings += payslip_data['adjustment_totals']['bonuses'] + payslip_data['adjustment_totals']['reimbursements']
    
    earnings_data.append(["Total Earnings", format_currency(total_earnings)])
    
    earnings_table = Table(earnings_data, colWidths=[8*cm, 8*cm])
    earnings_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(earnings_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Deductions section
    elements.append(Paragraph("DEDUCTIONS", styles['SectionTitle']))
    
    deductions_data = [["Description", "Amount"]]
    
    # Add standard deductions
    for deduction_name, amount in payslip_data['deductions'].items():
        deductions_data.append([deduction_name, format_currency(amount)])
    
    # Add any additional deductions from adjustments
    if payslip_data['has_adjustments'] and payslip_data['adjustment_totals']['additional_deductions'] > 0:
        deductions_data.append(["Additional Deductions", format_currency(payslip_data['adjustment_totals']['additional_deductions'])])
    
    # Calculate total deductions
    total_deductions = (
        payroll_item.tax_amount + 
        payroll_item.pension_amount + 
        payroll_item.nhf_amount + 
        payroll_item.other_deductions
    )
    if payslip_data['has_adjustments']:
        total_deductions += payslip_data['adjustment_totals']['additional_deductions']
    
    deductions_data.append(["Total Deductions", format_currency(total_deductions)])
    
    deductions_table = Table(deductions_data, colWidths=[8*cm, 8*cm])
    deductions_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(deductions_table)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Net pay section
    elements.append(Paragraph("NET PAY", styles['SectionTitle']))
    
    net_pay_data = [["Description", "Amount"]]
    net_pay_data.append(["Gross Pay", format_currency(payroll_item.gross_pay)])
    net_pay_data.append(["Total Deductions", format_currency(total_deductions)])
    
    # Display positive adjustments (bonuses and reimbursements) if any
    if payslip_data['has_adjustments'] and payslip_data['adjustment_totals']['positive_adjustments'] > 0:
        net_pay_data.append(["Positive Adjustments", format_currency(payslip_data['adjustment_totals']['positive_adjustments'])])
    
    net_pay_data.append(["Net Pay", format_currency(payroll_item.net_pay)])
    
    net_pay_table = Table(net_pay_data, colWidths=[8*cm, 8*cm])
    net_pay_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(net_pay_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # Footer text
    elements.append(Paragraph("This is a computer-generated document and does not require a signature.", styles['FooterText']))
    elements.append(Paragraph(f"Nigerian Payroll System | {datetime.now().year} © All Rights Reserved", styles['FooterText']))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF from the buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Generate filename
    filename = f"payslip_{employee.employee_id}_{payroll.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Create Payslip record
    payslip = Payslip(
        payroll_item_id=payroll_item_id,
        pdf_data=pdf_data,
        filename=filename,
        file_size=len(pdf_data),
        is_emailed=False,
        created_by_id=user_id
    )
    
    db.session.add(payslip)
    db.session.commit()
    
    return True, "Payslip generated successfully", payslip.id

def generate_all_payslips(payroll_id, user_id):
    """
    Generate payslips for all employees in a payroll run.
    
    Args:
        payroll_id: ID of the payroll to generate payslips for
        user_id: ID of the user generating the payslips
        
    Returns:
        A tuple of (success, message, generated_count)
    """
    # Get all payroll items for this payroll
    payroll_items = PayrollItem.query.filter_by(payroll_id=payroll_id).all()
    
    if not payroll_items:
        return False, "No payroll items found for this payroll", 0
    
    # Generate payslips for each item
    generated_count = 0
    for payroll_item in payroll_items:
        success, _, _ = create_payslip_pdf(payroll_item.id, user_id)
        if success:
            generated_count += 1
    
    return True, f"Generated {generated_count} payslips out of {len(payroll_items)} payroll items", generated_count

def download_payslip(payslip_id):
    """
    Get a payslip PDF by ID.
    
    Args:
        payslip_id: ID of the payslip to download
        
    Returns:
        A tuple of (success, file_data, filename) or (False, error_message, None)
    """
    payslip = Payslip.query.get(payslip_id)
    
    if not payslip:
        return False, "Payslip not found", None
    
    return True, payslip.pdf_data, payslip.filename