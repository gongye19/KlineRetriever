from __future__ import annotations

import os
from datetime import date, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import get_default_symbols
from data_loader import SyncConfig, incremental_sync, sync_data
from db import init_db
from search import load_symbol_series, search_similar

app = FastAPI(title="Kline Retriever API", version="1.0.0")
scheduler = BackgroundScheduler(timezone="UTC")
logger = logging.getLogger(__name__)

cors_origins = os.getenv("CORS_ORIGINS", "*")
allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SyncRequest(BaseModel):
    symbols: list[str] = Field(default_factory=get_default_symbols)
    start: str | None = None
    end: str | None = None


class SearchRequest(BaseModel):
    symbol: str
    interval: str = Field(pattern="^(1d|1w)$")
    start: str
    end: str
    top_n: int = Field(default=10, ge=1, le=50)


def _validate_interval(interval: str) -> None:
    if interval not in {"1d", "1w"}:
        raise HTTPException(status_code=400, detail="interval must be 1d or 1w")


def run_incremental_sync() -> dict[str, dict[str, int]]:
    return incremental_sync(symbols=get_default_symbols())


def safe_incremental_sync() -> None:
    try:
        report = run_incremental_sync()
        logger.info("incremental sync done: %s", report)
    except Exception as exc:  # pragma: no cover
        logger.exception("incremental sync failed: %s", exc)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # Startup sync ensures service bootstraps itself without manual clicks.
    safe_incremental_sync()

    hours = int(os.getenv("SYNC_INTERVAL_HOURS", "12"))
    scheduler.add_job(
        safe_incremental_sync,
        "interval",
        hours=hours,
        id="incremental-sync",
        replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> dict[str, list[str]]:
    return {"symbols": get_default_symbols()}


@app.post("/sync")
def sync(payload: SyncRequest) -> dict[str, dict[str, int]]:
    today = date.today().isoformat()
    start = payload.start or (date.today() - timedelta(days=365 * 3)).isoformat()
    end = payload.end or today
    symbols = [s.upper() for s in payload.symbols]
    config = SyncConfig(symbols=symbols, start=start, end=end)
    return sync_data(config)


@app.post("/sync/incremental")
def sync_incremental(symbols: list[str] | None = None) -> dict[str, dict[str, int]]:
    cleaned = [s.upper() for s in symbols] if symbols else None
    return incremental_sync(cleaned)


@app.get("/kline")
def get_kline(
    symbol: str = Query(..., min_length=1),
    interval: str = Query("1d"),
    start: str = Query(...),
    end: str = Query(...),
) -> dict:
    _validate_interval(interval)
    df = load_symbol_series(symbol=symbol.upper(), interval=interval, start=start, end=end)
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "count": len(df),
        "items": df.to_dict(orient="records"),
    }


@app.post("/search")
def search(payload: SearchRequest) -> dict:
    query_df, results = search_similar(
        symbol=payload.symbol.upper(),
        interval=payload.interval,
        start=payload.start,
        end=payload.end,
        top_n=payload.top_n,
    )
    return {
        "query": {
            "symbol": payload.symbol.upper(),
            "interval": payload.interval,
            "start": payload.start,
            "end": payload.end,
            "window_size": len(query_df),
        },
        "results": [
            {
                "symbol": r.symbol,
                "score": r.score,
                "start_date": r.start_date,
                "end_date": r.end_date,
            }
            for r in results
        ],
    }
