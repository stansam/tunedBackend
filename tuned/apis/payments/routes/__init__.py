from tuned.apis.payments.routes.method import PaymentMethodsView
from tuned.apis.payments.routes.payment import (
    CheckoutView, AdminVerifyPaymentView, AdminRejectPaymentView,
    ListPaymentsView, DownloadInvoiceView, DownloadReceiptView, GetOrderPaymentView
)
from tuned.apis.payments.routes.pesapal import PesapalIpnView
from tuned.apis.payments.routes.invoice import ListInvoicesView, GetInvoiceView
from tuned.apis.payments.routes.discount import ValidateDiscountAtCheckoutView

PAYMENT_ROUTES = [
    # Public
    {"url_rule": "/pesapal/ipn", "view_func": PesapalIpnView.as_view("pesapal_ipn"), "methods": ["GET"]},

    # Client
    {"url_rule": "/methods", "view_func": PaymentMethodsView.as_view("methods"), "methods": ["GET"]},
    {"url_rule": "/checkout", "view_func": CheckoutView.as_view("checkout"), "methods": ["POST"]},
    {"url_rule": "/", "view_func": ListPaymentsView.as_view("list_payments"), "methods": ["GET"]},
    {"url_rule": "/order/<order_id>", "view_func": GetOrderPaymentView.as_view("get_order_payment"), "methods": ["GET"]},
    {"url_rule": "/<payment_id>/invoice", "view_func": DownloadInvoiceView.as_view("download_invoice"), "methods": ["GET"]},
    {"url_rule": "/<payment_id>/receipt", "view_func": DownloadReceiptView.as_view("download_receipt"), "methods": ["GET"]},
    {"url_rule": "/invoices", "view_func": ListInvoicesView.as_view("list_invoices"), "methods": ["GET"]},
    {"url_rule": "/invoices/<invoice_id>", "view_func": GetInvoiceView.as_view("get_invoice"), "methods": ["GET"]},
    {"url_rule": "/discount/validate", "view_func": ValidateDiscountAtCheckoutView.as_view("validate_discount"), "methods": ["POST"]},

    # Admin
    {"url_rule": "/verify/<payment_id>", "view_func": AdminVerifyPaymentView.as_view("admin_verify"), "methods": ["PUT"]},
    {"url_rule": "/reject/<payment_id>", "view_func": AdminRejectPaymentView.as_view("admin_reject"), "methods": ["PUT"]},
]