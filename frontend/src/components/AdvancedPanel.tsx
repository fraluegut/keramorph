import { useState } from "react";
import { ChevronDown, ChevronUp, Download, Settings, Cpu, BarChart3 } from "lucide-react";
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
    a.download = `keramorph_results_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-slate-700 hover:bg-white/50 transition-all duration-200 group"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-ceramic-100 flex items-center justify-center group-hover:bg-ceramic-200 transition-colors">
            <Settings size={16} className="text-ceramic-600" />
          </div>
          <span className="font-semibold">Configuración Avanzada</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">Opciones de análisis</span>
          {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 space-y-6 border-t border-white/20 pt-6">
          {/* Model selector */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Cpu size={16} />
              Modelo de IA
            </label>
            <select
              value={modelType}
              onChange={(e) => onModelTypeChange(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white/50 focus:border-ceramic-400 focus:ring-2 focus:ring-ceramic-400/20 transition-all"
            >
              <option value="cnn">🧠 CNN (Red Neuronal Convolucional) - Producción</option>
              <option value="knn">📊 k-NN (Vecinos más Cercanos) - Baseline</option>
              <option value="xgboost">🌳 XGBoost (Gradient Boosting) - Baseline</option>
            </select>
          </div>

          {/* Top-K */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <BarChart3 size={16} />
              Número de predicciones (Top-K)
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min={1}
                max={10}
                value={topK}
                onChange={(e) => onTopKChange(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>1</span>
                <span className="font-semibold text-ceramic-600 bg-ceramic-100 px-3 py-1 rounded-full">
                  Top {topK} predicciones
                </span>
                <span>10</span>
              </div>
            </div>
          </div>

          {/* Export */}
          {results.length > 0 && (
            <div className="pt-4 border-t border-slate-200/50">
              <button
                type="button"
                onClick={exportJSON}
                className="flex items-center gap-3 w-full px-4 py-3 rounded-xl bg-gradient-to-r from-ceramic-50 to-ceramic-100 hover:from-ceramic-100 hover:to-ceramic-200 text-ceramic-700 font-semibold transition-all duration-200 hover:shadow-md group"
              >
                <Download size={18} className="group-hover:scale-110 transition-transform" />
                <span>Exportar Resultados (JSON)</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
