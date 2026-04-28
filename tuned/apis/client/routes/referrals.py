from flask import current_app
from flask import request
from flask_login import current_user, login_required
from flask.views import MethodView
from marshmallow import ValidationError
import logging

from tuned.utils.responses import success_response, error_response, validation_error_response
from tuned.apis.client.schemas.referrals import ReferralFilterSchema, RedeemRewardSchema, ReferralShareSchema
from tuned.interface import referral
from dataclasses import asdict
from typing import Any

logger = logging.getLogger(__name__)

_interface = referral


def _validation_error_payload(message: str) -> dict[str, list[str]]:
    return {"non_field_errors": [message]}

class ReferralListView(MethodView):
    decorators = [login_required]
    def get(self) -> tuple[Any, int]:
        try:
            schema = ReferralFilterSchema()
            schema.load(request.args.to_dict())
            referrals = _interface.get_active_by_referrer(str(current_user.id))
            return success_response({"referrals": [asdict(r) for r in referrals]})
        except ValidationError as err:
            logger.error(f"Error listing referrals: {err}")
            return validation_error_response(
                _validation_error_payload("Error listing referrals, invalid params provided")
            )
        except Exception as e:
            logger.error(f"Error listing referrals: {e}")
            return error_response("Failed to fetch referrals", status=500)

class ReferralStatsView(MethodView):
    decorators = [login_required]
    def get(self) -> tuple[Any, int]:
        try:
            referrals = _interface.get_active_by_referrer(str(current_user.id))
            total_earned = sum(r.points_earned for r in referrals if r.status == 'COMPLETED')
            total_used = sum(getattr(r, 'points_used', 0) for r in referrals)
            growth = _interface.get_referral_growth(str(current_user.id))
            
            stats = {
                "total_referrals": len(referrals),
                "total_earned": total_earned,
                "total_used": total_used,
                "current_balance": current_user.reward_points or 0,
                "growth": growth,
                "referral_code": current_user.referral_code
            }
            return success_response({"statistics": stats})
        except Exception as e:
            logger.error(f"Error fetching referral stats: {e}")
            return error_response("Failed to fetch referral statistics", status=500)

class ReferralShareView(MethodView):
    decorators = [login_required]
    def post(self) -> tuple[Any, int]:
        try:
            schema = ReferralShareSchema()
            data = schema.load(request.get_json())
            
            code = current_user.referral_code
            frontend_url = current_app.config.get("FRONTEND_URL") or "http://localhost:3000/"
            share_url = f'{frontend_url}/auth/register?ref={code}'
            message = data.get("message") or f"Join Tuned! Use my code {code}!"
            
            return success_response({
                "share_link": share_url,
                "message": message,
                "platform": data["platform"]
            })
        except ValidationError as err:
            logger.error(f"Error sharing referral: {err}")
            return validation_error_response(
                _validation_error_payload("Error sharing referral, invalid params provided")
            )
        except Exception as e:
            logger.error(f"Error sharing referral: {e}")
            return error_response("Failed to process share request", status=500)

class ReferralRedeemView(MethodView):
    decorators = [login_required]
    def post(self) -> tuple[Any, int]:
        try:
            schema = RedeemRewardSchema()
            data = schema.load(request.get_json())
            
            result = _interface.redeem_points(
                user_id=str(current_user.id),
                order_id=data['order_id'],
                points_to_redeem=data['points']
            )
            
            return success_response(
                asdict(result),
                message=f"Successfully redeemed {result.redeemed_points} points.",
            )
        except ValueError as err:
            logger.error(f"Error redeeming points: {err}")
            return error_response("Error redeeming points", status=500)
        except ValidationError as err:
            logger.error(f"Error redeeming points: {err}")
            return validation_error_response(
                _validation_error_payload("Error redeeming points, invalid params provided")
            )
        except Exception as e:
            logger.error(f"Error redeeming points: {e}")
            return error_response("Failed to redeem points", status=500)
