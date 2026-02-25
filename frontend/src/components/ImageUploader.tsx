import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X } from "lucide-react";
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
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-ceramic-500 bg-ceramic-50" : "border-gray-300 hover:border-ceramic-400"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-2 text-ceramic-400" size={32} />
        <p className="text-sm text-gray-600">
          {isDragActive
            ? "Suelta las imágenes aquí…"
            : "Arrastra imágenes PNG/JPG o haz clic para seleccionar"}
        </p>
        <p className="text-xs text-gray-400 mt-1">Soporta múltiples archivos</p>
      </div>

      {/* Thumbnails */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {files.map((sf) => (
            <div
              key={sf.id}
              className="relative group w-24 h-24 rounded-lg overflow-hidden border border-gray-200"
            >
              <img
                src={sf.preview}
                alt={sf.file.name}
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={() => onRemove(sf.id)}
                className="absolute top-1 right-1 bg-black/50 text-white rounded-full p-0.5
                  opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={14} />
              </button>
              <span className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-[10px] truncate px-1">
                {sf.file.name}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
