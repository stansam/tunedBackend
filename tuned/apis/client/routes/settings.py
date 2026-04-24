from flask import request
from flask_login import current_user, login_required
from flask.views import MethodView
from tuned.interface import preferences as _interface
from tuned.utils.responses import error_response, success_response, validation_error_response
from tuned.utils.auth import get_user_ip, get_user_agent
from tuned.dtos.base import BaseRequestDTO
from marshmallow import ValidationError
from tuned.apis.client.schemas.settings import (
    LocalizationUpdateSchema, NotificationUpdateSchema, EmailPreferenceUpdateSchema,
    PrivacyUpdateSchema, AccessibilityUpdateSchema, BillingPreferenceUpdateSchema
)
import logging

logger: logging.Logger = logging.getLogger(__name__)

class SettingsView(MethodView):
    decorators = [login_required]

    def get(self):
        try:
            settings_data = _interface.get_user_preferences(current_user.id)
            return success_response(settings_data.to_dict())
        except Exception as e:
            logger.error(f"Get settings error: {str(e)}")
            return error_response("Failed to fetch settings", status=500)

class SettingsCategoryView(MethodView):
    decorators = [login_required]

    def patch(self, category):
        schema_map = {
            "localization": LocalizationUpdateSchema(),
            "notification": NotificationUpdateSchema(),
            "email": EmailPreferenceUpdateSchema(),
            "privacy": PrivacyUpdateSchema(),
            "accessibility": AccessibilityUpdateSchema(),
            "billing": BillingPreferenceUpdateSchema()
        }

        schema = schema_map.get(category)
        if not schema:
            return error_response("Invalid settings category", status=400)

        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return validation_error_response(err.messages)

        try:
            locale = BaseRequestDTO(ip_address=get_user_ip(), user_agent=get_user_agent())
            success = _interface.update_category(category, current_user.id, data, locale)
            
            if success:
                return success_response({"success": True})
            else:
                return error_response("Failed to update settings", status=500)
        except Exception as e:
            logger.error(f"Update settings error for {category}: {str(e)}")
            return error_response("Failed to update settings", status=500)
