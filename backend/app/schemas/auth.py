from pydantic import BaseModel, EmailStr
from typing import Literal


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    team_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None
    team_id: str | None

