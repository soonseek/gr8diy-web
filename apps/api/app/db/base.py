"""Database base and utilities."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database."""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models import user  # noqa: F401

        # Create tables (use Alembic for migrations in production)
        await conn.run_sync(lambda conn: None)
