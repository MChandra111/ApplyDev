"""Server-Sent Events formatting helpers."""

import json
from typing import Any


def format_sse(data: dict[str, Any]) -> str:
    """Format one SSE message (event + data lines)."""
    payload = json.dumps(data, default=str)
    return f"event: message\ndata: {payload}\n\n"
