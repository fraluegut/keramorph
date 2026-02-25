import { useState } from "react";
import { ChevronDown, ChevronUp, Download } from "lucide-react";
import type { PredictResult } from "../types";

interface Props {
  results: PredictResult[];
  topK: number;
  onTopKChange: (k: number) => void;
  modelType: string;
  onModelTypeChange: (t: string) => void;
}

export default function AdvancedPanel({
  results,
  topK,
  onTopKChange,
  modelType,
  onModelTypeChange,
}: Props) {
  const [open, setOpen] = useState(false);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "keramorph_results.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        Modo avanzado
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100 pt-3">
          {/* Model selector */}
          <div className="flex items-center gap-4">
            <label className="text-xs text-gray-500">Modelo:</label>
            <select
              value={modelType}
              onChange={(e) => onModelTypeChange(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-2 py-1"
            >
              <option value="cnn">CNN (prod)</option>
              <option value="knn">k-NN (baseline)</option>
              <option value="xgboost">XGBoost (baseline)</option>
            </select>
          </div>

          {/* Top-K */}
          <div className="flex items-center gap-4">
            <label className="text-xs text-gray-500">Top-K:</label>
            <input
              type="range"
              min={1}
              max={10}
              value={topK}
              onChange={(e) => onTopKChange(Number(e.target.value))}
              className="w-32"
            />
            <span className="text-sm text-gray-700">{topK}</span>
          </div>

          {/* Export */}
          {results.length > 0 && (
            <button
              type="button"
              onClick={exportJSON}
              className="flex items-center gap-2 text-sm text-ceramic-600 hover:text-ceramic-800 transition-colors"
            >
              <Download size={14} />
              Exportar JSON
            </button>
          )}
        </div>
      )}
    </div>
  );
}
