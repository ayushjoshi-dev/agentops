"""
Alembic Migrations Environment
================================

WHY ALEMBIC?
------------
Alembic is the database migration tool for SQLAlchemy.

Instead of manually running SQL like:
    ALTER TABLE orders ADD COLUMN tracking_number VARCHAR(50);

Alembic lets you:
1. Write a Python migration file
2. Run: alembic upgrade head
3. The database schema is updated automatically

WHY MIGRATIONS MATTER:
----------------------
In production, you can't just DROP TABLE and recreate.
You have real data. Migrations apply changes incrementally.

Every schema change = a new migration file.
You can upgrade (apply change) or downgrade (revert change).

HOW TO USE:
-----------
1. Create migration:  alembic revision --autogenerate -m "add column x"
2. Apply migration:   alembic upgrade head
3. Revert:            alembic downgrade -1

Run from: backend/ directory
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the backend directory to the Python path
# so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base

# Import ALL models so Alembic can detect them for autogenerate
# Every model file must be imported here — Alembic reads Base.metadata
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.ticket import SupportTicket
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document, DocumentChunk
from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall

# Alembic Config object — reads alembic.ini
config = context.config

# Override the sqlalchemy.url with our settings
# configparser treats % as interpolation syntax, so we must escape them
# by doubling: % → %% (only needed when setting via set_main_option)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# Set up Python logging from alembic.ini config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for 'autogenerate' support
# Alembic compares this to the actual DB schema to generate migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This doesn't need an active database connection.
    Used for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (normal mode).
    
    Connects to the database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
