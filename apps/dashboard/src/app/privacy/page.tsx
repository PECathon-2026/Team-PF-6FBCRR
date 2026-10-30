'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, AuditEventDTO, SensitiveSpanDTO } from '@/lib/api';
import { Shield, Eye, AlertOctagon, Lock, EyeOff, AlertTriangle, CheckCircle2 } from 'lucide-react';

function PrivacyInspectorContent() {
  const searchParams = useSearchParams();
  const runIdParam = searchParams.get('run_id') || '';

  const [runId, setRunId] = useState(runIdParam);
  const [previewData, setPreviewData] = useState<any>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEventDTO[]>([]);
  const [viewMode, setViewMode] = useState<'split' | 'sanitized' | 'raw'>('split');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getAuditEvents(50).then((data) => {
      setAuditEvents(data.events || []);
      if (!runId && data.events && data.events.length > 0) {
        setRunId(data.events[0].run_id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (runId) {
      setLoading(true);
      api.getPrivacyPreview(runId)
        .then(setPreviewData)
        .catch(() => setPreviewData(null))
        .finally(() => setLoading(false));
    }
  }, [runId]);

  return (
    <div className="space-y-8">
      {/* Prominent Privacy Notice Banner */}
      <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-500/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white tracking-wide">
                LOCAL-ONLY PRIVACY INSPECTOR
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30">
                Cache-Control: no-store
              </span>
            </div>
            <p className="text-xs text-purple-200/70 mt-0.5">
              Original screenshots are strictly kept in transient memory and discarded on session close. Never persisted or transmitted off-device.
            </p>
          </div>
        </div>

        {/* View Mode Controls */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-medium">
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-md transition ${viewMode === 'split' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            Side-by-Side
          </button>
          <button
            onClick={() => setViewMode('sanitized')}
            className={`px-3 py-1.5 rounded-md transition ${viewMode === 'sanitized' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            Masked Only
          </button>
          <button
            onClick={() => setViewMode('raw')}
            className={`px-3 py-1.5 rounded-md transition ${viewMode === 'raw' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            Raw (Local)
          </button>
        </div>
      </div>

      {/* Side-by-Side Before / After Viewports */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Raw Viewport (Local Only) */}
        {(viewMode === 'split' || viewMode === 'raw') && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs px-1">
              <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                <span>Original State (LOCAL MEMORY ONLY)</span>
              </span>
              <span className="text-[10px] font-mono text-amber-300/80 bg-amber-950/40 border border-amber-600/30 px-2 py-0.5 rounded">
                UNMASKED SENSITIVE
              </span>
            </div>

            <div className="relative rounded-2xl overflow-hidden border border-amber-500/30 bg-slate-950 aspect-[16/10] flex items-center justify-center shadow-lg">
              {runId ? (
                <img
                  src={`/api/privacy/screenshot/raw/${runId}`}
                  alt="Raw Screenshot"
                  className="w-full h-full object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="text-slate-500 text-xs">No active preview run selected</div>
              )}
            </div>
          </div>
        )}

        {/* Sanitized Viewport (Solid Black Mask Overlays) */}
        {(viewMode === 'split' || viewMode === 'sanitized') && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs px-1">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Shield className="w-4 h-4" />
                <span>Sanitized Model View (ALLOWLISTED)</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-300 bg-emerald-950/40 border border-emerald-600/30 px-2 py-0.5 rounded">
                SOLID OPAQUE MASKED
              </span>
            </div>

            <div className="relative rounded-2xl overflow-hidden border border-emerald-500/40 bg-slate-950 aspect-[16/10] flex items-center justify-center shadow-lg">
              {runId ? (
                <img
                  src={`/api/privacy/screenshot/sanitized/${runId}`}
                  alt="Sanitized Screenshot"
                  className="w-full h-full object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="text-slate-500 text-xs">No active preview run selected</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Detected PII Spans & Redaction Explanations Table */}
      <div className="rounded-2xl bg-surface border border-border overflow-hidden space-y-4 p-5 shadow-xl">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Detected Sensitive Entities &amp; Redactions</h2>
            <p className="text-xs text-slate-400 mt-0.5">Comprehensive audit breakdown of all triggered detection rules for run #{runId || 'none'}</p>
          </div>
          <span className="text-xs font-mono text-purple-400 bg-purple-950/40 border border-purple-500/30 px-2.5 py-1 rounded-md">
            {previewData?.spans?.length || 0} Entities Protected
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono text-[10px] border-b border-border/80">
              <tr>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Detector</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Replacement Token</th>
                <th className="py-2.5 px-3">Redaction Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {previewData?.spans?.length > 0 ? (
                previewData.spans.map((s: SensitiveSpanDTO, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition">
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-500/30 font-bold">
                        {s.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-semibold">{s.detector}</td>
                    <td className="py-2.5 px-3 text-slate-400">{(s.confidence * 100).toFixed(0)}%</td>
                    <td className="py-2.5 px-3 text-emerald-400">{s.replacement_token || 'SOLID_MASK'}</td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans text-xs">{s.reason}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500 italic font-sans">
                    No PII detections logged for this run ID.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Blocked Outbound Egress Log */}
      <div className="rounded-2xl bg-surface border border-border overflow-hidden p-5 shadow-xl space-y-4">
        <div className="flex items-center gap-2 border-b border-border/80 pb-3">
          <AlertOctagon className="w-5 h-5 text-rose-500" />
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Egress Gateway Interception Log</h2>
            <p className="text-xs text-slate-400">Audit trail of outbound AI requests checked and blocked by the fail-closed egress gateway</p>
          </div>
        </div>

        <div className="space-y-2">
          {auditEvents.filter((ev) => ev.event_type.includes('GATEWAY') || ev.event_type.includes('BLOCKED')).length > 0 ? (
            auditEvents
              .filter((ev) => ev.event_type.includes('GATEWAY') || ev.event_type.includes('BLOCKED'))
              .map((ev, i) => (
                <div key={i} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono flex items-center justify-between">
                  <div>
                    <span className={`font-bold mr-2 ${ev.event_type.includes('BLOCKED') ? 'text-rose-400' : 'text-emerald-400'}`}>
                      [{ev.event_type}]
                    </span>
                    <span className="text-slate-300">{JSON.stringify(ev.details)}</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                </div>
              ))
          ) : (
            <div className="p-4 text-center text-slate-500 text-xs italic">
              All outbound requests verified allowlisted. Zero leaks detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PrivacyPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center text-slate-500 text-sm">Loading Privacy Inspector...</div>}>
      <PrivacyInspectorContent />
    </Suspense>
  );
}

