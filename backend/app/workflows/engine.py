from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import run_llm_json
from app.core.config import get_settings
from app.integrations.erp_client import create_erp_entry
from app.integrations.google_client import extract_invoice_data
from app.integrations.notion_client import create_task_page
from app.integrations.slack_client import send_message as slack_send_message
from app.integrations.google_client import get_calendar_events

from app.models.executions import Execution, ExecutionStep, ExecutionStatus, ExecutionStepStatus
from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode, WorkflowNodeType


def _render_template(template: str, context: dict[str, Any]) -> str:
    # Minimal mustache-ish renderer: replaces {{key}} with context values.
    out = template
    for k, v in context.items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


async def _execute_node(
    node: WorkflowNode,
    context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Returns (node_execution_record, context_delta).
    - node_execution_record: what gets stored in ExecutionStep.output_json
    - context_delta: what gets merged into the running context
    """
    node_data = node.node_data or {}

    if node.node_type == WorkflowNodeType.trigger:
        return {"triggered": True}, {"triggered": True}

    if node.node_type == WorkflowNodeType.llm_agent:
        prompt = node_data.get("prompt") or node_data.get("user_prompt") or "Summarize the input."
        kind = node_data.get("agent_kind") or "llm_agent"
        llm_res = await run_llm_json(kind=kind, prompt=prompt, input_payload=context)
        return llm_res, dict(llm_res.get("output") or {})

    if node.node_type == WorkflowNodeType.decision:
        prompt = node_data.get("prompt") or "Choose the best condition key."
        llm_res = await run_llm_json(kind="decision", prompt=prompt, input_payload=context)
        output = dict(llm_res.get("output") or {})
        return llm_res, output

    if node.node_type == WorkflowNodeType.slack:
        channel = str(node_data.get("channel") or "general")
        text_template = str(node_data.get("text") or node_data.get("text_template") or "")
        text = _render_template(text_template, context)
        res = await slack_send_message(channel=channel, text=text, context=context)
        return res, {"slack": res}

    if node.node_type == WorkflowNodeType.notion:
        title_template = str(node_data.get("title") or "New task")
        title = _render_template(title_template, context)
        res = await create_task_page(title=title, properties=node_data.get("properties") or {})
        return res, {"notion": res}

    if node.node_type == WorkflowNodeType.email:
        subject_template = str(node_data.get("subject") or "Response draft")
        body_template = str(node_data.get("body") or node_data.get("body_template") or "")
        subject = _render_template(subject_template, context)
        body = _render_template(body_template, context)
        # Stub: would call Google Workspace/Gmail in a real implementation.
        res = {"subject": subject, "body": body, "mock": True}
        return res, {"email": res}

    if node.node_type == WorkflowNodeType.api_action:
        action = str(node_data.get("action") or "erp_entry")
        # A tiny router for mock actions used by demo workflows.
        if action == "extract_invoice":
            extracted = await extract_invoice_data(context.get("text") or context.get("message") or "")
            return {"action": action, "extracted": extracted, "mock": True}, {"extracted": extracted}
        if action == "calendar_events":
            events = await get_calendar_events(str(context.get("user_id") or "user"))
            return {"action": action, "events": events, "mock": True}, {"events": events}

        if action == "update_erp":
            entry_type = str(node_data.get("entry_type") or "finance_entries")
            payload = node_data.get("payload") or context
            erp = await create_erp_entry(entry_type=entry_type, payload=payload)
            return {"action": action, "erp": erp, "mock": True}, {"erp": erp}

        return {"action": action, "mock": True, "input": context}, {"api_action": {"action": action}}

    if node.node_type == WorkflowNodeType.delay:
        seconds = int(node_data.get("seconds") or 1)
        seconds = max(0, min(seconds, 30))  # cap for demo stability
        await asyncio.sleep(seconds)
        return {"delay_seconds": seconds}, {"delay_seconds": seconds}

    if node.node_type == WorkflowNodeType.human_approval:
        # In production: pause workflow and resume after approval event.
        res = {"approval_required": True, "reason": node_data.get("reason") or "Review required"}
        return res, res

    # Safety net
    node_type_str = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
    return {"node_type": node_type_str, "mock": True}, {}


def _pick_next_node_id(
    outgoing_edges: list[WorkflowEdge],
    node_type: WorkflowNodeType,
    node_output: dict[str, Any],
) -> uuid.UUID | None:
    if not outgoing_edges:
        return None

    if node_type != WorkflowNodeType.decision:
        return outgoing_edges[0].to_node_id

    # Decision output expected to include selected_condition_key.
    selected_key = node_output.get("selected_condition_key") or node_output.get("condition_key")

    # Prefer exact condition match.
    if selected_key is not None:
        for e in outgoing_edges:
            if e.condition_key == str(selected_key):
                return e.to_node_id

    # Fallback to default edge.
    for e in outgoing_edges:
        if e.condition_key is None:
            return e.to_node_id

    # Otherwise first.
    return outgoing_edges[0].to_node_id


async def execute_workflow(execution_id: uuid.UUID, db: AsyncSession) -> None:
    """
    Executes a workflow graph step-by-step.
    - Runs in-process for the Celery worker wrapper (async engine).
    - Records per-node logs in `execution_steps`.
    """
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise ValueError("Execution not found")

    workflow = await db.get(Workflow, execution.workflow_id)
    if not workflow:
        raise ValueError("Workflow not found")

    import datetime as dt

    is_resume = execution.resume_node_id is not None and execution.status in {
        ExecutionStatus.queued,
        ExecutionStatus.running,
    }

    execution.status = ExecutionStatus.running
    if not execution.started_at:
        execution.started_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    nodes_res = await db.execute(
        select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id).order_by(WorkflowNode.created_at.asc())
    )
    edges_res = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow.id).order_by(WorkflowEdge.created_at.asc())
    )
    nodes = list(nodes_res.scalars().all())
    edges = list(edges_res.scalars().all())

    node_by_id = {n.id: n for n in nodes}
    outgoing_by_node: dict[uuid.UUID, list[WorkflowEdge]] = {}
    for e in edges:
        outgoing_by_node.setdefault(e.from_node_id, []).append(e)

    trigger_node = next((n for n in nodes if n.node_type == WorkflowNodeType.trigger), None)
    if not trigger_node:
        execution.status = ExecutionStatus.failed
        execution.error_text = "No trigger node in workflow"
        execution.finished_at = __import__("datetime").datetime.utcnow()
        await db.commit()
        return

    # Context:
    # - fresh run: start from input_payload
    # - resume: start from output_payload merged with approval payload + input payload
    context: dict[str, Any] = dict(execution.input_payload or {})
    if execution.output_payload:
        context.update(execution.output_payload)
    if execution.approval_payload:
        context["approval"] = execution.approval_payload

    current_node_id: uuid.UUID | None = execution.resume_node_id if is_resume else trigger_node.id

    # Step index: continue after the last recorded step.
    if is_resume:
        last_step_res = await db.execute(
            select(ExecutionStep)
            .where(ExecutionStep.execution_id == execution.id)
            .order_by(ExecutionStep.step_index.desc(), ExecutionStep.attempt.desc())
            .limit(1)
        )
        last_step = last_step_res.scalar_one_or_none()
        step_index = (last_step.step_index + 1) if last_step else 0
    else:
        step_index = 0

    while current_node_id:
        node = node_by_id[current_node_id]
        outgoing_edges = outgoing_by_node.get(current_node_id, [])

        # Retry policy (MVP): max 2 retries at step-level.
        max_retries = 2
        attempt = 1
        last_error: str | None = None

        while attempt <= max_retries + 1:
            started_at = dt.datetime.now(dt.timezone.utc)
            step = ExecutionStep(
                execution_id=execution.id,
                node_id=node.id,
                node_type=node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
                step_index=step_index,
                attempt=attempt,
                status=ExecutionStepStatus.running,
                input_json={"context": context},
            )
            db.add(step)
            await db.commit()
            await db.refresh(step)

            try:
                t0 = time.perf_counter()
                node_record, context_delta = await _execute_node(node=node, context=context)
                duration_ms = int((time.perf_counter() - t0) * 1000)

                # Human approval node pauses the execution.
                if node.node_type == WorkflowNodeType.human_approval:
                    next_node_id = _pick_next_node_id(
                        outgoing_edges=outgoing_edges,
                        node_type=node.node_type,
                        node_output={},
                    )
                    reason = (node_record.get("reason") if isinstance(node_record, dict) else None) or (
                        node.node_data.get("reason") if node.node_data else None
                    )

                    step.output_json = {
                        "node": node_record,
                        "duration_ms": duration_ms,
                        "pause": {"reason": reason, "resume_node_id": str(next_node_id) if next_node_id else None},
                    }
                    step.status = ExecutionStepStatus.awaiting_approval
                    step.finished_at = dt.datetime.now(dt.timezone.utc)
                    await db.commit()

                    # Persist pause/resume pointers on execution.
                    execution.status = ExecutionStatus.awaiting_approval
                    execution.paused_node_id = node.id
                    execution.resume_node_id = next_node_id
                    execution.paused_reason = str(reason) if reason else "Approval required"
                    execution.output_payload = context  # snapshot current context
                    await db.commit()
                    return

                step.output_json = {"node": node_record, "duration_ms": duration_ms}
                step.status = ExecutionStepStatus.succeeded
                step.finished_at = dt.datetime.now(dt.timezone.utc)
                step.tokens_prompt = 0
                step.tokens_completion = 0
                step.tokens_total = 0
                await db.commit()

                # Merge context updates
                context.update(context_delta or {})

                next_node_id = _pick_next_node_id(
                    outgoing_edges=outgoing_edges,
                    node_type=node.node_type,
                    node_output=context_delta if node.node_type == WorkflowNodeType.decision else {},
                )
                step_index += 1
                current_node_id = next_node_id
                break
            except Exception as e:  # noqa: BLE001
                last_error = str(e)
                step.error_text = last_error
                step.status = ExecutionStepStatus.failed
                step.finished_at = dt.datetime.now(dt.timezone.utc)
                await db.commit()

                attempt += 1
                if attempt <= max_retries + 1:
                    # Brief backoff before retry
                    await asyncio.sleep(1)
                else:
                    # Stop workflow on repeated failure
                    execution.status = ExecutionStatus.failed
                    execution.error_text = f"Step failed: node={node.id} error={last_error}"
                    execution.finished_at = dt.datetime.now(dt.timezone.utc)
                    await db.commit()
                    return

    execution.status = ExecutionStatus.succeeded
    execution.output_payload = context
    execution.resume_node_id = None
    execution.paused_node_id = None
    execution.paused_reason = None
    execution.approval_payload = {}
    execution.finished_at = dt.datetime.now(dt.timezone.utc)
    # duration_ms could be computed from started_at/finished_at
    await db.commit()

