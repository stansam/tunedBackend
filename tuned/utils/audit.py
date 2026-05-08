import json
import re
from typing import Any, Optional, Set
from datetime import datetime
import uuid
from decimal import Decimal
from enum import Enum
from sqlalchemy.inspection import inspect
import logging

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS: Set[str] = {
    "password", "token", "secret", "card_number", "cvv", 
    "pin", "api_key", "authorization", "password_hash"
}

def sanitize_ip(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    
    ipv4_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])$"
    
    if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
        return ip
    return None

def truncate_user_agent(ua: Optional[str], max_len: int = 255) -> Optional[str]:
    if not ua:
        return None
    return ua[:max_len]

def mask_sensitive_fields(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: ("********" if k.lower() in SENSITIVE_FIELDS else mask_sensitive_fields(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_fields(item) for item in data]
    return data

def json_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value

    raise TypeError(f"Type {type(obj)} not serializable")

def model_to_dict(model):
    mapper = inspect(model)
    return {
        c.key: mapper.attrs[c.key].value
        for c in mapper.mapper.column_attrs
    }

def sanitize_json_snapshot(data: Any) -> Optional[dict[str, Any]]:
    if data is None:
        return None
    try:
        masked_data = mask_sensitive_fields(data)
        if not isinstance(masked_data, dict):
            try:
                masked_data = model_to_dict(masked_data)
            except (TypeError, AttributeError) as e:
                logger.warning(f"Non-serializable data snapshot intercepted: {str(e)}")
                if hasattr(masked_data, "__dict__"):
                    masked_data = {
                        k: v
                        for k, v in masked_data.__dict__.items()
                        if not k.startswith("_")
                    }
                else:
                    masked_data = {"data": masked_data}

        normalized = json.loads(
            json.dumps(masked_data, default=json_serializer)
        )
        return normalized
    except (TypeError, ValueError) as e:
        logger.exception(f"failed to serialize data snapshot: {str(e)}")
        return {"error": "Non-serializable data snapshot intercepted"}
