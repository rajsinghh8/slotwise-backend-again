# Availability router: weekly schedules and date overrides for staff members
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AvailabilitySchedule, AvailabilityOverride, StaffProfile, User, UserRole
from app.schemas import (
    AvailabilityScheduleCreate, AvailabilityScheduleUpdate, AvailabilityScheduleOut,
    AvailabilityOverrideCreate, AvailabilityOverrideOut,
)
from app.core.auth import get_current_user, require_manager

router = APIRouter(tags=["availability"])


def _can_manage_staff(current_user: User, profile: StaffProfile) -> bool:
    """Check if current user can manage this staff profile."""
    if current_user.role == UserRole.manager:
        return True
    if current_user.role == UserRole.staff and profile.user_id == current_user.id:
        return True
    return False


async def _get_staff_profile_or_404(staff_id: uuid.UUID, db: AsyncSession) -> StaffProfile:
    result = await db.execute(select(StaffProfile).where(StaffProfile.id == staff_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    return profile


# ── Weekly Schedules ──────────────────────────────────────────────────────────

@router.post(
    "/staff/{staff_id}/schedules",
    response_model=AvailabilityScheduleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    staff_id: uuid.UUID,
    payload: AvailabilityScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a weekly availability block for a staff member."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if not _can_manage_staff(current_user, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    schedule = AvailabilitySchedule(
        staff_profile_id=staff_id,
        **payload.model_dump(),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.get("/staff/{staff_id}/schedules", response_model=List[AvailabilityScheduleOut])
async def list_schedules(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all weekly schedule blocks for a staff member."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    # Staff can only see their own; managers see all; customers see any
    if current_user.role == UserRole.staff and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view another staff member's schedule")

    result = await db.execute(
        select(AvailabilitySchedule).where(AvailabilitySchedule.staff_profile_id == staff_id)
    )
    return result.scalars().all()


@router.put("/staff/{staff_id}/schedules/{schedule_id}", response_model=AvailabilityScheduleOut)
async def update_schedule(
    staff_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: AvailabilityScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a weekly schedule block."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if not _can_manage_staff(current_user, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(AvailabilitySchedule).where(
            and_(AvailabilitySchedule.id == schedule_id, AvailabilitySchedule.staff_profile_id == staff_id)
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/staff/{staff_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    staff_id: uuid.UUID,
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a weekly schedule block."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if not _can_manage_staff(current_user, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(AvailabilitySchedule).where(
            and_(AvailabilitySchedule.id == schedule_id, AvailabilitySchedule.staff_profile_id == staff_id)
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()


# ── Date Overrides ────────────────────────────────────────────────────────────

@router.post(
    "/staff/{staff_id}/overrides",
    response_model=AvailabilityOverrideOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_override(
    staff_id: uuid.UUID,
    payload: AvailabilityOverrideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a date-specific override (day off or custom hours)."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if not _can_manage_staff(current_user, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    override = AvailabilityOverride(staff_profile_id=staff_id, **payload.model_dump())
    db.add(override)
    await db.commit()
    await db.refresh(override)
    return override


@router.get("/staff/{staff_id}/overrides", response_model=List[AvailabilityOverrideOut])
async def list_overrides(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all date overrides for a staff member."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if current_user.role == UserRole.staff and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view another staff member's overrides")

    result = await db.execute(
        select(AvailabilityOverride).where(AvailabilityOverride.staff_profile_id == staff_id)
    )
    return result.scalars().all()


@router.delete("/staff/{staff_id}/overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_override(
    staff_id: uuid.UUID,
    override_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a date override."""
    profile = await _get_staff_profile_or_404(staff_id, db)
    if not _can_manage_staff(current_user, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(AvailabilityOverride).where(
            and_(AvailabilityOverride.id == override_id, AvailabilityOverride.staff_profile_id == staff_id)
        )
    )
    override = result.scalar_one_or_none()
    if not override:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")

    await db.delete(override)
    await db.commit()
