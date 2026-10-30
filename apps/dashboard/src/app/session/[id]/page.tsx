'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api, StepResponseDTO, DOMElementDTO } from '@/lib/api';
import {
  Shield, AlertTriangle, CheckCircle2, XCircle, ArrowRight,
  Eye, RefreshCw, Lock, Zap, Clock, ChevronDown, ChevronRight
} from 'lucide-react';

export default function SessionViewPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [stepData, setStepData] = useState<StepResponseDTO | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [activeTab, setActiveTab] = useState<'dom' | 'timeline' | 'preview'>('preview');
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});

  const handleStep = async () => {
    setLoading(true);
    try {
      const data = await api.stepSession(sessionId);
      setStepData(data);
      setHistory((prev) => [...prev, data]);
    } catch (err: any) {
      alert(`Step error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approved: boolean) => {
    setApproving(true);
    try {
      await api.approveAction(sessionId, approved, approved ? 'User approved via dashboard' : 'User rejected via dashboard');
      await handleStep();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  useEffect(() => {
    // Initial step upon session entry
    handleStep();
  }, [sessionId]);

  const runId = stepData?.observation?.run_id;

  return (
    <div className="space-y-6">
      {/* Session Top Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-surface border border-border">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
              Session {sessionId.slice(0, 8)}
            </span>
            <span className="text-xs text-slate-400">
              Page: <strong className="text-slate-200">{stepData?.observation?.page_title || 'Loading page...'}</strong>
            </span>
          </div>
          <h1 className="text-sm font-medium text-slate-300 mt-1">
            Origin: <span className="text-emerald-400 font-mono text-xs">{stepData?.observation?.page_origin || 'local'}</span>
          </h1>
        </div>

        {/* Step Controls */}
        <div className="flex items-center gap-3">
          {stepData?.is_finished ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>TASK FINISHED</span>
            </div>
          ) : stepData?.requires_approval ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-950/60 border border-amber-500/40 text-amber-400 text-xs font-semibold animate-pulse">
              <AlertTriangle className="w-4 h-4" />
              <span>APPROVAL REQUIRED</span>
            </div>
          ) : (
            <button
              onClick={handleStep}
              disabled={loading}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow transition disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 fill-white" />}
              <span>Execute Next Step</span>
            </button>
          )}

          <button
            onClick={() => router.push(`/privacy?run_id=${runId}`)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition"
          >
            <Eye className="w-3.5 h-3.5 text-purple-400" />
            <span>Inspect Masks</span>
          </button>
        </div>
      </div>

      {/* Human-in-the-Loop Approval Modal Card (High-Risk Interception) */}
      {stepData?.requires_approval && (
        <div className="p-5 rounded-2xl bg-amber-950/30 border-2 border-amber-500/60 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40 mt-0.5">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold uppercase text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
                  High-Risk Policy Trigger
                </span>
                <span className="text-xs text-slate-400">Human Approval Gatekeeper</span>
              </div>
              <h2 className="text-base font-bold text-white mt-1">
                Action requires human authorization before execution
              </h2>
              <p className="text-xs text-amber-200/80 mt-1">
                Reason: {stepData.risk_reason || 'Outbound dispatch or payment action detected'}
              </p>
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs font-mono space-y-1 text-slate-300">
            <div><span className="text-slate-500">Proposed Action:</span> <span className="text-amber-300 font-bold">{stepData.action.action_type}</span></div>
            <div><span className="text-slate-500">Target Element:</span> {stepData.action.element_id || 'Page'}</div>
            <div><span className="text-slate-500">Intent:</span> {stepData.action.reason}</div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => handleApprove(false)}
              disabled={approving}
              className="px-4 py-2 rounded-xl bg-rose-950/80 hover:bg-rose-900 border border-rose-500/40 text-rose-300 font-semibold text-xs flex items-center gap-1.5 transition"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject &amp; Abort Action</span>
            </button>
            <button
              onClick={() => handleApprove(true)}
              disabled={approving}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-950 transition"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Approve &amp; Proceed Safely</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Viewport + Live Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Browser Viewport (Sanitized) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Active Camoufox Viewport</span>
            </span>
            <span className="font-mono text-[11px] text-purple-400 bg-purple-950/40 border border-purple-500/30 px-2 py-0.5 rounded">
              SOLID PIXEL MASKED
            </span>
          </div>

          <div className="relative rounded-2xl overflow-hidden border border-border bg-slate-950 aspect-[16/10] flex items-center justify-center shadow-xl">
            {runId ? (
              <img
                src={`/api/privacy/screenshot/sanitized/${runId}`}
                alt="Sanitized Viewport"
                className="w-full h-full object-contain"
                onError={(e: any) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <div className="text-center text-xs text-slate-500">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-600" />
                <span>Capturing sanitized viewport...</span>
              </div>
            )}
          </div>

          {/* Redactions Summary Ticker */}
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="text-slate-400">Redactions applied:</span>
            {stepData?.observation?.redactions_summary &&
            Object.keys(stepData.observation.redactions_summary).length > 0 ? (
              Object.entries(stepData.observation.redactions_summary).map(([cat, count]) => (
                <span
                  key={cat}
                  className="px-2 py-0.5 rounded-md bg-purple-950/60 border border-purple-500/40 text-purple-300 font-mono text-[11px]"
                >
                  [{cat}: {count}]
                </span>
              ))
            ) : (
              <span className="text-slate-500 italic">No sensitive elements on current view</span>
            )}
          </div>
        </div>

        {/* Right Column: Tabbed Inspector (DOM / Timeline) */}
        <div className="lg:col-span-5 flex flex-col h-[520px] rounded-2xl bg-surface border border-border overflow-hidden">
          {/* Tab Headers */}
          <div className="flex border-b border-border bg-slate-950/50 text-xs font-medium">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex-1 py-3 text-center border-b-2 transition ${
                activeTab === 'preview' ? 'border-emerald-500 text-emerald-400 bg-surface' : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              Action Timeline
            </button>
            <button
              onClick={() => setActiveTab('dom')}
              className={`flex-1 py-3 text-center border-b-2 transition ${
                activeTab === 'dom' ? 'border-purple-500 text-purple-400 bg-surface' : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              Sanitized DOM Tree
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
            {activeTab === 'preview' ? (
              <div className="space-y-3">
                {history.length === 0 ? (
                  <div className="text-slate-500 text-center py-10">No actions executed yet. Click &quot;Execute Next Step&quot;.</div>
                ) : (
                  history.map((h, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-200">Step {h.step}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          h.risk_level === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-600/40' : 'bg-emerald-950 text-emerald-400 border border-emerald-600/40'
                        }`}>
                          {h.risk_level}
                        </span>
                      </div>
                      <div className="font-mono text-slate-300">
                        <span className="text-purple-400 font-bold">{h.action.action_type}</span>
                        {h.action.element_id && <span className="text-slate-400"> on #{h.action.element_id}</span>}
                        {h.action.secret_alias && (
                          <span className="text-emerald-400 font-semibold"> (vault alias: {h.action.secret_alias})</span>
                        )}
                      </div>
                      <div className="text-slate-400 text-[11px] leading-tight">{h.action.reason}</div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-1.5 font-mono text-[11px]">
                {stepData?.observation?.elements.map((el) => {
                  const isRedacted = el.sanitized_text?.includes('[REDACTED:');
                  return (
                    <div
                      key={el.id}
                      className={`p-2 rounded-lg border transition ${
                        isRedacted
                          ? 'bg-purple-950/30 border-purple-500/50 text-purple-200'
                          : 'bg-slate-900/60 border-slate-800 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span className="font-bold text-slate-200">&lt;{el.tag}&gt; #{el.id}</span>
                        {isRedacted && (
                          <span className="px-1.5 py-0.2 rounded bg-purple-900/80 text-purple-300 font-bold text-[9px]">
                            SANITIZED
                          </span>
                        )}
                      </div>
                      <div className="mt-1 break-words">
                        {el.sanitized_text || <span className="text-slate-600 italic">empty</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

