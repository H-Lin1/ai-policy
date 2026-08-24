from __future__ import annotations

import time
from collections.abc import Generator
from functools import lru_cache
from typing import Literal

from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import Settings, get_settings
from .errors import AppError


class Base(DeclarativeBase):
    """SQLAlchemy metadata root for future business models."""


DatabaseWarmupStatus = Literal["ok", "not_configured", "unavailable"]


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, future=True, connect_args=connect_args)


def database_engine(settings: Settings | None = None) -> Engine | None:
    settings = settings or get_settings()
    if not settings.normalized_database_url:
        return None
    return get_engine(settings.normalized_database_url)


def get_db(settings: Settings | None = None) -> Generator[Session, None, None]:
    engine = database_engine(settings)
    if engine is None:
        raise AppError(
            "DATABASE_NOT_CONFIGURED",
            "数据库尚未配置",
            status_code=503,
        )
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def request_db_session(
    settings: Settings = Depends(get_settings),
) -> Generator[Session | None, None, None]:
    """Yield one optional database session shared by dependencies in a request."""

    try:
        engine = database_engine(settings)
    except Exception:  # noqa: BLE001 - configuration details stay private.
        yield None
        return
    if engine is None:
        yield None
        return

    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        session = factory()
    except Exception:  # noqa: BLE001 - connection details stay private.
        yield None
        return
    try:
        yield session
    finally:
        session.close()


def warm_database_connection(
    settings: Settings | None = None,
) -> tuple[DatabaseWarmupStatus, float]:
    """Prime one pooled database connection with a read-only probe."""

    started = time.perf_counter()
    try:
        engine = database_engine(settings)
        if engine is None:
            return "not_configured", 0.0
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - startup warmup must fail closed and stay generic.
        return "unavailable", round((time.perf_counter() - started) * 1000, 2)
    return "ok", round((time.perf_counter() - started) * 1000, 2)


def check_database(settings: Settings | None = None) -> tuple[bool, str]:
    engine = database_engine(settings)
    if engine is None:
        return False, "not_configured"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "ok"
    except SQLAlchemyError:
        return False, "unavailable"
