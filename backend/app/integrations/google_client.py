from __future__ import annotations

from typing import Any


async def extract_invoice_data(text: str) -> dict[str, Any]:
    # Mock extractor
    return {"invoice_number": "INV-0001", "amount": 123.45, "currency": "USD", "supplier": "Mock Supplies"}


async def get_calendar_events(user_id: str) -> list[dict[str, Any]]:
    return [{"id": "evt_1", "title": "Mock Event", "start": "2026-01-01T10:00:00Z"}]

