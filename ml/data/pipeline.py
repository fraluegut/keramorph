"""
Keramorph – Data pipeline.

Downloads / converts raw images and generates normalised variants.
• DVC-tracked raw data is expected in ml/data/raw/<class_name>/*.{png,jpg}
• This module writes processed / normalised images for training.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import structlog
from sklearn.model_selection import train_test_split

logger = structlog.get_logger(__name__)

# ── public API ──────────────────────────────────────────

__all__ = [
    "build_dataset",
    "generate_splits",
    "compute_dataset_hash",
    "DatasetCard",
]


class DatasetCard:
    """Lightweight metadata about a dataset version."""

    def __init__(
        self,
        *,
        name: str,
        version: str,
        num_classes: int,
        num_samples: int,
        class_counts: dict[str, int],
        hash: str,
        notes: str = "",
    ) -> None:
        self.name = name
        self.version = version
        self.num_classes = num_classes
        self.num_samples = num_samples
        self.class_counts = class_counts
        self.hash = hash
        self.notes = notes

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "DatasetCard":
        return cls(**json.loads(path.read_text()))


def build_dataset(
    raw_dir: str | Path,
    processed_dir: str | Path,
    target_size: tuple[int, int] = (224, 224),
) -> DatasetCard:
    """Read raw images, clean & resize, write to *processed_dir*."""
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    if processed_dir.exists():
        shutil.rmtree(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    class_counts: dict[str, int] = {}
    total = 0

    for class_dir in sorted(raw_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        label = class_dir.name
        out_dir = processed_dir / label
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        for img_path in sorted(class_dir.glob("*")):
            if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}:
                continue
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.warning("skipping_unreadable", path=str(img_path))
                continue

            img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            out_path = out_dir / f"{img_path.stem}.png"
            cv2.imwrite(str(out_path), img)
            count += 1
            total += 1

        class_counts[label] = count
        logger.info("processed_class", label=label, count=count)

    ds_hash = compute_dataset_hash(processed_dir)
    card = DatasetCard(
        name="keramorph",
        version="0.1.0",
        num_classes=len(class_counts),
        num_samples=total,
        class_counts=class_counts,
        hash=ds_hash,
    )
    card.save(processed_dir / "dataset_card.json")
    logger.info("dataset_built", total=total, classes=len(class_counts), hash=ds_hash)
    return card


def generate_splits(
    processed_dir: str | Path,
    output_dir: str | Path | None = None,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    """Create reproducible train / val / test splits, STRATIFIED by class.

    Returns dict with keys 'train', 'val', 'test'. Each value is a list of
    dicts: ``{"path": "rel/path.png", "label": "ClassA"}``.
    Also writes ``splits.json`` to *output_dir* (defaults to *processed_dir*).
    """
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir) if output_dir else processed_dir

    paths: list[str] = []
    labels: list[str] = []

    for class_dir in sorted(processed_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        for img_path in sorted(class_dir.glob("*.png")):
            paths.append(str(img_path.relative_to(processed_dir)))
            labels.append(class_dir.name)

    # stratified split
    X_train, X_temp, y_train, y_temp = train_test_split(
        paths, labels, test_size=val_ratio + test_ratio, stratify=labels, random_state=seed
    )
    relative_test = test_ratio / (val_ratio + test_ratio)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=relative_test, stratify=y_temp, random_state=seed
    )

    def _to_records(xs: list[str], ys: list[str]) -> list[dict[str, Any]]:
        return [{"path": x, "label": y} for x, y in zip(xs, ys)]

    splits = {
        "train": _to_records(X_train, y_train),
        "val": _to_records(X_val, y_val),
        "test": _to_records(X_test, y_test),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "splits.json").write_text(json.dumps(splits, indent=2))
    logger.info(
        "splits_generated",
        train=len(splits["train"]),
        val=len(splits["val"]),
        test=len(splits["test"]),
    )
    return splits


def compute_dataset_hash(data_dir: str | Path) -> str:
    """SHA-256 over sorted file paths + contents."""
    h = hashlib.sha256()
    for p in sorted(Path(data_dir).rglob("*")):
        if p.is_file() and p.suffix in {".png", ".jpg", ".jpeg"}:
            h.update(str(p).encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]
