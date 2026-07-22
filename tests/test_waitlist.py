# Tests for waitlist endpoints
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, StaffProfile, Service, Location


@pytest.mark.asyncio
async def test_join_waitlist(
    client: AsyncClient,
    customer_token: str,
    test_service: Service,
    test_location: Location,
):
    """Customer can join waitlist."""
    future_date = (date.today() + timedelta(days=14)).isoformat()
    resp = await client.post(
        "/api/v1/waitlist",
        json={
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "requested_date": future_date,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_active"] is True
    assert data["is_notified"] is False


@pytest.mark.asyncio
async def test_join_waitlist_duplicate(
    client: AsyncClient,
    customer_token: str,
    test_service: Service,
    test_location: Location,
):
    """Cannot join same waitlist twice."""
    future_date = (date.today() + timedelta(days=20)).isoformat()
    payload = {
        "service_id": str(test_service.id),
        "location_id": str(test_location.id),
        "requested_date": future_date,
    }
    await client.post("/api/v1/waitlist", json=payload, headers={"Authorization": f"Bearer {customer_token}"})
    resp2 = await client.post("/api/v1/waitlist", json=payload, headers={"Authorization": f"Bearer {customer_token}"})
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_waitlist_customer(
    client: AsyncClient,
    customer_token: str,
    customer_user: User,
    test_service: Service,
    test_location: Location,
):
    """Customer sees only their own waitlist entries."""
    future_date = (date.today() + timedelta(days=21)).isoformat()
    await client.post(
        "/api/v1/waitlist",
        json={
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "requested_date": future_date,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    resp = await client.get(
        "/api/v1/waitlist",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert all(item["customer_id"] == str(customer_user.id) for item in items)


@pytest.mark.asyncio
async def test_leave_waitlist(
    client: AsyncClient,
    customer_token: str,
    test_service: Service,
    test_location: Location,
):
    """Customer can leave waitlist."""
    future_date = (date.today() + timedelta(days=22)).isoformat()
    join_resp = await client.post(
        "/api/v1/waitlist",
        json={
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "requested_date": future_date,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    entry_id = join_resp.json()["id"]
    resp = await client.delete(
        f"/api/v1/waitlist/{entry_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_staff_cannot_join_waitlist(
    client: AsyncClient,
    staff_token: str,
    test_service: Service,
    test_location: Location,
):
    """Staff cannot join waitlist."""
    future_date = (date.today() + timedelta(days=23)).isoformat()
    resp = await client.post(
        "/api/v1/waitlist",
        json={
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "requested_date": future_date,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 403
