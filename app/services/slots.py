# Slot generation service: computes available appointment slots for a staff member on a date
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

import uuid
from datetime import datetime, date, time, timedelta, timezone
from typing import List, Tuple
import pytz

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AvailabilitySchedule, AvailabilityOverride, Appointment,
    DayOfWeek, OverrideType, AppointmentStatus, StaffProfile
)


DAY_MAP = {
    0: DayOfWeek.monday,
    1: DayOfWeek.tuesday,
    2: DayOfWeek.wednesday,
    3: DayOfWeek.thursday,
    4: DayOfWeek.friday,
    5: DayOfWeek.saturday,
    6: DayOfWeek.sunday,
}

SLOT_INTERVAL_MINUTES = 15


def _combine_utc(local_date: date, local_time: time, tz: pytz.BaseTzInfo) -> datetime:
    """Combine a local date + time into a UTC-aware datetime."""
    local_dt = datetime.combine(local_date, local_time)
    local_aware = tz.localize(local_dt)
    return local_aware.astimezone(timezone.utc)


async def get_working_blocks(
    db: AsyncSession,
    staff_profile_id: uuid.UUID,
    target_date: date,
    location_timezone: str,
) -> List[Tuple[datetime, datetime]]:
    """
    Return list of (utc_start, utc_end) working blocks for staff on target_date.
    Overrides take precedence over regular schedule.
    Returns empty list if day off or no schedule.
    """
    tz = pytz.timezone(location_timezone)
    dow = DAY_MAP[target_date.weekday()]

    # Check for overrides on this date
    override_result = await db.execute(
        select(AvailabilityOverride).where(
            and_(
                AvailabilityOverride.staff_profile_id == staff_profile_id,
                AvailabilityOverride.override_date == target_date,
            )
        )
    )
    overrides = override_result.scalars().all()

    if overrides:
        # Check for day_off override
        if any(o.override_type == OverrideType.day_off for o in overrides):
            return []
        # Custom hours
        blocks = []
        for o in overrides:
            if o.override_type == OverrideType.custom_hours and o.start_time and o.end_time:
                utc_start = _combine_utc(target_date, o.start_time, tz)
                utc_end = _combine_utc(target_date, o.end_time, tz)
                blocks.append((utc_start, utc_end))
        return sorted(blocks, key=lambda x: x[0])

    # No overrides — use regular weekly schedule
    schedule_result = await db.execute(
        select(AvailabilitySchedule).where(
            and_(
                AvailabilitySchedule.staff_profile_id == staff_profile_id,
                AvailabilitySchedule.day_of_week == dow,
            )
        )
    )
    schedules = schedule_result.scalars().all()

    blocks = []
    for s in schedules:
        utc_start = _combine_utc(target_date, s.start_time, tz)
        utc_end = _combine_utc(target_date, s.end_time, tz)
        blocks.append((utc_start, utc_end))
    return sorted(blocks, key=lambda x: x[0])


async def get_booked_intervals(
    db: AsyncSession,
    staff_profile_id: uuid.UUID,
    target_date: date,
    location_timezone: str,
) -> List[Tuple[datetime, datetime]]:
    """Return list of (utc_start, utc_end) for existing confirmed appointments on this date."""
    tz = pytz.timezone(location_timezone)
    day_start = _combine_utc(target_date, time(0, 0, 0), tz)
    day_end = _combine_utc(target_date, time(23, 59, 59), tz)

    result = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.staff_profile_id == staff_profile_id,
                Appointment.status == AppointmentStatus.confirmed,
                Appointment.start_time >= day_start,
                Appointment.start_time < day_end,
            )
        )
    )
    appointments = result.scalars().all()
    return [(a.start_time, a.end_time) for a in appointments]


def generate_slots(
    working_blocks: List[Tuple[datetime, datetime]],
    booked_intervals: List[Tuple[datetime, datetime]],
    duration_minutes: int,
    location_timezone: str,
) -> List[Tuple[datetime, datetime]]:
    """
    Generate all valid 15-min-spaced slots in local time that:
    - Fit entirely within a working block
    - Don't overlap any booked interval
    - Are not in the past
    Returns list of (local_start, local_end) as tz-aware datetimes.
    """
    tz = pytz.timezone(location_timezone)
    now_utc = datetime.now(timezone.utc)
    interval = timedelta(minutes=SLOT_INTERVAL_MINUTES)
    duration = timedelta(minutes=duration_minutes)

    slots = []
    for block_start, block_end in working_blocks:
        current = block_start
        while current + duration <= block_end:
            slot_end = current + duration
            # Not in the past
            if current > now_utc:
                # No overlap with booked intervals
                overlap = False
                for booked_start, booked_end in booked_intervals:
                    # Overlap condition: slot_start < booked_end AND slot_end > booked_start
                    if current < booked_end and slot_end > booked_start:
                        overlap = True
                        break
                if not overlap:
                    # Convert to local time for response
                    local_start = current.astimezone(tz)
                    local_end = slot_end.astimezone(tz)
                    slots.append((local_start, local_end))
            current += interval
    return slots


async def compute_available_slots(
    db: AsyncSession,
    staff_profile_id: uuid.UUID,
    service_duration_minutes: int,
    target_date: date,
    location_timezone: str,
) -> List[Tuple[datetime, datetime]]:
    """Full pipeline: get working blocks, subtract booked, return open slots."""
    working_blocks = await get_working_blocks(db, staff_profile_id, target_date, location_timezone)
    if not working_blocks:
        return []
    booked_intervals = await get_booked_intervals(db, staff_profile_id, target_date, location_timezone)
    return generate_slots(working_blocks, booked_intervals, service_duration_minutes, location_timezone)
