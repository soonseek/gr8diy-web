"""Alembic environment configuration for async PostgreSQL."""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import AFTER config is set up
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection

# Import Base and models
from app.db.base import Base
from app.models import user  # noqa: F401

from app.core.config import get_settings

# Get database URL from settings
settings = get_settings()
database_url = settings.DATABASE_URL

print(f"[ALEMBIC DEBUG] Database URL: {database_url}")

# Set sqlalchemy URL in config
config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

print(f"[ALEMBIC DEBUG] Target metadata tables: {list(target_metadata.tables.keys())}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a synchronous connection wrapper."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode using asyncpg with proper SSL handling."""
    print("[ALEMBIC DEBUG] Creating async engine...")

    # Import asyncpg and URL utilities
    import asyncpg
    from sqlalchemy import URL

    # Build SQLAlchemy URL with asyncpg_kwargs in query string
    # SQLAlchemy extracts these and passes them to asyncpg.connect()
    url_obj = URL.create(
        "postgresql+asyncpg",
        username="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        database="gr8diy",
        query={"ssl": "disable"},  # Pass ssl=disable to asyncpg
    )

    print(f"[ALEMBIC DEBUG] Engine URL: {url_obj}")

    connectable = create_async_engine(
        url_obj,
        poolclass=pool.NullPool,
        echo=settings.DEBUG,
    )

    print("[ALEMBIC DEBUG] Connecting to database...")

    try:
        async with connectable.connect() as connection:
            print("[ALEMBIC DEBUG] Connection established, running migrations...")

            await connection.run_sync(do_run_migrations)

            print("[ALEMBIC DEBUG] Migrations completed")
    except Exception as e:
        print(f"[ALEMBIC DEBUG] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await connectable.dispose()
        print("[ALEMBIC DEBUG] Engine disposed")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    print("[ALEMBIC DEBUG] Running in online mode")
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    print("[ALEMBIC DEBUG] Running in offline mode")
    run_migrations_offline()
else:
    run_migrations_online()
