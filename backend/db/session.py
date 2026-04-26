from __future__ import annotations

from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine

from backend.core.config import get_settings


@lru_cache
def get_engine(database_url: str, echo: bool) -> Engine:
    return create_engine(database_url, echo=echo, pool_pre_ping=True, future=True)


@lru_cache
def _session_factory(database_url: str, echo: bool) -> sessionmaker[Session]:
    engine = get_engine(database_url, echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_session_factory(database_url: str, echo: bool) -> sessionmaker[Session]:
    return _session_factory(database_url, echo)


def get_db() -> Generator[Session, None, None]:
    settings = get_settings()
    if not settings.database.url:
        raise RuntimeError("DATABASE__URL is required before opening a DB session.")

    session_local = _session_factory(settings.database.url, settings.database.echo)
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def ping_database(database_url: str | None = None) -> tuple[bool, str | None]:
    settings = get_settings()
    url = database_url or settings.database.url
    if not url:
        return False, "DATABASE__URL is missing."

    try:
        engine = get_engine(url, settings.database.echo)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as exc:
        return False, f"{exc.__class__.__name__}: {exc}"
    except Exception as exc:  # pragma: no cover - defensive fallback
        return False, f"{exc.__class__.__name__}: {exc}"


def check_required_tables(
    required_tables: set[str],
    database_url: str | None = None,
) -> tuple[bool, list[str]]:
    settings = get_settings()
    url = database_url or settings.database.url
    if not url:
        return False, sorted(required_tables)

    try:
        engine = get_engine(url, settings.database.echo)
        table_names = set(inspect(engine).get_table_names())
        missing = sorted(required_tables.difference(table_names))
        return len(missing) == 0, missing
    except Exception:
        return False, sorted(required_tables)


def check_required_columns(
    required_columns: dict[str, set[str]],
    database_url: str | None = None,
) -> tuple[bool, dict[str, list[str]]]:
    settings = get_settings()
    url = database_url or settings.database.url
    if not url:
        return False, {table_name: sorted(columns) for table_name, columns in required_columns.items()}

    try:
        engine = get_engine(url, settings.database.echo)
        inspector = inspect(engine)
        missing_by_table: dict[str, list[str]] = {}
        for table_name, expected_columns in required_columns.items():
            table_names = set(inspector.get_table_names())
            if table_name not in table_names:
                missing_by_table[table_name] = sorted(expected_columns)
                continue

            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = sorted(expected_columns.difference(actual_columns))
            if missing_columns:
                missing_by_table[table_name] = missing_columns
        return len(missing_by_table) == 0, missing_by_table
    except Exception:
        return False, {table_name: sorted(columns) for table_name, columns in required_columns.items()}


def clear_db_cache() -> None:
    _session_factory.cache_clear()
    get_engine.cache_clear()
