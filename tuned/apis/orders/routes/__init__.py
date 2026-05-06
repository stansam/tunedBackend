from tuned.apis.orders.routes.orders import CreateOrderView, ValidateDiscountView, UploadOrderFilesView, SaveDraftView

ORDER_ROUTES = [
    {"url_rule": "/", "view_func": CreateOrderView.as_view("create_order"), "methods": ["POST"]},
    {"url_rule": "/validate-discount", "view_func": ValidateDiscountView.as_view("validate_discount"), "methods": ["POST"]},
    {"url_rule": "/<string:order_id>/upload-files", "view_func": UploadOrderFilesView.as_view("upload_files"), "methods": ["POST"]},
    {"url_rule": "/draft", "view_func": SaveDraftView.as_view("draft"), "methods": ["POST", "GET"]}
]
