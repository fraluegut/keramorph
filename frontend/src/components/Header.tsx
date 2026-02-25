import { Github, Sparkles } from "lucide-react";

export default function Header() {
  return (
    <header className="glass-card sticky top-0 z-50 animate-float">
      <div className="mx-auto max-w-7xl flex items-center justify-between px-6 py-4">
        {/* Logo / Name */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-ceramic-500 to-ceramic-700 flex items-center justify-center text-white font-bold text-xl shadow-lg ceramic-glow">
              K
            </div>
            <div className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-gradient-to-r from-yellow-400 to-orange-500 flex items-center justify-center">
              <Sparkles size={8} className="text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold leading-tight tracking-tight bg-gradient-to-r from-ceramic-700 to-ceramic-600 bg-clip-text text-transparent">
              Keramorph
            </h1>
            <p className="text-sm text-slate-600 font-medium">
              Clasificación inteligente de perfiles cerámicos
            </p>
            <p className="text-xs text-slate-500">
              Tecnología avanzada por ArqueoBytes
            </p>
          </div>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6">
          <a
            href="https://github.com/arqueobytes/keramorph"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/50 hover:bg-white/80 text-slate-700 hover:text-ceramic-700 transition-all duration-200 hover:shadow-md group"
          >
            <Github size={16} className="group-hover:scale-110 transition-transform" />
            <span className="font-medium">GitHub</span>
          </a>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-ceramic-100 text-ceramic-700 text-xs font-semibold">
            <div className="w-2 h-2 rounded-full bg-ceramic-500 animate-pulse-slow"></div>
            v0.1.0
          </div>
        </div>
      </div>
    </header>
  );
}
