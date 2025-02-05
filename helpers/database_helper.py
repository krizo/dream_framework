from datetime import datetime
from typing import Any


def serialize_value(value: Any) -> Any:
    """
    Serialize value for database storage.

    @param value: Value to serialize
    @return: Serialized value suitable for JSON storage
    """
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    return value
