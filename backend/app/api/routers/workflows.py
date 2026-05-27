from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_team
from app.core.database import get_db
from app.models.executions import Execution, ExecutionStatus
from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode, WorkflowNodeType
from app.schemas.workflows import ExecuteWorkflowRequest, ExecuteWorkflowResponse, WorkflowCreateRequest, WorkflowResponse
from app.workers.tasks import execute_workflow_task

router = APIRouter()


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(team=Depends(get_current_team), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Workflow).where(Workflow.team_id == team.id))
    workflows = res.scalars().all()
    return [WorkflowResponse(id=w.id, name=w.name, description=w.description, graph_version=w.graph_version) for w in workflows]


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(req: WorkflowCreateRequest, team=Depends(get_current_team), db: AsyncSession = Depends(get_db)):
    workflow = Workflow(team_id=team.id, name=req.name, description=req.description)
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    # Store nodes + edges from the React Flow graph.
    for n in req.nodes:
        node = WorkflowNode(
            workflow_id=workflow.id,
            id=n.id,
            node_type=WorkflowNodeType(n.type),
            label=n.label,
            pos_x=n.position_x,
            pos_y=n.position_y,
            node_data=dict(n.data or {}),
        )
        db.add(node)

    for e in req.edges:
        edge = WorkflowEdge(
            workflow_id=workflow.id,
            from_node_id=e.from_node_id,
            to_node_id=e.to_node_id,
            condition_key=e.condition_key,
        )
        if e.id:
            edge.id = e.id
        db.add(edge)

    await db.commit()
    return WorkflowResponse(id=workflow.id, name=workflow.name, description=workflow.description, graph_version=workflow.graph_version)


@router.post("/{workflow_id}/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(
    workflow_id: uuid.UUID,
    req: ExecuteWorkflowRequest,
    team=Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    workflow = await db.get(Workflow, workflow_id)
    if not workflow or workflow.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    execution = Execution(
        workflow_id=workflow.id,
        team_id=team.id,
        status=ExecutionStatus.queued,
        input_payload=req.input_payload or {},
        output_payload={},
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Enqueue background execution
    execute_workflow_task.delay(str(execution.id))

    return ExecuteWorkflowResponse(execution_id=execution.id, status=execution.status.value)

