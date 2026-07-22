# Tests for availability schedule and override endpoints
import pytest
from httpx import AsyncClient
from tests.utils.factories import schedule_payload


@pytest.mark.asyncio
async def test_create_schedule(client: AsyncClient, staff_token: str, test_staff_profile):
    """Staff can create their own weekly schedule."""
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/schedules",
        json=schedule_payload(day_of_week="monday", start_time="09:00:00", end_time="17:00:00"),
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["day_of_week"] == "monday"


@pytest.mark.asyncio
async def test_create_schedule_manager(client: AsyncClient, manager_token: str, test_staff_profile):
    """Manager can create a schedule for any staff."""
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/schedules",
        json=schedule_payload(day_of_week="tuesday"),
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_schedules(client: AsyncClient, staff_token: str, test_staff_profile):
    """Staff can list their own schedules."""
    resp = await client.get(
        f"/api/v1/staff/{test_staff_profile.id}/schedules",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_invalid_schedule_time_order(client: AsyncClient, staff_token: str, test_staff_profile):
    """Schedule with start >= end returns 422."""
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/schedules",
        json={"day_of_week": "friday", "start_time": "17:00:00", "end_time": "09:00:00"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_override_day_off(client: AsyncClient, staff_token: str, test_staff_profile):
    """Staff can add a day-off override."""
    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=10)).isoformat()
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/overrides",
        json={"override_date": future_date, "override_type": "day_off"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["override_type"] == "day_off"


@pytest.mark.asyncio
async def test_create_override_custom_hours(client: AsyncClient, staff_token: str, test_staff_profile):
    """Staff can add a custom-hours override."""
    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=11)).isoformat()
    resp = await client.post(
        f"/api/v1/staff/{test_staff_profile.id}/overrides",
        json={
            "override_date": future_date,
            "override_type": "custom_hours",
            "start_time": "10:00:00",
            "end_time": "13:00:00",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_overrides(client: AsyncClient, staff_token: str, test_staff_profile):
    """Staff can list their own overrides."""
    resp = await client.get(
        f"/api/v1/staff/{test_staff_profile.id}/overrides",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
