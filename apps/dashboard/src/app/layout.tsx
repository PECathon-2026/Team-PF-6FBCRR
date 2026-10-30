import './globals.css';
import Link from 'next/link';
import { Shield, Eye, BarChart3, Settings, PlayCircle } from 'lucide-react';

export const metadata = {
  title: 'PrivacyLens — Privacy-Preserving AI Browser Agent',
  description: 'Stealth Camoufox browser agent with zero-leak egress gateway and local secret injection',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 flex flex-col min-h-screen">
        {/* Navigation Bar */}
        <header className="border-b border-border/80 bg-surface/80 backdrop-blur sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 text-lg font-bold tracking-tight text-white hover:opacity-90">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <Shield className="w-5 h-5" />
              </div>
              <span>Privacy<span className="text-emerald-400">Lens</span></span>
              <span className="text-xs font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full ml-1">
                Camoufox Stealth
              </span>
            </Link>

            <nav className="flex items-center gap-1 text-sm font-medium text-slate-300">
              <Link href="/" className="px-3 py-1.5 rounded-md hover:bg-surfaceSubtle hover:text-white transition flex items-center gap-1.5">
                <PlayCircle className="w-4 h-4 text-slate-400" />
                <span>Task Studio</span>
              </Link>
              <Link href="/privacy" className="px-3 py-1.5 rounded-md hover:bg-surfaceSubtle hover:text-white transition flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-purple-400" />
                <span>Privacy Inspector</span>
              </Link>
              <Link href="/evaluation" className="px-3 py-1.5 rounded-md hover:bg-surfaceSubtle hover:text-white transition flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                <span>Evaluation Dashboard</span>
              </Link>
              <Link href="/settings" className="px-3 py-1.5 rounded-md hover:bg-surfaceSubtle hover:text-white transition flex items-center gap-1.5">
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Settings & Vault</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/40 text-xs text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>LOCAL-ONLY: SAFE</span>
            </div>
            <span className="text-xs text-slate-400 border-l border-slate-700 pl-3">
              Firefox 157.0 Stealth
            </span>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-border/60 bg-surface/40 py-4 px-6 text-center text-xs text-slate-400">
          PrivacyLens v0.1.0 &bull; Anti-detect Stealth Browser Architecture &bull; Solid Opaque Masking &bull; Zero Egress Leakage
        </footer>
      </body>
    </html>
  );
}

