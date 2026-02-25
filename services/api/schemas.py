"""
Keramorph API – Pydantic response schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    label: str
    probability: float = Field(ge=0, le=1)
    rank: int


class QualityInfo(BaseModel):
    score: float = Field(ge=0, le=1)
    warnings: list[str] = []
    ok: bool


class ModelInfo(BaseModel):
    type: str
    version: str
    path: str


class PredictResponse(BaseModel):
    """Response from POST /predict."""

    predictions: list[Prediction]
    quality: QualityInfo
    artifacts: dict[str, str] = {}  # base64 PNGs
    model_info: ModelInfo
    latency_ms: float


class PredictMultiResponse(BaseModel):
    """Response from POST /predict with multiple images."""

    results: list[PredictResponse]


class FeedbackRequest(BaseModel):
    """User feedback: 'this was actually class X'."""

    image_id: str
    predicted_label: str
    correct_label: str
    notes: str = ""


class FeedbackResponse(BaseModel):
    status: str = "received"
    image_id: str


class HealthResponse(BaseModel):
    status: str
    version: str


class ModelMetaResponse(BaseModel):
    name: str
    type: str
    version: str
    stage: str
    num_classes: int
    labels: list[str]
    dataset_hash: str = ""
    metrics: dict[str, float] = {}
