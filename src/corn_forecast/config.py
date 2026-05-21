from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from corn_forecast.paths import PROJECT_ROOT


CornBeltBbox = Tuple[float, float, float, float]


@dataclass(frozen=True)
class ProjectConfig:
    root: Path = PROJECT_ROOT
    symbol: str = "CORN"
    start: str = "2011-01-01"
    end: Optional[str] = None
    split_date: str = "2022-12-31"
    corn_belt_bbox: CornBeltBbox = (49.0, -104.0, 37.0, -80.0)

    @classmethod
    def from_args(cls, args: object) -> "ProjectConfig":
        return cls(
            root=Path(getattr(args, "root", PROJECT_ROOT)).resolve(),
            symbol=getattr(args, "symbol", "CORN"),
            start=getattr(args, "start", "2011-01-01"),
            end=getattr(args, "end", None),
            split_date=getattr(args, "split_date", "2022-12-31"),
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
