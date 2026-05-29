"""Fix generated ChartBook figure assets."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs_src" / "figures"
TARGET_DIR = ROOT / "reports" / "chartbook" / "cb" / "figures"
CHARTBOOK_DIR = ROOT / "reports" / "chartbook"
WEATHER_PLOTS_DIR = (
    ROOT
    / "weather_corn_etf"
    / "corn_etf_daily_decision_leadbylead_expanding_yearly"
    / "signal_buffer_0p0pct"
    / "plots"
)


def _copy_png_tree(source_dir: Path, target_dir: Path) -> None:
    if not source_dir.exists():
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(source_dir.rglob("*.png")):
        relative_path = source.relative_to(source_dir)
        target = target_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _copy_figures() -> None:
    _copy_png_tree(SOURCE_DIR, TARGET_DIR)
    _copy_png_tree(WEATHER_PLOTS_DIR, TARGET_DIR / "weather_daily_decision")


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
