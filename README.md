# Keramorph

**Sistema ML de clasificación de perfiles cerámicos** — identifica tipos cerámicos a partir de imágenes de silueta/contorno usando Computer Vision clásica + Deep Learning.

> Proyecto desarrollado por **ArqueoBytes**.

---

## Visión general

Sube 1 o varias imágenes de un perfil cerámico y obtén:

- **Top-K predicciones** (p. ej. "Forma X / Tipo Y") con probabilidad/confianza
- **Explicación visual**: overlay del contorno, imagen normalizada, heatmap (CNN)
- **Alertas de calidad**: "imagen mala / perfil incompleto / perspectiva rara"
- **Metadatos**: versión del modelo, fecha, dataset, latencia

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────┐
│   Frontend   │────▶│  FastAPI API  │────▶│  Inference Engine  │
│  React+Vite  │◀────│  /predict     │◀────│  CNN / kNN / XGB   │
│  Tailwind    │     │  /feedback    │     │  contour + feats   │
└─────────────┘     │  /healthz     │     └───────────────────┘
                    │  /model       │              │
                    └──────────────┘              │
                           │               ┌──────▼──────┐
                           │               │   MLflow     │
                           └──────────────▶│   Registry   │
                                           └─────────────┘
```

### 3 capas

| Capa | Tech | Responsabilidad |
|------|------|-----------------|
| **Frontend** | React 18, Vite, Tailwind | Upload, visualización resultados, modo avanzado |
| **Backend** | FastAPI, Pydantic v2 | REST API, validación, logging, tracing |
| **ML/MLOps** | PyTorch, timm, scikit-learn, MLflow, DVC | Pipelines data→train→eval→deploy |

## Enfoque ML (2 etapas)

### Etapa 1 — Normalización del perfil (CV clásica)

- Detección contorno (Canny / threshold / adaptive)
- Limpieza morfológica + suavizado
- Alineación (centro, escala, orientación)
- Extracción de representaciones:
  - Imagen binaria normalizada → para CNN
  - Descriptores de Fourier → para baselines
  - Hu moments + features geométricas → para baselines

### Etapa 2 — Clasificador

| Modelo | Tipo | Features |
|--------|------|----------|
| **k-NN** | Baseline interpretable | Fourier + Hu + geom |
| **XGBoost** | Baseline potente | Fourier + Hu + geom |
| **EfficientNet-B0** | Producción | Imagen normalizada 224×224 |
| **Siamese** (opcional) | Metric learning | Embeddings de similitud |

## Estructura del proyecto

```
keramorph/
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/       # Header, ImageUploader, ResultCard, AdvancedPanel
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   └── types.ts
│   └── package.json
├── services/
│   ├── api/                  # FastAPI (main, schemas, config, observability)
│   └── inference/            # ModelRuntime (carga modelo, predict, artefactos)
├── ml/
│   ├── data/                 # Pipeline datos + DVC
│   ├── features/             # Extracción contorno, descriptores, calidad
│   ├── training/             # Train baselines + CNN
│   ├── evaluation/           # Métricas, confusión, reportes
│   └── configs/              # train_config.yaml
├── tests/                    # pytest (features, API, data pipeline)
├── infra/
│   ├── docker/               # Dockerfile.api, Dockerfile.frontend, Caddyfile
│   └── compose/              # docker-compose.yml (API + MLflow + Postgres + MinIO + Redis)
├── .github/workflows/ci.yml  # GitHub Actions CI/CD
├── Makefile                  # Targets: data, train, eval, docker, deploy, test, lint
├── pyproject.toml
└── .env.example
```

## Quickstart

### Requisitos previos

- Python ≥ 3.10
- Node.js ≥ 20
- Docker + Docker Compose (para stack completo)

### 1. Clonar e instalar

```bash
git clone https://github.com/arqueobytes/keramorph.git
cd keramorph

# Python
python -m venv .venv && source .venv/bin/activate
make install

# Frontend
cd frontend && npm ci && cd ..
```

### 2. Levantar infraestructura local

```bash
cp .env.example .env
make compose-up    # Postgres + MLflow + MinIO + Redis
```

### 3. Preparar datos

Coloca imágenes en `ml/data/raw/<nombre_tipo>/*.png` y ejecuta:

```bash
make data          # procesar + generar splits
```

### 4. Entrenar

```bash
make train         # k-NN + XGBoost + CNN
```

Monitorea en MLflow: http://localhost:5000

### 5. Evaluar

```bash
make eval
```

### 6. Servir

```bash
# En terminales separadas:
make api           # FastAPI en :8000
make front         # Vite dev server en :5173
```

Abre http://localhost:5173 → sube imágenes → identifica.

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/predict` | Clasificar imágenes (multipart/form-data) |
| `POST` | `/feedback` | Corrección del usuario |
| `GET` | `/healthz` | Liveness check |
| `GET` | `/readyz` | Readiness (modelo cargado) |
| `GET` | `/model` | Metadata del modelo |

### Ejemplo `POST /predict`

```bash
curl -X POST http://localhost:8000/predict \
  -F "files=@perfil1.png" \
  -F "files=@perfil2.png"
```

Respuesta:

```json
{
  "results": [
    {
      "predictions": [
        {"label": "Forma_14", "probability": 0.87, "rank": 1},
        {"label": "Forma_7",  "probability": 0.06, "rank": 2}
      ],
      "quality": {"score": 0.95, "warnings": [], "ok": true},
      "artifacts": {
        "overlay_contour": "iVBORw0KGgo...",
        "normalized_input": "iVBORw0KGgo..."
      },
      "model_info": {"type": "cnn", "version": "0.1.0", "path": "models/current"},
      "latency_ms": 42.3
    }
  ]
}
```

## Observabilidad

- **Logs** estructurados (JSON) con `structlog` — `request_id`, `model_version`, `latency_ms`
- **Métricas** p50/p95 latencia, error rate, throughput
- **Trazas** OpenTelemetry (preparado)
- **Data drift** monitor básico: distribución tamaños, brillo, ratio contorno/imagen

## MLOps Pipeline

```
make data → make train → make eval → make package → make docker → make deploy
```

Todo queda registrado en **MLflow**:
- `params`: arquitectura, augmentations, seed
- `metrics`: accuracy, F1 macro, top-k, calibración
- `artifacts`: matriz confusión, ejemplos fallidos, PR curves
- `dataset_version` + `code_version` (commit hash)

## Testing

```bash
make test          # unit tests
make test-cov      # con coverage
make lint          # ruff
make typecheck     # mypy
```

## Despliegue

```bash
make docker        # build imagen API
make docker-front  # build imagen frontend
make deploy        # push + deploy staging
```

**Estrategia**:
- Staging siempre antes de producción
- Rollout canary (manual inicialmente)
- Fallback al modelo anterior si sube error/latencia

## Licencia

MIT

---

*Keramorph v0.1.0 — ArqueoBytes*
