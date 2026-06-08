from tuned.apis.media.routes.media import (
    DownloadMediaView,
    BulkDownloadMediaView,
    DownloadOrderFilesView,
    DownloadDeliveryFilesView
)
from typing import Any

MEDIA_ROUTES: list[dict[str, Any]] = [
    {
        "rule": "/download/<string:asset_id>",
        "view_func": DownloadMediaView.as_view("download_media"),
        "methods": ["GET"]
    },
    {
        "rule": "/download/bulk",
        "view_func": BulkDownloadMediaView.as_view("bulk_download_media"),
        "methods": ["POST"]
    },
    {
        "rule": "/download/order/<string:order_id>",
        "view_func": DownloadOrderFilesView.as_view("download_order_files"),
        "methods": ["GET"]
    },
    {
        "rule": "/download/delivery/<string:delivery_id>",
        "view_func": DownloadDeliveryFilesView.as_view("download_delivery_files"),
        "methods": ["GET"]
    },
]

__all__ = ["MEDIA_ROUTES"]