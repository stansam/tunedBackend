from io import BytesIO
import logging
from typing import Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from tuned.core.logging import get_logger
logger:logging.Logger = get_logger(__name__)

def generate_invoice_pdf(order: Any, include_logo: bool = True, language: str = 'en', invoice: Any = None) -> BytesIO:
    logger.info(f'Generating beautiful PDF invoice for order {order.id}')
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Premium branding colors
    primary_color = colors.HexColor("#4f46e5")    # Indigo
    secondary_color = colors.HexColor("#1f2937")  # Slate Dark
    text_color = colors.HexColor("#374151")       # Charcoal Text
    light_bg = colors.HexColor("#f9fafb")         # Cool Off-White
    border_color = colors.HexColor("#e5e7eb")     # Light gray border
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=secondary_color,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=text_color,
        leading=14
    )
    bold_body = ParagraphStyle(
        'InvoiceBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white
    )
    
    elements: list[Flowable] = []
    
    # Header Section
    invoice_num = invoice.invoice_number if invoice else (order.invoice.invoice_number if getattr(order, 'invoice', None) else 'INV-TEMP')
    header_data = [
        [
            Paragraph("TUNED ESSAYS", title_style),
            Paragraph("INVOICE", ParagraphStyle('InvoiceText', parent=title_style, alignment=2, fontSize=28, textColor=secondary_color))
        ],
        [
            Paragraph("Professional Academic Solutions & Research Services<br/>support@tunedessays.com | +1 (800) 555-0199", subtitle_style),
            Paragraph(f"<b>Invoice No:</b> {invoice_num}<br/><b>Date:</b> {order.created_at.strftime('%B %d, %Y') if order.created_at else 'N/A'}", ParagraphStyle('RightMeta', parent=body_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[320, 210])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Billing info & Order specs
    client_name = f"{order.client.first_name} {order.client.last_name}" if getattr(order, 'client', None) else "Valued Client"
    client_email = order.client.email if getattr(order, 'client', None) else "N/A"
    
    billing_data = [
        [
            Paragraph("Billed To", section_heading),
            Paragraph("Order Details", section_heading)
        ],
        [
            Paragraph(f"<b>Name:</b> {client_name}<br/><b>Email:</b> {client_email}", body_style),
            Paragraph(f"<b>Order Number:</b> #{order.order_number}<br/><b>Status:</b> PAID", body_style)
        ]
    ]
    billing_table = Table(billing_data, colWidths=[270, 260])
    billing_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
    ]))
    elements.append(billing_table)
    elements.append(Spacer(1, 25))
    
    # Items Table
    item_title = order.title or f"Custom Essay - Order #{order.order_number}"
    service_name = order.service.name if getattr(order, 'service', None) else "Academic Research Service"
    academic_lvl = order.academic_level.name if getattr(order, 'academic_level', None) else "Undergraduate"
    
    table_data = [
        [Paragraph("Item & Description", table_header), Paragraph("Details", table_header), Paragraph("Quantity", table_header), Paragraph("Price", table_header)],
        [
            Paragraph(f"<b>{item_title}</b><br/><font color='#6b7280'>{service_name}</font>", body_style),
            Paragraph(f"Level: {academic_lvl}<br/>Format: {order.format_style.value if order.format_style else 'APA'}", body_style),
            Paragraph(f"{order.page_count or 1} Pages<br/>({order.word_count or 275} Words)", body_style),
            Paragraph(f"${order.subtotal or order.total_price:.2f}", body_style)
        ]
    ]
    
    # Financial breakdowns
    subtotal = float(order.subtotal or order.total_price or 0.0)
    discount = float(order.discount_amount or 0.0)
    total = float(order.total_price or 0.0)
    
    table_data.append([Paragraph("", body_style), Paragraph("", body_style), Paragraph("Subtotal:", bold_body), Paragraph(f"${subtotal:.2f}", body_style)])
    if discount > 0:
        table_data.append([Paragraph("", body_style), Paragraph("", body_style), Paragraph("Discount Applied:", bold_body), Paragraph(f"-${discount:.2f}", body_style)])
    table_data.append([Paragraph("", body_style), Paragraph("", body_style), Paragraph("Total Paid:", bold_body), Paragraph(f"${total:.2f}", bold_body)])
    
    item_table = Table(table_data, colWidths=[200, 150, 100, 80])
    item_table_style: list[tuple[Any, ...]] = [
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,1), 1, border_color),
    ]
    
    # Align summary cells to grid nicely
    item_table_style.extend([
        ('SPAN', (0, 2), (1, 2)),
        ('LINEABOVE', (2, 2), (-1, 2), 1, border_color),
        ('BACKGROUND', (2, -1), (-1, -1), light_bg),
        ('PADDING', (2, 2), (-1, -1), 8),
    ])
    if discount > 0:
        item_table_style.append(('SPAN', (0, 3), (1, 3)))
        item_table_style.append(('SPAN', (0, 4), (1, 4)))
    else:
        item_table_style.append(('SPAN', (0, 3), (1, 3)))
        
    item_table.setStyle(TableStyle(item_table_style))
    elements.append(item_table)
    elements.append(Spacer(1, 40))
    
    # Terms & Signature Block
    footer_data = [
        [
            Paragraph("<b>Terms & Conditions</b><br/><font color='#6b7280'>All services rendered are subject to our standard service terms. This document acts as proof of payment and invoice delivery.</font>", body_style),
            Paragraph("Authorized Signature<br/><br/><b>Tuned Essays Finance Team</b>", ParagraphStyle('Sig', parent=body_style, alignment=1))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[330, 200])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEABOVE', (1,0), (1,0), 0.5, colors.HexColor("#9ca3af")),
        ('TOPPADDING', (1,0), (1,0), 10),
    ]))
    elements.append(footer_table)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_receipt_pdf(payment: Any) -> BytesIO:
    logger.info(f'Generating beautiful PDF receipt for payment {payment.id}')
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#10b981")    # Success Green
    secondary_color = colors.HexColor("#1f2937")  # Slate Dark
    text_color = colors.HexColor("#374151")       # Charcoal
    light_bg = colors.HexColor("#f9fafb")
    border_color = colors.HexColor("#e5e7eb")
    
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=secondary_color,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'ReceiptBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=text_color,
        leading=14
    )
    bold_body = ParagraphStyle(
        'ReceiptBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white
    )
    
    elements: list[Flowable] = []
    
    # Header Section
    header_data = [
        [
            Paragraph("TUNED ESSAYS", title_style),
            Paragraph("RECEIPT", ParagraphStyle('ReceiptText', parent=title_style, alignment=2, fontSize=28, textColor=secondary_color))
        ],
        [
            Paragraph("Professional Academic Solutions & Research Services<br/>support@tunedessays.com | +1 (800) 555-0199", subtitle_style),
            Paragraph(f"<b>Receipt No:</b> {payment.payment_id}<br/><b>Date:</b> {payment.created_at.strftime('%B %d, %Y') if payment.created_at else 'N/A'}", ParagraphStyle('RightMeta', parent=body_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[320, 210])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Billing info & Transaction Details
    client_name = f"{payment.user.first_name} {payment.user.last_name}" if getattr(payment, 'user', None) else "Valued Client"
    client_email = payment.user.email if getattr(payment, 'user', None) else "N/A"
    
    trans_data = [
        [
            Paragraph("Payer Information", section_heading),
            Paragraph("Transaction Specifics", section_heading)
        ],
        [
            Paragraph(f"<b>Name:</b> {client_name}<br/><b>Email:</b> {client_email}", body_style),
            Paragraph(f"<b>Order Number:</b> #{payment.order.order_number if getattr(payment, 'order', None) else 'N/A'}<br/><b>Payment ID:</b> {payment.payment_id}<br/><b>Payment Status:</b> {payment.status.value}", body_style)
        ]
    ]
    trans_table = Table(trans_data, colWidths=[270, 260])
    trans_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
    ]))
    elements.append(trans_table)
    elements.append(Spacer(1, 25))
    
    # Receipt Table
    item_title = payment.order.title if getattr(payment, 'order', None) else "Custom Essay Assignment"
    method_name = payment.accepted_method.name if getattr(payment, 'accepted_method', None) else "Card/Direct Transfer"
    
    table_data = [
        [Paragraph("Transaction Particulars", table_header), Paragraph("Method Used", table_header), Paragraph("Reference Code", table_header), Paragraph("Amount Paid", table_header)],
        [
            Paragraph(f"<b>{item_title}</b><br/><font color='#6b7280'>Tuned Essays Fulfillment Service</font>", body_style),
            Paragraph(f"{method_name}", body_style),
            Paragraph(f"{payment.client_proof_reference or 'Direct Gateway Transaction'}", body_style),
            Paragraph(f"${payment.amount:.2f}", bold_body)
        ]
    ]
    
    receipt_table = Table(table_data, colWidths=[230, 110, 110, 80])
    receipt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,1), 1, border_color),
        ('BACKGROUND', (0, -1), (-1, -1), light_bg),
    ]))
    elements.append(receipt_table)
    elements.append(Spacer(1, 40))
    
    # Note / Success Statement
    footer_data = [
        [
            Paragraph("<b>Thank you for your business!</b><br/><font color='#6b7280'>Your transaction has been processed securely. If you have any inquiries regarding this charge, please contact support@tunedessays.com.</font>", body_style),
            Paragraph("Securely Processed By<br/><br/><b>Tuned Essays Ledger</b>", ParagraphStyle('Sig', parent=body_style, alignment=1))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[330, 200])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEABOVE', (1,0), (1,0), 0.5, colors.HexColor("#9ca3af")),
        ('TOPPADDING', (1,0), (1,0), 10),
    ]))
    elements.append(footer_table)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
