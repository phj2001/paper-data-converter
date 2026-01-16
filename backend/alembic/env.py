import os
import sys
from logging.config import fileConfig

from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db import DATABASE_URL
from models import Base

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    from sqlalchemy import create_engine

    connectable = create_engine(DATABASE_URL, pool_pre_ping=True)

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
