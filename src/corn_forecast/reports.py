import json
import os
from pathlib import Path
from typing import Dict

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import roc_curve


def save_metrics(metrics: Dict[str, Dict[str, float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, allow_nan=True)


def load_metrics(path: Path) -> Dict[str, Dict[str, float]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_predictions(predictions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(path, index=False)


def plot_prediction_probabilities(predictions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = predictions.copy()
    frame["week"] = pd.to_datetime(frame["week"])

    fig, ax = plt.subplots(figsize=(11, 5))
    for model, group in frame.groupby("model"):
        ax.plot(group["week"], group["y_prob"], label=model, linewidth=1.4)
    ax.axhline(0.5, color="black", linestyle="--", linewidth=0.9)
    ax.set_title("Predicted probability of positive next-week CORN return")
    ax.set_xlabel("Week")
    ax.set_ylabel("P(up next week)")
    ax.legend(loc="best")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_roc_curves(predictions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    for model, group in predictions.groupby("model"):
        if group["y_true"].nunique() < 2:
            continue
        fpr, tpr, _ = roc_curve(group["y_true"], group["y_prob"])
        ax.plot(fpr, tpr, label=model, linewidth=1.6)
    ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=0.9)
    ax.set_title("ROC curves by feature set")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def write_markdown_report(metrics: Dict[str, Dict[str, float]], predictions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CORN ETF One-Week Direction MVP",
        "",
        "## Metrics",
        "",
        "| Feature set | Accuracy | Balanced accuracy | F1 | ROC-AUC | Log loss | Test rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model, values in metrics.items():
        lines.append(
            "| {model} | {accuracy:.3f} | {balanced_accuracy:.3f} | {f1:.3f} | {roc_auc:.3f} | {log_loss:.3f} | {n_test} |".format(
                model=model,
                accuracy=values.get("accuracy", float("nan")),
                balanced_accuracy=values.get("balanced_accuracy", float("nan")),
                f1=values.get("f1", float("nan")),
                roc_auc=values.get("roc_auc", float("nan")),
                log_loss=values.get("log_loss", float("nan")),
                n_test=int(values.get("n_test", 0)),
            )
        )

    start = pd.to_datetime(predictions["week"]).min().date()
    end = pd.to_datetime(predictions["week"]).max().date()
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Prediction window: {start} to {end}.",
            "- Figures: `reports/figures/predicted_probabilities.png` and `reports/figures/roc_curves.png`.",
            "- CSV/JSON outputs are generated locally and ignored by git.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_report_artifacts(metrics_path: Path, predictions_path: Path, report_path: Path, figures_dir: Path) -> None:
    metrics = load_metrics(metrics_path)
    predictions = pd.read_csv(predictions_path)
    plot_prediction_probabilities(predictions, figures_dir / "predicted_probabilities.png")
    plot_roc_curves(predictions, figures_dir / "roc_curves.png")
    write_markdown_report(metrics, predictions, report_path)
