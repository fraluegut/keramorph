import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, Image as ImageIcon, Sparkles } from "lucide-react";
import type { SelectedFile } from "../types";

interface Props {
  files: SelectedFile[];
  onAdd: (files: File[]) => void;
  onRemove: (id: string) => void;
  disabled?: boolean;
}

export default function ImageUploader({ files, onAdd, onRemove, disabled }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (!disabled) onAdd(accepted);
    },
    [onAdd, disabled],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/png": [], "image/jpeg": [] },
    disabled,
    multiple: true,
  });

  return (
    <div className="space-y-6">
      {/* Dropzone */}
      <div className="relative">
        <div
          {...getRootProps()}
          className={`gradient-border rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 group
            ${isDragActive
              ? "bg-gradient-to-br from-ceramic-50 to-ceramic-100 ceramic-glow"
              : "bg-white/50 hover:bg-white/70"
            }
            ${disabled ? "opacity-50 cursor-not-allowed" : "hover:shadow-xl hover:scale-[1.02]"}
          `}
        >
          <input {...getInputProps()} />
          <div className="relative">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-6 transition-all duration-300
              ${isDragActive
                ? "bg-ceramic-500 text-white shadow-lg ceramic-glow"
                : "bg-gradient-to-br from-ceramic-100 to-ceramic-200 text-ceramic-600 group-hover:from-ceramic-200 group-hover:to-ceramic-300"
              }`}>
              <Upload size={32} className={`transition-transform duration-300 ${isDragActive ? 'scale-110' : 'group-hover:scale-110'}`} />
            </div>
            {isDragActive && (
              <div className="absolute -top-2 -right-2">
                <Sparkles size={20} className="text-ceramic-500 animate-pulse" />
              </div>
            )}
          </div>

          <h3 className="text-xl font-semibold text-slate-800 mb-2">
            {isDragActive ? "¡Suelta las imágenes!" : "Sube tus perfiles cerámicos"}
          </h3>
          <p className="text-slate-600 mb-4 max-w-md mx-auto">
            {isDragActive
              ? "Las imágenes se procesarán automáticamente"
              : "Arrastra y suelta imágenes PNG o JPG, o haz clic para seleccionar archivos"}
          </p>

          <div className="flex items-center justify-center gap-4 text-sm text-slate-500">
            <div className="flex items-center gap-1">
              <ImageIcon size={16} />
              <span>PNG, JPG</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-slate-300"></div>
            <div className="flex items-center gap-1">
              <Upload size={16} />
              <span>Múltiples archivos</span>
            </div>
          </div>
        </div>
      </div>

      {/* Thumbnails */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <ImageIcon size={20} />
            Imágenes seleccionadas ({files.length})
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {files.map((sf) => (
              <div
                key={sf.id}
                className="relative group rounded-xl overflow-hidden bg-white shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105"
              >
                <div className="aspect-square">
                  <img
                    src={sf.preview}
                    alt={sf.file.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                <button
                  type="button"
                  onClick={() => onRemove(sf.id)}
                  className="absolute top-2 right-2 bg-red-500/90 hover:bg-red-600 text-white rounded-full p-1.5
                    opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110 shadow-lg"
                >
                  <X size={14} />
                </button>
                <div className="absolute bottom-0 left-0 right-0 p-2">
                  <span className="text-white text-xs font-medium truncate block opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    {sf.file.name}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
