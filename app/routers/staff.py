# Staff profiles router: manage staff profiles and their services
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import StaffProfile, StaffService, Service, User, UserRole
from app.schemas import (
    StaffProfileCreate, StaffProfileUpdate, StaffProfileOut, StaffProfileDetailOut,
    StaffServiceCreate, StaffServiceOut
)
from app.core.auth import get_current_user, require_manager

router = APIRouter(prefix="/staff", tags=["staff"])


@router.post("", response_model=StaffProfileOut, status_code=status.HTTP_201_CREATED)
async def create_staff_profile(
    payload: StaffProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Create a staff profile. Manager only."""
    # Ensure user exists and has staff role
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role not in (UserRole.staff, UserRole.manager):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="User must have staff or manager role")

    # Check no profile exists
    existing = await db.execute(select(StaffProfile).where(StaffProfile.user_id == payload.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff profile already exists for this user")

    profile = StaffProfile(**payload.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("", response_model=List[StaffProfileOut])
async def list_staff(
    location_id: uuid.UUID = Query(None),
    service_id: uuid.UUID = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List staff profiles, optionally filtered by location and/or service."""
    query = select(StaffProfile)
    if location_id:
        query = query.where(StaffProfile.location_id == location_id)
    if service_id:
        query = query.join(StaffService).where(StaffService.service_id == service_id)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/me", response_model=StaffProfileDetailOut)
async def get_my_staff_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current staff member's profile (staff role required)."""
    if current_user.role not in (UserRole.staff, UserRole.manager):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff or manager role required")
    result = await db.execute(
        select(StaffProfile)
        .options(selectinload(StaffProfile.user), selectinload(StaffProfile.location))
        .where(StaffProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    return profile


@router.get("/{staff_id}", response_model=StaffProfileDetailOut)
async def get_staff_profile(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a staff profile by ID."""
    result = await db.execute(
        select(StaffProfile)
        .options(selectinload(StaffProfile.user), selectinload(StaffProfile.location))
        .where(StaffProfile.id == staff_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    return profile


@router.put("/{staff_id}", response_model=StaffProfileOut)
async def update_staff_profile(
    staff_id: uuid.UUID,
    payload: StaffProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a staff profile. Staff can update their own; managers can update any."""
    result = await db.execute(select(StaffProfile).where(StaffProfile.id == staff_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

    if current_user.role == UserRole.staff and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another staff member's profile")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile


# ── Staff Services (M2M) ──────────────────────────────────────────────────────

@router.post("/{staff_id}/services", response_model=StaffServiceOut, status_code=status.HTTP_201_CREATED)
async def add_staff_service(
    staff_id: uuid.UUID,
    payload: StaffServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Assign a service to a staff member. Manager only."""
    result = await db.execute(select(StaffProfile).where(StaffProfile.id == staff_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

    svc_result = await db.execute(select(Service).where(Service.id == payload.service_id))
    if not svc_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    existing = await db.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == staff_id,
            StaffService.service_id == payload.service_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already assigned")

    ss = StaffService(staff_profile_id=staff_id, service_id=payload.service_id)
    db.add(ss)
    await db.commit()
    await db.refresh(ss)
    return ss


@router.get("/{staff_id}/services", response_model=List[StaffServiceOut])
async def list_staff_services(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all services offered by a staff member."""
    result = await db.execute(
        select(StaffService).where(StaffService.staff_profile_id == staff_id)
    )
    return result.scalars().all()


@router.delete("/{staff_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff_service(
    staff_id: uuid.UUID,
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Remove a service from a staff member. Manager only."""
    result = await db.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == staff_id,
            StaffService.service_id == service_id,
        )
    )
    ss = result.scalar_one_or_none()
    if not ss:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff service mapping not found")
    await db.delete(ss)
    await db.commit()
