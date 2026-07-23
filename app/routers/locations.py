# Locations router: CRUD for business locations (manager only for write operations)
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Location, User
from app.schemas import LocationCreate, LocationUpdate, LocationOut
from app.core.auth import get_current_user, require_manager

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Create a new location. Manager only."""
    location = Location(**payload.model_dump())
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


@router.get("", response_model=List[LocationOut])
async def list_locations(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all active locations."""
    result = await db.execute(
        select(Location).where(Location.is_active == True).offset(offset).limit(limit)
    )
    return result.scalars().all()


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single location by ID."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: uuid.UUID,
    payload: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Update a location. Manager only."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(location, key, value)

    await db.commit()
    await db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Soft-delete a location (set inactive). Manager only."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    location.is_active = False
    await db.commit()
