"""Alembic environment configuration for async PostgreSQL."""
import asyncio
import logging
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

# Setup logger for alembic env
logger = logging.getLogger("alembic.env")

# Import AFTER config is set up
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import make_url

# Import Base and models
from app.db.base import Base
from app.models import user  # noqa: F401

from app.core.config import get_settings

# Get database URL from settings
settings = get_settings()
database_url = settings.DATABASE_URL

logger.info(f"Database URL: {database_url}")

# Set sqlalchemy URL in config
config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

logger.info(f"Target metadata tables: {list(target_metadata.tables.keys())}")


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
    logger.info("Creating async engine...")

    # Parse the database URL from settings
    url = make_url(database_url)

    # Configure SSL based on environment
    # For local development, disable SSL; for production, use prefer/require
    ssl_mode = "disable" if settings.ENVIRONMENT == "development" else "prefer"

    # Update query parameters for SSL
    query = dict(url.query or {})
    query["ssl"] = ssl_mode

    # Rebuild URL with SSL configuration
    url_obj = url.set(query=query)

    logger.info(f"Engine URL: {url_obj.render_as_string(hide_password=True)}")
    logger.debug(f"SSL mode: {ssl_mode}")

    connectable = create_async_engine(
        url_obj,
        poolclass=pool.NullPool,
        echo=settings.DEBUG,
    )

    logger.info("Connecting to database...")

    try:
        async with connectable.connect() as connection:
            logger.info("Connection established, running migrations...")

            await connection.run_sync(do_run_migrations)

            logger.info("Migrations completed")
    except Exception as e:
        logger.error(f"Migration error: {type(e).__name__}: {e}", exc_info=True)
        raise
    finally:
        await connectable.dispose()
        logger.info("Engine disposed")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.info("Running in online mode")
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    logger.info("Running in offline mode")
    run_migrations_offline()
else:
    run_migrations_online()
