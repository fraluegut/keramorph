import type { PredictResult } from "../types";
import { AlertTriangle, CheckCircle, Clock, Trophy, TrendingUp, Eye } from "lucide-react";

interface Props {
  result: PredictResult;
  filename: string;
}

export default function ResultCard({ result, filename }: Props) {
  const topPred = result.predictions[0];

  return (
    <div className="glass-card rounded-2xl overflow-hidden hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] animate-float">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-ceramic-50/50 border-b border-white/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-ceramic-500 to-ceramic-600 flex items-center justify-center text-white font-bold text-sm">
              {filename.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 truncate max-w-[200px]">{filename}</h3>
              <p className="text-xs text-slate-500">Análisis completado</p>
            </div>
          </div>
          <div className="flex items-center gap-1 text-xs text-slate-500 bg-white/50 rounded-full px-3 py-1">
            <Clock size={12} />
            <span className="font-medium">{result.latency_ms.toFixed(0)} ms</span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Quality badge */}
        <QualityBadge quality={result.quality} />

        {/* Winner */}
        {topPred && (
          <div className="relative">
            <div className="text-center py-4 bg-gradient-to-br from-ceramic-50 to-ceramic-100 rounded-xl border border-ceramic-200/50">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Trophy className="text-ceramic-600" size={20} />
                <p className="text-xs text-ceramic-700 uppercase tracking-wider font-semibold">Clase ganadora</p>
              </div>
              <p className="text-3xl font-bold bg-gradient-to-r from-ceramic-700 to-ceramic-600 bg-clip-text text-transparent mb-2">
                {topPred.label}
              </p>
              <div className="flex items-center justify-center gap-2">
                <TrendingUp size={16} className="text-ceramic-600" />
                <p className="text-lg font-semibold text-ceramic-700">
                  {(topPred.probability * 100).toFixed(1)}% confianza
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Top-5 bars */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <TrendingUp size={16} />
            Top 5 predicciones
          </h4>
          <div className="space-y-3">
            {result.predictions.map((pred, index) => (
              <div key={pred.rank} className="group">
                <div className="flex items-center gap-3">
                  <div className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold
                    ${index === 0 ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-md' :
                      index === 1 ? 'bg-gradient-to-r from-slate-300 to-slate-400 text-white' :
                      index === 2 ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-white' :
                      'bg-slate-200 text-slate-600'}`}>
                    {pred.rank}
                  </div>
                  <span className="flex-1 text-sm font-medium text-slate-700 truncate">
                    {pred.label}
                  </span>
                  <span className="text-sm font-semibold text-ceramic-600 min-w-[3rem] text-right">
                    {(pred.probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="mt-2 bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ease-out shadow-sm
                      ${index === 0 ? 'bg-gradient-to-r from-ceramic-500 to-ceramic-600' :
                        index === 1 ? 'bg-gradient-to-r from-ceramic-400 to-ceramic-500' :
                        'bg-gradient-to-r from-ceramic-300 to-ceramic-400'}`}
                    style={{
                      width: `${Math.max(pred.probability * 100, 2)}%`,
                      transitionDelay: `${index * 100}ms`
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Visual artifacts */}
        {Object.keys(result.artifacts).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Eye size={16} />
              Visualización del análisis
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Object.entries(result.artifacts).map(([key, b64]) => (
                <div key={key} className="group">
                  <div className="relative rounded-lg overflow-hidden border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                    <img
                      src={`data:image/png;base64,${b64}`}
                      alt={key}
                      className="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1 text-center font-medium capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model info */}
        <div className="pt-4 border-t border-slate-200/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span className="bg-slate-100 rounded-full px-3 py-1">
                <span className="font-medium">Modelo:</span> {result.model_info.type}
              </span>
              <span className="bg-slate-100 rounded-full px-3 py-1">
                <span className="font-medium">Versión:</span> {result.model_info.version}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function QualityBadge({ quality }: { quality: PredictResult["quality"] }) {
  if (quality.ok) {
    return (
      <div className="flex items-center gap-2 text-green-700 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl px-4 py-3 border border-green-200/50 shadow-sm">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-500 text-white">
          <CheckCircle size={16} />
        </div>
        <div>
          <p className="font-semibold text-sm">Calidad excelente</p>
          <p className="text-xs text-green-600">Score: {quality.score.toFixed(2)}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-amber-700 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl px-4 py-3 border border-amber-200/50 shadow-sm">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-500 text-white">
          <AlertTriangle size={16} />
        </div>
        <div>
          <p className="font-semibold text-sm">Alertas de calidad</p>
          <p className="text-xs text-amber-600">Score: {quality.score.toFixed(2)}</p>
        </div>
      </div>
      <div className="space-y-2">
        {quality.warnings.map((w, i) => (
          <div key={i} className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50/50 rounded-lg px-3 py-2">
            <div className="w-1 h-1 rounded-full bg-amber-500 mt-2 flex-shrink-0"></div>
            <span>{w}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
