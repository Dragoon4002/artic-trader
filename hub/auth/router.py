"""Auth endpoints: login, register, refresh, API key generation."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models.user import User
from . import service
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
async def register(body: AuthRequest, db: AsyncSession = Depends(get_session)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=body.email, password_hash=service.hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=service.create_jwt(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: AuthRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not service.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=service.create_jwt(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(user: User = Depends(get_current_user)):
    return TokenResponse(access_token=service.create_jwt(user.id))


# API key management

class ApiKeyResponse(BaseModel):
    api_key: str


api_keys_router = APIRouter(prefix="/api/keys", tags=["keys"])


@api_keys_router.post("", response_model=ApiKeyResponse)
async def generate_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    raw, hashed = service.generate_api_key()
    user.api_key_hash = hashed
    await db.commit()
    return ApiKeyResponse(api_key=raw)
