'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { apiJson, ApiError } from '@/lib/api';

type SprintTicketApi = {
  id: string;
  name: string;
  score: number;
  reasoning?: string;
  estimated_pts: number;
  assigned_to: string;
  selected: boolean;
};

type SprintPlan = {
  sprint_name?: string;
  sprint_number?: number;
  total_capacity_pts?: number;
  used_capacity_pts?: number;
  utilization_pct?: number;
  tickets: SprintTicketApi[];
  agent_model?: string | null;
};

type SprintStatus = {
  sprint_name?: string | null;
  velocity_pct?: number;
  tickets?: Record<string, unknown>[];
  in_progress_count?: number | null;
  updated_at?: string | null;
};

type UiTicket = {
  id: string;
  k2Score: number;
  title: string;
  assignee: string;
  storyPoints: number;
  included: boolean;
};

function mapToUi(t: SprintTicketApi): UiTicket {
  return {
    id: t.id,
    k2Score: t.score,
    title: t.name,
    assignee: t.assigned_to,
    storyPoints: Math.max(0, Math.round(Number(t.estimated_pts) || 0)),
    included: t.selected,
  };
}

function toApiPayload(tickets: UiTicket[]): SprintTicketApi[] {
  return tickets.map((t) => ({
    id: t.id,
    name: t.title,
    score: t.k2Score,
    estimated_pts: t.storyPoints,
    assigned_to: t.assignee,
    selected: t.included,
    reasoning: '',
    priority: 'P3',
  }));
}

