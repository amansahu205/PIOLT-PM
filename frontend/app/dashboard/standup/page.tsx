'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { RefreshCw } from 'lucide-react';
import { apiJson, ApiError } from '@/lib/api';

type DigestRow = {
  engineer: string;
  status: string;
  did?: string;
  working_on?: string;
  blocker?: string | null;
  sources?: string[];
};

type StandupDoc = {
  generated_at?: string;
  digest?: DigestRow[];
  summary?: string;
};

function statusStyle(status: string) {
  if (status === 'blocked')
    return { bg: 'rgba(239, 68, 68, 0.15)', text: '#EF4444', border: '#EF4444', label: 'Blocked' };
  if (status === 'check_in')
    return { bg: 'rgba(245, 158, 11, 0.15)', text: '#F59E0B', border: '#F59E0B', label: 'Check in' };
  return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981', border: '#22d3ee', label: 'On track' };
}

export default function StandupDigestPage() {
  const [data, setData] = useState<StandupDoc | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setErr('');
    try {
      const doc = await apiJson<StandupDoc>('/api/v1/standup/today');
      setData(doc);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Failed to load standup');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const regenerate = async () => {
    setBusy(true);
    setErr('');
    try {
      await apiJson('/api/v1/standup/generate', { method: 'POST', json: {} });
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Generate failed');
    } finally {
      setBusy(false);
    }
  };

  const digest = data?.digest ?? [];
  const genAt = data?.generated_at
    ? new Date(data.generated_at).toLocaleString()
    : '—';

  return (
    <div className="min-h-screen bg-[#020817]">
      <Sidebar />

      <main className="ml-[260px] p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-[32px] font-semibold text-white" style={{ fontFamily: 'var(--font-syne)' }}>
            Standup Digest
          </h1>
          <motion.button
            type="button"
            onClick={regenerate}
            disabled={busy || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-full text-sm"
            style={{
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: '#F59E0B',
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span style={{ fontFamily: 'var(--font-mono)' }}>Cached · {genAt}</span>
            <RefreshCw size={14} className={busy ? 'animate-spin' : ''} />
            <span>{busy ? 'Generating…' : 'Regenerate'}</span>
          </motion.button>
        </div>

        {err && <p className="text-red-400 mb-4">{err}</p>}

        {loading ? (
          <p className="text-neutral-500">Loading…</p>
        ) : (
          <div className="space-y-4">
            {digest.length === 0 ? (
              <p className="text-neutral-500">No digest yet. Click Regenerate.</p>
            ) : (
              digest.map((row, index) => {
                const st = statusStyle(row.status);
                return (
                  <motion.div
                    key={`${row.engineer}-${index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.08 }}
                    className="rounded-xl p-6"
                    style={{
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderLeft: `3px solid ${st.border}`,
                    }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white" style={{ fontFamily: 'var(--font-syne)' }}>
                        {row.engineer}
                      </h3>
                      <span
                        className="px-3 py-1 rounded-full text-xs font-medium"
                        style={{ background: st.bg, color: st.text }}
                      >
                        {st.label}
                      </span>
                    </div>
                    {row.did && (
                      <p className="text-sm text-neutral-300 mb-2">
                        <span className="text-neutral-500">Did: </span>
                        {row.did}
                      </p>
                    )}
                    {row.working_on && (
                      <p className="text-sm text-neutral-300 mb-2">
                        <span className="text-neutral-500">Working on: </span>
                        {row.working_on}
                      </p>
                    )}
                    {row.blocker && (
                      <p className="text-sm text-red-300 mt-2">Blocker: {row.blocker}</p>
                    )}
                    {row.sources && row.sources.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {row.sources.map((s, i) => (
                          <span
                            key={i}
                            className="text-xs px-2 py-1 rounded"
                            style={{ background: 'rgba(34,211,238,0.1)', color: '#22d3ee' }}
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </motion.div>
                );
              })
            )}
            {data?.summary && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 rounded-xl text-sm text-neutral-400 border border-white/10"
              >
                {data.summary}
              </motion.div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
