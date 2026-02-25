# Arquitectura — Keramorph

## Diagrama de capas

```
                    ┌──────────────────────────────┐
                    │         FRONTEND              │
                    │   React 18 + Vite + Tailwind  │
                    │   Drag&drop upload            │
                    │   Result cards + overlays     │
                    │   Advanced mode panel         │
                    └─────────────┬────────────────┘
                                  │ multipart/form-data
                                  ▼
                    ┌──────────────────────────────┐
                    │          BACKEND              │
                    │   FastAPI + Pydantic v2       │
                    │                               │
                    │   POST /predict               │
                    │   POST /feedback              │
                    │   GET  /healthz, /readyz      │
                    │   GET  /model                 │
                    │                               │
                    │   Structured logging (JSON)   │
                    │   OpenTelemetry tracing       │
                    └─────────────┬────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │      INFERENCE ENGINE         │
                    │                               │
                    │   1. Decode image             │
                    │   2. Extract contour          │
                    │   3. Assess quality           │
                    │   4. Normalise profile        │
                    │   5. Run model (CNN/kNN/XGB)  │
                    │   6. Build artifacts (b64)    │
                    │   7. Return structured result │
                    └─────────────┬────────────────┘
                                  │
                    ┌─────────────▼────────────────┐
                    │        MLOPS PLATFORM         │
                    │                               │
                    │   MLflow Tracking + Registry  │
                    │   DVC (data versioning)       │
                    │   PostgreSQL (MLflow backend) │
                    │   MinIO (S3 artifacts)        │
                    │   GitHub Actions (CI/CD)      │
                    └──────────────────────────────┘
```

## Flujo de datos en inferencia

1. Usuario sube imagen(es) png/jpg vía drag&drop en el frontend
2. Frontend envía `POST /predict` con `multipart/form-data`
3. API decodifica imagen → escala de grises
4. **Contour extraction**: Canny/threshold + morphology cleanup
5. **Quality assessment**: tamaño, contraste, fill ratio, aspect ratio
6. **Normalisation**: crop → center → scale → 224×224 binary
7. **Model predict**: top-K clases con probabilidad
8. **Artifacts**: overlay contour (verde), imagen normalizada → base64 PNG
9. Respuesta JSON estructurada → frontend renderiza cards con barras de confianza

## Flujo MLOps

```
raw data  →  make data   →  processed + splits
                              ↓
                          make train   →  MLflow run (params + metrics + artifacts)
                              ↓
                          make eval    →  confusion matrix, F1, top-k accuracy
                              ↓
                          make package →  model weights + label map + config
                              ↓
                          make docker  →  container image
                              ↓
                          make deploy  →  staging → canary → production
```
