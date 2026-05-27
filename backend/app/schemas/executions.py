from __future__ import annotations

from pydantic import BaseModel
from typing import Any
import uuid
import datetime as dt


class ExecutionStepResponse(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    node_type: str
    step_index: int
    attempt: int
    status: str
    started_at: dt.datetime | None
    finished_at: dt.datetime | None
    error_text: str | None
    input_json: dict[str, Any]
    output_json: dict[str, Any]


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    team_id: uuid.UUID
    status: str
    error_text: str | None
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    duration_ms: int | None
    created_at: dt.datetime
    started_at: dt.datetime | None
    finished_at: dt.datetime | None
    steps: list[ExecutionStepResponse] = []

