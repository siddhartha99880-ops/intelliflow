from __future__ import annotations

from typing import Any


async def send_message(channel: str, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    # MVP mock: return payload instead of calling Slack API.
    return {
        "channel": channel,
        "text": text,
        "mock": True,
        "context": context or {},
    }


async def trigger_from_message(message: str) -> dict[str, Any]:
    # MVP mock: return parsed message.
    return {"message": message, "mock": True}

