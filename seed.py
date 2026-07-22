# Seed script: creates initial data in the SlotWise database
import os
import asyncio
from dotenv import load_dotenv
load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import DATABASE_URL, Base
from app.models import (
    User, UserRole, Location, Service, StaffProfile, StaffService,
    AvailabilitySchedule, DayOfWeek, Appointment, AppointmentStatus
)
from app.core.security import get_password_hash


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        manager_user = User(
            email="manager@slotwise.com",
            hashed_password=get_password_hash("manager123"),
            full_name="Alice Manager",
            role=UserRole.manager,
        )
        staff_user1 = User(
            email="staff1@slotwise.com",
            hashed_password=get_password_hash("staff123"),
            full_name="Bob Stylist",
            role=UserRole.staff,
        )
        staff_user2 = User(
            email="staff2@slotwise.com",
            hashed_password=get_password_hash("staff123"),
            full_name="Carol Therapist",
            role=UserRole.staff,
        )
        customer1 = User(
            email="customer1@example.com",
            hashed_password=get_password_hash("customer123"),
            full_name="Dave Customer",
            role=UserRole.customer,
        )
        customer2 = User(
            email="customer2@example.com",
            hashed_password=get_password_hash("customer123"),
            full_name="Eve Customer",
            role=UserRole.customer,
        )
        db.add_all([manager_user, staff_user1, staff_user2, customer1, customer2])
        await db.flush()

        # --- Locations ---
        location1 = Location(
            name="Downtown Studio",
            address="123 Main St",
            city="Los Angeles",
            timezone="America/Los_Angeles",
        )
        location2 = Location(
            name="Uptown Salon",
            address="456 Oak Ave",
            city="New York",
            timezone="America/New_York",
        )
        db.add_all([location1, location2])
        await db.flush()

        # --- Services ---
        svc_haircut = Service(
            name="Haircut",
            description="Professional haircut and styling",
            duration_minutes=45,
            price=Decimal("35.00"),
        )
        svc_massage = Service(
            name="Swedish Massage",
            description="60-minute relaxing full-body massage",
            duration_minutes=60,
            price=Decimal("89.99"),
        )
        svc_color = Service(
            name="Hair Coloring",
            description="Full hair coloring service",
            duration_minutes=90,
            price=Decimal("120.00"),
        )
        db.add_all([svc_haircut, svc_massage, svc_color])
        await db.flush()

        # --- Staff Profiles ---
        profile1 = StaffProfile(
            user_id=staff_user1.id,
            location_id=location1.id,
            bio="5 years of experience in hair styling.",
        )
        profile2 = StaffProfile(
            user_id=staff_user2.id,
            location_id=location2.id,
            bio="Certified massage therapist.",
        )
        db.add_all([profile1, profile2])
        await db.flush()

        # --- Staff Services ---
        db.add_all([
            StaffService(staff_profile_id=profile1.id, service_id=svc_haircut.id),
            StaffService(staff_profile_id=profile1.id, service_id=svc_color.id),
            StaffService(staff_profile_id=profile2.id, service_id=svc_massage.id),
        ])
        await db.flush()

        # --- Availability Schedules ---
        for day in [DayOfWeek.monday, DayOfWeek.tuesday, DayOfWeek.wednesday, DayOfWeek.thursday, DayOfWeek.friday]:
            db.add(AvailabilitySchedule(
                staff_profile_id=profile1.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
            ))
            db.add(AvailabilitySchedule(
                staff_profile_id=profile2.id,
                day_of_week=day,
                start_time=time(10, 0),
                end_time=time(18, 0),
            ))

        # Weekend for profile2
        db.add(AvailabilitySchedule(
            staff_profile_id=profile2.id,
            day_of_week=DayOfWeek.saturday,
            start_time=time(10, 0),
            end_time=time(15, 0),
        ))
        await db.flush()

        # --- Sample future appointments ---
        import pytz
        la_tz = pytz.timezone("America/Los_Angeles")
        future_date = datetime.now(timezone.utc) + timedelta(days=3)
        start_local = la_tz.localize(datetime(future_date.year, future_date.month, future_date.day, 10, 0))
        start_utc = start_local.astimezone(timezone.utc)

        appt1 = Appointment(
            customer_id=customer1.id,
            staff_profile_id=profile1.id,
            service_id=svc_haircut.id,
            location_id=location1.id,
            start_time=start_utc,
            end_time=start_utc + timedelta(minutes=svc_haircut.duration_minutes),
            status=AppointmentStatus.confirmed,
            price_at_booking=svc_haircut.price,
            notes="First visit",
        )
        db.add(appt1)

        start2 = start_utc + timedelta(hours=2)
        appt2 = Appointment(
            customer_id=customer2.id,
            staff_profile_id=profile1.id,
            service_id=svc_color.id,
            location_id=location1.id,
            start_time=start2,
            end_time=start2 + timedelta(minutes=svc_color.duration_minutes),
            status=AppointmentStatus.confirmed,
            price_at_booking=svc_color.price,
        )
        db.add(appt2)

        await db.commit()

    print("Seed complete!")
    print(f"  Manager:   manager@slotwise.com / manager123")
    print(f"  Staff 1:   staff1@slotwise.com / staff123 (Downtown Studio - LA)")
    print(f"  Staff 2:   staff2@slotwise.com / staff123 (Uptown Salon - NY)")
    print(f"  Customer 1: customer1@example.com / customer123")
    print(f"  Customer 2: customer2@example.com / customer123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
