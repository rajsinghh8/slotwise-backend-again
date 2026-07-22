# Dashboard router: manager analytics and reporting
import os
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Appointment, AppointmentStatus, StaffProfile, User
from app.schemas import DashboardStats
from app.core.auth import require_manager

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_manager),
):
    """Return dashboard statistics for managers."""
    now_utc = datetime.now(timezone.utc)
    seven_days_ago = now_utc - timedelta(days=7)

    # Total counts by status
    counts = await db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .group_by(Appointment.status)
    )
    status_counts = {row[0]: row[1] for row in counts.fetchall()}

    total = sum(status_counts.values())
    completed = status_counts.get(AppointmentStatus.completed, 0)
    no_show = status_counts.get(AppointmentStatus.no_show, 0)
    cancelled = status_counts.get(AppointmentStatus.cancelled, 0)

    # Recent appointments (last 7 days)
    recent_result = await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.created_at >= seven_days_ago
        )
    )
    recent = recent_result.scalar_one() or 0

    # Staff busyness: count of confirmed appointments per staff member
    busyness_result = await db.execute(
        select(
            StaffProfile.id,
            func.count(Appointment.id).label("appointment_count"),
        )
        .join(Appointment, Appointment.staff_profile_id == StaffProfile.id, isouter=True)
        .group_by(StaffProfile.id)
        .order_by(func.count(Appointment.id).desc())
        .limit(20)
    )
    staff_busyness = [
        {"staff_profile_id": str(row[0]), "appointment_count": row[1]}
        for row in busyness_result.fetchall()
    ]

    return DashboardStats(
        total_appointments=total,
        completed_appointments=completed,
        no_show_appointments=no_show,
        cancelled_appointments=cancelled,
        recent_appointments=recent,
        staff_busyness=staff_busyness,
    )
