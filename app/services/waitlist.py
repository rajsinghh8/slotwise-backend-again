# Waitlist notification service for SlotWise
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WaitlistEntry, User


async def notify_waitlist(
    db: AsyncSession,
    service_id: uuid.UUID,
    location_id: uuid.UUID,
    cancelled_date: date,
    staff_profile_id: Optional[uuid.UUID] = None,
) -> None:
    """
    Find the longest-waiting active waitlist entry matching the cancelled slot
    and mark them as notified (placeholder for real email/push notification).
    """
    # Build query: match service, location, date, and optional specific staff
    conditions = [
        WaitlistEntry.service_id == service_id,
        WaitlistEntry.location_id == location_id,
        WaitlistEntry.requested_date == cancelled_date,
        WaitlistEntry.is_active == True,
        WaitlistEntry.is_notified == False,
    ]

    # Match either: requesting this specific staff, or requesting any staff (None)
    if staff_profile_id is not None:
        conditions.append(
            or_(
                WaitlistEntry.staff_profile_id == staff_profile_id,
                WaitlistEntry.staff_profile_id == None,
            )
        )

    result = await db.execute(
        select(WaitlistEntry)
        .where(and_(*conditions))
        .order_by(WaitlistEntry.created_at.asc())
        .limit(1)
    )
    entry = result.scalar_one_or_none()

    if entry is not None:
        entry.is_notified = True
        await db.flush()
        # TODO: Send actual email/push notification to entry.customer
        # For now this is a stub — the record is marked so we know who was notified
