"""
Keramorph – Inference runtime.

Loads a trained model (CNN or baseline) and provides a high-level
``predict()`` that accepts raw images and returns structured predictions
with quality assessment and visual artefacts.
"""
from __future__ import annotations

import base64
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import structlog

from ml.features.extraction import (
    ContourResult,
    QualityReport,
    assess_quality,
    extract_all_descriptors,
    extract_contour,
    normalise_profile,
)

logger = structlog.get_logger(__name__)

__all__ = ["ModelRuntime", "PredictionResult"]


class PredictionResult:
    """Structured prediction output."""

    def __init__(
        self,
        predictions: list[dict[str, Any]],
        quality: dict[str, Any],
        artifacts: dict[str, str],
        model_info: dict[str, str],
        latency_ms: float,
    ) -> None:
        self.predictions = predictions
        self.quality = quality
        self.artifacts = artifacts
        self.model_info = model_info
        self.latency_ms = latency_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "predictions": self.predictions,
            "quality": self.quality,
            "artifacts": self.artifacts,
            "model_info": self.model_info,
            "latency_ms": self.latency_ms,
        }


class ModelRuntime:
    """Manages model loading and inference for all model types."""

    def __init__(
        self,
        model_type: str = "cnn",
        model_path: str | Path = "models/current",
        label_map_path: str | Path | None = None,
        device: str = "cpu",
        confidence_threshold: float = 0.3,
    ) -> None:
        self.model_type = model_type
        self.model_path = Path(model_path)
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.model: Any = None
        self.label_map: dict[str, int] = {}
        self.inv_label_map: dict[int, str] = {}
        self._model_version = "unknown"
        self._loaded = False

    def load(self) -> None:
        """Load model and label map from disk.

        Raises ``FileNotFoundError`` if the label map or the model file is
        missing: a runtime without a trained model must never look ready, or
        it would return meaningless predictions.
        """
        lm_path = (
            self.model_path / "label_map.json"
            if not self.model_path.suffix
            else self.model_path.parent / "label_map.json"
        )
        if not lm_path.exists():
            raise FileNotFoundError(
                f"Label map not found: {lm_path}. Train a model first (make train)."
            )
        self.label_map = json.loads(lm_path.read_text())
        if not self.label_map:
            raise ValueError(f"Label map is empty: {lm_path}")
        self.inv_label_map = {v: k for k, v in self.label_map.items()}

        if self.model_type == "cnn":
            self._load_cnn()
        elif self.model_type in ("knn", "xgboost"):
            self._load_sklearn()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        self._loaded = True
        logger.info("model_loaded", type=self.model_type, path=str(self.model_path))

    def _load_cnn(self) -> None:
        weights_path = self.model_path / "best_cnn.pt" if self.model_path.is_dir() else self.model_path
        if not weights_path.exists():
            # Checked before importing torch: fail fast and never fall back to
            # randomly initialised weights.
            raise FileNotFoundError(
                f"Model weights not found: {weights_path}. Train a model first (make train)."
            )

        import torch
        import timm

        self.model = timm.create_model(
            "efficientnet_b0", pretrained=False, in_chans=1, num_classes=len(self.label_map)
        )
        state = torch.load(str(weights_path), map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
        self.model.eval()
        self.model.to(self.device)

    def _load_sklearn(self) -> None:
        import joblib

        pkl_path = self.model_path / f"model_{self.model_type}.pkl" if self.model_path.is_dir() else self.model_path
        if pkl_path.exists():
            self.model = joblib.load(pkl_path)
        else:
            raise FileNotFoundError(f"Model file not found: {pkl_path}")

    # ── inference ───────────────────────────────────────

    def predict(
        self,
        image_bytes: bytes,
        top_k: int = 5,
    ) -> PredictionResult:
        """Run full inference pipeline on a raw image (bytes).

        Returns structured PredictionResult.
        """
        t0 = time.perf_counter()

        # decode
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return self._error_result("Could not decode image", t0)

        # contour extraction
        cr = extract_contour(img)
        quality = assess_quality(img, cr)

        if cr is None:
            return self._error_result("No contour detected", t0, quality)

        # artefacts
        artifacts = self._build_artifacts(img, cr)

        # prediction
        if self.model_type == "cnn":
            predictions = self._predict_cnn(img, cr, top_k)
        else:
            predictions = self._predict_sklearn(cr, top_k)

        latency = (time.perf_counter() - t0) * 1000
        return PredictionResult(
            predictions=predictions,
            quality={"score": quality.score, "warnings": quality.warnings, "ok": quality.ok},
            artifacts=artifacts,
            model_info={
                "type": self.model_type,
                "version": self._model_version,
                "path": str(self.model_path),
            },
            latency_ms=round(latency, 2),
        )

    def _predict_cnn(
        self, img: np.ndarray, cr: ContourResult, top_k: int
    ) -> list[dict[str, Any]]:
        import torch

        norm_img = normalise_profile(img, cr)
        tensor = torch.from_numpy(norm_img).float().unsqueeze(0).unsqueeze(0) / 255.0
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        return self._probs_to_predictions(probs, top_k)

    def _predict_sklearn(self, cr: ContourResult, top_k: int) -> list[dict[str, Any]]:
        feats = extract_all_descriptors(cr).reshape(1, -1)
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(feats)[0]
            return self._probs_to_predictions(probs, top_k)
        else:
            pred = self.model.predict(feats)[0]
            return [{"label": str(pred), "probability": 1.0, "rank": 1}]

    def _probs_to_predictions(
        self, probs: np.ndarray, top_k: int
    ) -> list[dict[str, Any]]:
        indices = np.argsort(probs)[::-1][:top_k]
        results = []
        for rank, idx in enumerate(indices, 1):
            label = self.inv_label_map.get(int(idx), f"class_{idx}")
            prob = float(probs[idx])
            results.append({"label": label, "probability": round(prob, 4), "rank": rank})
        return results

    def _build_artifacts(
        self, img: np.ndarray, cr: ContourResult
    ) -> dict[str, str]:
        """Generate visual overlay artefacts as base64 PNGs."""
        artifacts: dict[str, str] = {}

        # contour overlay
        overlay = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(overlay, [cr.contour], -1, (0, 255, 0), 2)
        artifacts["overlay_contour"] = self._encode_png(overlay)

        # normalised input
        norm = normalise_profile(img, cr)
        artifacts["normalized_input"] = self._encode_png(norm)

        return artifacts

    @staticmethod
    def _encode_png(img: np.ndarray) -> str:
        _, buf = cv2.imencode(".png", img)
        return base64.b64encode(buf.tobytes()).decode("ascii")

    def _error_result(
        self,
        message: str,
        t0: float,
        quality: QualityReport | None = None,
    ) -> PredictionResult:
        latency = (time.perf_counter() - t0) * 1000
        return PredictionResult(
            predictions=[],
            quality={
                "score": quality.score if quality else 0,
                "warnings": (quality.warnings if quality else []) + [message],
                "ok": False,
            },
            artifacts={},
            model_info={"type": self.model_type, "version": self._model_version, "path": str(self.model_path)},
            latency_ms=round(latency, 2),
        )

    # ── health check ───────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._loaded and self.model is not None
