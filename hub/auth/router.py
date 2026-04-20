"""Auth endpoints — register, login, refresh (rotating), /me, API keys."""

from __future__ import annotations

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


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str


@router.post("/register", response_model=TokenResponse)
async def register(body: AuthRequest, db: AsyncSession = Depends(get_session)):
    existing = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="email already registered")
    user = User(email=body.email, password_hash=service.hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    issued = await service.issue_refresh(db, user.id)
    return TokenResponse(
        access_token=service.create_jwt(user.id),
        refresh_token=issued.raw_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: AuthRequest, db: AsyncSession = Depends(get_session)):
    user = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if not user or not service.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    issued = await service.issue_refresh(db, user.id)
    return TokenResponse(
        access_token=service.create_jwt(user.id),
        refresh_token=issued.raw_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    result = await service.rotate_refresh(db, body.refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="invalid or reused refresh token")
    user_id, issued = result
    return TokenResponse(
        access_token=service.create_jwt(user_id),
        refresh_token=issued.raw_token,
    )


@router.post("/logout")
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_session)):
    await service.revoke_family_by_token(db, body.refresh_token)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return MeResponse(id=user.id, email=user.email)


# -------- API keys --------


class ApiKeyResponse(BaseModel):
    api_key: str


api_keys_router = APIRouter(prefix="/api/keys", tags=["keys"])


@api_keys_router.post("", response_model=ApiKeyResponse)
async def create_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    raw, hashed = service.generate_api_key()
    user.api_key_hash = hashed
    await db.commit()
    return ApiKeyResponse(api_key=raw)
