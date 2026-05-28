"""Copy generated figure assets into the ChartBook output tree."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "docs_src" / "figures"
TARGET_DIR = ROOT / "docs_src" / "reports" / "chartbook" / "cb" / "figures"
FINAL_REPORT = ROOT / "docs_src" / "reports" / "chartbook" / "cb" / "final_report.html"


def main() -> int:
    if SOURCE_DIR.exists():
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        for source in sorted(SOURCE_DIR.glob("final_*.png")):
            shutil.copy2(source, TARGET_DIR / source.name)

    if FINAL_REPORT.exists():
        html = FINAL_REPORT.read_text(encoding="utf-8")
        html = html.replace('src="cb/figures/', 'src="figures/')
        FINAL_REPORT.write_text(html, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
