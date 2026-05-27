from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.team import Team, APIKey
from app.models.user import User
from app.schemas.auth import AuthTokenResponse, LoginRequest, MeResponse, SignUpRequest

router = APIRouter()


async def _get_or_create_team(db: AsyncSession, team_name: str) -> Team:
    res = await db.execute(select(Team).where(Team.name == team_name))
    team = res.scalar_one_or_none()
    if team:
        return team
    team = Team(name=team_name)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def _create_user(db: AsyncSession, req: SignUpRequest) -> User:
    team = await _get_or_create_team(db, req.team_name)
    user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        team_id=team.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    # Create an API key for quick integrations
    api_key = APIKey(name="default", key=f"key_{user.id}", user_id=user.id)
    db.add(api_key)
    await db.commit()
    return user


@router.post("/signup", response_model=AuthTokenResponse)
async def signup(req: SignUpRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await _create_user(db, req)
    token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=token)


@router.post("/login", response_model=AuthTokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == req.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    team = None
    if user.team_id:
        team = await db.get(Team, user.team_id)
    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        team_id=str(team.id) if team else None,
    )

