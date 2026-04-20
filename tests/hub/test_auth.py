"""Auth flow — register, login, refresh rotation, reuse detection."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def _register(client, email="a@b.com", pw="pw12345") -> dict:
    r = await client.post("/auth/register", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return r.json()


async def test_register_login_returns_tokens(client):
    tokens = await _register(client)
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    r = await client.post(
        "/auth/login", json={"email": "a@b.com", "password": "pw12345"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"] != tokens["refresh_token"]  # fresh login = fresh token


async def test_refresh_rotates_token(client):
    tokens = await _register(client, email="rot@b.com")
    r = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    assert new["access_token"]


async def test_refresh_reuse_revokes_family(client):
    """Replaying a consumed refresh token must invalidate all siblings."""
    tokens = await _register(client, email="reuse@b.com")
    first = tokens["refresh_token"]

    # First rotation succeeds
    r1 = await client.post("/auth/refresh", json={"refresh_token": first})
    assert r1.status_code == 200
    second = r1.json()["refresh_token"]

    # Replaying the first (already-used) token: rejected + triggers family revocation
    r_reuse = await client.post("/auth/refresh", json={"refresh_token": first})
    assert r_reuse.status_code == 401

    # The legitimate chain-successor must now also be rejected
    r_after = await client.post("/auth/refresh", json={"refresh_token": second})
    assert r_after.status_code == 401


async def test_me_requires_valid_jwt(client):
    tokens = await _register(client, email="me@b.com")
    r = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "me@b.com"

    r_bad = await client.get("/auth/me", headers={"Authorization": "Bearer nope"})
    assert r_bad.status_code == 401
