# Database engine, session factory, and get_db dependency for SlotWise
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DEFAULT_DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada"


def _to_async_url(url: str) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// if not already async."""
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = _to_async_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency that yields an AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
