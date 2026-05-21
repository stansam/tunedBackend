
from tuned.apis.payments.routes.payments import (
    PaymentMethodsView, CheckoutView, PesapalIpnView, 
    AdminVerifyPaymentView, AdminRejectPaymentView,
    ListPaymentsView, DownloadInvoiceView, DownloadReceiptView
)

PAYMENT_ROUTES = [
    {"url_rule": "/methods", "view_func": PaymentMethodsView.as_view("methods"), "methods": ["GET"]},
    {"url_rule": "/checkout", "view_func": CheckoutView.as_view("checkout"), "methods": ["POST"]},
    {"url_rule": "/pesapal/ipn", "view_func": PesapalIpnView.as_view("pesapal_ipn"), "methods": ["GET"]},
    {"url_rule": "/verify/<payment_id>", "view_func": AdminVerifyPaymentView.as_view("admin_verify"), "methods": ["PUT"]},
    {"url_rule": "/reject/<payment_id>", "view_func": AdminRejectPaymentView.as_view("admin_reject"), "methods": ["PUT"]},
    {"url_rule": "/list", "view_func": ListPaymentsView.as_view("list_payments"), "methods": ["GET"]},
    {"url_rule": "/<payment_id>/invoice", "view_func": DownloadInvoiceView.as_view("download_invoice"), "methods": ["GET"]},
    {"url_rule": "/<payment_id>/receipt", "view_func": DownloadReceiptView.as_view("download_receipt"), "methods": ["GET"]}
]