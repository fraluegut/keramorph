import type { PredictMultiResponse } from "./types";

const BASE_URL = "/api";

export async function predictImages(
  files: File[],
  topK: number = 5,
): Promise<PredictMultiResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));

  const res = await fetch(`${BASE_URL}/predict?top_k=${topK}`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Prediction failed (${res.status}): ${text}`);
  }

  return res.json();
}

export async function sendFeedback(payload: {
  image_id: string;
  predicted_label: string;
  correct_label: string;
  notes?: string;
}): Promise<void> {
  await fetch(`${BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${BASE_URL}/healthz`);
  return res.json();
}

export async function getModelMeta(): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE_URL}/model`);
  return res.json();
}
