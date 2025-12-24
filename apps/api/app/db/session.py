"""Database session management."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
