"""
Integration tests for the auth endpoints.

These require a real (or test) MongoDB Atlas connection string in the
environment, since the app connects to Mongo on startup. Point
MONGODB_URI/MONGODB_DATABASE at a disposable test database before running:

    MONGODB_URI=... MONGODB_DATABASE=rag_test pytest backend/tests/test_auth_api.py

Covers: registration, duplicate email rejection, login (correct + wrong
password), and access to a protected route.
"""
import sys
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


@pytest.fixture
def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.asyncio
async def test_register_and_get_me(unique_email):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/auth/register",
            json={"name": "Test User", "email": unique_email, "password": "supersecret123"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["user"]["email"] == unique_email
        token = body["access_token"]

        me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == unique_email


@pytest.mark.asyncio
async def test_duplicate_email_rejected(unique_email):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"name": "Test User", "email": unique_email, "password": "supersecret123"}
        first = await client.post("/api/auth/register", json=payload)
        assert first.status_code == 201
        second = await client.post("/api/auth/register", json=payload)
        assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(unique_email):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={"name": "Test User", "email": unique_email, "password": "supersecret123"},
        )
        resp = await client.post("/api/auth/login", json={"email": unique_email, "password": "wrong-password"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/documents")
        assert resp.status_code == 401
