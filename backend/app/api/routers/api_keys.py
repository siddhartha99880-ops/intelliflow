from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.team import APIKey
from app.core.security import create_access_token

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_api_keys(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(APIKey).where(APIKey.user_id == user.id))
    keys = res.scalars().all()
    return [{"id": str(k.id), "name": k.name, "key": k.key} for k in keys]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_api_key(payload: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    name = payload.get("name") or "API Key"
    # MVP: key is predictable-ish token string.
    key = f"key_{user.id}_{uuid.uuid4()}"
    api_key = APIKey(name=name, key=key, user_id=user.id)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return {"id": str(api_key.id), "name": api_key.name, "key": api_key.key}

