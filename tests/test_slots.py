# Tests for slot availability endpoint
import pytest
from datetime import date, timedelta, time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import StaffService, AvailabilitySchedule, DayOfWeek, StaffProfile, Service, Location


@pytest.mark.asyncio
async def test_get_slots_no_schedule(
    client: AsyncClient,
    customer_token: str,
    test_staff_profile: StaffProfile,
    test_service: Service,
    test_location: Location,
    db_session: AsyncSession,
):
    """Returns slots list (possibly empty) for a date with no schedule."""
    # Ensure service assigned (if not already)
    existing_ss = await db_session.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == test_staff_profile.id,
            StaffService.service_id == test_service.id,
        )
    )
    if not existing_ss.scalar_one_or_none():
        db_session.add(StaffService(staff_profile_id=test_staff_profile.id, service_id=test_service.id))
        await db_session.commit()

    # Use a date far in the future with no schedule set
    future_date = (date.today() + timedelta(days=400)).isoformat()
    resp = await client.get(
        "/api/v1/slots",
        params={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(test_service.id),
            "date": future_date,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_slots_with_schedule(
    client: AsyncClient,
    customer_token: str,
    test_staff_profile: StaffProfile,
    test_service: Service,
    test_location: Location,
    db_session: AsyncSession,
):
    """Returns slots when staff has a schedule."""
    # Assign service to staff if not already
    existing_ss = await db_session.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == test_staff_profile.id,
            StaffService.service_id == test_service.id,
        )
    )
    if not existing_ss.scalar_one_or_none():
        db_session.add(StaffService(staff_profile_id=test_staff_profile.id, service_id=test_service.id))

    # Add schedule for all days if not already set
    for dow in DayOfWeek:
        existing_sched = await db_session.execute(
            select(AvailabilitySchedule).where(
                AvailabilitySchedule.staff_profile_id == test_staff_profile.id,
                AvailabilitySchedule.day_of_week == dow,
            ).limit(1)
        )
        if not existing_sched.scalar_one_or_none():
            db_session.add(AvailabilitySchedule(
                staff_profile_id=test_staff_profile.id,
                day_of_week=dow,
                start_time=time(9, 0),
                end_time=time(17, 0),
            ))
    await db_session.commit()

    # Find a future weekday (use 60 days to avoid any overrides from other tests)
    future_date = date.today() + timedelta(days=60)
    resp = await client.get(
        "/api/v1/slots",
        params={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(test_service.id),
            "date": future_date.isoformat(),
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    slots = resp.json()
    assert isinstance(slots, list)
    assert len(slots) > 0


@pytest.mark.asyncio
async def test_get_slots_wrong_service(
    client: AsyncClient,
    customer_token: str,
    test_staff_profile: StaffProfile,
    test_location: Location,
):
    """Returns 404 or 422 if staff doesn't offer the service."""
    import uuid
    future_date = (date.today() + timedelta(days=5)).isoformat()
    resp = await client.get(
        "/api/v1/slots",
        params={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(uuid.uuid4()),  # nonexistent service
            "date": future_date,
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code in (404, 422)
