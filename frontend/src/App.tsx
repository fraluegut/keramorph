import { useState, useCallback } from "react";
import { Search, Loader2 } from "lucide-react";
import Header from "./components/Header";
import ImageUploader from "./components/ImageUploader";
import ResultCard from "./components/ResultCard";
import AdvancedPanel from "./components/AdvancedPanel";
import { predictImages } from "./api";
import type { SelectedFile, PredictResult } from "./types";

let fileIdCounter = 0;

export default function App() {
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [results, setResults] = useState<PredictResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);
  const [modelType, setModelType] = useState("cnn");

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

    try {
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
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto w-full max-w-4xl px-4 py-8 space-y-6">
        {/* Upload Section */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">1. Sube imágenes de perfiles cerámicos</h2>
          <ImageUploader
            files={files}
            onAdd={addFiles}
            onRemove={removeFile}
            disabled={loading}
          />
        </section>

        {/* Identify Button */}
        <button
          type="button"
          onClick={handlePredict}
          disabled={files.length === 0 || loading}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-ceramic-600
            text-white py-3 px-6 font-medium text-sm transition-colors
            hover:bg-ceramic-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Identificando…
            </>
          ) : (
            <>
              <Search size={18} />
              Identificar
            </>
          )}
        </button>

        {/* Error */}
        {error && (
          <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">
            {error}
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <section className="space-y-4">
            <h2 className="text-xl font-semibold">2. Resultados</h2>
            <div className="grid gap-4 md:grid-cols-2">
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
      <footer className="border-t border-ceramic-200 bg-white py-4 text-center text-xs text-gray-400">
        Keramorph v0.1.0 · ArqueoBytes · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
