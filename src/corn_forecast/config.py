from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from corn_forecast.paths import PROJECT_ROOT


CornBeltBbox = Tuple[float, float, float, float]


@dataclass(frozen=True)
class ProjectConfig:
    """Central research defaults for the weekly CORN forecasting pipeline."""

    root: Path = PROJECT_ROOT
    symbol: str = "CORN"
    start: str = "2011-01-01"
    end: Optional[str] = None
    split_date: str = "2022-12-31"
    test_window_weeks: int = 13
    retrain_step_weeks: int = 13
    validation_scheme: str = "expanding"
    train_window_weeks: int = 260
    long_threshold: float = 0.55
    short_threshold: float = 0.45
    allow_short: bool = False
    transaction_cost_bps: float = 5.0
    buffer_bps: float = 25.0
    fixed_return_threshold: float = 0.02
    corn_belt_bbox: CornBeltBbox = (49.0, -104.0, 37.0, -80.0)

    @classmethod
    def from_args(cls, args: object) -> "ProjectConfig":
        return cls(
            root=Path(getattr(args, "root", PROJECT_ROOT)).resolve(),
            symbol=getattr(args, "symbol", "CORN"),
            start=getattr(args, "start", "2011-01-01"),
            end=getattr(args, "end", None),
            split_date=getattr(args, "split_date", "2022-12-31"),
            test_window_weeks=getattr(args, "test_window_weeks", 13),
            retrain_step_weeks=getattr(args, "retrain_step_weeks", 13),
            validation_scheme=getattr(args, "validation_scheme", "expanding"),
            train_window_weeks=getattr(args, "train_window_weeks", 260),
            long_threshold=getattr(args, "long_threshold", 0.55),
            short_threshold=getattr(args, "short_threshold", 0.45),
            allow_short=getattr(args, "allow_short", False),
            transaction_cost_bps=getattr(args, "transaction_cost_bps", 5.0),
            buffer_bps=getattr(args, "buffer_bps", 25.0),
            fixed_return_threshold=getattr(args, "fixed_return_threshold", 0.02),
        )

    @property
    def raw_prices_path(self) -> Path:
        return self.root / "data" / "raw" / f"prices_{self.symbol}.csv"

    @property
    def raw_usda_path(self) -> Path:
        return self.root / "data" / "raw" / "usda_releases.csv"

    @property
    def weather_path(self) -> Path:
        return self.root / "data" / "interim" / "weather_weekly.parquet"

    @property
    def weather_catalog_path(self) -> Path:
        return self.root / "data" / "interim" / "weather_request_catalog.csv"

    @property
    def panel_path(self) -> Path:
        return self.root / "data" / "processed" / "feature_panel.parquet"

    @property
    def metrics_path(self) -> Path:
        return self.root / "reports" / "metrics.json"

    @property
    def predictions_path(self) -> Path:
        return self.root / "reports" / "predictions.csv"

    @property
    def report_path(self) -> Path:
        return self.root / "reports" / "model_report.md"

    @property
    def price_target_metrics_path(self) -> Path:
        return self.root / "reports" / "price_target_tests.json"

    @property
    def price_target_predictions_path(self) -> Path:
        return self.root / "reports" / "price_target_predictions.csv"

    @property
    def threshold_metrics_path(self) -> Path:
        return self.root / "reports" / "threshold_selection.json"

    @property
    def threshold_predictions_path(self) -> Path:
        return self.root / "reports" / "threshold_selection_predictions.csv"

    @property
    def expected_return_metrics_path(self) -> Path:
        return self.root / "reports" / "expected_return_metrics.json"

    @property
    def expected_return_predictions_path(self) -> Path:
        return self.root / "reports" / "expected_return_predictions.csv"
