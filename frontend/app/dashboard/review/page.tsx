'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { ChevronDown, Check, X, Pencil, CheckCircle2 } from 'lucide-react';
import { apiJson, ApiError } from '@/lib/api';

type ActionType = 'SLACK_MESSAGE' | 'MONDAY_BOARD' | 'GMAIL_SEND' | 'CALENDAR_EVENT';

interface ActionCard {
  id: string;
  type: ActionType;
  title: string;
  content: string;
  reasoning: string[];
}

const typeConfig: Record<
  ActionType,
  {
    label: string;
    color: string;
    bg: string;
  }
> = {
  SLACK_MESSAGE: { label: 'SLACK_MESSAGE', color: 'text-cyan-400', bg: 'bg-cyan-500/20' },
  MONDAY_BOARD: { label: 'MONDAY_BOARD', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  GMAIL_SEND: { label: 'GMAIL_SEND', color: 'text-red-400', bg: 'bg-red-500/20' },
  CALENDAR_EVENT: { label: 'CALENDAR_EVENT', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
};

const apiTypeToUi = (raw: string | undefined): ActionType => {
  const t = (raw || '').toLowerCase();
  if (t.includes('slack')) return 'SLACK_MESSAGE';
  if (t.includes('monday')) return 'MONDAY_BOARD';
  if (t.includes('gmail') || t.includes('email') || t.includes('send')) return 'GMAIL_SEND';
  if (t.includes('calendar')) return 'CALENDAR_EVENT';
  return 'SLACK_MESSAGE';
};

function normalizeReasoning(r: unknown): string[] {
  if (Array.isArray(r)) return r.map((x) => String(x));
  if (typeof r === 'string') return r.split('\n').filter(Boolean);
  return [];
}

function mapDocToCard(doc: Record<string, unknown>): ActionCard {
  const id = String(doc.id || '');
  const type = apiTypeToUi(typeof doc.type === 'string' ? doc.type : undefined);
  const title = String(doc.title || 'Untitled action');
  const content = String(doc.description ?? '');
  const reasoning = normalizeReasoning(doc.reasoning);
  return { id, type, title, content, reasoning };
}

export default function ReviewQueuePage() {
  const [actions, setActions] = useState<ActionCard[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editedContents, setEditedContents] = useState<Record<string, string>>({});
  const [approvingAll, setApprovingAll] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr('');
    try {
      const list = await apiJson<Record<string, unknown>[]>('/api/v1/review');
      const mapped = (Array.isArray(list) ? list : []).map(mapDocToCard);
      setActions(mapped);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleApprove = async (id: string) => {
    setBusyId(id);
    setErr('');
    try {
      await apiJson(`/api/v1/review/${encodeURIComponent(id)}/approve`, { method: 'POST', json: {} });
      setActions((prev) => prev.filter((a) => a.id !== id));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Approve failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleReject = async (id: string) => {
    const reason = typeof window !== 'undefined' ? window.prompt('Reason (optional)', '') || '' : '';
    setBusyId(id);
    setErr('');
    try {
      await apiJson(`/api/v1/review/${encodeURIComponent(id)}/reject`, {
        method: 'POST',
        json: { reason },
      });
      setActions((prev) => prev.filter((a) => a.id !== id));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Reject failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleApproveAll = async () => {
    setApprovingAll(true);
    setErr('');
    try {
      for (const action of actions) {
        await apiJson(`/api/v1/review/${encodeURIComponent(action.id)}/approve`, { method: 'POST', json: {} });
        setActions((prev) => prev.filter((a) => a.id !== action.id));
      }
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Approve all failed');
      await load();
    } finally {
      setApprovingAll(false);
    }
  };

  const pendingCount = actions.length;

  return (
    <div className="min-h-screen bg-[#020817] flex">
      <Sidebar />

      <main className="flex-1 ml-[260px] p-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-white font-[family-name:var(--font-syne)]">Review Queue</h1>
            <AnimatePresence mode="wait">
              {pendingCount > 0 && (
                <motion.span
                  key={pendingCount}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  className="px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-medium flex items-center gap-2"
                >
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  {pendingCount} pending
                </motion.span>
              )}
            </AnimatePresence>
          </div>

          {pendingCount > 0 && (
            <motion.button
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleApproveAll}
              disabled={approvingAll}
              className="px-5 py-2.5 rounded-lg bg-cyan-500 text-black font-semibold text-sm flex items-center gap-2 hover:bg-cyan-400 transition-colors disabled:opacity-50"
            >
              {approvingAll ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full"
                  />
                  Approving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Approve All ({pendingCount})
                </>
              )}
            </motion.button>
          )}
        </motion.div>

        {loading && <p className="text-neutral-500 mb-4">Loading queue…</p>}
        {err && <p className="text-red-400 mb-4">{err}</p>}

        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {actions.map((action, index) => {
              const config = typeConfig[action.type];
              const isExpanded = expandedIds.has(action.id);
              const isEditing = editingId === action.id;
              const currentContent = editedContents[action.id] ?? action.content;
              const isBusy = busyId === action.id;

              return (
                <motion.div
                  key={action.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{
                    opacity: 0,
                    x: 100,
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    transition: { duration: 0.3 },
                  }}
                  transition={{ delay: index * 0.1 }}
                  className="rounded-xl bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] p-6 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
                >
                  <div className="flex items-start justify-between mb-4">
                    <span className={`px-3 py-1 rounded-md text-xs font-mono font-medium ${config.color} ${config.bg}`}>
                      {config.label}
                    </span>
                  </div>

                  <h3 className="text-xl font-semibold text-white mb-4 font-[family-name:var(--font-syne)]">{action.title}</h3>

                  <div
                    className={`relative rounded-lg bg-black/40 border p-4 mb-4 transition-colors ${
                      isEditing ? 'border-cyan-500/50 shadow-[0_0_20px_rgba(34,211,238,0.1)]' : 'border-white/[0.06]'
                    }`}
                  >
                    <textarea
                      value={currentContent}
                      onChange={(e) => setEditedContents({ ...editedContents, [action.id]: e.target.value })}
                      onFocus={() => setEditingId(action.id)}
                      onBlur={() => setEditingId(null)}
                      className="w-full bg-transparent text-neutral-300 font-mono text-sm resize-none outline-none min-h-[80px]"
                      style={{ caretColor: '#22d3ee' }}
                      disabled={isBusy}
                    />
                    {isEditing && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="absolute bottom-2 right-2 text-xs text-cyan-400/60"
                      >
                        Local edit (not synced to server)
                      </motion.div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleExpand(action.id)}
                    className="flex items-center gap-2 text-sm text-neutral-400 hover:text-neutral-200 transition-colors mb-4"
                  >
                    <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
                      <ChevronDown className="w-4 h-4" />
                    </motion.div>
                    Agent Reasoning
                  </button>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="rounded-lg bg-black/60 border border-white/[0.04] p-4 mb-4">
                          {action.reasoning.length ? (
                            action.reasoning.map((line, i) => (
                              <p key={i} className="text-sm text-neutral-400 font-mono leading-relaxed">
                                {line}
                              </p>
                            ))
                          ) : (
                            <p className="text-sm text-neutral-500">No reasoning stored.</p>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="flex items-center gap-3 flex-wrap">
                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleApprove(action.id)}
                      disabled={isBusy}
                      className="px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 text-sm font-medium flex items-center gap-2 hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
                    >
                      <Check className="w-4 h-4" />
                      {isBusy ? '…' : 'Approve'}
                    </motion.button>

                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setEditingId(action.id)}
                      className="px-4 py-2 rounded-lg border border-white/[0.08] text-neutral-300 text-sm font-medium flex items-center gap-2 hover:bg-white/[0.04] transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                      Edit
                    </motion.button>

                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleReject(action.id)}
                      disabled={isBusy}
                      className="px-4 py-2 rounded-lg text-red-400 text-sm font-medium flex items-center gap-2 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                    >
                      <X className="w-4 h-4" />
                      Reject
                    </motion.button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {actions.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.4 }}
                className="w-20 h-20 rounded-full bg-cyan-500/20 flex items-center justify-center mb-6"
              >
                <CheckCircle2 className="w-10 h-10 text-cyan-400" />
              </motion.div>
              <h3 className="text-2xl font-semibold text-white mb-2 font-[family-name:var(--font-syne)]">All actions reviewed</h3>
              <p className="text-neutral-400">No pending actions in the queue</p>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
