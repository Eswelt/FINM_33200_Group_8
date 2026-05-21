from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_project_dirs(root: Path) -> None:
    """Create the local data/report directories used by the pipeline."""
    for relative in (
        "data/raw",
        "data/interim",
        "data/processed",
        "reports/figures",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
