# Keramorph

**Machine-learning classification of archaeological ceramic profiles.**

Keramorph identifies ceramic types from profile (silhouette/contour) drawings by combining classical computer vision with deep learning. Upload one or several profile images and get ranked predictions, a visual explanation and image-quality warnings.

Built by [Javier Luengo](https://javierluengo.es) for **ArqueoBytes**.

> **Status: v0.1.0, early scaffold.** The pipeline code exists (contour extraction, shape descriptors, training and evaluation scripts, API, frontend), but **there is no dataset and no trained model in this repository**.
> - Until you train a model, the API starts but `/readyz` and `/predict` answer **503**. It never falls back to untrained weights.
> - The **demo mode of the frontend is mock data**: a fixed, hand-written result for one sample piece. It is not a real prediction.

---

## What it does (once a model is trained)

- **Top-K predictions** (e.g. *Form 14 / Type X*) with probabilities.
- **Visual explanation**: contour overlay and normalised input image.
- **Quality alerts**: image too small, low contrast, no contour found, contour too small or filling the whole image, extreme aspect ratio.
- **Metadata**: model type, model version and latency.

## Architecture

```
┌────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Frontend  │────▶│ FastAPI API │────▶│ Inference engine │
│ React+Vite │◀────│  /predict   │◀────│ CNN / kNN / XGB  │
│  Tailwind  │     │  /feedback  │     │ contour+features │
└────────────┘     │  /healthz   │     └──────────────────┘
                   │  /model     │              │
                   └─────────────┘       ┌──────▼──────┐
                          └─────────────▶│   MLflow    │
                                         │  registry   │
                                         └─────────────┘
```

| Layer | Tech | Responsibility |
|---|---|---|
| Frontend | React 18, Vite, Tailwind | Upload, results, advanced mode |
| Backend | FastAPI, Pydantic v2 | REST API, validation, logging |
| ML / MLOps | PyTorch, timm, scikit-learn, MLflow, DVC | data → train → evaluate → deploy |

## Two-stage ML approach

**Stage 1 — profile normalisation (classical CV)**

- Contour detection (Canny / threshold / adaptive)
- Morphological clean-up and smoothing
- Alignment of centre, scale and orientation
- Representations: normalised binary image (for the CNN), Fourier descriptors, Hu moments and geometric features (for baselines)

**Stage 2 — classifier**

| Model | Role | Input |
|---|---|---|
| k-NN | Interpretable baseline | Fourier + Hu + geometry |
| XGBoost | Strong baseline | Fourier + Hu + geometry |
| EfficientNet-B0 | Production model | Normalised 224×224 image |
| Siamese network | Planned, not implemented | Similarity embeddings |

## Project structure

```
keramorph/
├── frontend/            # React + Vite + Tailwind
├── services/
│   ├── api/             # FastAPI (main, schemas, config, observability)
│   └── inference/       # Model runtime
├── ml/
│   ├── data/            # Data pipeline + DVC
│   ├── features/        # Contours, descriptors, quality checks
│   ├── training/        # Baselines and CNN
│   ├── evaluation/      # Metrics, confusion matrices, reports
│   └── configs/         # train_config.yaml
├── tests/               # pytest
├── infra/               # Dockerfiles and Compose (API, MLflow, Postgres, MinIO, Redis)
├── docs/                # Architecture notes
├── .github/workflows/   # CI
├── Makefile
└── pyproject.toml
```

## Quickstart

Requirements: Python ≥ 3.10, Node.js ≥ 20, Docker + Compose (for the full stack).

```bash
git clone https://github.com/fraluegut/keramorph.git
cd keramorph

python -m venv .venv && source .venv/bin/activate
make install
cd frontend && npm ci && cd ..

cp .env.example .env
make compose-up      # Postgres, MLflow, MinIO, Redis
```

You must provide the data: put your own labelled profile images in `ml/data/raw/<type_name>/*.png` (one folder per type), then:

```bash
make data            # process and split
make train           # k-NN + XGBoost + CNN
make eval
make api             # FastAPI on :8000
make front           # Vite dev server on :5173
```

MLflow runs at http://localhost:5000 and the app at http://localhost:5173.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/predict` | Classify images (multipart/form-data) |
| `POST` | `/feedback` | Submit a user correction (currently only logged, not stored) |
| `GET` | `/healthz` | Liveness |
| `GET` | `/readyz` | Readiness (200 only when a model is loaded, otherwise 503) |
| `GET` | `/model` | Model metadata |

```bash
curl -X POST http://localhost:8000/predict \
  -F "files=@profile1.png" -F "files=@profile2.png"
```

```json
{
  "results": [{
    "predictions": [
      {"label": "Form_14", "probability": 0.87, "rank": 1},
      {"label": "Form_7",  "probability": 0.06, "rank": 2}
    ],
    "quality": {"score": 0.95, "warnings": [], "ok": true},
    "artifacts": {"overlay_contour": "<base64>", "normalized_input": "<base64>"},
    "model_info": {"type": "cnn", "version": "0.1.0"},
    "latency_ms": 42.3
  }]
}
```

## MLOps and quality

- Structured JSON logs (`structlog`) with request ID, model version and latency.
- Training and evaluation runs are tracked in MLflow: parameters, validation and test metrics (accuracy, top-k), the logged models and a text confusion matrix. A dataset hash is computed by the data pipeline but not yet logged to MLflow.
- DVC is configured (MinIO remote for local development) but no data is tracked yet. CI runs on GitHub Actions.
- Tests and checks: `make test`, `make test-cov`, `make lint` (ruff), `make typecheck` (mypy).

## License

MIT
