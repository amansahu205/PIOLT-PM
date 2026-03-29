'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  GitPullRequest,
  Zap,
  RefreshCw,
  Phone,
  ArrowRight,
} from 'lucide-react';
import Sidebar from '@/components/sidebar';
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

function useCounter(end: number, duration: number = 1500) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let startTime: number | null = null;
    let animationFrame: number;
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) animationFrame = requestAnimationFrame(animate);
    };
    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [end, duration]);
  return count;
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  delay,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: 'red' | 'amber' | 'cyan';
  delay: number;
}) {
  const count = useCounter(value);
  const colors = {
    red: { glow: 'rgba(239, 68, 68, 0.3)', text: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)' },
    amber: { glow: 'rgba(245, 158, 11, 0.3)', text: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' },
    cyan: { glow: 'rgba(34, 211, 238, 0.3)', text: '#22d3ee', bg: 'rgba(34, 211, 238, 0.1)' },
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.25, 0.1, 0.25, 1] }}
      whileHover={{ y: -2 }}
      className="relative p-6 rounded-xl"
      style={{
        background: 'rgba(255, 255, 255, 0.03)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: `inset 0 1px 0 rgba(255,255,255,0.06), 0 0 40px ${colors[color].glow}`,
        transition: 'all 0.2s ease',
      }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="p-2.5 rounded-lg" style={{ background: colors[color].bg }}>
          <Icon size={20} style={{ color: colors[color].text }} />
        </div>
      </div>
      <p className="text-4xl font-bold mb-1" style={{ fontFamily: 'var(--font-syne)', color: colors[color].text }}>
        {count}
        {label === 'Sprint Velocity' && ' pts'}
      </p>
      <p className="text-sm text-neutral-400">{label}</p>
    </motion.div>
  );
}

function mapStatus(s: string): { key: 'blocked' | 'on-track' | 'check-in'; label: string } {
  if (s === 'blocked') return { key: 'blocked', label: 'BLOCKED' };
  if (s === 'check_in') return { key: 'check-in', label: 'CHECK IN' };
  return { key: 'on-track', label: 'ON TRACK' };
}

