"""SQLAlchemy async engine + session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import settings


def _normalize_async_url(url: str) -> str:
    """Render/Heroku give `postgres://…`; SQLAlchemy needs `postgresql+asyncpg://…`."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    # asyncpg rejects ?sslmode=…; expects ?ssl=require for managed Postgres.
    if "sslmode=" in url:
        url = url.replace("sslmode=require", "ssl=require").replace("sslmode=", "ssl=")
    return url


engine = create_async_engine(
    _normalize_async_url(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    """FastAPI Depends generator."""
    async with async_session() as session:
        yield session
