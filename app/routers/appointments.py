# Appointments router: booking, listing, status updates, cancellation
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Appointment, AppointmentStatus, Service, StaffProfile,
    Location, User, UserRole, StaffService
)
from app.schemas import (
    AppointmentCreate, AppointmentCreateByManager, AppointmentOut, AppointmentDetailOut,
    AppointmentCancelRequest, AppointmentStatusUpdate
)
from app.core.auth import get_current_user, require_manager
from app.services.waitlist import notify_waitlist

router = APIRouter(prefix="/appointments", tags=["appointments"])

FINAL_STATUSES = {AppointmentStatus.completed, AppointmentStatus.no_show, AppointmentStatus.cancelled}


async def _check_no_overlap(
    db: AsyncSession,
    staff_profile_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_id: Optional[uuid.UUID] = None,
) -> None:
    """Raise 409 if any confirmed appointment overlaps [start_time, end_time)."""
    q = select(Appointment).where(
        and_(
            Appointment.staff_profile_id == staff_profile_id,
            Appointment.status == AppointmentStatus.confirmed,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
    )
    if exclude_id:
        q = q.where(Appointment.id != exclude_id)

    # Use FOR UPDATE SKIP LOCKED to prevent race conditions
    result = await db.execute(q.with_for_update(skip_locked=False))
    overlap = result.scalar_one_or_none()
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already booked. Please choose another time.",
        )


async def _book_appointment(
    db: AsyncSession,
    customer_id: uuid.UUID,
    payload: AppointmentCreate,
) -> Appointment:
    """Core booking logic used by both customer and manager endpoints."""
    # Verify staff profile exists
    staff_result = await db.execute(select(StaffProfile).where(StaffProfile.id == payload.staff_profile_id))
    staff = staff_result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")

    # Verify staff works at this location
    if staff.location_id != payload.location_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Staff member does not work at this location",
        )

    # Verify service exists and staff offers it
    svc_result = await db.execute(select(Service).where(Service.id == payload.service_id, Service.is_active == True))
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    ss_result = await db.execute(
        select(StaffService).where(
            StaffService.staff_profile_id == payload.staff_profile_id,
            StaffService.service_id == payload.service_id,
        )
    )
    if not ss_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Staff member does not offer this service",
        )

    # Validate location
    loc_result = await db.execute(select(Location).where(Location.id == payload.location_id, Location.is_active == True))
    if not loc_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    # Make start_time UTC-aware
    start_time = payload.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    else:
        start_time = start_time.astimezone(timezone.utc)

    # Must not be in the past
    now_utc = datetime.now(timezone.utc)
    if start_time <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot book an appointment in the past",
        )

    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Check no overlap
    await _check_no_overlap(db, payload.staff_profile_id, start_time, end_time)

    appointment = Appointment(
        customer_id=customer_id,
        staff_profile_id=payload.staff_profile_id,
        service_id=payload.service_id,
        location_id=payload.location_id,
        start_time=start_time,
        end_time=end_time,
        status=AppointmentStatus.confirmed,
        price_at_booking=service.price,
        notes=payload.notes,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book an appointment as the authenticated customer."""
    if current_user.role == UserRole.staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff cannot book appointments through this endpoint")
    return await _book_appointment(db, current_user.id, payload)


@router.post("/manager", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment_by_manager(
    payload: AppointmentCreateByManager,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Manager books an appointment on behalf of a customer."""
    # Verify customer exists
    cust_result = await db.execute(select(User).where(User.id == payload.customer_id))
    if not cust_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return await _book_appointment(db, payload.customer_id, payload)


@router.get("", response_model=List[AppointmentOut])
async def list_appointments(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    location_id: Optional[uuid.UUID] = Query(None),
    staff_profile_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List appointments:
    - Customers see only their own
    - Staff see only appointments for themselves
    - Managers see all
    """
    q = select(Appointment)

    if current_user.role == UserRole.customer:
        q = q.where(Appointment.customer_id == current_user.id)
    elif current_user.role == UserRole.staff:
        # Get staff profile for this user
        sp_result = await db.execute(select(StaffProfile).where(StaffProfile.user_id == current_user.id))
        sp = sp_result.scalar_one_or_none()
        if not sp:
            return []
        q = q.where(Appointment.staff_profile_id == sp.id)
    # manager sees all — apply optional filters
    if location_id:
        q = q.where(Appointment.location_id == location_id)
    if staff_profile_id and current_user.role == UserRole.manager:
        q = q.where(Appointment.staff_profile_id == staff_profile_id)
    if status_filter:
        q = q.where(Appointment.status == status_filter)

    q = q.order_by(Appointment.start_time.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{appointment_id}", response_model=AppointmentDetailOut)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an appointment by ID. Access controlled by role."""
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.service), selectinload(Appointment.location))
        .where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Access control
    if current_user.role == UserRole.customer and appt.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == UserRole.staff:
        sp_result = await db.execute(select(StaffProfile).where(StaffProfile.user_id == current_user.id))
        sp = sp_result.scalar_one_or_none()
        if not sp or appt.staff_profile_id != sp.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an appointment.
    - Customers: only if >24h before start
    - Staff/Managers: any time
    """
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Access control
    if current_user.role == UserRole.customer:
        if appt.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if appt.status in FINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Appointment is already {appt.status.value} and cannot be changed",
        )

    # 24-hour rule for customers
    if current_user.role == UserRole.customer:
        now_utc = datetime.now(timezone.utc)
        start = appt.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if (start - now_utc) < timedelta(hours=24):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot cancel within 24 hours of appointment. Please call us directly.",
            )

    appt.status = AppointmentStatus.cancelled
    appt.cancellation_reason = payload.cancellation_reason
    await db.commit()
    await db.refresh(appt)

    # Notify waitlist
    appt_date = appt.start_time.date()
    await notify_waitlist(db, appt.service_id, appt.location_id, appt_date, appt.staff_profile_id)
    await db.commit()

    return appt


@router.post("/{appointment_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update appointment to completed or no_show (staff/manager only).
    Only allowed after the appointment end time has passed.
    """
    if current_user.role == UserRole.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers cannot update appointment status")

    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Staff can only update their own appointments
    if current_user.role == UserRole.staff:
        sp_result = await db.execute(select(StaffProfile).where(StaffProfile.user_id == current_user.id))
        sp = sp_result.scalar_one_or_none()
        if not sp or appt.staff_profile_id != sp.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if appt.status in FINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Appointment is already {appt.status.value} and cannot be changed",
        )

    if payload.status not in (AppointmentStatus.completed, AppointmentStatus.no_show, AppointmentStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status must be completed, no_show, or cancelled",
        )

    # Completed/no_show only allowed after appointment end time
    if payload.status in (AppointmentStatus.completed, AppointmentStatus.no_show):
        now_utc = datetime.now(timezone.utc)
        end = appt.end_time
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if now_utc < end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot mark as completed/no_show before the appointment has ended",
            )

    appt.status = payload.status
    if payload.cancellation_reason:
        appt.cancellation_reason = payload.cancellation_reason
    await db.commit()
    await db.refresh(appt)
    return appt
