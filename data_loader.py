from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import pandas as pd
import yfinance as yf
from sqlalchemy import text

from db import get_engine, init_db


@dataclass(frozen=True)
class SyncConfig:
    symbols: list[str]
    start: str
    end: str


DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "JPM",
    "XOM",
    "WMT",
    "KO",
    "SPY",
    "QQQ",
    "IWM",
]


def _download(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        progress=False,
        auto_adjust=False,
        threads=False,
    )
    if df.empty:
        return df
    # yfinance sometimes creates MultiIndex columns.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df = df.reset_index()
    rename_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=rename_map)
    if "date" not in df.columns:
        # Weekly data may contain Datetime column depending on version.
        dt_cols = [c for c in df.columns if str(c).lower().startswith("date")]
        if dt_cols:
            df = df.rename(columns={dt_cols[0]: "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df[["date", "open", "high", "low", "close", "volume"]].dropna()


def _upsert_symbol(symbols: Iterable[str]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for symbol in symbols:
            conn.execute(
                text(
                    """
                    INSERT INTO symbols(symbol, name, active)
                    VALUES (:symbol, :name, 1)
                    ON CONFLICT(symbol) DO UPDATE SET active=1;
                    """
                ),
                {"symbol": symbol, "name": symbol},
            )


def _upsert_kline(symbol: str, df: pd.DataFrame, table: str) -> int:
    if df.empty:
        return 0
    engine = get_engine()
    rows = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text(
                    f"""
                    INSERT INTO {table}(symbol, date, open, high, low, close, volume)
                    VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
                    ON CONFLICT(symbol, date) DO UPDATE SET
                        open=excluded.open,
                        high=excluded.high,
                        low=excluded.low,
                        close=excluded.close,
                        volume=excluded.volume;
                    """
                ),
                {
                    "symbol": symbol,
                    "date": row["date"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]) if pd.notna(row["volume"]) else None,
                },
            )
            rows += 1
    return rows


def sync_data(config: SyncConfig) -> dict[str, dict[str, int]]:
    init_db()
    _upsert_symbol(config.symbols)
    report: dict[str, dict[str, int]] = {}

    for symbol in config.symbols:
        daily_df = _download(symbol, config.start, config.end, "1d")
        weekly_df = _download(symbol, config.start, config.end, "1wk")
        daily_count = _upsert_kline(symbol, daily_df, "kline_daily")
        weekly_count = _upsert_kline(symbol, weekly_df, "kline_weekly")
        report[symbol] = {"daily": daily_count, "weekly": weekly_count}
    return report


def incremental_sync(symbols: list[str] | None = None) -> dict[str, dict[str, int]]:
    init_db()
    symbols = symbols or DEFAULT_SYMBOLS
    _upsert_symbol(symbols)
    engine = get_engine()
    today = datetime.now().strftime("%Y-%m-%d")
    report: dict[str, dict[str, int]] = {}

    for symbol in symbols:
        with engine.connect() as conn:
            latest_daily = conn.execute(
                text("SELECT MAX(date) AS max_date FROM kline_daily WHERE symbol = :symbol"),
                {"symbol": symbol},
            ).scalar()
        start = "2021-01-01"
        if latest_daily:
            latest_dt = pd.to_datetime(str(latest_daily))
            start = (latest_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        daily_df = _download(symbol, start, today, "1d")
        weekly_df = _download(symbol, start, today, "1wk")
        daily_count = _upsert_kline(symbol, daily_df, "kline_daily")
        weekly_count = _upsert_kline(symbol, weekly_df, "kline_weekly")
        report[symbol] = {"daily": daily_count, "weekly": weekly_count}
    return report


def default_config() -> SyncConfig:
    today = datetime.now().strftime("%Y-%m-%d")
    return SyncConfig(
        symbols=DEFAULT_SYMBOLS,
        start="2021-01-01",
        end=today,
    )
