# Pydantic v2 schemas for SlotWise request/response models
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import uuid
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.models import UserRole, DayOfWeek, AppointmentStatus, OverrideType


# ── Base Config ───────────────────────────────────────────────────────────────

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.customer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(OrmBase):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


# ── Location ──────────────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    name: str
    address: str
    city: str
    timezone: str = "UTC"


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class LocationOut(OrmBase):
    id: uuid.UUID
    name: str
    address: str
    city: str
    timezone: str
    is_active: bool
    created_at: datetime


# ── Service ───────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: Decimal

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        return round(v, 2)

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return round(v, 2)
        return v


class ServiceOut(OrmBase):
    id: uuid.UUID
    name: str
    description: Optional[str]
    duration_minutes: int
    price: Decimal
    is_active: bool
    created_at: datetime


# ── Staff Profile ─────────────────────────────────────────────────────────────

class StaffProfileCreate(BaseModel):
    user_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None


class StaffProfileUpdate(BaseModel):
    location_id: Optional[uuid.UUID] = None
    bio: Optional[str] = None


class StaffProfileOut(OrmBase):
    id: uuid.UUID
    user_id: uuid.UUID
    location_id: Optional[uuid.UUID]
    bio: Optional[str]
    created_at: datetime


class StaffProfileDetailOut(OrmBase):
    id: uuid.UUID
    user_id: uuid.UUID
    location_id: Optional[uuid.UUID]
    bio: Optional[str]
    created_at: datetime
    user: UserOut
    location: Optional[LocationOut]


# ── Staff Service (M2M) ───────────────────────────────────────────────────────

class StaffServiceCreate(BaseModel):
    service_id: uuid.UUID


class StaffServiceOut(OrmBase):
    id: uuid.UUID
    staff_profile_id: uuid.UUID
    service_id: uuid.UUID
    created_at: datetime


# ── Availability Schedule ─────────────────────────────────────────────────────

class AvailabilityScheduleCreate(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_times(self) -> "AvailabilityScheduleCreate":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AvailabilityScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class AvailabilityScheduleOut(OrmBase):
    id: uuid.UUID
    staff_profile_id: uuid.UUID
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    created_at: datetime


# ── Availability Override ─────────────────────────────────────────────────────

class AvailabilityOverrideCreate(BaseModel):
    override_date: date
    override_type: OverrideType
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def validate_custom_hours(self) -> "AvailabilityOverrideCreate":
        if self.override_type == OverrideType.custom_hours:
            if self.start_time is None or self.end_time is None:
                raise ValueError("start_time and end_time required for custom_hours override")
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time")
        return self


class AvailabilityOverrideOut(OrmBase):
    id: uuid.UUID
    staff_profile_id: uuid.UUID
    override_date: date
    override_type: OverrideType
    start_time: Optional[time]
    end_time: Optional[time]
    note: Optional[str]
    created_at: datetime


# ── Appointment ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    staff_profile_id: uuid.UUID
    service_id: uuid.UUID
    location_id: uuid.UUID
    start_time: datetime
    notes: Optional[str] = None


class AppointmentCreateByManager(AppointmentCreate):
    customer_id: uuid.UUID


class AppointmentOut(OrmBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    staff_profile_id: uuid.UUID
    service_id: uuid.UUID
    location_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    price_at_booking: Decimal
    notes: Optional[str]
    cancellation_reason: Optional[str]
    created_at: datetime


class AppointmentDetailOut(OrmBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    staff_profile_id: uuid.UUID
    service_id: uuid.UUID
    location_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    price_at_booking: Decimal
    notes: Optional[str]
    cancellation_reason: Optional[str]
    created_at: datetime
    service: ServiceOut
    location: LocationOut


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    cancellation_reason: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    cancellation_reason: Optional[str] = None


# ── Available Slots ───────────────────────────────────────────────────────────

class AvailableSlotsRequest(BaseModel):
    staff_profile_id: uuid.UUID
    service_id: uuid.UUID
    date: date


class SlotOut(BaseModel):
    start_time: datetime  # local time
    end_time: datetime    # local time


# ── Waitlist ──────────────────────────────────────────────────────────────────

class WaitlistEntryCreate(BaseModel):
    service_id: uuid.UUID
    location_id: uuid.UUID
    staff_profile_id: Optional[uuid.UUID] = None
    requested_date: date


class WaitlistEntryOut(OrmBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    service_id: uuid.UUID
    location_id: uuid.UUID
    staff_profile_id: Optional[uuid.UUID]
    requested_date: date
    is_notified: bool
    is_active: bool
    created_at: datetime


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_appointments: int
    completed_appointments: int
    no_show_appointments: int
    cancelled_appointments: int
    recent_appointments: int  # last 7 days
    staff_busyness: List[dict]


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list


# ── Numbers ───────────────────────────────────────────────────────────────────

class NumberCreate(BaseModel):
    value: int


class NumberOut(OrmBase):
    id: int
    value: int
    created_at: datetime

