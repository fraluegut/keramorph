// ── Types matching the API response schemas ──

export interface Prediction {
  label: string;
  probability: number;
  rank: number;
}

export interface QualityInfo {
  score: number;
  warnings: string[];
  ok: boolean;
}

export interface ModelInfo {
  type: string;
  version: string;
  path: string;
}

export interface PredictResult {
  predictions: Prediction[];
  quality: QualityInfo;
  artifacts: Record<string, string>; // base64 PNGs
  model_info: ModelInfo;
  latency_ms: number;
}

export interface PredictMultiResponse {
  results: PredictResult[];
}

export interface SelectedFile {
  file: File;
  preview: string; // object URL
  id: string;
}
