# Slots router: compute and return available booking time slots
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import StaffProfile, Service, Location, StaffService, User
from app.schemas import SlotOut
from app.core.auth import get_current_user
from app.services.slots import compute_available_slots

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("", response_model=List[SlotOut])
async def get_available_slots(
    staff_profile_id: uuid.UUID = Query(...),
    service_id: uuid.UUID = Query(...),
    date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Return available 15-minute-spaced booking slots for a staff member on a given date.
    Times are returned in the location's local timezone.
    """
    # Verify staff profile
    sp_result = await db.execute(select(StaffProfile).where(StaffProfile.id == staff_profile_id))
    staff = sp_result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

    # Verify staff offers this service
    ss_result = await db.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == staff_profile_id,
            StaffService.service_id == service_id,
        )
    )
    if not ss_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Staff member does not offer this service",
        )

    # Get service duration
    svc_result = await db.execute(select(Service).where(Service.id == service_id, Service.is_active == True))
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    # Get location timezone
    if not staff.location_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Staff member has no assigned location")

    loc_result = await db.execute(select(Location).where(Location.id == staff.location_id))
    location = loc_result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    slots = await compute_available_slots(
        db=db,
        staff_profile_id=staff_profile_id,
        service_duration_minutes=service.duration_minutes,
        target_date=date,
        location_timezone=location.timezone,
    )

    return [SlotOut(start_time=s, end_time=e) for s, e in slots]
