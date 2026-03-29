'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { RefreshCw } from 'lucide-react';
import { apiJson, ApiError } from '@/lib/api';
import { EngineerStatusCard } from '@/components/ui/engineer-status-card';

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
    return { bg: 'rgba(239, 68, 68, 0.15)', text: '#EF4444', border: 'rgba(239,68,68,0.3)', glow: '0 0 12px rgba(239,68,68,0.2)', label: 'Blocked' };
  if (status === 'check_in')
    return { bg: 'rgba(245, 158, 11, 0.15)', text: '#F59E0B', border: 'rgba(245,158,11,0.3)', glow: 'none', label: 'Check in' };
  return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981', border: 'rgba(16,185,129,0.3)', glow: 'none', label: 'On track' };
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

      <motion.main
        className="ml-[260px] p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-[32px] font-bold text-white" style={{ fontFamily: 'var(--font-syne)', letterSpacing: '-0.02em' }}>
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
              digest.map((row, index) => (
                  <EngineerStatusCard 
                    key={`${row.engineer}-${index}`}
                    {...row}
                    index={index}
                  />
              ))
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
      </motion.main>
    </div>
  );
}
