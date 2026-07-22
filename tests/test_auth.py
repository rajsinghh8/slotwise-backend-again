# Tests for authentication endpoints: register, login, /me
import pytest
from httpx import AsyncClient
from tests.utils.factories import user_register_payload


@pytest.mark.asyncio
async def test_register_customer(client: AsyncClient):
    """Test successful customer registration returns 201."""
    import uuid as _u
    payload = user_register_payload(email=f"newcust_{_u.uuid4().hex[:8]}@example.com", role="customer")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "customer"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registering with a duplicate email returns 409."""
    import uuid as _u
    email = f"dup_{_u.uuid4().hex[:8]}@example.com"
    payload = user_register_payload(email=email)
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient, customer_user):
    """Test valid login returns 200 and access token."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "cust_pass_123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, customer_user):
    """Test login with wrong password returns 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    """Test login with non-existent email returns 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, customer_user, customer_token: str):
    """Test /me returns the authenticated user."""
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == customer_user.email
    assert data["role"] == "customer"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Test /me without token returns 403 (HTTPBearer requirement)."""
    resp = await client.get("/api/v1/auth/me")
    # HTTPBearer returns 403 when no credentials provided
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Test /me with invalid token returns 401 or 403."""
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code in (401, 403)
