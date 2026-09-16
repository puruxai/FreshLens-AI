from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# PostgreSQL Connection Engine & Session Factory
connect_args = {}
if "pooler.supabase.com" in settings.DATABASE_URL or ":6543" in settings.DATABASE_URL:
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative base for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# DB initialization function for FastAPI lifecycle
async def init_databases() -> None:
    # Import all SQLAlchemy models to register them with Base.metadata
    from app.modules.user.models import User
    from app.modules.inventory.models import InventoryItem, Batch
    from app.modules.inspection.models import QualityInspection
    from app.modules.image_analysis.models import ImageAnalysis
    from app.modules.storage.models import StorageReading
    from app.modules.notification.models import Notification, NotificationPreference
    from app.modules.system.models import SystemLog

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to yield PostgreSQL sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
