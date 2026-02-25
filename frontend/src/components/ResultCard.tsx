import type { PredictResult } from "../types";
import { AlertTriangle, CheckCircle, Clock } from "lucide-react";

interface Props {
  result: PredictResult;
  filename: string;
}

export default function ResultCard({ result, filename }: Props) {
  const topPred = result.predictions[0];

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
        <span className="text-sm font-medium truncate max-w-[200px]">{filename}</span>
        <span className="flex items-center gap-1 text-xs text-gray-400">
          <Clock size={12} />
          {result.latency_ms.toFixed(0)} ms
        </span>
      </div>

      <div className="p-4 space-y-4">
        {/* Quality badge */}
        <QualityBadge quality={result.quality} />

        {/* Winner */}
        {topPred && (
          <div className="text-center py-2">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Clase ganadora</p>
            <p className="text-2xl font-bold text-ceramic-700 mt-1">{topPred.label}</p>
            <p className="text-sm text-gray-500">
              {(topPred.probability * 100).toFixed(1)}% confianza
            </p>
          </div>
        )}

        {/* Top-5 bars */}
        <div className="space-y-2">
          {result.predictions.map((pred) => (
            <div key={pred.rank} className="flex items-center gap-2">
              <span className="w-28 text-xs text-gray-600 truncate text-right">
                {pred.label}
              </span>
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                <div
                  className="bg-ceramic-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(pred.probability * 100, 1)}%` }}
                />
              </div>
              <span className="w-12 text-xs text-gray-500 text-right">
                {(pred.probability * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>

        {/* Visual artifacts */}
        {Object.keys(result.artifacts).length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Visualización</p>
            <div className="flex gap-3 overflow-x-auto">
              {Object.entries(result.artifacts).map(([key, b64]) => (
                <div key={key} className="flex-shrink-0">
                  <img
                    src={`data:image/png;base64,${b64}`}
                    alt={key}
                    className="h-32 rounded border border-gray-200"
                  />
                  <p className="text-[10px] text-gray-400 mt-1 text-center">{key}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model info */}
        <div className="text-[10px] text-gray-400 pt-2 border-t border-gray-100 flex gap-4">
          <span>modelo: {result.model_info.type}</span>
          <span>versión: {result.model_info.version}</span>
        </div>
      </div>
    </div>
  );
}

function QualityBadge({ quality }: { quality: PredictResult["quality"] }) {
  if (quality.ok) {
    return (
      <div className="flex items-center gap-1.5 text-green-600 bg-green-50 rounded-lg px-3 py-1.5 text-xs">
        <CheckCircle size={14} />
        Calidad OK (score: {quality.score.toFixed(2)})
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 text-amber-600 bg-amber-50 rounded-lg px-3 py-1.5 text-xs">
        <AlertTriangle size={14} />
        Alertas de calidad (score: {quality.score.toFixed(2)})
      </div>
      {quality.warnings.map((w, i) => (
        <p key={i} className="text-[11px] text-amber-700 pl-2">
          • {w}
        </p>
      ))}
    </div>
  );
}
