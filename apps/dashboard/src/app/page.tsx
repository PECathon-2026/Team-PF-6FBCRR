'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Shield, Lock, AlertTriangle, ArrowRight, Play, Server, CheckCircle2, RefreshCw } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [task, setTask] = useState('Add item to cart and proceed to payment review without completing final purchase');
  const [url, setUrl] = useState('');
  const [scenarioKey, setScenarioKey] = useState('checkout');
  const [agentType, setAgentType] = useState('mock');
  const [isLocalOnly, setIsLocalOnly] = useState(true);
  const [cloudOptIn, setCloudOptIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [fixtures, setFixtures] = useState<any[]>([]);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth({ status: 'offline' }));
    api.getFixtures().then(setFixtures).catch(() => {});
  }, []);

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.startSession(
        task,
        url || undefined,
        scenarioKey || undefined,
        agentType
      );
      router.push(`/session/${data.session_id}`);
    } catch (err: any) {
      alert(`Launch error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const selectScenario = (f: any) => {
    setScenarioKey(f.key);
    setTask(f.task);
    setUrl('');
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Banner / System Health */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-xl bg-surface border border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Anti-Detect Stealth Browser Engine</h2>
            <p className="text-xs text-slate-400">Firefox 157.0 with anti-fingerprint presets &amp; solid opaque pixel masking</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">
            <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span className="text-slate-300">API: {health?.status || 'Connecting...'}</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700">
            <span className="text-slate-300">Egress Gate: DENY-BY-DEFAULT</span>
          </div>
        </div>
      </div>

      {/* Task Composer Form */}
      <div className="p-6 rounded-2xl bg-surface border border-border shadow-xl space-y-6">
        <div className="border-b border-border/80 pb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Compose Agent Task</h1>
            <p className="text-sm text-slate-400 mt-0.5">Automate browser workflows without exposing PII, credentials, or faces to AI models</p>
          </div>

          {/* Local vs Cloud Toggle */}
          <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              type="button"
              onClick={() => setIsLocalOnly(true)}
              className={`px-3 py-1.5 rounded-md transition ${isLocalOnly ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              🔒 Local-Only (Safe)
            </button>
            <button
              type="button"
              onClick={() => {
                if (confirm('Enable Cloud Opt-In? External models may receive sanitized observations. Raw secrets remain strictly in local memory.')) {
                  setIsLocalOnly(false);
                  setCloudOptIn(true);
                }
              }}
              className={`px-3 py-1.5 rounded-md transition ${!isLocalOnly ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              ☁️ Cloud Opt-In
            </button>
          </div>
        </div>

        <form onSubmit={handleLaunch} className="space-y-6">
          {/* Natural Language Task Input */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-200 flex items-center justify-between">
              <span>Agent Instruction / Task Goal</span>
              <span className="text-xs font-normal text-slate-400">Strict PII redaction active</span>
            </label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              rows={3}
              required
              className="w-full bg-slate-900 border border-border rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              placeholder="e.g. Add item to cart and proceed to payment review..."
            />
          </div>

          {/* Quick Scenario Pre-fill Pills */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Synthetic Benchmark Scenarios</span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {fixtures.map((f) => (
                <button
                  type="button"
                  key={f.key}
                  onClick={() => selectScenario(f)}
                  className={`text-left p-3 rounded-xl border text-xs transition ${
                    scenarioKey === f.key
                      ? 'bg-emerald-950/40 border-emerald-500/60 text-emerald-200'
                      : 'bg-slate-900/80 border-border/80 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="font-semibold text-slate-100 mb-0.5">{f.name}</div>
                  <div className="text-[11px] text-slate-400 truncate">{f.task}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {/* Custom URL Input */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-200">Target Web URL (Optional)</label>
              <input
                type="text"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setScenarioKey('');
                }}
                placeholder="Leave blank to use selected benchmark scenario"
                className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              />
            </div>

            {/* AI Model Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-200">AI Model Adapter</label>
              <select
                value={agentType}
                onChange={(e) => setAgentType(e.target.value)}
                className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              >
                <option value="mock">Deterministic Mock Agent (100% Offline Benchmark)</option>
                <option value="ollama">Ollama Local LLM (qwen2.5-coder / llama3.2)</option>
              </select>
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-2 flex items-center justify-between border-t border-border/60">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              <span>All secrets injected directly into DOM from local in-memory vault</span>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition shadow-lg shadow-emerald-950 flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Launching Camoufox...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Launch Privacy-Preserving Agent</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-xl bg-surface/70 border border-border/80 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-sm">
            0%
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Zero Egress Leakage</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Strict deny-by-default gateway validates every observation payload against synthetic canaries before model dispatch.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-surface/70 border border-border/80 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-sm">
            🛡️
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Solid Opaque Pixel Masking</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Irreversible Pillow solid rectangle overlays strip PII visual tokens with padding and EXIF scrubbing.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-surface/70 border border-border/80 space-y-2">
          <div className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-sm">
            🔑
          </div>
          <h3 className="font-semibold text-slate-200 text-sm">Local Secret Vault</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Credit cards, passwords, and OTPs never enter model prompt tokens; injected directly into live browser DOM.
          </p>
        </div>
      </div>
    </div>
  );
}

