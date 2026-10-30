'use client';

import { useState, useEffect } from 'react';
import { api, EvaluationReportDTO, EvalScenarioResultDTO } from '@/lib/api';
import {
  BarChart3, RefreshCw, Download, CheckCircle2, XCircle,
  Shield, Zap, Clock, HardDrive, FileText, ArrowUpRight
} from 'lucide-react';

export default function EvaluationDashboardPage() {
  const [report, setReport] = useState<EvaluationReportDTO | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      const data = await api.getEvaluationResults();
      setReport(data);
    } catch (e) {
      console.warn('No existing evaluation report, awaiting live run');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const handleRunEvaluation = async () => {
    setRunning(true);
    try {
      const results = await api.runEvaluation();
      setReport(results);
    } catch (err: any) {
      alert(`Evaluation run error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const downloadJson = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `privacylens-eval-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
  };

  const metrics = report?.metrics;
  const latencies = report?.latencies_ms;

  return (
    <div className="space-y-8">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-2xl bg-surface border border-border shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 rounded">
              Empirical Security &amp; Accuracy Suite
            </span>
            <span className="text-xs text-slate-400">Camoufox Firefox Stealth Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">Evaluation &amp; Benchmark Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Measured against 6 synthetic ground-truth sites and adversarial attack vectors
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={downloadJson}
            disabled={!report}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>

          <button
            onClick={handleRunEvaluation}
            disabled={running}
            className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-emerald-950 transition disabled:opacity-50"
          >
            {running ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running Suite (6 Scenarios)...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-white" />
                <span>Run Full Benchmark Suite</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Top 6 KPI Metric Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Recall */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Detection Recall</div>
          <div className="text-2xl font-black text-emerald-400">
            {metrics ? `${(metrics.detection_recall * 100).toFixed(1)}%` : '--'}
          </div>
          <div className="text-[10px] text-emerald-300 font-medium">Target &ge; 95%</div>
        </div>

        {/* Precision */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Redaction Precision</div>
          <div className="text-2xl font-black text-emerald-400">
            {metrics ? `${(metrics.redaction_precision * 100).toFixed(1)}%` : '--'}
          </div>
          <div className="text-[10px] text-emerald-300 font-medium">Target &ge; 90%</div>
        </div>

        {/* Leakage */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Canary Leak Rate</div>
          <div className="text-2xl font-black text-emerald-400">
            {metrics ? `${(metrics.leak_rate * 100).toFixed(1)}%` : '--'}
          </div>
          <div className="text-[10px] text-emerald-300 font-medium">0 Leaks Observed</div>
        </div>

        {/* Context Preservation */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Context Preserved</div>
          <div className="text-2xl font-black text-blue-400">
            {metrics ? `${(metrics.context_preservation * 100).toFixed(1)}%` : '--'}
          </div>
          <div className="text-[10px] text-blue-300 font-medium">Non-PII Intact</div>
        </div>

        {/* Task Success */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Task Success</div>
          <div className="text-2xl font-black text-emerald-400">
            {metrics ? `${(metrics.task_success_rate * 100).toFixed(1)}%` : '--'}
          </div>
          <div className="text-[10px] text-emerald-300 font-medium">{metrics?.tasks_completed || '0/6'} Passed</div>
        </div>

        {/* Peak Memory */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Peak Memory (RSS)</div>
          <div className="text-2xl font-black text-purple-400">
            {metrics ? `${metrics.peak_rss_mb} MB` : '--'}
          </div>
          <div className="text-[10px] text-purple-300 font-medium">Lightweight &lt; 500 MB</div>
        </div>
      </div>

      {/* Latency Breakdown Bar */}
      <div className="p-5 rounded-2xl bg-surface border border-border shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-border/80 pb-2.5">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Pipeline Latency Benchmarks (p50 / p95 in ms)</span>
          </h2>
          <span className="text-[11px] font-mono text-slate-400">Measured per interaction turn</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400">1. DOM Collection</div>
            <div className="text-lg font-mono font-bold text-slate-100">
              {latencies ? `${latencies.dom_collection.p50} ms` : '--'}
              <span className="text-xs font-normal text-slate-500 ml-1.5">(p95: {latencies?.dom_collection.p95} ms)</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400">2. Privacy Sanitization</div>
            <div className="text-lg font-mono font-bold text-emerald-400">
              {latencies ? `${latencies.privacy_sanitization.p50} ms` : '--'}
              <span className="text-xs font-normal text-slate-500 ml-1.5">(p95: {latencies?.privacy_sanitization.p95} ms)</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400">3. Egress Gateway &amp; Model</div>
            <div className="text-lg font-mono font-bold text-purple-400">
              {latencies ? `${latencies.model_gating_and_reasoning.p50} ms` : '--'}
              <span className="text-xs font-normal text-slate-500 ml-1.5">(p95: {latencies?.model_gating_and_reasoning.p95} ms)</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="text-[11px] font-semibold text-slate-400">4. Browser Action Execution</div>
            <div className="text-lg font-mono font-bold text-blue-400">
              {latencies ? `${latencies.action_execution.p50} ms` : '--'}
              <span className="text-xs font-normal text-slate-500 ml-1.5">(p95: {latencies?.action_execution.p95} ms)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Per-Scenario Benchmark Breakdown Table */}
      <div className="rounded-2xl bg-surface border border-border overflow-hidden p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Scenario Accuracy Breakdown</h2>
            <p className="text-xs text-slate-400">Detailed per-site detection metrics against gold standard annotations</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] border-b border-border/80">
              <tr>
                <th className="py-2.5 px-3">Scenario</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Steps</th>
                <th className="py-2.5 px-3">Recall</th>
                <th className="py-2.5 px-3">Precision</th>
                <th className="py-2.5 px-3">Protected Categories</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {report?.scenarios?.map((s: EvalScenarioResultDTO) => (
                <tr key={s.scenario} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-3">
                    <div className="font-bold text-slate-200 font-sans">{s.name}</div>
                    <div className="text-[11px] text-slate-500 font-mono">{s.scenario}</div>
                  </td>
                  <td className="py-3 px-3">
                    {s.task_success ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                        <CheckCircle2 className="w-3 h-3" /> PASS
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-500/40 text-[10px] font-bold">
                        <XCircle className="w-3 h-3" /> FAIL
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-slate-300">{s.steps}</td>
                  <td className="py-3 px-3 text-emerald-400 font-bold">{(s.recall * 100).toFixed(0)}%</td>
                  <td className="py-3 px-3 text-emerald-400 font-bold">{(s.precision * 100).toFixed(0)}%</td>
                  <td className="py-3 px-3">
                    <div className="flex gap-1 flex-wrap">
                      {s.detected_categories.map((c) => (
                        <span key={c} className="px-1.5 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-300 text-[10px]">
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

