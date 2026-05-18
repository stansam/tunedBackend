from tuned.apis.order_deliveries.routes.delivery import (
    CreateDeliveryView,
    GetOrderDeliveriesView,
    GetDeliveryByIdView,
    AddDeliveryFilesView,
    UpdateDeliveryStatusView,
    MarkClientNotifiedView,
    DeleteDeliveryView,
)

DELIVERY_ROUTES = [
    {
        "url_rule": "/create/<string:order_id>",
        "view_func": CreateDeliveryView.as_view("create_delivery"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/list/<string:order_id>",
        "view_func": GetOrderDeliveriesView.as_view("get_order_deliveries"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<string:delivery_id>",
        "view_func": GetDeliveryByIdView.as_view("get_delivery_by_id"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<string:delivery_id>/files",
        "view_func": AddDeliveryFilesView.as_view("add_delivery_files"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<string:delivery_id>/status",
        "view_func": UpdateDeliveryStatusView.as_view("update_delivery_status"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/<string:delivery_id>/notified",
        "view_func": MarkClientNotifiedView.as_view("mark_client_notified"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/<string:delivery_id>",
        "view_func": DeleteDeliveryView.as_view("delete_delivery"),
        "methods": ["DELETE"],
    },
]