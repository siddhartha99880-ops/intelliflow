from __future__ import annotations

from typing import Any


async def create_task_page(title: str, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "title": title,
        "properties": properties or {},
        "mock": True,
    }


async def update_database_item(database_id: str, item_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    return {"database_id": database_id, "item_id": item_id, "properties": properties, "mock": True}

