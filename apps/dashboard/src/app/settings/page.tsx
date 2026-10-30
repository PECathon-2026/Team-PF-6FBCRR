'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Shield, Key, Lock, Globe, Server, Trash2, Plus, CheckCircle2, Download } from 'lucide-react';

export default function SettingsPage() {
  const [localOnlyMode, setLocalOnlyMode] = useState(true);
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('qwen2.5-coder:7b');
  const [headless, setHeadless] = useState(true);
  const [osProfile, setOsProfile] = useState<'windows' | 'macos' | 'linux'>('macos');
  
  // Vault secrets state
  const [vaultAliases, setVaultAliases] = useState<string[]>([]);
  const [newAlias, setNewAlias] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newCategory, setNewCategory] = useState('CREDIT_CARD');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const refreshVault = async () => {
    try {
      const data = await api.getVaultSecrets();
      setVaultAliases(data.aliases || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshVault();
  }, []);

  const handleAddSecret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlias || !newValue) return;
    await api.addVaultSecret(newAlias, newValue, newCategory);
    setNewAlias('');
    setNewValue('');
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
    refreshVault();
  };

  const handleDeleteSecret = async (alias: string) => {
    if (!confirm(`Delete secret alias '${alias}' from in-memory vault?`)) return;
    await api.deleteVaultSecret(alias);
    refreshVault();
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System Settings &amp; Local Vault</h1>
        <p className="text-xs text-slate-400 mt-1">Configure browser anti-fingerprinting, AI model routing, and local secret credentials</p>
      </div>

      {/* Network & Local-Only Gating */}
      <div className="p-6 rounded-2xl bg-surface border border-border shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2.5">
            <Shield className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold text-white">Local-Only AI Gatekeeper</h2>
              <p className="text-xs text-slate-400">Enforce fail-closed network block preventing any external cloud API transmission</p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={localOnlyMode}
              onChange={(e) => setLocalOnlyMode(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
          </label>
        </div>

        <div className="text-xs text-slate-400 leading-relaxed">
          {localOnlyMode ? (
            <span className="text-emerald-400 font-medium">
              🔒 Local-Only Active: Outbound HTTP/HTTPS requests to external model providers are blocked at the network interface.
            </span>
          ) : (
            <span className="text-amber-400 font-medium">
              ⚠️ Cloud Opt-In Mode: Gated egress will sanitize payloads and verify canaries before dispatching to approved remote endpoints.
            </span>
          )}
        </div>
      </div>

      {/* Camoufox Stealth Browser Engine */}
      <div className="p-6 rounded-2xl bg-surface border border-border shadow-xl space-y-5">
        <div className="flex items-center gap-2.5 border-b border-border/80 pb-3">
          <Globe className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-sm font-bold text-white">Camoufox Anti-Detect Browser Settings</h2>
            <p className="text-xs text-slate-400">Stealth Firefox 157.0 with anti-fingerprint properties and uBlock Origin addon</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold">Execution Mode</label>
            <select
              value={headless ? 'headless' : 'headful'}
              onChange={(e) => setHeadless(e.target.value === 'headless')}
              className="w-full bg-slate-900 border border-border rounded-xl p-2.5 text-slate-200"
            >
              <option value="headless">Headless (Background Isolated Context)</option>
              <option value="headful">Headful (Live Displayed GUI Window)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold">OS Fingerprint Spoof Target</label>
            <select
              value={osProfile}
              onChange={(e: any) => setOsProfile(e.target.value)}
              className="w-full bg-slate-900 border border-border rounded-xl p-2.5 text-slate-200"
            >
              <option value="macos">macOS Apple Silicon (Sonoma / M-series)</option>
              <option value="windows">Windows 11 x64 (Direct3D11 / DirectX)</option>
              <option value="linux">Ubuntu Linux x64 (Mesa / Wayland)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Local Secret Vault Manager */}
      <div className="p-6 rounded-2xl bg-surface border border-border shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2.5">
            <Key className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold text-white">Local Secret Vault</h2>
              <p className="text-xs text-slate-400">Secrets are injected directly into live browser DOM without model exposure</p>
            </div>
          </div>
          <span className="text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">
            {vaultAliases.length} Aliases Active
          </span>
        </div>

        {/* Add Secret Form */}
        <form onSubmit={handleAddSecret} className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
          <div>
            <label className="text-slate-400 font-medium block mb-1">Secret Alias</label>
            <input
              type="text"
              placeholder="e.g. personal_card"
              value={newAlias}
              onChange={(e) => setNewAlias(e.target.value)}
              className="w-full bg-slate-900 border border-border rounded-lg p-2 text-slate-100"
              required
            />
          </div>

          <div>
            <label className="text-slate-400 font-medium block mb-1">Secret Value</label>
            <input
              type="password"
              placeholder="••••••••••••"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full bg-slate-900 border border-border rounded-lg p-2 text-slate-100"
              required
            />
          </div>

          <div>
            <label className="text-slate-400 font-medium block mb-1">Category</label>
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              className="w-full bg-slate-900 border border-border rounded-lg p-2 text-slate-100"
            >
              <option value="CREDIT_CARD">Credit / Debit Card</option>
              <option value="PASSWORD">Password / Token</option>
              <option value="CVV">CVV Security Code</option>
              <option value="NAME">Full Name</option>
              <option value="ADDRESS">Address</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              className="w-full py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-1.5 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register</span>
            </button>
          </div>
        </form>

        {savedSuccess && (
          <div className="text-xs text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Secret registered successfully into in-memory vault</span>
          </div>
        )}

        {/* Existing Vault Aliases List */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Vault Aliases</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {vaultAliases.map((alias) => (
              <div
                key={alias}
                className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-slate-200">{alias}</div>
                  <div className="text-[11px] text-slate-500">Value: &bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; [MASKED]</div>
                </div>
                <button
                  onClick={() => handleDeleteSecret(alias)}
                  className="p-1.5 rounded-lg hover:bg-rose-950/60 text-slate-500 hover:text-rose-400 transition"
                  title="Remove from vault"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

