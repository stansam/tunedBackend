from io import BytesIO
import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_invoice_pdf(order: Any, include_logo: bool = True, language: str = 'en') -> BytesIO:
    # TODO: implement ReportLab or WeasyPrint
    logger.info(f'Generating PDF invoice for order {order.id}')
    
    pdf_buffer = BytesIO()
    pdf_content = f"""
    INVOICE
    
    Order Number: {order.order_number}
    Date: {order.created_at.strftime('%Y-%m-%d')}
    
    Total: ${order.total_price:.2f}
    
    This is a generated invoice.
    """.encode('utf-8')
    
    pdf_buffer.write(pdf_content)
    pdf_buffer.seek(0)
    
    return pdf_buffer


def generate_receipt_pdf(payment: Any) -> BytesIO:
    # TODO: update implementation
    logger.info(f'Generating PDF receipt for payment {payment.id}')
    
    pdf_buffer = BytesIO()
    pdf_content = f"""
    PAYMENT RECEIPT
    
    Transaction ID: {payment.transaction_id or payment.id}
    Date: {payment.paid_at.strftime('%Y-%m-%d') if payment.paid_at else 'N/A'}
    
    Amount: ${payment.amount:.2f}
    Status: {payment.status.value}
    
    Thank you for your payment.
    """.encode('utf-8')
    
    pdf_buffer.write(pdf_content)
    pdf_buffer.seek(0)
    
    return pdf_buffer
