"""
Tests – Data pipeline.
"""
import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from ml.data.pipeline import build_dataset, compute_dataset_hash, generate_splits


@pytest.fixture
def fake_raw_dir(tmp_path: Path) -> Path:
    """Create a tiny fake raw dataset."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    if raw_dir.exists():
        import shutil
        shutil.rmtree(raw_dir)
    if processed_dir.exists():
        import shutil
        shutil.rmtree(processed_dir)
    
    for cls in ["TypeA", "TypeB"]:
        cls_dir = raw_dir / cls
        cls_dir.mkdir(parents=True)
        for i in range(6):
            img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
            cv2.imwrite(str(cls_dir / f"sample_{i}.png"), img)
    return raw_dir


class TestBuildDataset:
    def test_creates_processed_dir(self, fake_raw_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "processed"
        card = build_dataset(fake_raw_dir, out, target_size=(64, 64))
        assert out.exists()
        assert card.num_classes == 2
        assert card.num_samples == 12
        assert (out / "dataset_card.json").exists()

    def test_images_are_resized(self, fake_raw_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "processed"
        build_dataset(fake_raw_dir, out, target_size=(64, 64))
        sample = next((out / "TypeA").glob("*.png"))
        img = cv2.imread(str(sample), cv2.IMREAD_GRAYSCALE)
        assert img.shape == (64, 64)


class TestGenerateSplits:
    def test_split_counts(self, fake_raw_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "processed"
        build_dataset(fake_raw_dir, out, target_size=(64, 64))
        splits = generate_splits(out, val_ratio=0.2, test_ratio=0.2)
        total = len(splits["train"]) + len(splits["val"]) + len(splits["test"])
        assert total == 12

    def test_splits_json_written(self, fake_raw_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "processed"
        build_dataset(fake_raw_dir, out)
        generate_splits(out)
        assert (out / "splits.json").exists()


class TestDatasetHash:
    def test_deterministic(self, fake_raw_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "processed"
        build_dataset(fake_raw_dir, out)
        h1 = compute_dataset_hash(out)
        h2 = compute_dataset_hash(out)
        assert h1 == h2
