from __future__ import annotations

from typing import Any

# Simple in-process mock store.
_STATE: dict[str, list[dict[str, Any]]] = {
    "customers": [],
    "orders": [],
    "inventory": [],
    "finance_entries": [],
}


async def create_customer(name: str, email: str | None = None) -> dict[str, Any]:
    obj = {"id": f"cust_{len(_STATE['customers'])+1}", "name": name, "email": email}
    _STATE["customers"].append(obj)
    return obj


async def create_erp_entry(entry_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Used for invoices / updates / finance entries.
    obj = {"id": f"{entry_type}_{len(_STATE.get(entry_type, []))+1}", "payload": payload}
    key = entry_type if entry_type in _STATE else "finance_entries"
    _STATE[key].append(obj)
    return obj