export default function DashboardPage() {
  const [standup, setStandup] = useState<StandupDoc | null>(null);
  const [blockerCount, setBlockerCount] = useState(0);
  const [prCount, setPrCount] = useState(0);
  const [velocity, setVelocity] = useState(0);
  const [sprintLabel, setSprintLabel] = useState('Sprint');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setErr('');
    try {
      const [blockers, sprint, su] = await Promise.all([
        apiJson<{ id?: string }[]>('/api/v1/blockers'),
        apiJson<{ sprint_name?: string; velocity_pct?: number; tickets?: unknown[] }>('/api/v1/sprint/current'),
        apiJson<StandupDoc>('/api/v1/standup/today'),
      ]);
      setBlockerCount(Array.isArray(blockers) ? blockers.length : 0);
      const tickets = sprint?.tickets;
      setPrCount(Array.isArray(tickets) ? tickets.length : 0);
      setVelocity(Math.round(sprint?.velocity_pct ?? 0));
      if (sprint?.sprint_name) setSprintLabel(sprint.sprint_name);
      setStandup(su);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleRefreshStandup = async () => {
    setRefreshing(true);
    try {
      await apiJson('/api/v1/standup/generate', { method: 'POST', json: {} });
      const su = await apiJson<StandupDoc>('/api/v1/standup/today');
      setStandup(su);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Regenerate failed');
    } finally {
      setRefreshing(false);
    }
  };

  const digest = standup?.digest ?? [];
  const genAt = standup?.generated_at
    ? new Date(standup.generated_at).toLocaleString()
    : '—';

  return (
    <div className="min-h-screen bg-[#020817]">
      <Sidebar />

      <motion.main
        className="ml-[260px] min-h-screen p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <div className="flex items-center justify-between mb-8">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
            className="text-[32px] font-bold text-white"
            style={{ fontFamily: 'var(--font-syne)', letterSpacing: '-0.02em' }}
          >
            Good morning, Alex
          </motion.h1>
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="px-4 py-2 rounded-full text-sm font-medium"
            style={{
              background: 'rgba(34, 211, 238, 0.1)',
              border: '1px solid rgba(34, 211, 238, 0.2)',
              color: '#22d3ee',
            }}
          >
            {sprintLabel}
          </motion.div>
        </div>

        {err && <p className="text-red-400 text-sm mb-4">{err}</p>}

        <div className="grid grid-cols-3 gap-6 mb-8">
          <StatCard label="Active Blockers" value={blockerCount} icon={TrendingUp} color="red" delay={0.1} />
          <StatCard label="PRs Awaiting Review" value={prCount} icon={GitPullRequest} color="amber" delay={0.2} />
          <StatCard label="Sprint Velocity" value={velocity || 34} icon={Zap} color="cyan" delay={0.3} />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24, duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
          className="rounded-xl p-6 mb-8"
          style={{
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 0 40px rgba(34,211,238,0.04)',
          }}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-white" style={{ fontFamily: 'var(--font-syne)' }}>
                Today&apos;s Standup
              </h2>
              <span className="text-sm text-neutral-500">Generated {genAt}</span>
            </div>
            <button
              type="button"
              onClick={handleRefreshStandup}
              disabled={loading || refreshing}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-neutral-400 hover:text-white transition-colors disabled:opacity-50"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              {refreshing ? 'Regenerating…' : 'Refresh'}
            </button>
          </div>

          {loading ? (
            <p className="text-neutral-500">Loading digest…</p>
          ) : digest.length === 0 ? (
            <p className="text-neutral-500">No engineers in digest yet. Try Refresh to generate.</p>
          ) : (
            <div className="space-y-4">
              {digest.map((row, i) => {
                const m = mapStatus(row.status);
                const borderColors = {
                  blocked: '#EF4444',
                  'on-track': '#22d3ee',
                  'check-in': '#F59E0B',
                };
                const pillColors = {
                  blocked: { bg: 'rgba(239, 68, 68, 0.15)', text: '#EF4444', border: 'rgba(239,68,68,0.3)', glow: '0 0 12px rgba(239,68,68,0.2)' },
                  'on-track': { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981', border: 'rgba(16,185,129,0.3)', glow: 'none' },
                  'check-in': { bg: 'rgba(245, 158, 11, 0.15)', text: '#F59E0B', border: 'rgba(245,158,11,0.3)', glow: 'none' },
                };
                const msg = [row.did, row.working_on].filter(Boolean).join(' · ') || standup?.summary || '';
                return (
                  <motion.div
                    key={`${row.engineer}-${i}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.08 * i, ease: [0.25, 0.1, 0.25, 1] }}
                    whileHover={{ y: -2 }}
                    className="p-5 rounded-xl"
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      backdropFilter: 'blur(24px)',
                      WebkitBackdropFilter: 'blur(24px)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderLeft: `3px solid ${borderColors[m.key]}`,
                      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)',
                      transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold text-white">{row.engineer}</h4>
                      <span
                        className="text-xs font-medium px-2.5 py-1 rounded-full"
                        style={{
                          background: pillColors[m.key].bg,
                          color: pillColors[m.key].text,
                          border: `1px solid ${pillColors[m.key].border}`,
                          boxShadow: pillColors[m.key].glow,
                        }}
                      >
                        {m.label}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-300 mb-3 leading-relaxed">{msg}</p>
                    {row.blocker && (
                      <p className="text-sm text-red-300/90 mb-2">Blocker: {row.blocker}</p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {(row.sources || []).map((tag, j) => (
                        <span
                          key={j}
                          className="text-xs px-2 py-1 rounded"
                          style={{
                            fontFamily: 'var(--font-mono, monospace)',
                            background: 'rgba(34, 211, 238, 0.1)',
                            color: '#22d3ee',
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <Link
            href="/dashboard/voice"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-all hover:scale-[1.02]"
            style={{
              background: 'linear-gradient(135deg, #22d3ee 0%, #0ea5e9 100%)',
              color: '#020817',
              boxShadow: '0 0 30px rgba(34, 211, 238, 0.4)',
            }}
          >
            <Phone size={16} />
            Voice Agent
          </Link>
          <Link
            href="/dashboard/blockers"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm text-neutral-300 hover:text-white transition-colors"
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            View All Blockers
            <ArrowRight size={16} />
          </Link>
        </motion.div>
      </motion.main>
    </div>
  );
}
