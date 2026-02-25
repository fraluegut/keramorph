"""
Keramorph – Training module.

Trains all model variants:
  • baseline_knn  — k-NN on shape descriptors
  • baseline_xgb  — XGBoost on shape descriptors
  • prod_cnn      — EfficientNet-B0 / MobileNet on normalised contour images
  • siamese       — Siamese / metric-learning (optional)
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cv2
import mlflow
import mlflow.sklearn
import mlflow.pytorch
import numpy as np
import structlog
import yaml
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from ml.features.extraction import (
    extract_all_descriptors,
    extract_contour,
    normalise_profile,
)

logger = structlog.get_logger(__name__)

__all__ = ["train_baseline_knn", "train_baseline_xgb", "train_cnn", "run_training"]


# ─── helpers ────────────────────────────────────────────

def _load_config(config_path: str | Path = "ml/configs/train_config.yaml") -> dict[str, Any]:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _load_splits(processed_dir: str | Path) -> dict[str, list[dict[str, Any]]]:
    path = Path(processed_dir) / "splits.json"
    return json.loads(path.read_text())


def _extract_features_for_split(
    processed_dir: Path,
    records: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """Extract descriptor vectors for a list of split records."""
    X_list: list[np.ndarray] = []
    y_list: list[str] = []

    prep = config.get("preprocessing", {})
    n_fourier = prep.get("fourier_descriptors", 64)

    for rec in records:
        img_path = processed_dir / rec["path"]
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        cr = extract_contour(
            img,
            method=prep.get("contour_method", "canny"),
            canny_low=prep.get("canny_low", 50),
            canny_high=prep.get("canny_high", 150),
            morph_kernel=prep.get("morph_kernel", 5),
            morph_iters=prep.get("morph_iterations", 2),
        )
        if cr is None:
            continue
        feats = extract_all_descriptors(cr, num_fourier=n_fourier)
        X_list.append(feats)
        y_list.append(rec["label"])

    return np.array(X_list), np.array(y_list)


# ─── baseline k-NN ──────────────────────────────────────

def train_baseline_knn(
    config: dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> KNeighborsClassifier:
    """Train k-NN on descriptor features."""
    knn_cfg = config["models"]["baseline_knn"]
    model = KNeighborsClassifier(
        n_neighbors=knn_cfg.get("n_neighbors", 5),
        metric=knn_cfg.get("metric", "euclidean"),
    )
    model.fit(X_train, y_train)

    val_acc = float(model.score(X_val, y_val))
    logger.info("knn_trained", val_accuracy=val_acc)

    mlflow.log_param("model_type", "knn")
    mlflow.log_param("n_neighbors", knn_cfg.get("n_neighbors", 5))
    mlflow.log_metric("val_accuracy", val_acc)
    mlflow.sklearn.log_model(model, "model_knn")

    return model


# ─── baseline XGBoost ───────────────────────────────────

def train_baseline_xgb(
    config: dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> XGBClassifier:
    """Train XGBoost on descriptor features."""
    xgb_cfg = config["models"]["baseline_xgb"]
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    y_val_enc = le.transform(y_val)

    model = XGBClassifier(
        n_estimators=xgb_cfg.get("n_estimators", 300),
        max_depth=xgb_cfg.get("max_depth", 6),
        learning_rate=xgb_cfg.get("learning_rate", 0.1),
        use_label_encoder=False,
        eval_metric="mlogloss",
    )
    model.fit(
        X_train,
        y_train_enc,
        eval_set=[(X_val, y_val_enc)],
        verbose=False,
    )

    val_acc = float(model.score(X_val, y_val_enc))
    logger.info("xgb_trained", val_accuracy=val_acc)

    mlflow.log_params({
        "model_type": "xgboost",
        "n_estimators": xgb_cfg.get("n_estimators", 300),
        "max_depth": xgb_cfg.get("max_depth", 6),
        "learning_rate": xgb_cfg.get("learning_rate", 0.1),
    })
    mlflow.log_metric("val_accuracy", val_acc)
    mlflow.sklearn.log_model(model, "model_xgb")

    return model


# ─── CNN (PyTorch) ──────────────────────────────────────

def train_cnn(
    config: dict[str, Any],
    processed_dir: str | Path,
    splits: dict[str, list[dict[str, Any]]],
) -> Any:
    """Train a CNN (EfficientNet-B0 / MobileNet) on normalised contour images.

    Uses PyTorch + timm.
    """
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    import timm

    cnn_cfg = config["models"]["prod_cnn"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processed_dir = Path(processed_dir)

    # ── dataset ────────────
    class ProfileDataset(Dataset):
        def __init__(self, records: list[dict[str, Any]], label_map: dict[str, int]) -> None:
            self.records = records
            self.label_map = label_map
            self.prep = config.get("preprocessing", {})

        def __len__(self) -> int:
            return len(self.records)

        def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
            rec = self.records[idx]
            img = cv2.imread(str(processed_dir / rec["path"]), cv2.IMREAD_GRAYSCALE)
            if img is None:
                img = np.zeros((224, 224), dtype=np.uint8)

            cr = extract_contour(img)
            if cr is not None:
                img = normalise_profile(img, cr, target_size=tuple(self.prep.get("target_size", [224, 224])))
            else:
                img = cv2.resize(img, tuple(self.prep.get("target_size", [224, 224])))

            tensor = torch.from_numpy(img).float().unsqueeze(0) / 255.0  # (1, H, W)
            label = self.label_map[rec["label"]]
            return tensor, label

    # label mapping
    all_labels = sorted(set(r["label"] for split in splits.values() for r in split))
    label_map = {lbl: i for i, lbl in enumerate(all_labels)}
    num_classes = len(label_map)

    train_ds = ProfileDataset(splits["train"], label_map)
    val_ds = ProfileDataset(splits["val"], label_map)
    train_dl = DataLoader(train_ds, batch_size=cnn_cfg.get("batch_size", 32), shuffle=True, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=cnn_cfg.get("batch_size", 32), shuffle=False, num_workers=0)

    # ── model ──────────────
    arch = cnn_cfg.get("architecture", "efficientnet_b0")
    model = timm.create_model(arch, pretrained=cnn_cfg.get("pretrained", True), in_chans=1, num_classes=num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=cnn_cfg.get("label_smoothing", 0.1))
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=cnn_cfg.get("learning_rate", 1e-3),
        weight_decay=cnn_cfg.get("weight_decay", 1e-4),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cnn_cfg.get("epochs", 50)
    )

    # ── training loop ──────
    best_val_acc = 0.0
    patience_counter = 0
    patience = cnn_cfg.get("early_stopping_patience", 7)

    for epoch in range(1, cnn_cfg.get("epochs", 50) + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_dl:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += labels.size(0)

        scheduler.step()
        train_acc = correct / max(total, 1)
        train_loss = running_loss / max(total, 1)

        # validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_dl:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_total += labels.size(0)
        val_acc = val_correct / max(val_total, 1)

        mlflow.log_metrics({
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_accuracy": val_acc,
            "epoch": epoch,
        }, step=epoch)

        logger.info("epoch", epoch=epoch, train_loss=round(train_loss, 4), train_acc=round(train_acc, 4), val_acc=round(val_acc, 4))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            # save best
            torch.save(model.state_dict(), str(processed_dir.parent / "best_cnn.pt"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("early_stopping", epoch=epoch)
                break

    mlflow.log_metric("best_val_accuracy", best_val_acc)

    # save label map
    label_map_path = processed_dir.parent / "label_map.json"
    label_map_path.write_text(json.dumps(label_map, indent=2))
    mlflow.log_artifact(str(label_map_path))
    mlflow.pytorch.log_model(model, "model_cnn")

    logger.info("cnn_trained", best_val_accuracy=best_val_acc, architecture=arch)
    return model


# ─── orchestrator ───────────────────────────────────────

def run_training(config_path: str = "ml/configs/train_config.yaml") -> None:
    """Run full training pipeline: baselines + CNN."""
    config = _load_config(config_path)
    processed_dir = Path(config["data"]["processed_dir"])
    splits = _load_splits(processed_dir)

    mlflow_cfg = config.get("mlflow", {})
    mlflow.set_tracking_uri(mlflow_cfg.get("tracking_uri", "http://localhost:5000"))
    mlflow.set_experiment(mlflow_cfg.get("experiment_name", "keramorph"))

    # ── descriptor-based features ──
    logger.info("extracting_features")
    X_train, y_train = _extract_features_for_split(processed_dir, splits["train"], config)
    X_val, y_val = _extract_features_for_split(processed_dir, splits["val"], config)

    # ── baseline k-NN ──
    with mlflow.start_run(run_name="baseline_knn"):
        mlflow.log_param("seed", config.get("seed", 42))
        train_baseline_knn(config, X_train, y_train, X_val, y_val)

    # ── baseline XGBoost ──
    with mlflow.start_run(run_name="baseline_xgb"):
        mlflow.log_param("seed", config.get("seed", 42))
        train_baseline_xgb(config, X_train, y_train, X_val, y_val)

    # ── CNN ──
    with mlflow.start_run(run_name="prod_cnn"):
        mlflow.log_param("seed", config.get("seed", 42))
        train_cnn(config, processed_dir, splits)

    logger.info("training_complete")


if __name__ == "__main__":
    run_training()
