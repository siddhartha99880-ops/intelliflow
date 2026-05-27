from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_team, get_current_user
from app.core.database import get_db
from app.models.team import Team

router = APIRouter()


@router.get("/me", response_model=dict)
async def team_me(team: Team = Depends(get_current_team)):
    return {"id": str(team.id), "name": team.name}


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(payload: dict, team: Team = Depends(get_current_team), user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    MVP mock invite endpoint.
    payload expected: { "email": "...", "role": "member" | "owner" }
    """
    if user.team_id != team.id:
        raise HTTPException(status_code=403, detail="Not in team")

    email = payload.get("email")
    role = payload.get("role") or "member"
    if not email:
        raise HTTPException(status_code=400, detail="Missing email")

    # Real implementation: store invite tokens + send email.
    return {"invited": True, "email": email, "role": role, "team_id": str(team.id)}

