from pathlib import Path

from config import load_symbols_from_file


def test_load_symbols_from_file_deduplicates_and_ignores_comments(tmp_path: Path) -> None:
    file_path = tmp_path / "symbols.txt"
    file_path.write_text(
        "\n".join(
            [
                "# core symbols",
                "aapl",
                " msft ",
                "AAPL",
                "",
                "nvda",
            ]
        ),
        encoding="utf-8",
    )
    symbols = load_symbols_from_file(file_path)
    assert symbols == ["AAPL", "MSFT", "NVDA"]
