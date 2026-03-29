'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { apiJson, ApiError } from '@/lib/api';
import { BlockerRadarCard } from '@/components/ui/blocker-radar-card';

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
                return (
                  <BlockerRadarCard
                    key={id}
                    {...blocker}
                    onDismiss={() => handleDismiss(id)}
                    index={index}
                  />
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
