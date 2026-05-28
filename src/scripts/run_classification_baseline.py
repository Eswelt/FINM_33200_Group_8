"""One-click runner for the current CORN ETF classification baseline.

Run from the repository root:

    uv run --extra dev doit baseline
"""

from cli import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "classify-move",
                "--start",
                "2011-01-01",
                "--end",
                "2026-05-15",
                "--split-date",
                "2022-12-31",
                "--fixed-return-threshold",
                "0.02",
                "--feature-sets",
                "price_only,price_calendar",
            ]
        )
    )
