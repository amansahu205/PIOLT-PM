'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { apiJson, ApiError } from '@/lib/api';

type BlockerApi = {
  id?: string | null;
  severity?: string;
  type?: string;
  engineer?: string;
  description?: string;
  blocked_for?: string;
  draft_ping?: string;
  resolver?: string;
};

const severityStyles: Record<string, { badge: string; glow: string }> = {
  CRITICAL: {
    badge: 'bg-red-500/20 text-red-400 border-red-500/30 shadow-[0_0_20px_rgba(239,68,68,0.3)]',
    glow: 'shadow-[0_0_30px_rgba(239,68,68,0.15)]',
  },
  MEDIUM: {
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30 shadow-[0_0_12px_rgba(245,158,11,0.2)]',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.08)]',
  },
  WATCH: {
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.2)]',
    glow: '',
  },
};

function sevKey(s?: string): keyof typeof severityStyles {
  const u = (s || '').toUpperCase();
  if (u.includes('CRITICAL') || u === 'HIGH') return 'CRITICAL';
  if (u.includes('WATCH') || u === 'LOW') return 'WATCH';
  return 'MEDIUM';
}

export default function BlockerRadarPage() {
  const [blockers, setBlockers] = useState<BlockerApi[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setErr('');
    try {
      const list = await apiJson<BlockerApi[]>('/api/v1/blockers');
      setBlockers(Array.isArray(list) ? list : []);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Failed to load blockers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleScan = async () => {
    setIsScanning(true);
    setErr('');
    try {
      const list = await apiJson<BlockerApi[]>('/api/v1/blockers/scan', { method: 'POST', json: {} });
      setBlockers(Array.isArray(list) ? list : []);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await apiJson(`/api/v1/blockers/${encodeURIComponent(id)}/dismiss`, {
        method: 'PATCH',
        json: { reason: 'dismissed_from_ui' },
      });
      setBlockers((prev) => prev.filter((b) => (b.id || '') !== id));
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Dismiss failed');
    }
  };

  return (
    <div className="min-h-screen bg-[#020817] flex">
      <Sidebar />

      <motion.main
        className="flex-1 ml-[260px] p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-4">
            <h1 className="font-syne text-[32px] font-bold text-white" style={{ letterSpacing: '-0.02em' }}>Blocker Radar</h1>
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <motion.div
                className="w-2 h-2 rounded-full bg-emerald-500"
                animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <span>API-connected</span>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleScan}
            disabled={isScanning || loading}
            className="px-4 py-2 rounded-lg bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] text-white text-sm font-medium hover:bg-white/[0.08] transition-colors disabled:opacity-50"
          >
            {isScanning ? (
              <span className="flex items-center gap-2">
                <motion.div
                  className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
                Scanning...
              </span>
            ) : (
              'Scan Now'
            )}
          </motion.button>
        </motion.div>

        {err && <p className="text-red-400 mb-4">{err}</p>}
        {loading && <p className="text-neutral-500">Loading…</p>}

        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {!loading &&
              blockers.map((blocker, index) => {
                const id = blocker.id || String(index);
                const sk = sevKey(blocker.severity);
                const st = severityStyles[sk];
                return (
                  <motion.div
                    key={id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: 300 }}
                    whileHover={{ y: -2 }}
                    className={`p-6 rounded-2xl backdrop-blur-2xl ${st.glow}`}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      backdropFilter: 'blur(24px)',
                      WebkitBackdropFilter: 'blur(24px)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: `inset 0 1px 0 rgba(255,255,255,0.06)`,
                      transition: 'border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease',
                    }}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${st.badge}`}>
                        {blocker.severity || sk}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-white/[0.06] text-neutral-300 border border-white/[0.08]">
                        {blocker.type || 'BLOCKER'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-white font-medium">{blocker.engineer || '—'}</span>
                      {blocker.blocked_for && (
                        <span className="px-2 py-0.5 rounded-md text-xs font-mono bg-white/[0.06] text-neutral-400 border border-white/[0.08]">
                          {blocker.blocked_for}
                        </span>
                      )}
                    </div>
                    <p className="text-neutral-400 text-sm mb-4">{blocker.description || ''}</p>
                    {blocker.draft_ping && (
                      <div className="p-4 rounded-xl bg-black/30 border border-white/[0.06] mb-4">
                        <p className="font-mono text-sm text-neutral-300">{blocker.draft_ping}</p>
                      </div>
                    )}
                    <div className="flex items-center gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="button"
                        className="px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-400 text-sm font-medium border border-cyan-500/30"
                        disabled
                        title="Queued via Review after approve in product"
                      >
                        Ping {blocker.resolver || 'resolver'}
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="button"
                        onClick={() => handleDismiss(id)}
                        className="px-4 py-2 rounded-lg bg-transparent text-neutral-400 text-sm font-medium border border-white/[0.08] hover:bg-white/[0.04]"
                      >
                        Dismiss
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
          </AnimatePresence>

          {!loading && blockers.length === 0 && (
            <p className="text-center text-neutral-500 py-16">No active blockers. Run Scan or check integrations.</p>
          )}
        </div>
      </motion.main>
    </div>
  );
}
