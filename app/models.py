# SQLAlchemy ORM models for SlotWise appointment booking system
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

import enum
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String, Boolean, Numeric, Integer, ForeignKey, Text,
    Enum as SAEnum, Date, Time, DateTime, UniqueConstraint,
    CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    customer = "customer"
    staff = "staff"
    manager = "manager"


class DayOfWeek(str, enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class AppointmentStatus(str, enum.Enum):
    confirmed = "confirmed"
    completed = "completed"
    no_show = "no_show"
    cancelled = "cancelled"


class OverrideType(str, enum.Enum):
    day_off = "day_off"
    custom_hours = "custom_hours"


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    staff_profile: Mapped[Optional["StaffProfile"]] = relationship("StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    appointments_as_customer: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="customer", foreign_keys="Appointment.customer_id")
    waitlist_entries: Mapped[List["WaitlistEntry"]] = relationship("WaitlistEntry", back_populates="customer", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    staff_profiles: Mapped[List["StaffProfile"]] = relationship("StaffProfile", back_populates="location")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="location")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    staff_services: Mapped[List["StaffService"]] = relationship("StaffService", back_populates="service", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="service")
    waitlist_entries: Mapped[List["WaitlistEntry"]] = relationship("WaitlistEntry", back_populates="service")


class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="staff_profile")
    location: Mapped[Optional["Location"]] = relationship("Location", back_populates="staff_profiles")
    staff_services: Mapped[List["StaffService"]] = relationship("StaffService", back_populates="staff_profile", cascade="all, delete-orphan")
    availability_schedules: Mapped[List["AvailabilitySchedule"]] = relationship("AvailabilitySchedule", back_populates="staff_profile", cascade="all, delete-orphan")
    availability_overrides: Mapped[List["AvailabilityOverride"]] = relationship("AvailabilityOverride", back_populates="staff_profile", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="staff_profile")
    waitlist_entries: Mapped[List["WaitlistEntry"]] = relationship("WaitlistEntry", back_populates="staff_profile")


class StaffService(Base):
    __tablename__ = "staff_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("staff_profile_id", "service_id", name="uq_staff_service"),
    )

    # Relationships
    staff_profile: Mapped["StaffProfile"] = relationship("StaffProfile", back_populates="staff_services")
    service: Mapped["Service"] = relationship("Service", back_populates="staff_services")


class AvailabilitySchedule(Base):
    """Weekly recurring availability for a staff member."""
    __tablename__ = "availability_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(SAEnum(DayOfWeek), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_schedule_time_order"),
        Index("ix_availability_schedule_staff_day", "staff_profile_id", "day_of_week"),
    )

    # Relationships
    staff_profile: Mapped["StaffProfile"] = relationship("StaffProfile", back_populates="availability_schedules")


class AvailabilityOverride(Base):
    """Date-specific overrides: day off or custom hours."""
    __tablename__ = "availability_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False)
    override_date: Mapped[date] = mapped_column(Date, nullable=False)
    override_type: Mapped[OverrideType] = mapped_column(SAEnum(OverrideType), nullable=False)
    # For custom_hours: start/end times for this specific date (multiple blocks via multiple rows)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_availability_override_staff_date", "staff_profile_id", "override_date"),
    )

    # Relationships
    staff_profile: Mapped["StaffProfile"] = relationship("StaffProfile", back_populates="availability_overrides")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    staff_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    # Start/end stored in UTC
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.confirmed)
    price_at_booking: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_appointment_time_order"),
        Index("ix_appointment_staff_time", "staff_profile_id", "start_time", "end_time"),
        Index("ix_appointment_customer", "customer_id"),
        Index("ix_appointment_location", "location_id"),
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", back_populates="appointments_as_customer", foreign_keys=[customer_id])
    staff_profile: Mapped["StaffProfile"] = relationship("StaffProfile", back_populates="appointments")
    service: Mapped["Service"] = relationship("Service", back_populates="appointments")
    location: Mapped["Location"] = relationship("Location", back_populates="appointments")


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    # Optional: specific staff requested (None = any available)
    staff_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="SET NULL"), nullable=True)
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_waitlist_service_date", "service_id", "requested_date"),
        Index("ix_waitlist_customer", "customer_id"),
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", back_populates="waitlist_entries")
    service: Mapped["Service"] = relationship("Service", back_populates="waitlist_entries")
    location: Mapped["Location"] = relationship("Location")
    staff_profile: Mapped[Optional["StaffProfile"]] = relationship("StaffProfile", back_populates="waitlist_entries")


class NumberEntry(Base):
    __tablename__ = "numbers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

