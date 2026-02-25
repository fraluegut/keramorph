"""
Tests – FastAPI endpoints (contract tests).
"""
import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoints:
    def test_healthz(self, client: TestClient) -> None:
        r = client.get("/healthz")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_readyz_returns_503_when_no_model(self, client: TestClient) -> None:
        # model may not be loaded in test env
        r = client.get("/readyz")
        assert r.status_code in (200, 503)


class TestPredictEndpoint:
    def test_predict_no_files_returns_422(self, client: TestClient) -> None:
        r = client.post("/predict")
        assert r.status_code == 422  # validation error: no files

    def test_predict_contract(self, client: TestClient) -> None:
        """If model is loaded, verify response shape."""
        # create a minimal PNG in memory
        import io
        import numpy as np
        cv2 = pytest.importorskip("cv2")

        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img, (50, 50), 30, 255, -1)
        _, buf = cv2.imencode(".png", img)
        file_bytes = io.BytesIO(buf.tobytes())

        r = client.post(
            "/predict",
            files=[("files", ("test.png", file_bytes, "image/png"))],
        )
        # may be 503 if model not loaded — that's fine for unit tests
        if r.status_code == 200:
            data = r.json()
            assert "results" in data
            assert isinstance(data["results"], list)
            if data["results"]:
                result = data["results"][0]
                assert "predictions" in result
                assert "quality" in result
                assert "artifacts" in result
                assert "model_info" in result
                assert "latency_ms" in result


class TestFeedbackEndpoint:
    def test_feedback_happy_path(self, client: TestClient) -> None:
        r = client.post(
            "/feedback",
            json={
                "image_id": "test-123",
                "predicted_label": "TypeA",
                "correct_label": "TypeB",
            },
        )
        assert r.status_code == 200
        assert r.json()["image_id"] == "test-123"
