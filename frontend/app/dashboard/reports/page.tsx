'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { apiJson, ApiError } from '@/lib/api';

type StatusReport = {
  id?: string | null;
  week_id?: string;
  subject?: string;
  body?: string;
  hex_embed_url?: string | null;
  status?: string;
  sent_at?: string | null;
};

function metricsFromBody(body: string) {
  const lines = body.split('\n').filter((l) => /^[•\-\*]\s/.test(l.trim()) || /^\d+\./.test(l.trim()));
  const prMentions = (body.match(/\bPRs?\b|\bpull requests?\b/gi) || []).length;
  const blockerMentions = (body.match(/\bblockers?\b/gi) || []).length;
  return {
    bullets: Math.max(lines.length, Math.min(20, (body.match(/shipped|merged|resolved|completed/gi) || []).length)),
    prs: prMentions || Math.min(12, Math.floor(body.length / 400)),
    blockers: blockerMentions || 0,
  };
}

// Count-up animation hook
function useCountUp(end: number, duration: number = 1500) {
  const [count, setCount] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    if (!hasStarted) {
      setHasStarted(true);
      let startTime: number;
      const animate = (currentTime: number) => {
        if (!startTime) startTime = currentTime;
        const progress = Math.min((currentTime - startTime) / duration, 1);
        setCount(Math.floor(progress * end));
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      requestAnimationFrame(animate);
    }
  }, [end, duration, hasStarted]);

  return count;
}

function MetricCard({
  label,
  value,
  color,
  delay,
}: {
  label: string;
  value: number;
  color: 'cyan' | 'blue' | 'green';
  delay: number;
}) {
  const count = useCountUp(value);
  const colorMap = {
    cyan: { glow: 'shadow-[0_0_30px_rgba(34,211,238,0.15)]', text: 'text-cyan-400', border: 'border-cyan-500/20' },
    blue: { glow: 'shadow-[0_0_30px_rgba(59,130,246,0.15)]', text: 'text-blue-400', border: 'border-blue-500/20' },
    green: { glow: 'shadow-[0_0_30px_rgba(16,185,129,0.15)]', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className={`
        bg-white/[0.04] backdrop-blur-xl rounded-2xl p-6
        border border-white/[0.08] ${colorMap[color].border}
        ${colorMap[color].glow}
      `}
    >
      <p className="text-sm text-neutral-400 mb-2">{label}</p>
      <p className={`text-4xl font-bold font-heading ${colorMap[color].text}`}>{count}</p>
    </motion.div>
  );
}

function HexEmbed({ url }: { url?: string | null }) {
  const [loaded, setLoaded] = useState(false);

  // DEMO OVERRIDE: For the Hackathon presentation, we force a Hex embed to always show.
  // Replace this placeholder link with your actual Hex Project "Public Share" link:
  const displayUrl = url || "https://app.hex.tech/019d3aa4-867e-711e-8c94-61029db9dba9/app/032qTCX1Ufercb0e54nKuw/latest?embedded=true";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="bg-white/[0.04] backdrop-blur-xl rounded-2xl p-6 border border-cyan-500/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
    >
      <div className="relative h-[550px] rounded-xl overflow-hidden bg-[#0a0f1a] border border-white/[0.08]">
        {!loaded && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#0a0f1a]/80">
            <div className="w-12 h-12 rounded-full border-2 border-cyan-500/30 border-t-cyan-500 animate-spin" />
          </div>
        )}
        {/* We add allow="clipboard-write" and other standard sandbox permissions for Hex to run scripts and embeds */}
        <iframe 
          title="Hex analytics" 
          src={displayUrl} 
          className="absolute inset-0 w-full h-full border-0" 
          onLoad={() => setLoaded(true)} 
          sandbox="allow-scripts allow-same-origin allow-popups"
        />
      </div>
      <div className="mt-4 flex items-center justify-center gap-2 text-neutral-500 text-sm">
        <span className="text-cyan-500/80">Powered by Hex</span>
      </div>
    </motion.div>
  );
}

