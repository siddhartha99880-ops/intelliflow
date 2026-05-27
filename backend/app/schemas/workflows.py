from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Literal
import uuid


class WorkflowNodePayload(BaseModel):
    id: uuid.UUID
    type: Literal[
        "trigger",
        "llm_agent",
        "decision",
        "api_action",
        "slack",
        "notion",
        "email",
        "delay",
        "human_approval",
    ]
    label: str
    position_x: int = 0
    position_y: int = 0
    data: dict[str, Any] = {}


class WorkflowEdgePayload(BaseModel):
    id: uuid.UUID | None = None
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    condition_key: str | None = None


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str | None = None
    nodes: list[WorkflowNodePayload]
    edges: list[WorkflowEdgePayload]


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    graph_version: int


class ExecuteWorkflowRequest(BaseModel):
    # User-provided starting context (ex: slack message text, gmail payload, etc.)
    input_payload: dict[str, Any] = {}


class ExecuteWorkflowResponse(BaseModel):
    execution_id: uuid.UUID
    status: str

