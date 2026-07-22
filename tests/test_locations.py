# Tests for location endpoints
import pytest
from httpx import AsyncClient
from tests.utils.factories import location_payload


@pytest.mark.asyncio
async def test_create_location(client: AsyncClient, manager_token: str):
    """Manager can create a location."""
    resp = await client.post(
        "/api/v1/locations",
        json=location_payload(name="New Location"),
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Location"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_location_forbidden_for_customer(client: AsyncClient, customer_token: str):
    """Customer cannot create a location."""
    resp = await client.post(
        "/api/v1/locations",
        json=location_payload(name="Illegal Location"),
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_locations(client: AsyncClient, customer_token: str, test_location):
    """Authenticated user can list locations."""
    resp = await client.get(
        "/api/v1/locations",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_location(client: AsyncClient, customer_token: str, test_location):
    """Authenticated user can get a location by ID."""
    resp = await client.get(
        f"/api/v1/locations/{test_location.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_location.id)


@pytest.mark.asyncio
async def test_get_location_not_found(client: AsyncClient, customer_token: str):
    """Returns 404 for non-existent location."""
    import uuid
    resp = await client.get(
        f"/api/v1/locations/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_location(client: AsyncClient, manager_token: str, test_location):
    """Manager can update a location."""
    resp = await client.put(
        f"/api/v1/locations/{test_location.id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_location(client: AsyncClient, manager_token: str):
    """Manager can soft-delete a location."""
    # Create a fresh location to delete
    create_resp = await client.post(
        "/api/v1/locations",
        json=location_payload(name="To Delete"),
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    loc_id = create_resp.json()["id"]
    resp = await client.delete(
        f"/api/v1/locations/{loc_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 204
