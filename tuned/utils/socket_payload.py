from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


def safe_payload(data: Any) -> Any:
    """
    Recursively convert non-JSON-serialisable types in a dict/list to safe primitives.
    - datetime → ISO-8601 string
    - uuid.UUID → str
    - Enum → .value
    """
    if isinstance(data, dict):
        return {k: safe_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [safe_payload(v) for v in data]
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, uuid.UUID):
        return str(data)
    if hasattr(data, "value"):  # Enum
        return data.value
    return data
