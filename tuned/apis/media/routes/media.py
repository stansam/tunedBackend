import os
from flask import request, make_response
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
import logging

from tuned.apis.media.schemas.media import BulkDownloadSchema
from tuned.utils.responses import error_response
from tuned.utils.dependencies import get_services
from tuned.core.logging import get_logger

logger = get_logger(__name__)


class DownloadMediaView(MethodView):
    decorators = [login_required]

    def get(self, asset_id: str):
        try:
            services = get_services()
            
            # Check download permission
            if not services.media.verify_download_permission(asset_id, current_user.id):
                logger.warning(
                    "[DownloadMediaView] User %s unauthorized to download asset %s",
                    current_user.id, asset_id
                )
                return error_response(message="Unauthorized to download this file", status=403)

            asset = services.media.get_by_id(asset_id)

            response = make_response()

            response.headers['X-Accel-Redirect'] = f"/protected_media/{asset.storage_path}"
            response.headers['Content-Disposition'] = f"attachment; filename=\"{asset.original_filename}\""

            return response
        except Exception as exc:
            logger.error("[DownloadMediaView] Failed to download asset %s: %r", asset_id, exc)
            return error_response(message="Failed to download file", status=500)


class BulkDownloadMediaView(MethodView):
    decorators = [login_required]

    def post(self):
        try:
            data = request.get_json()
            if not data:
                return error_response(message="No input data provided", status=400)

            try:
                dto = BulkDownloadSchema().load(data)
            except ValidationError as err:
                return error_response(message="Validation failed", status=400)

            services = get_services()
            zip_rel_path = services.media.create_bulk_zip(dto["asset_ids"], current_user.id)

            response = make_response()
            response.headers['X-Accel-Redirect'] = f"/protected_media/{zip_rel_path}"
            response.headers['Content-Disposition'] = "attachment; filename=\"files.zip\""
            response.headers['Content-Type'] = "application/zip"
            return response
        except ValidationError as val_err:
            return error_response(message=str(val_err), status=400)
        except Exception as exc:
            logger.error("[BulkDownloadMediaView] Failed to download bulk package: %r", exc)
            return error_response(message="Failed to download package", status=500)


class DownloadOrderFilesView(MethodView):
    decorators = [login_required]

    def get(self, order_id: str):
        try:
            services = get_services()
            zip_rel_path = services.media.create_order_zip(order_id, current_user.id)

            response = make_response()
            response.headers['X-Accel-Redirect'] = f"/protected_media/{zip_rel_path}"
            response.headers['Content-Disposition'] = f"attachment; filename=\"order_{order_id}_files.zip\""
            response.headers['Content-Type'] = "application/zip"
            return response
        except ValidationError as val_err:
            return error_response(message=str(val_err), status=403)
        except Exception as exc:
            logger.error("[DownloadOrderFilesView] Failed to download order %s package: %r", order_id, exc)
            return error_response(message="Failed to download order package", status=500)

class DownloadOrderFileView(MethodView):
    decorators = [login_required]

    def get(self, file_id: str, order_id: str):
        try:
            services = get_services()
            file = services.order.get_order_file(file_id, order_id, current_user.id)
            
            response = make_response()
            response.headers['X-Accel-Redirect'] = f"/protected_media/{file.url}"
            response.headers['Content-Disposition'] = f"attachment; filename=\"{file.filename}\""
            return response
        except ValidationError as val_err:
            return error_response(message=str(val_err), status=403)
        except Exception as exc:
            logger.error("[DownloadOrderFileView] Failed to download order file %s: %r", file_id, exc)
            return error_response(message="Failed to download order file", status=500)


class DownloadDeliveryFilesView(MethodView):
    decorators = [login_required]

    def get(self, delivery_id: str):
        try:
            services = get_services()
            zip_rel_path = services.media.create_delivery_zip(delivery_id, current_user.id)

            response = make_response()
            response.headers['X-Accel-Redirect'] = f"/protected_media/{zip_rel_path}"
            response.headers['Content-Disposition'] = f"attachment; filename=\"delivery_{delivery_id}_files.zip\""
            response.headers['Content-Type'] = "application/zip"
            return response
        except ValidationError as val_err:
            return error_response(message=str(val_err), status=403)
        except Exception as exc:
            logger.error("[DownloadDeliveryFilesView] Failed to download delivery %s package: %r", delivery_id, exc)
            return error_response(message="Failed to download delivery package", status=500)
