import { useState, useCallback } from "react";
import { Search, Loader2, AlertTriangle, Sparkles, BookOpen, ExternalLink } from "lucide-react";
import Header from "./components/Header";
import ImageUploader from "./components/ImageUploader";
import ResultCard from "./components/ResultCard";
import AdvancedPanel from "./components/AdvancedPanel";
import { predictImages } from "./api";
import type { SelectedFile, PredictResult } from "./types";

let fileIdCounter = 0;

interface MockInsight {
  probability: number;
  summary: string;
  description: string;
  citation: {
    title: string;
    reference: string;
    link: string;
  };
}

export default function App() {
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [results, setResults] = useState<PredictResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);
  const [modelType, setModelType] = useState("cnn");
  const [demoPiece4, setDemoPiece4] = useState(true);
  const [mockInsight, setMockInsight] = useState<MockInsight | null>(null);

  const addFiles = useCallback((newFiles: File[]) => {
    const additions: SelectedFile[] = newFiles.map((f) => ({
      file: f,
      preview: URL.createObjectURL(f),
      id: `file-${++fileIdCounter}`,
    }));
    setFiles((prev) => [...prev, ...additions]);
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => {
      const removed = prev.find((f) => f.id === id);
      if (removed) URL.revokeObjectURL(removed.preview);
      return prev.filter((f) => f.id !== id);
    });
  }, []);

  const handlePredict = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setMockInsight(null);

    try {
      if (demoPiece4) {
        const probability = 0.93;
        const mockResult: PredictResult = {
          predictions: [
            {
              label: "Pieza 4 · Imitación Terra Sigillata (cerámica vaccea)",
              probability,
              rank: 1,
            },
            {
              label: "Pieza 3 · Perfil sigillata vaccea",
              probability: 0.045,
              rank: 2,
            },
            {
              label: "Pieza 5 · Fragmento Drag. 27",
              probability: 0.025,
              rank: 3,
            },
          ],
          quality: {
            score: 0.96,
            warnings: [],
            ok: true,
          },
          artifacts: {},
          model_info: {
            type: "cnn-vaccea-demo",
            version: "0.1.0-demo",
            path: "mock-piece-4",
          },
          latency_ms: 418,
        };

        setResults([mockResult]);
        setMockInsight({
          probability,
          summary: `El modelo simulado asigna ${(probability * 100).toFixed(1)}% de probabilidad a la pieza 4 descrita en la documentación vaccea de terra sigillata.`,
          description:
            "La geometría coincide con la morfología descrita para la pieza 4 del conjunto de Montealegre de Campos, identificada como cerámica de imitación de terra sigillata en contextos vacceos.",
          citation: {
            title:
              "Imitaciones de Terra Sigillata en cerámica vaccea. Un conjunto procedente de Montealegre de Campos (Valladolid)",
            reference: "As produções cerâmicas da imitação na Hispania. Oporto, 2013.",
            link: "https://www.researchgate.net/publication/321263932_Imitaciones_de_Terra_Sigillata_en_ceramica_vaccea_Un_conjunto_procedente_de_Montealegre_de_Campos_Valladolid",
          },
        });
        return;
      }

      const response = await predictImages(
        files.map((sf) => sf.file),
        topK,
      );
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-white to-ceramic-50/30">
      <Header />

      <main className="flex-1 mx-auto w-full max-w-7xl px-6 py-12 space-y-12">
        {/* Hero Section */}
        <section className="text-center space-y-6">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-slate-800 via-ceramic-700 to-slate-800 bg-clip-text text-transparent">
              Clasificación Inteligente de Perfiles Cerámicos
            </h1>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Utiliza inteligencia artificial avanzada para identificar automáticamente tipos cerámicos
              a partir de imágenes de perfiles. Tecnología de vanguardia para arqueología y investigación.
            </p>
          </div>

          <div className="flex items-center justify-center gap-8 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-ceramic-500"></div>
              <span>IA Avanzada</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-ceramic-500"></div>
              <span>Procesamiento Rápido</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-ceramic-500"></div>
              <span>Análisis Visual</span>
            </div>
          </div>
        </section>

        {/* Upload Section */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-slate-800">Sube tus imágenes</h2>
            <p className="text-slate-600">Selecciona imágenes de perfiles cerámicos para análisis automático</p>
          </div>
          <ImageUploader
            files={files}
            onAdd={addFiles}
            onRemove={removeFile}
            disabled={loading}
          />
          <div className="flex flex-col items-center gap-3 text-sm text-slate-600">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-ceramic-700">Modo demo · Pieza 4 (Vaccea)</span>
              <button
                type="button"
                onClick={() => setDemoPiece4((prev) => !prev)}
                className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors ${demoPiece4 ? "bg-ceramic-500" : "bg-slate-300"}`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform shadow ${demoPiece4 ? "translate-x-7" : "translate-x-1"}`}
                />
              </button>
              <span className="text-xs text-slate-500">{demoPiece4 ? "Activo" : "Inactivo"}</span>
            </div>
            <p className="text-xs text-slate-500 text-center max-w-2xl">
              Activa este modo para mockear la identificación de la pieza 4 de terra sigillata vaccea mientras el servicio real se despliega.
            </p>
          </div>
        </section>

        {/* Identify Button */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handlePredict}
            disabled={files.length === 0 || loading}
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-r from-ceramic-600 to-ceramic-700
              text-white py-4 px-12 font-semibold text-lg transition-all duration-300
              hover:from-ceramic-700 hover:to-ceramic-800 hover:shadow-xl hover:shadow-ceramic-500/25
              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
              transform hover:scale-105 active:scale-95"
          >
            <div className="relative flex items-center justify-center gap-3">
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  <span>Analizando imágenes...</span>
                </>
              ) : (
                <>
                  <Search size={24} />
                  <span>Iniciar Análisis</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent
                    -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                </>
              )}
            </div>
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="max-w-2xl mx-auto">
            <div className="glass-card rounded-2xl border-red-200/50 bg-gradient-to-r from-red-50 to-pink-50 p-6">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                  <AlertTriangle size={16} className="text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-red-800 mb-1">Error en el análisis</h3>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <section className="space-y-8">
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-bold text-slate-800">Resultados del Análisis</h2>
              <p className="text-slate-600">Clasificación inteligente completada con éxito</p>
            </div>
            <div className="grid gap-8 md:grid-cols-2">
              {results.map((r, i) => (
                <ResultCard
                  key={i}
                  result={r}
                  filename={files[i]?.file.name ?? `imagen_${i + 1}`}
                />
              ))}
            </div>
          </section>
        )}

        {mockInsight && (
          <section className="glass-card rounded-2xl border border-ceramic-200/60 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <Sparkles className="text-ceramic-500" size={28} />
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-ceramic-500">Demo arqueológica</p>
                <h3 className="text-xl font-semibold text-slate-800">Identificación simulada de la pieza 4</h3>
              </div>
            </div>
            <p className="text-slate-700 text-lg font-medium">{mockInsight.summary}</p>
            <div className="rounded-2xl bg-slate-50 border border-slate-200 p-5 space-y-3">
              <p className="text-sm text-slate-600">{mockInsight.description}</p>
              <a
                href={mockInsight.citation.link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm font-semibold text-ceramic-600 hover:text-ceramic-700"
              >
                <BookOpen size={16} />
                <span>
                  {mockInsight.citation.title} · {mockInsight.citation.reference}
                </span>
                <ExternalLink size={14} />
              </a>
            </div>
            <p className="text-xs text-slate-400">* Resultado simulado para demostrar el flujo completo mientras el modelo real se entrena.</p>
          </section>
        )}

        {/* Advanced */}
        <AdvancedPanel
          results={results}
          topK={topK}
          onTopKChange={setTopK}
          modelType={modelType}
          onModelTypeChange={setModelType}
        />
      </main>

      {/* Footer */}
      <footer className="glass-card mt-16 border-t border-white/20">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="flex items-center justify-center gap-6 text-sm text-slate-600">
            <span className="font-medium">Keramorph v0.1.0</span>
            <div className="w-1 h-1 rounded-full bg-slate-300"></div>
            <span>Desarrollado por ArqueoBytes</span>
            <div className="w-1 h-1 rounded-full bg-slate-300"></div>
            <span>{new Date().getFullYear()}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
