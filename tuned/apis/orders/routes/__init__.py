from tuned.apis.orders.routes.orders import (
    CreateOrderView, ValidateDiscountView,
    UploadOrderFilesView, SaveDraftView, GetDraftView, ListClientOrders, GetOrderView
)

ORDER_ROUTES = [
    {"url_rule": "", "view_func": CreateOrderView.as_view("create_order"), "methods": ["POST"]},
    {"url_rule": "/validate-discount", "view_func": ValidateDiscountView.as_view("validate_discount"), "methods": ["POST"]},
    {"url_rule": "/<string:order_id>/upload-files", "view_func": UploadOrderFilesView.as_view("upload_files"), "methods": ["POST"]},
    {"url_rule": "/draft",                    "view_func": SaveDraftView.as_view("save_draft"),             "methods": ["POST"]},
    {"url_rule": "/draft",                    "view_func": GetDraftView.as_view("get_draft"),               "methods": ["GET"]},
    {"url_rule": "/detail/<string:order_number>", "view_func": GetOrderView.as_view("order_details"), "methods": ["GET"]},
    {"url_rule": "/list", "view_func": ListClientOrders.as_view("list_client_orders"), "methods": ["POST"]}
]
