from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_SQLITE_URL = f"sqlite:///{DATA_DIR / 'kline.db'}"


def _normalize_database_url(url: str | None) -> str:
    if not url:
        return DEFAULT_SQLITE_URL
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def get_engine() -> Engine:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_url = _normalize_database_url(os.getenv("DATABASE_URL"))
    return create_engine(db_url, pool_pre_ping=True, future=True)


def init_db() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    active INTEGER NOT NULL DEFAULT 1
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS kline_daily (
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open DOUBLE PRECISION NOT NULL,
                    high DOUBLE PRECISION NOT NULL,
                    low DOUBLE PRECISION NOT NULL,
                    close DOUBLE PRECISION NOT NULL,
                    volume DOUBLE PRECISION,
                    PRIMARY KEY (symbol, date)
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS kline_weekly (
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open DOUBLE PRECISION NOT NULL,
                    high DOUBLE PRECISION NOT NULL,
                    low DOUBLE PRECISION NOT NULL,
                    close DOUBLE PRECISION NOT NULL,
                    volume DOUBLE PRECISION,
                    PRIMARY KEY (symbol, date)
                );
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_kline_daily_date ON kline_daily(date);"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_kline_weekly_date ON kline_weekly(date);"
            )
        )
