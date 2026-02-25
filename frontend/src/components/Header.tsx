import { Github } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-ceramic-200 bg-white/80 backdrop-blur sticky top-0 z-50">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-4 py-3">
        {/* Logo / Name */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-ceramic-600 flex items-center justify-center text-white font-bold text-lg">
            K
          </div>
          <div>
            <h1 className="text-lg font-semibold leading-tight tracking-tight">
              Keramorph
            </h1>
            <p className="text-xs text-gray-500">
              Clasificación de perfiles cerámicos · ArqueoBytes
            </p>
          </div>
        </div>

        {/* Links */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <a
            href="https://github.com/arqueobytes/keramorph"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-ceramic-700 transition-colors"
          >
            <Github size={16} />
            GitHub
          </a>
          <span className="text-ceramic-400">|</span>
          <span className="text-xs text-gray-400">v0.1.0</span>
        </div>
      </div>
    </header>
  );
}
