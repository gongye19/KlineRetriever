from __future__ import annotations

import os
from pathlib import Path

DEFAULT_SYMBOLS_FALLBACK = [
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

SYMBOLS_FILE_PATH = Path(__file__).resolve().parent / "config" / "symbols.txt"


def _clean_symbol_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in items:
        s = raw.strip().upper()
        if not s or s.startswith("#"):
            continue
        if s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


def load_symbols_from_file(path: Path | None = None) -> list[str]:
    file_path = path or SYMBOLS_FILE_PATH
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8")
    return _clean_symbol_list(content.splitlines())


def get_default_symbols() -> list[str]:
    # Optional env override for emergency online changes.
    env_value = os.getenv("DEFAULT_SYMBOLS", "").strip()
    if env_value:
        return _clean_symbol_list(env_value.split(","))

    symbols = load_symbols_from_file()
    if symbols:
        return symbols
    return DEFAULT_SYMBOLS_FALLBACK.copy()
