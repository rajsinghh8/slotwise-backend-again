# Tests for service endpoints
import pytest
from httpx import AsyncClient
from tests.utils.factories import service_payload


@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, manager_token: str):
    """Manager can create a service."""
    resp = await client.post(
        "/api/v1/services",
        json=service_payload(name="Test Massage", duration_minutes=60, price="89.99"),
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Massage"
    assert data["price"] == "89.99"


@pytest.mark.asyncio
async def test_create_service_forbidden_customer(client: AsyncClient, customer_token: str):
    """Customer cannot create a service."""
    resp = await client.post(
        "/api/v1/services",
        json=service_payload(),
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_services(client: AsyncClient, customer_token: str, test_service):
    """Authenticated user can list services."""
    resp = await client.get(
        "/api/v1/services",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_service(client: AsyncClient, customer_token: str, test_service):
    """Authenticated user can get a service by ID."""
    resp = await client.get(
        f"/api/v1/services/{test_service.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_service.id)


@pytest.mark.asyncio
async def test_update_service(client: AsyncClient, manager_token: str, test_service):
    """Manager can update a service."""
    resp = await client.put(
        f"/api/v1/services/{test_service.id}",
        json={"price": "75.00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == "75.00"


@pytest.mark.asyncio
async def test_delete_service(client: AsyncClient, manager_token: str):
    """Manager can soft-delete a service."""
    create_resp = await client.post(
        "/api/v1/services",
        json=service_payload(name="To Delete Service"),
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    svc_id = create_resp.json()["id"]
    resp = await client.delete(
        f"/api/v1/services/{svc_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 204
