# Tests for staff profile endpoints
import pytest
from httpx import AsyncClient
from tests.utils.factories import user_register_payload


@pytest.mark.asyncio
async def test_create_staff_profile(client: AsyncClient, manager_token: str, test_location):
    """Manager can create a staff profile for a fresh staff user."""
    import uuid as _u
    from app.core.security import get_password_hash
    # Register a new staff user first
    email = f"staff_new_{_u.uuid4().hex[:8]}@slotwise.com"
    reg_resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "somepass123",
        "full_name": "New Staff",
        "role": "staff",
    })
    assert reg_resp.status_code == 201
    new_user_id = reg_resp.json()["id"]
    resp = await client.post(
        "/api/v1/staff",
        json={
            "user_id": new_user_id,
            "location_id": str(test_location.id),
            "bio": "Expert stylist",
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == new_user_id


@pytest.mark.asyncio
async def test_create_staff_profile_duplicate(client: AsyncClient, manager_token: str, test_staff_profile):
    """Creating a duplicate staff profile returns 409."""
    resp = await client.post(
        "/api/v1/staff",
        json={
            "user_id": str(test_staff_profile.user_id),
            "location_id": str(test_staff_profile.location_id),
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_staff(client: AsyncClient, customer_token: str, test_staff_profile):
    """Authenticated user can list staff."""
    resp = await client.get(
        "/api/v1/staff",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_staff_profile(client: AsyncClient, customer_token: str, test_staff_profile):
    """Authenticated user can get a staff profile by ID."""
    resp = await client.get(
        f"/api/v1/staff/{test_staff_profile.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_staff_profile.id)


@pytest.mark.asyncio
async def test_add_staff_service(client: AsyncClient, manager_token: str, test_staff_profile, manager_user):
    """Manager can assign a new service to staff (creates a fresh service first)."""
    # Create a fresh service to assign
    svc_resp = await client.post(
        "/api/v1/services",
        json={"name": "New Test Service", "duration_minutes": 30, "price": "25.00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert svc_resp.status_code == 201
    new_svc_id = svc_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/services",
        json={"service_id": new_svc_id},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_staff_services(client: AsyncClient, customer_token: str, test_staff_profile):
    """Authenticated user can list services for a staff member."""
    resp = await client.get(
        f"/api/v1/staff/{test_staff_profile.id}/services",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
