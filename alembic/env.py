import sys
import logging
from logging.config import fileConfig


from alembic import context

# ensure project root is on path
sys.path.insert(0, "")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
try:
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)
except Exception:
    # If the ini file doesn't contain expected logging sections, skip logging config.
    logging.basicConfig()
logger = logging.getLogger("alembic.env")

# Import project models and settings
from app.db.base import Base, UserBase  # noqa: E402
from app.config import settings  # noqa: E402

# Map specific databases to their metadata
target_metadata = {
    "default": Base.metadata,
    "user": UserBase.metadata
}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    # For offline mode, we might need to run for each DB explicitly or just default.
    # A simple approach for multi-db offline is iterating known DBs.

    # Database URLs
    db_urls = {
        "default": settings.DATABASE_URL,
        "user": settings.USER_DATABASE_URL,
    }

    for name, url in db_urls.items():
        context.configure(
            url=url,
            target_metadata=target_metadata.get(name),
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            render_as_batch=False,
            # Use distinct upgrade functions or branches if we had them,
            # but here we just distinguish by name
        )

        with context.begin_transaction():
            context.run_migrations(engine_name=name)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """

    # We can import engines directly from app.db to ensure we use the same config
    from app.db.database import engine as run_engine, user_engine

    engines = {
        "default": run_engine,
        "user": user_engine
    }

    for name, engine in engines.items():
        logger.info(f"Migrating database: {name}")

        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata.get(name),
                compare_type=True,
                render_as_batch=False,
                upgrade_token=f"{name}_upgrades",
                downgrade_token=f"{name}_downgrades",
            )

            with context.begin_transaction():
                context.run_migrations(engine_name=name)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