function StakeholderEmail({
  report,
  onRefresh,
}: {
  report: StatusReport;
  onRefresh: () => Promise<void>;
}) {
  const [body, setBody] = useState(report.body || '');
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState('');
  const baseline = report.body || '';

  useEffect(() => {
    setBody(report.body || '');
  }, [report.id, report.body]);

  const save = async () => {
    if (!report.id || body === baseline) return;
    setSaving(true);
    setErr('');
    try {
      await apiJson<StatusReport>(`/api/v1/reports/${encodeURIComponent(report.id)}/edit`, {
        method: 'PATCH',
        json: { body },
      });
      await onRefresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const send = async () => {
    if (!report.id) return;
    setSending(true);
    setErr('');
    try {
      await apiJson(`/api/v1/reports/${encodeURIComponent(report.id)}/send`, { method: 'POST', json: {} });
      await onRefresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Send failed');
    } finally {
      setSending(false);
    }
  };

  const sent = report.status === 'sent' || !!report.sent_at;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="lg:col-span-3 bg-white/[0.04] backdrop-blur-xl rounded-2xl p-6 border border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Email Preview</h3>
          <button
            type="button"
            onClick={() => save()}
            disabled={saving || body === (report.body || '')}
            className="text-sm text-cyan-400 hover:text-cyan-300 disabled:opacity-40"
          >
            {saving ? 'Saving…' : 'Save draft'}
          </button>
        </div>
        {err && <p className="text-red-400 text-sm mb-2">{err}</p>}
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          onBlur={() => void save()}
          rows={16}
          className="w-full min-h-[300px] p-4 rounded-xl bg-[#0a0f1a] border border-white/[0.08] whitespace-pre-wrap font-sans text-neutral-300 text-sm leading-relaxed focus:outline-none focus:border-cyan-500/50"
        />
        <p className="mt-3 text-xs text-neutral-500">Edits sync to the API on blur or Save draft.</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="lg:col-span-2 bg-white/[0.04] backdrop-blur-xl rounded-2xl p-6 border border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
      >
        <h3 className="text-lg font-medium text-white mb-6">Send Options</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-neutral-400 block mb-2">To</label>
            <div className="px-4 py-3 rounded-xl bg-[#0a0f1a] border border-white/[0.08] text-neutral-300 text-sm">Stakeholders (from project settings)</div>
          </div>
          <div>
            <label className="text-sm text-neutral-400 block mb-2">Subject</label>
            <div className="px-4 py-3 rounded-xl bg-[#0a0f1a] border border-white/[0.08] text-neutral-300 text-sm">
              {report.subject || 'Weekly status'}
            </div>
          </div>
          <div className="pt-4">
            {sent ? (
              <div className="flex items-center justify-center gap-3 py-4 text-emerald-400">
                <span>Queued / sent ({report.sent_at || 'recorded'})</span>
              </div>
            ) : (
              <motion.button
                type="button"
                onClick={() => void send()}
                disabled={sending}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-4 rounded-xl font-medium text-white bg-gradient-to-r from-cyan-500 to-cyan-400 shadow-[0_0_30px_rgba(34,211,238,0.3)] disabled:opacity-70 flex items-center justify-center gap-2"
              >
                {sending ? (
                  <>
                    <div className="w-5 h-5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    <span>Queueing…</span>
                  </>
                ) : (
                  <>
                    <span>Send via Gmail (review queue)</span>
                  </>
                )}
              </motion.button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'this-week' | 'email'>('this-week');
  const [report, setReport] = useState<StatusReport | null>(null);
  const [history, setHistory] = useState<StatusReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [err, setErr] = useState('');

  const refresh = useCallback(async () => {
    setErr('');
    try {
      const cur = await apiJson<StatusReport>('/api/v1/reports/current');
      setReport(cur);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setReport(null);
      } else if (e instanceof ApiError && e.status !== 401) {
        setErr(e.message);
      }
    }
    try {
      const h = await apiJson<StatusReport[]>('/api/v1/reports/history');
      setHistory(Array.isArray(h) ? h : []);
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    (async () => {
      await refresh();
      setLoading(false);
    })();
  }, [refresh]);

  const handleGenerate = async () => {
    setGenerating(true);
    setErr('');
    try {
      const r = await apiJson<StatusReport>('/api/v1/reports/generate', { method: 'POST', json: {} });
      setReport(r);
      await refresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Generate failed');
    } finally {
      setGenerating(false);
    }
  };

  const m = report?.body ? metricsFromBody(report.body) : { bullets: 0, prs: 0, blockers: 0 };
  const weekLabel = report?.week_id || 'Current week';

  return (
    <div className="min-h-screen bg-[#020817] flex">
      <Sidebar />

      <main className="flex-1 ml-[260px] p-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8 flex flex-wrap items-end justify-between gap-4"
        >
          <div>
            <h1 className="text-3xl font-bold text-white font-heading mb-2">Weekly Status Report</h1>
            <p className="text-neutral-400">{weekLabel}</p>
            {report?.status && (
              <p className="text-neutral-500 text-sm mt-1">
                Status: {report.status}
                {report.id && ` · id ${report.id.slice(0, 8)}…`}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || loading}
            className="px-4 py-2 rounded-lg bg-white/[0.06] border border-white/[0.1] text-white text-sm hover:bg-white/[0.1] disabled:opacity-50"
          >
            {generating ? 'Generating…' : report ? 'Regenerate report' : 'Generate report'}
          </button>
        </motion.div>

        {err && <p className="text-red-400 mb-4">{err}</p>}
        {loading && <p className="text-neutral-500 mb-4">Loading…</p>}

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="inline-flex p-1 rounded-xl bg-white/[0.04] border border-white/[0.08]">
            {[
              { id: 'this-week', label: 'This Week' },
              { id: 'email', label: 'Stakeholder Email' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as 'this-week' | 'email')}
                className={`
                  relative px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300
                  ${activeTab === tab.id ? 'text-white' : 'text-neutral-400 hover:text-neutral-200'}
                `}
              >
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTabReports"
                    className="absolute inset-0 bg-white/[0.08] rounded-lg"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{tab.label}</span>
              </button>
            ))}
          </div>
        </motion.div>

        {!report && !loading && (
          <p className="text-neutral-500 mb-6">No report for this week yet. Click Generate report.</p>
        )}

        {history.length > 0 && (
          <div className="mb-6 text-sm text-neutral-500">
            Recent:{' '}
            {history.slice(0, 4).map((h) => (
              <span key={h.id || h.week_id} className="mr-3">
                {h.week_id || h.subject || '—'} ({h.status})
              </span>
            ))}
          </div>
        )}

        <AnimatePresence mode="wait">
          {activeTab === 'this-week' ? (
            <motion.div
              key="this-week"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              {report?.body && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <MetricCard label="Highlights (est.)" value={m.bullets} color="cyan" delay={0.1} />
                  <MetricCard label="PR momentum (est.)" value={m.prs} color="blue" delay={0.2} />
                  <MetricCard label="Blocker mentions" value={m.blockers} color="green" delay={0.3} />
                </div>
              )}
              <HexEmbed url={report?.hex_embed_url} />
            </motion.div>
          ) : (
            <motion.div
              key="email"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {report ? (
                <StakeholderEmail report={report} onRefresh={refresh} />
              ) : (
                <p className="text-neutral-500">Generate a report first to edit and send email.</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <style jsx global>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}
