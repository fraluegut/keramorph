"""
Keramorph API – FastAPI application.

Endpoints:
  POST /predict         — classify one or more ceramic profile images
  POST /feedback        — user correction for future training data
  GET  /healthz         — liveness
  GET  /readyz          — readiness (model loaded?)
  GET  /model           — model metadata
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.api.config import settings
from services.api.observability import setup_logging, setup_tracing
from services.api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    ModelMetaResponse,
    Prediction,
    PredictMultiResponse,
    PredictResponse,
    QualityInfo,
    ModelInfo,
)
from services.inference.runtime import ModelRuntime

logger = structlog.get_logger(__name__)

# ── global runtime ──────────────────────────────────────
_runtime: ModelRuntime | None = None

__version__ = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown hooks."""
    global _runtime
    setup_logging(settings.log_level)
    setup_tracing()

    logger.info("starting", env=settings.app_env, model_type=settings.model_type)

    _runtime = ModelRuntime(
        model_type=settings.model_type,
        model_path=settings.model_path,
        device="cpu",
        confidence_threshold=settings.confidence_threshold,
    )
    try:
        _runtime.load()
    except Exception as exc:
        logger.error("model_load_failed", error=str(exc))
        # The API still starts, but /readyz and /predict answer 503 until a model exists.

    yield  # app running

    logger.info("shutting_down")


# ── app ─────────────────────────────────────────────────
app = FastAPI(
    title="Keramorph API",
    description="Ceramic profile classification service",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── routes ──────────────────────────────────────────────

@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.get("/readyz", response_model=HealthResponse, tags=["ops"])
async def readyz() -> HealthResponse:
    if _runtime is None or not _runtime.is_ready:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return HealthResponse(status="ready", version=__version__)


@app.get("/model", response_model=ModelMetaResponse, tags=["ops"])
async def model_meta() -> ModelMetaResponse:
    if _runtime is None:
        raise HTTPException(503, "Runtime not initialised")
    return ModelMetaResponse(
        name=settings.model_name,
        type=_runtime.model_type,
        version=_runtime._model_version,
        stage=settings.model_stage,
        num_classes=len(_runtime.label_map),
        labels=list(_runtime.label_map.keys()),
    )


@app.post("/predict", response_model=PredictMultiResponse, tags=["inference"])
async def predict(
    files: list[UploadFile] = File(..., description="One or more ceramic profile images"),
    top_k: int = 5,
    model_type: str | None = None,
) -> PredictMultiResponse:
    """Classify ceramic profile image(s).

    Accepts multipart/form-data with one or more image files.
    """
    if _runtime is None or not _runtime.is_ready:
        raise HTTPException(503, "Model not ready")

    results: list[PredictResponse] = []
    for upload in files:
        request_id = str(uuid.uuid4())[:8]
        image_bytes = await upload.read()

        t0 = time.perf_counter()
        result = _runtime.predict(image_bytes, top_k=top_k)
        latency = (time.perf_counter() - t0) * 1000

        logger.info(
            "prediction",
            request_id=request_id,
            filename=upload.filename,
            top_label=result.predictions[0]["label"] if result.predictions else "none",
            latency_ms=round(latency, 2),
            model_version=_runtime._model_version,
        )

        results.append(
            PredictResponse(
                predictions=[Prediction(**p) for p in result.predictions],
                quality=QualityInfo(**result.quality),
                artifacts=result.artifacts,
                model_info=ModelInfo(**result.model_info),
                latency_ms=result.latency_ms,
            )
        )

    return PredictMultiResponse(results=results)


@app.post("/feedback", response_model=FeedbackResponse, tags=["feedback"])
async def feedback(body: FeedbackRequest) -> FeedbackResponse:
    """Record user correction for future training data."""
    logger.info(
        "feedback_received",
        image_id=body.image_id,
        predicted=body.predicted_label,
        correct=body.correct_label,
    )
    # TODO: persist to database / file for retraining pipeline
    return FeedbackResponse(image_id=body.image_id)
