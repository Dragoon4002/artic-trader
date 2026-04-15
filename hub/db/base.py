"""SQLAlchemy async engine + session factory."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ..config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
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


async def init_db():
    """Create all tables (dev). For prod use Alembic."""
    from . import models  # noqa: F401 — ensure all models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
