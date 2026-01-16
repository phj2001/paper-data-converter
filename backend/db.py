import json
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _load_database_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config_url = data.get("database_url")
            if config_url:
                return config_url
        except Exception:
            pass

    raise RuntimeError("DATABASE_URL is not configured")


DATABASE_URL = _load_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
