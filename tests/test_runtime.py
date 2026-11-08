"""
Tests - the inference runtime must refuse to run without a trained model.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.api import main as api_main
from services.inference.runtime import ModelRuntime


class TestRuntimeWithoutModel:
    @pytest.mark.parametrize("model_type", ["cnn", "knn", "xgboost"])
    def test_load_fails_without_label_map(self, tmp_path: Path, model_type: str) -> None:
        runtime = ModelRuntime(model_type=model_type, model_path=tmp_path)
        with pytest.raises(FileNotFoundError, match="Label map"):
            runtime.load()
        assert not runtime.is_ready

    def test_load_fails_with_empty_label_map(self, tmp_path: Path) -> None:
        (tmp_path / "label_map.json").write_text("{}")
        runtime = ModelRuntime(model_type="cnn", model_path=tmp_path)
        with pytest.raises(ValueError, match="empty"):
            runtime.load()
        assert not runtime.is_ready

    def test_cnn_without_weights_never_uses_random_weights(self, tmp_path: Path) -> None:
        (tmp_path / "label_map.json").write_text(json.dumps({"A": 0, "B": 1}))
        runtime = ModelRuntime(model_type="cnn", model_path=tmp_path)
        with pytest.raises(FileNotFoundError, match="weights"):
            runtime.load()
        assert not runtime.is_ready
        assert runtime.model is None

    def test_sklearn_without_model_file_fails(self, tmp_path: Path) -> None:
        (tmp_path / "label_map.json").write_text(json.dumps({"A": 0, "B": 1}))
        runtime = ModelRuntime(model_type="knn", model_path=tmp_path)
        with pytest.raises(FileNotFoundError, match="Model file"):
            runtime.load()
        assert not runtime.is_ready


class TestApiWithoutModel:
    def test_not_ready_and_predict_unavailable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            api_main, "_runtime", ModelRuntime(model_type="cnn", model_path=tmp_path)
        )
        client = TestClient(api_main.app)
        assert client.get("/readyz").status_code == 503
        r = client.post("/predict", files=[("files", ("x.png", b"not an image", "image/png"))])
        assert r.status_code == 503
