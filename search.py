from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine
from sqlalchemy import text

from db import get_engine


@dataclass
class SearchResult:
    symbol: str
    score: float
    start_date: str
    end_date: str


def load_symbol_series(
    symbol: str,
    interval: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    table = "kline_daily" if interval == "1d" else "kline_weekly"
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(
            text(
                f"""
                SELECT symbol, date, open, high, low, close, volume
                FROM {table}
                WHERE symbol = :symbol
                  AND date >= :start
                  AND date <= :end
                ORDER BY date ASC;
                """
            ),
            conn,
            params={"symbol": symbol.upper(), "start": start, "end": end},
        )
    return df


def _normalize(close_values: np.ndarray) -> np.ndarray:
    base = close_values[0]
    if base == 0:
        return close_values
    return close_values / base


def _score(query_norm: np.ndarray, candidate_norm: np.ndarray) -> float:
    if len(query_norm) != len(candidate_norm):
        return 0.0
    if np.allclose(query_norm, query_norm[0]) and np.allclose(
        candidate_norm, candidate_norm[0]
    ):
        return 1.0
    if np.std(query_norm) == 0 or np.std(candidate_norm) == 0:
        return 0.0
    return float(1.0 - cosine(query_norm, candidate_norm))


def search_similar(
    symbol: str,
    interval: str,
    start: str,
    end: str,
    top_n: int = 10,
) -> tuple[pd.DataFrame, list[SearchResult]]:
    query_df = load_symbol_series(symbol, interval, start, end)
    if query_df.empty:
        return query_df, []

    window = len(query_df)
    if window < 5:
        return query_df, []

    query_norm = _normalize(query_df["close"].astype(float).to_numpy())
    table = "kline_daily" if interval == "1d" else "kline_weekly"

    engine = get_engine()
    results: list[SearchResult] = []
    with engine.connect() as conn:
        symbols_df = pd.read_sql_query(
            text("SELECT symbol FROM symbols WHERE active = 1 ORDER BY symbol ASC;"),
            conn,
        )

        for candidate_symbol in symbols_df["symbol"].tolist():
            if candidate_symbol == symbol.upper():
                continue
            candidate_df = pd.read_sql_query(
                text(
                    f"""
                    SELECT date, close
                    FROM {table}
                    WHERE symbol = :symbol
                      AND date >= :start
                      AND date <= :end
                    ORDER BY date ASC;
                    """
                ),
                conn,
                params={"symbol": candidate_symbol, "start": start, "end": end},
            )
            if len(candidate_df) != window:
                continue
            candidate_norm = _normalize(candidate_df["close"].astype(float).to_numpy())
            score = _score(query_norm, candidate_norm)
            if np.isnan(score):
                continue
            results.append(
                SearchResult(
                    symbol=candidate_symbol,
                    score=score,
                    start_date=str(candidate_df["date"].iloc[0]),
                    end_date=str(candidate_df["date"].iloc[-1]),
                )
            )

    results = sorted(results, key=lambda x: x.score, reverse=True)[:top_n]
    return query_df, results


def load_series_for_symbol(
    symbol: str,
    interval: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    return load_symbol_series(symbol, interval, start, end)
