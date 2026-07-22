# Test configuration and fixtures for SlotWise pytest suite
import os
import uuid as _uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv('.env_3698610c-0a42-47f4-8734-fc3a8dd320bd', override=True)

from app.main import app
from app.database import Base, get_db
from app.models import (
    User, UserRole, Location, Service, StaffProfile, StaffService,
    AvailabilitySchedule, DayOfWeek
)
from app.core.security import get_password_hash

MAIN_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada")
_parts = MAIN_DB_URL.rsplit("/", 1)
TEST_DB_URL = (_parts[0] + "/" + _parts[1] + "_test") if len(_parts) == 2 else MAIN_DB_URL


@pytest.fixture(scope="session")
async def db_engine():
    # Create schema in main DB
    main_engine = create_async_engine(MAIN_DB_URL, poolclass=NullPool)
    async with main_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await main_engine.dispose()

    # Test DB engine
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_factory(db_engine):
    """Session factory for creating per-test sessions."""
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
async def db_session(session_factory):
    """Session-scoped DB session for creating shared fixtures."""
    async with session_factory() as session:
        yield session
        try:
            await session.rollback()
        except Exception:
            pass


@pytest.fixture
async def test_db_session(session_factory):
    """Function-scoped DB session for individual tests."""
    async with session_factory() as session:
        yield session
        try:
            await session.rollback()
        except Exception:
            pass


@pytest.fixture(scope="session")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── Shared test data fixtures (unique emails per test to avoid conflicts) ─────

@pytest.fixture(scope="session")
async def manager_user(db_session: AsyncSession) -> User:
    unique = _uuid.uuid4().hex[:8]
    user = User(
        email=f"mgr_{unique}@slotwise.com",
        hashed_password=get_password_hash("mgr_pass_123"),
        full_name="Test Manager",
        role=UserRole.manager,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="session")
async def customer_user(db_session: AsyncSession) -> User:
    unique = _uuid.uuid4().hex[:8]
    user = User(
        email=f"cust_{unique}@slotwise.com",
        hashed_password=get_password_hash("cust_pass_123"),
        full_name="Test Customer",
        role=UserRole.customer,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="session")
async def staff_user(db_session: AsyncSession) -> User:
    unique = _uuid.uuid4().hex[:8]
    user = User(
        email=f"staff_{unique}@slotwise.com",
        hashed_password=get_password_hash("staff_pass_123"),
        full_name="Test Staff",
        role=UserRole.staff,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="session")
async def test_location(db_session: AsyncSession) -> Location:
    location = Location(
        name=f"Test Location {_uuid.uuid4().hex[:6]}",
        address="1 Test Street",
        city="Test City",
        timezone="America/Los_Angeles",
    )
    db_session.add(location)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(location)
    return location


@pytest.fixture(scope="session")
async def test_service(db_session: AsyncSession) -> Service:
    from decimal import Decimal
    service = Service(
        name=f"Test Haircut {_uuid.uuid4().hex[:6]}",
        description="A test haircut service",
        duration_minutes=60,
        price=Decimal("50.00"),
    )
    db_session.add(service)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.fixture(scope="session")
async def test_staff_profile(db_session: AsyncSession, staff_user: User, test_location: Location) -> StaffProfile:
    profile = StaffProfile(
        user_id=staff_user.id,
        location_id=test_location.id,
        bio="Test staff member",
    )
    db_session.add(profile)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture(scope="session")
async def manager_token(client: AsyncClient, manager_user: User) -> str:
    resp = await client.post("/api/v1/auth/login", json={
        "email": manager_user.email,
        "password": "mgr_pass_123",
    })
    assert resp.status_code == 200, f"Manager login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
async def customer_token(client: AsyncClient, customer_user: User) -> str:
    resp = await client.post("/api/v1/auth/login", json={
        "email": customer_user.email,
        "password": "cust_pass_123",
    })
    assert resp.status_code == 200, f"Customer login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
async def staff_token(client: AsyncClient, staff_user: User) -> str:
    resp = await client.post("/api/v1/auth/login", json={
        "email": staff_user.email,
        "password": "staff_pass_123",
    })
    assert resp.status_code == 200, f"Staff login failed: {resp.text}"
    return resp.json()["access_token"]
