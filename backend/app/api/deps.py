from fastapi import Depends, Header, HTTPException, status
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.team import Team


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    user = await db.get(User, uuid.UUID(str(user_id)))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_team(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Team:
    if user.team_id:
        team = await db.get(Team, user.team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Team not found")
        return team

    # For MVP: auto-provision a default team on first login.
    default_name = "Default Team"
    res = await db.execute(select(Team).where(Team.name == default_name))
    team = res.scalar_one_or_none()
    if team:
        return team

    team = Team(name=default_name)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    user.team_id = team.id
    await db.commit()
    return team

