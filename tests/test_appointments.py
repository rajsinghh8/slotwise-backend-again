# Tests for appointment booking, listing, cancellation, and status updates
import pytest
from datetime import datetime, timedelta, timezone, date, time
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    Appointment, AppointmentStatus, StaffService, AvailabilitySchedule,
    DayOfWeek, User, StaffProfile, Service, Location
)


async def _ensure_staff_can_do_service(db_session, staff_profile, service):
    existing = await db_session.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == staff_profile.id,
            StaffService.service_id == service.id,
        )
    )
    if not existing.scalar_one_or_none():
        db_session.add(StaffService(staff_profile_id=staff_profile.id, service_id=service.id))
        await db_session.commit()


async def _insert_appointment(db_session, staff_profile, service, location, customer, hours_from_now=72):
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(minutes=service.duration_minutes)
    appt = Appointment(
        customer_id=customer.id,
        staff_profile_id=staff_profile.id,
        service_id=service.id,
        location_id=location.id,
        start_time=start,
        end_time=end,
        status=AppointmentStatus.confirmed,
        price_at_booking=service.price,
    )
    db_session.add(appt)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest.mark.asyncio
async def test_create_appointment(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Customer can book an appointment."""
    await _ensure_staff_can_do_service(db_session, test_staff_profile, test_service)
    for dow in DayOfWeek:
        existing = await db_session.execute(
            select(AvailabilitySchedule).where(
                AvailabilitySchedule.staff_profile_id == test_staff_profile.id,
                AvailabilitySchedule.day_of_week == dow,
            )
        )
        if not existing.scalar_one_or_none():
            db_session.add(AvailabilitySchedule(
                staff_profile_id=test_staff_profile.id,
                day_of_week=dow,
                start_time=time(8, 0),
                end_time=time(20, 0),
            ))
    await db_session.commit()

    start = datetime.now(timezone.utc) + timedelta(hours=500)
    resp = await client.post(
        "/api/v1/appointments",
        json={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "start_time": start.isoformat(),
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "confirmed"
    assert data["customer_id"] == str(customer_user.id)


@pytest.mark.asyncio
async def test_create_appointment_past_time(
    client, customer_token, test_staff_profile, test_service, test_location
):
    """Cannot book an appointment in the past."""
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    resp = await client.post(
        "/api/v1/appointments",
        json={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "start_time": past.isoformat(),
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_appointments_customer_sees_own(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Customer only sees their own appointments."""
    await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=600)
    resp = await client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200
    items = resp.json()
    assert all(item["customer_id"] == str(customer_user.id) for item in items)


@pytest.mark.asyncio
async def test_manager_sees_all_appointments(
    client, manager_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Manager can see all appointments."""
    await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=700)
    resp = await client.get("/api/v1/appointments", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_appointment_by_owner(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Customer can get their own appointment."""
    appt = await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=800)
    resp = await client.get(f"/api/v1/appointments/{appt.id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == str(appt.id)


@pytest.mark.asyncio
async def test_cancel_appointment_within_24h(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Customer cannot cancel within 24h."""
    appt = await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=2)
    resp = await client.post(
        f"/api/v1/appointments/{appt.id}/cancel",
        json={},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_cancel_appointment_outside_24h(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Customer can cancel if >24h in advance."""
    appt = await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=900)
    resp = await client.post(
        f"/api/v1/appointments/{appt.id}/cancel",
        json={"cancellation_reason": "Change of plans"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_manager_can_cancel_anytime(
    client, manager_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Manager can cancel even within 24h."""
    appt = await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=1)
    resp = await client.post(
        f"/api/v1/appointments/{appt.id}/cancel",
        json={"cancellation_reason": "Staff emergency"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_double_booking_rejected(
    client, customer_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Double-booking same time slot is rejected."""
    first_appt = await _insert_appointment(
        db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=1000
    )
    overlap_start = first_appt.start_time + timedelta(minutes=10)
    resp2 = await client.post(
        "/api/v1/appointments",
        json={
            "staff_profile_id": str(test_staff_profile.id),
            "service_id": str(test_service.id),
            "location_id": str(test_location.id),
            "start_time": overlap_start.isoformat(),
        },
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp2.status_code in (409, 422)


@pytest.mark.asyncio
async def test_cannot_complete_appointment_before_end_time(
    client, manager_token, customer_user, test_staff_profile, test_service, test_location, db_session
):
    """Cannot mark appointment as completed before end time."""
    appt = await _insert_appointment(db_session, test_staff_profile, test_service, test_location, customer_user, hours_from_now=1100)
    resp = await client.post(
        f"/api/v1/appointments/{appt.id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_dashboard(client, manager_token):
    """Manager can access dashboard stats."""
    resp = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_appointments" in data
    assert "staff_busyness" in data
