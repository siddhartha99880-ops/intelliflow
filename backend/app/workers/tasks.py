from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.workflows.engine import execute_workflow
from app.workers.celery_app import celery


@celery.task(name="workflows.execute", bind=True)
def execute_workflow_task(self, execution_id: str) -> dict:
    """
    Celery wrapper around the async workflow engine.
    """
    execution_uuid = uuid.UUID(execution_id)

    async def _run() -> None:
        async with async_session() as session:  # type: ignore[misc]
            await execute_workflow(execution_id=execution_uuid, db=session)

    asyncio.run(_run())
    return {"execution_id": execution_id, "status": "completed"}

