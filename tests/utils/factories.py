# Factory helpers for building valid test request payloads
import uuid
from datetime import datetime, timedelta, timezone, date, time


def user_register_payload(
    email: str = None,
    password: str = "TestPass123!",
    full_name: str = "Test User",
    role: str = "customer",
) -> dict:
    return {
        "email": email or f"user_{uuid.uuid4().hex[:8]}@example.com",
        "password": password,
        "full_name": full_name,
        "role": role,
    }


def location_payload(
    name: str = "Test Location",
    address: str = "123 Test St",
    city: str = "Test City",
    timezone: str = "America/Los_Angeles",
) -> dict:
    return {
        "name": name,
        "address": address,
        "city": city,
        "timezone": timezone,
    }


def service_payload(
    name: str = "Test Service",
    duration_minutes: int = 60,
    price: str = "49.99",
    description: str = "A test service",
) -> dict:
    return {
        "name": name,
        "description": description,
        "duration_minutes": duration_minutes,
        "price": price,
    }


def schedule_payload(
    day_of_week: str = "monday",
    start_time: str = "09:00:00",
    end_time: str = "17:00:00",
) -> dict:
    return {
        "day_of_week": day_of_week,
        "start_time": start_time,
        "end_time": end_time,
    }


def appointment_payload(
    staff_profile_id: str = None,
    service_id: str = None,
    location_id: str = None,
    hours_from_now: int = 48,
    notes: str = None,
) -> dict:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    payload = {
        "staff_profile_id": staff_profile_id or str(uuid.uuid4()),
        "service_id": service_id or str(uuid.uuid4()),
        "location_id": location_id or str(uuid.uuid4()),
        "start_time": start.isoformat(),
    }
    if notes:
        payload["notes"] = notes
    return payload


def waitlist_payload(
    service_id: str = None,
    location_id: str = None,
    requested_date: str = None,
    staff_profile_id: str = None,
) -> dict:
    payload = {
        "service_id": service_id or str(uuid.uuid4()),
        "location_id": location_id or str(uuid.uuid4()),
        "requested_date": requested_date or (date.today() + timedelta(days=7)).isoformat(),
    }
    if staff_profile_id:
        payload["staff_profile_id"] = staff_profile_id
    return payload