export default function SprintPlanningPage() {
  const [activeTab, setActiveTab] = useState<'ai-draft' | 'velocity'>('ai-draft');
  const [showModal, setShowModal] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [generating, setGenerating] = useState(false);
  const [patching, setPatching] = useState(false);

  const [current, setCurrent] = useState<SprintStatus | null>(null);
  const [draft, setDraft] = useState<SprintPlan | null>(null);
  const [tickets, setTickets] = useState<UiTicket[]>([]);

  const totalCapacity = draft?.total_capacity_pts && draft.total_capacity_pts > 0 ? draft.total_capacity_pts : 90;

  const load = useCallback(async () => {
    setErr('');
    try {
      const cur = await apiJson<SprintStatus>('/api/v1/sprint/current');
      setCurrent(cur);
    } catch (e) {
      if (e instanceof ApiError && e.status !== 401) {
        setErr((prev) => prev || e.message);
      }
      setCurrent(null);
    }

    try {
      const d = await apiJson<SprintPlan>('/api/v1/sprint/draft');
      setDraft(d);
      setTickets((d.tickets || []).map(mapToUi));
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setDraft(null);
        setTickets([]);
      } else if (e instanceof ApiError && e.status !== 401) {
        setErr((prev) => prev || e.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const usedCapacity = useMemo(() => {
    return tickets.filter((t) => t.included).reduce((sum, t) => sum + t.storyPoints, 0);
  }, [tickets]);

  const capacityPercent = totalCapacity > 0 ? (usedCapacity / totalCapacity) * 100 : 0;

  const getCapacityColor = () => {
    if (capacityPercent > 100) return 'bg-red-500';
    if (capacityPercent > 95) return 'bg-amber-500';
    if (capacityPercent >= 80) return 'bg-blue-500';
    return 'bg-cyan-400';
  };

  const getCapacityGlow = () => {
    if (capacityPercent > 100) return 'shadow-[0_0_20px_rgba(239,68,68,0.5)]';
    if (capacityPercent > 95) return 'shadow-[0_0_20px_rgba(245,158,11,0.3)]';
    if (capacityPercent >= 80) return 'shadow-[0_0_20px_rgba(59,130,246,0.3)]';
    return 'shadow-[0_0_20px_rgba(34,211,238,0.3)]';
  };

  const persistTickets = async (next: UiTicket[]) => {
    if (!draft) return;
    setPatching(true);
    try {
      const updated = await apiJson<SprintPlan>('/api/v1/sprint/draft/tickets', {
        method: 'PATCH',
        json: { tickets: toApiPayload(next) },
      });
      setDraft(updated);
      setTickets((updated.tickets || []).map(mapToUi));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Failed to update draft');
    } finally {
      setPatching(false);
    }
  };

  const toggleTicket = (id: string) => {
    setTickets((prev) => {
      const next = prev.map((t) => (t.id === id ? { ...t, included: !t.included } : t));
      void persistTickets(next);
      return next;
    });
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setErr('');
    try {
      const d = await apiJson<SprintPlan>('/api/v1/sprint/draft/generate', { method: 'POST', json: {} });
      setDraft(d);
      setTickets((d.tickets || []).map(mapToUi));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    setErr('');
    try {
      await apiJson('/api/v1/sprint/approve', { method: 'POST', json: {} });
      setShowModal(false);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Approve failed');
    } finally {
      setIsApproving(false);
    }
  };

  const getScoreBadgeStyle = (score: number) => {
    if (score >= 90) return 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.4)]';
    if (score >= 70) return 'bg-blue-500/20 text-blue-400';
    return 'bg-white/10 text-neutral-400';
  };

  const displayName = draft?.sprint_name || current?.sprint_name || 'Sprint';

  return (
    <div className="min-h-screen bg-[#020817] flex">
      <Sidebar />

      <main className="flex-1 ml-[260px] p-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex flex-wrap items-center gap-4 mb-2">
            <h1 className="text-[32px] font-bold text-white font-[family-name:var(--font-syne)]">{displayName} Draft</h1>
            <motion.div
              className="px-3 py-1.5 rounded-full text-xs font-medium relative overflow-hidden"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                backdropFilter: 'blur(20px)',
              }}
            >
              <span className="relative z-10 text-neutral-300">
                Scored by K2 Think V2 · {draft?.agent_model || 'MBZUAI'}
              </span>
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
                animate={{ x: ['-100%', '100%'] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              />
            </motion.div>
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating || loading}
              className="px-4 py-2 rounded-lg bg-white/[0.06] border border-white/[0.1] text-sm text-white hover:bg-white/[0.1] disabled:opacity-50"
            >
              {generating ? 'Generating…' : 'Generate / refresh draft'}
            </button>
          </div>

          <div
            className="inline-flex p-1 rounded-lg mt-4"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {(['ai-draft', 'velocity'] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab ? 'bg-white/10 text-white' : 'text-neutral-400 hover:text-white'
                }`}
              >
                {tab === 'ai-draft' ? 'AI Draft' : 'Velocity Data'}
              </button>
            ))}
          </div>
        </motion.div>

        {err && <p className="text-red-400 mb-4">{err}</p>}
        {loading && <p className="text-neutral-500 mb-4">Loading sprint…</p>}

        {activeTab === 'velocity' && (
          <div className="mb-8 p-6 rounded-xl bg-white/[0.04] border border-white/[0.08]">
            <h2 className="text-lg font-semibold text-white mb-2">Live board</h2>
            {current ? (
              <div className="text-neutral-300 text-sm space-y-1">
                <p>
                  <span className="text-neutral-500">Sprint:</span> {current.sprint_name || '—'}
                </p>
                <p>
                  <span className="text-neutral-500">Velocity indicator:</span> {current.velocity_pct ?? '—'}%
                </p>
                <p>
                  <span className="text-neutral-500">In progress:</span> {current.in_progress_count ?? '—'}
                </p>
                {current.updated_at && (
                  <p className="text-neutral-500 text-xs mt-2">Updated {current.updated_at}</p>
                )}
                {Array.isArray(current.tickets) && current.tickets.length > 0 && (
                  <ul className="mt-4 space-y-2 list-disc list-inside text-neutral-400">
                    {current.tickets.slice(0, 12).map((row, i) => (
                      <li key={i}>{JSON.stringify(row)}</li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-neutral-500">Could not load current sprint.</p>
            )}
          </div>
        )}

        {activeTab === 'ai-draft' && (
          <>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="sticky top-4 z-20 mb-6 p-4 rounded-xl"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                backdropFilter: 'blur(20px)',
                boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05)',
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-white font-medium">
                  Sprint Capacity: {Math.round(capacityPercent)}% · {usedCapacity}/{Math.round(totalCapacity)} pts
                  {patching && <span className="text-neutral-500 text-sm ml-2">Saving…</span>}
                </span>
                {capacityPercent > 100 && (
                  <motion.span
                    animate={{ x: [-2, 2, -2] }}
                    transition={{ duration: 0.1, repeat: Infinity }}
                    className="text-red-400 text-sm font-medium"
                  >
                    Over capacity!
                  </motion.span>
                )}
              </div>
              <div className="h-3 rounded-full bg-white/5 overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${getCapacityColor()} ${getCapacityGlow()}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(capacityPercent, 100)}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </motion.div>

            {!draft && !loading && (
              <p className="text-neutral-500 mb-6">No AI draft yet. Use &quot;Generate / refresh draft&quot; above.</p>
            )}

            {draft && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-xl overflow-hidden"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05)',
                }}
              >
                <div className="grid grid-cols-[80px_1fr_180px_80px_60px] gap-4 px-6 py-4 border-b border-white/5">
                  <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider">K2 Score</span>
                  <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Ticket</span>
                  <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Assignee</span>
                  <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider text-center">SP</span>
                  <span className="text-xs font-medium text-neutral-400 uppercase tracking-wider text-center">Include</span>
                </div>

                <div className="divide-y divide-white/5">
                  {tickets.map((ticket, index) => (
                    <motion.div
                      key={ticket.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.08 }}
                      whileHover={{
                        scale: 1.005,
                        backgroundColor: 'rgba(255,255,255,0.02)',
                      }}
                      className="grid grid-cols-[80px_1fr_180px_80px_60px] gap-4 px-6 py-4 items-center cursor-pointer transition-colors"
                      onClick={() => toggleTicket(ticket.id)}
                    >
                      <div>
                        <span
                          className={`inline-flex items-center justify-center w-12 h-7 rounded-md text-sm font-mono font-bold ${getScoreBadgeStyle(ticket.k2Score)}`}
                        >
                          {ticket.k2Score}
                        </span>
                      </div>
                      <span className={`font-medium ${ticket.included ? 'text-white' : 'text-neutral-500'}`}>{ticket.title}</span>
                      <span className={`text-sm ${ticket.included ? 'text-neutral-300' : 'text-neutral-500'}`}>{ticket.assignee}</span>
                      <span
                        className={`text-center font-mono font-medium ${ticket.included ? 'text-white' : 'text-neutral-500'}`}
                      >
                        {ticket.storyPoints}
                      </span>
                      <div className="flex justify-center">
                        <motion.button
                          type="button"
                          whileTap={{ scale: 0.9 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleTicket(ticket.id);
                          }}
                          className={`w-6 h-6 rounded-md flex items-center justify-center transition-all ${
                            ticket.included
                              ? 'bg-cyan-500 text-white shadow-[0_0_10px_rgba(34,211,238,0.4)]'
                              : 'bg-white/5 border border-white/10 text-transparent hover:border-white/20'
                          }`}
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </motion.button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex justify-end mt-8"
            >
              <motion.button
                type="button"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowModal(true)}
                disabled={!draft || tickets.length === 0}
                className="px-8 py-4 rounded-xl font-semibold text-lg bg-cyan-500 text-white shadow-[0_0_30px_rgba(34,211,238,0.4)] hover:shadow-[0_0_40px_rgba(34,211,238,0.6)] transition-shadow disabled:opacity-40"
              >
                Approve Sprint &rarr;
              </motion.button>
            </motion.div>
          </>
        )}

        <AnimatePresence>
          {showModal && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50"
                style={{
                  backgroundColor: 'rgba(2, 8, 23, 0.8)',
                  backdropFilter: 'blur(8px)',
                }}
                onClick={() => setShowModal(false)}
                role="presentation"
              />

              <motion.div
                initial={{ opacity: 0, y: 100, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 100, scale: 0.95 }}
                transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md p-8 rounded-2xl"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05), 0 25px 50px -12px rgba(0,0,0,0.5)',
                }}
              >
                <h2 className="text-2xl font-bold text-white mb-4 font-[family-name:var(--font-syne)]">Confirm Sprint</h2>
                <p className="text-neutral-300 mb-8">
                  Stage Monday.com and calendar actions in the review queue for <strong className="text-white">{displayName}</strong>?
                </p>

                <div className="flex gap-4">
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="flex-1 py-3 rounded-xl font-semibold bg-cyan-500 text-white shadow-[0_0_20px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_rgba(34,211,238,0.6)] transition-shadow disabled:opacity-50"
                  >
                    {isApproving ? (
                      <motion.span animate={{ opacity: [1, 0.5, 1] }} transition={{ duration: 1, repeat: Infinity }}>
                        Staging…
                      </motion.span>
                    ) : (
                      'Confirm'
                    )}
                  </motion.button>
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowModal(false)}
                    className="flex-1 py-3 rounded-xl font-semibold text-neutral-300 hover:text-white border border-white/10 hover:border-white/20 transition-colors"
                  >
                    Cancel
                  </motion.button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
