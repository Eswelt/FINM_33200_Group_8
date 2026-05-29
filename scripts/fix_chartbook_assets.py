"""Fix generated ChartBook figure assets."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs_src" / "figures"
TARGET_DIR = ROOT / "reports" / "chartbook" / "cb" / "figures"
CHARTBOOK_DIR = ROOT / "reports" / "chartbook"


def _copy_figures() -> None:
    if not SOURCE_DIR.exists():
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for source in sorted(SOURCE_DIR.rglob("*.png")):
        relative_path = source.relative_to(SOURCE_DIR)
        target = TARGET_DIR / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _fix_figure_paths() -> None:
    cb_dir = CHARTBOOK_DIR / "cb"
    if not cb_dir.exists():
        return

    for html_path in cb_dir.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        fixed = html.replace('src="cb/figures/', 'src="figures/')
        if fixed != html:
            html_path.write_text(fixed, encoding="utf-8")


def main() -> int:
    _copy_figures()
    _fix_figure_paths()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
