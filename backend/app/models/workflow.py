from __future__ import annotations

import enum
import uuid

from sqlalchemy import String, ForeignKey, JSON, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime as dt

from app.core.database import Base


class WorkflowNodeType(str, enum.Enum):
    trigger = "trigger"
    llm_agent = "llm_agent"
    decision = "decision"
    api_action = "api_action"
    slack = "slack"
    notion = "notion"
    email = "email"
    delay = "delay"
    human_approval = "human_approval"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # React Flow graph metadata
    graph_version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    team = relationship("Team", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)

    # Store enum values in Postgres reliably (e.g. "trigger", "llm_agent").
    node_type: Mapped[WorkflowNodeType] = mapped_column(SAEnum(WorkflowNodeType), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)

    # UI position for React Flow
    pos_x: Mapped[int] = mapped_column(Integer, default=0)
    pos_y: Mapped[int] = mapped_column(Integer, default=0)

    # Arbitrary JSON config for the node (LLM prompt, API params, etc.)
    node_data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)

    from_node_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflow_nodes.id"), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflow_nodes.id"), nullable=False)

    # For decision branching, you can attach a condition key. If null, the edge is considered the default.
    condition_key: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=dt.datetime.utcnow)

    workflow = relationship("Workflow", back_populates="edges")

