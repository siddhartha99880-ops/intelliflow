from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_team
from app.core.database import get_db
from app.models.executions import Execution, ExecutionStatus, ExecutionStep
from app.schemas.executions import ExecutionResponse, ExecutionStepResponse
from app.workers.tasks import execute_workflow_task

router = APIRouter()


@router.get("", response_model=list[ExecutionResponse])
async def list_executions(team=Depends(get_current_team), limit: int = 20, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Execution).where(Execution.team_id == team.id).order_by(Execution.created_at.desc()).limit(limit)
    )
    executions = res.scalars().all()

    # MVP: do not eagerly load steps for list. Return empty steps.
    return [
        ExecutionResponse(
            id=e.id,
            workflow_id=e.workflow_id,
            team_id=e.team_id,
            status=e.status.value,
            error_text=e.error_text,
            input_payload=e.input_payload or {},
            output_payload=e.output_payload or {},
            tokens_prompt=e.tokens_prompt,
            tokens_completion=e.tokens_completion,
            tokens_total=e.tokens_total,
            duration_ms=e.duration_ms,
            created_at=e.created_at,
            started_at=e.started_at,
            finished_at=e.finished_at,
            steps=[],
        )
        for e in executions
    ]


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: uuid.UUID, team=Depends(get_current_team), db: AsyncSession = Depends(get_db)):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.team_id != team.id:
        raise HTTPException(status_code=404, detail="Execution not found")

    steps_res = await db.execute(
        select(ExecutionStep).where(ExecutionStep.execution_id == execution.id).order_by(ExecutionStep.step_index, ExecutionStep.attempt)
    )
    steps = steps_res.scalars().all()

    return ExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        team_id=execution.team_id,
        status=execution.status.value,
        error_text=execution.error_text,
        input_payload=execution.input_payload or {},
        output_payload=execution.output_payload or {},
        tokens_prompt=execution.tokens_prompt,
        tokens_completion=execution.tokens_completion,
        tokens_total=execution.tokens_total,
        duration_ms=execution.duration_ms,
        created_at=execution.created_at,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        steps=[
            ExecutionStepResponse(
                id=s.id,
                node_id=s.node_id,
                node_type=s.node_type,
                step_index=s.step_index,
                attempt=s.attempt,
                status=str(s.status),
                started_at=s.started_at,
                finished_at=s.finished_at,
                error_text=s.error_text,
                input_json=s.input_json or {},
                output_json=s.output_json or {},
            )
            for s in steps
        ],
    )


@router.post("/{execution_id}/approve", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def approve_execution(
    execution_id: uuid.UUID,
    payload: dict | None = None,
    team=Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.team_id != team.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.status != ExecutionStatus.awaiting_approval:
        raise HTTPException(status_code=400, detail="Execution is not awaiting approval")

    execution.approval_payload = dict(payload or {})
    execution.status = ExecutionStatus.queued
    execution.error_text = None
    await db.commit()

    execute_workflow_task.delay(str(execution.id))
    return {"execution_id": str(execution.id), "status": execution.status.value}


@router.post("/{execution_id}/reject", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def reject_execution(
    execution_id: uuid.UUID,
    payload: dict | None = None,
    team=Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.team_id != team.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.status != ExecutionStatus.awaiting_approval:
        raise HTTPException(status_code=400, detail="Execution is not awaiting approval")

    reason = (payload or {}).get("reason") if payload else None
    execution.status = ExecutionStatus.failed
    execution.error_text = f"Rejected by human{': ' + str(reason) if reason else ''}"
    import datetime as dt

    execution.finished_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()

    return {"execution_id": str(execution.id), "status": execution.status.value}

