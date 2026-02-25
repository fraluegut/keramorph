"""
Keramorph – Model evaluation.

Computes classification metrics, confusion matrices, calibration,
per-class reports and logs everything to MLflow.
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import mlflow
import numpy as np
import structlog
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    top_k_accuracy_score,
)

from ml.features.extraction import extract_all_descriptors, extract_contour

logger = structlog.get_logger(__name__)

__all__ = ["evaluate_model", "generate_report"]


def _top_k_acc(y_true: np.ndarray, y_proba: np.ndarray, k: int) -> float:
    """Top-k accuracy (handles edge cases)."""
    if y_proba.shape[1] < k:
        return float("nan")
    return float(top_k_accuracy_score(y_true, y_proba, k=k, labels=range(y_proba.shape[1])))


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_names: list[str],
    top_k: list[int] | None = None,
    model_name: str = "model",
) -> dict[str, Any]:
    """Evaluate a sklearn-compatible model and log to MLflow.

    Returns a dict with all metrics and artefact paths.
    """
    top_k = top_k or [1, 3, 5]

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    metrics: dict[str, Any] = {
        "accuracy": float(acc),
        "f1_macro": float(f1),
    }

    if y_proba is not None:
        for k in top_k:
            metrics[f"top_{k}_accuracy"] = _top_k_acc(y_test, y_proba, k)
        try:
            metrics["log_loss"] = float(log_loss(y_test, y_proba))
        except Exception:
            pass

    # confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    metrics["confusion_matrix"] = cm.tolist()

    # per-class report
    report = classification_report(y_test, y_pred, target_names=label_names, output_dict=True, zero_division=0)
    metrics["per_class"] = report

    # log to MLflow
    for k, v in metrics.items():
        if isinstance(v, (int, float)):
            mlflow.log_metric(f"test_{k}", v)

    # save confusion matrix as artifact
    _log_confusion_matrix_artifact(cm, label_names, model_name)

    logger.info(
        "evaluation_complete",
        model=model_name,
        accuracy=round(acc, 4),
        f1_macro=round(f1, 4),
    )
    return metrics


def _log_confusion_matrix_artifact(
    cm: np.ndarray, label_names: list[str], model_name: str
) -> None:
    """Render a confusion matrix as text and log to MLflow."""
    lines = [f"Confusion Matrix — {model_name}", ""]
    header = "".join(f"{n:>12}" for n in label_names)
    lines.append(f"{'':>12}{header}")
    for i, row in enumerate(cm):
        vals = "".join(f"{int(v):>12}" for v in row)
        lines.append(f"{label_names[i]:>12}{vals}")
    text = "\n".join(lines)
    mlflow.log_text(text, f"confusion_matrix_{model_name}.txt")


def generate_report(
    config: dict[str, Any],
    processed_dir: str | Path,
    splits: dict[str, list[dict[str, Any]]],
    models: dict[str, Any],
    label_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Evaluate all models on the test split and return joint report."""
    processed_dir = Path(processed_dir)
    test_records = splits["test"]

    from ml.training.train import _extract_features_for_split

    X_test, y_test = _extract_features_for_split(processed_dir, test_records, config)

    results: dict[str, dict[str, Any]] = {}
    for name, model in models.items():
        with mlflow.start_run(run_name=f"eval_{name}"):
            res = evaluate_model(model, X_test, y_test, label_names, model_name=name)
            results[name] = res

    logger.info("report_generated", models=list(results.keys()))
    return results
