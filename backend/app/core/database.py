from collections.abc import Generator
from pathlib import Path
from shutil import copy2

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _sqlite_file_path(url: str) -> Path | None:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return None
    return Path(url.removeprefix(prefix))


def _bootstrap_sqlite_database() -> None:
    default_target = Path("./data/advanced_marketplace.db")
    legacy_source = Path("./advanced_marketplace.db")
    target_path = _sqlite_file_path(settings.database_url)
    if target_path is None:
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path == default_target and not target_path.exists() and legacy_source.exists():
        copy2(legacy_source, target_path)


_bootstrap_sqlite_database()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
