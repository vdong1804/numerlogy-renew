"""SSE (Server-Sent Events) formatting helpers for the chat streaming endpoint.

Single responsibility: convert event name + dict payload to SSE wire bytes.
All JSON is UTF-8 with ensure_ascii=False so Vietnamese text is preserved.
"""

from __future__ import annotations

import json


def sse_event(event: str, data: dict) -> bytes:
    """Encode a single SSE frame as UTF-8 bytes.

    Format:
        event: <event>\n
        data: <json>\n
        \n

    Args:
        event: Event type string (delta | citations | done | error).
        data:  Payload dict; serialized with ensure_ascii=False.

    Returns:
        UTF-8 encoded bytes ready to yield from a StreamingResponse generator.
    """
    return (f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n").encode()
