# Waitlist router: join and manage the waitlist for fully-booked slots
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import WaitlistEntry, Service, Location, StaffProfile, User, UserRole
from app.schemas import WaitlistEntryCreate, WaitlistEntryOut
from app.core.auth import get_current_user, require_manager

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post("", response_model=WaitlistEntryOut, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    payload: WaitlistEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join the waitlist for a fully-booked day."""
    if current_user.role != UserRole.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can join the waitlist")

    # Verify service, location exist
    svc = await db.execute(select(Service).where(Service.id == payload.service_id, Service.is_active == True))
    if not svc.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    loc = await db.execute(select(Location).where(Location.id == payload.location_id, Location.is_active == True))
    if not loc.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    # Optional staff preference
    if payload.staff_profile_id:
        sp = await db.execute(select(StaffProfile).where(StaffProfile.id == payload.staff_profile_id))
        if not sp.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

    # Check if already on waitlist for same date+service+location
    existing = await db.execute(
        select(WaitlistEntry).where(
            and_(
                WaitlistEntry.customer_id == current_user.id,
                WaitlistEntry.service_id == payload.service_id,
                WaitlistEntry.location_id == payload.location_id,
                WaitlistEntry.requested_date == payload.requested_date,
                WaitlistEntry.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already on waitlist for this date and service")

    entry = WaitlistEntry(customer_id=current_user.id, **payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("", response_model=List[WaitlistEntryOut])
async def list_waitlist(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List waitlist entries.
    - Customers see only their own
    - Managers see all
    """
    q = select(WaitlistEntry)
    if current_user.role == UserRole.customer:
        q = q.where(WaitlistEntry.customer_id == current_user.id)
    elif current_user.role == UserRole.staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff cannot view waitlist")

    q = q.order_by(WaitlistEntry.created_at.asc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_waitlist(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Leave (deactivate) a waitlist entry."""
    result = await db.execute(select(WaitlistEntry).where(WaitlistEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found")

    if current_user.role == UserRole.customer and entry.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    entry.is_active = False
    await db.commit()
