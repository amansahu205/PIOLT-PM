'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '@/components/sidebar';
import { apiJson, ApiError } from '@/lib/api';

const suggestionPills = [
  "What's blocking my team?",
  'Sprint summary',
  "Who hasn't committed today?",
  'Send Friday report',
];

type VoiceContext = {
  refresh_timestamp?: string;
  sprint_name?: string;
  days_remaining?: string | number;
  velocity_pct?: string | number;
  blocker_count?: number;
  blockers_summary?: string;
  standup_summary?: string;
  recent_activity?: string;
};

type TranscriptRow = {
  id?: string;
  call_sid?: string;
  caller?: string;
  started_at?: string;
  called_at?: string;
  duration_seconds?: number | null;
  status?: string;
};

function formatDuration(sec?: number | null) {
  if (sec == null || Number.isNaN(sec)) return '—';
  const s = Math.floor(sec);
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, '0')}`;
}

function formatWhen(iso?: string) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

export default function VoiceAgentPage() {
  const [ctx, setCtx] = useState<VoiceContext | null>(null);
  const [rows, setRows] = useState<TranscriptRow[]>([]);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(true);

  const phoneDisplay = useMemo(
    () => process.env.NEXT_PUBLIC_TWILIO_PHONE || '+1 (203) 555-PILOT',
    [],
  );

  /** E.164-style dial string; display string may include spaces or vanity letters (stripped here). */
  const telHref = useMemo(() => {
    const digits = phoneDisplay.replace(/\D/g, '');
    if (!digits) return 'tel:';
    return digits.length === 11 && digits.startsWith('1') ? `tel:+${digits}` : `tel:+${digits}`;
  }, [phoneDisplay]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setErr('');
      try {
        const [c, t] = await Promise.all([
          apiJson<VoiceContext>('/api/v1/voice/context'),
          apiJson<TranscriptRow[]>('/api/v1/voice/transcripts?limit=12'),
        ]);
        if (!cancelled) {
          setCtx(c);
          setRows(Array.isArray(t) ? t : []);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof ApiError ? e.message : 'Failed to load voice data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#020817] flex">
      <Sidebar />

      <main className="flex-1 ml-[260px] p-8 flex flex-col">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-wrap items-center gap-3 mb-8"
        >
          <h1 className="text-[32px] font-bold text-white font-[family-name:var(--font-syne)]">Voice Agent</h1>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#10B981]/10 border border-[#10B981]/30">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-[#10B981]" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-[#10B981] animate-ping" />
            </div>
            <span className="text-[#10B981] text-sm font-medium">Live</span>
          </div>
        </motion.div>

        {loading && <p className="text-neutral-500 mb-4">Loading context…</p>}
        {err && <p className="text-red-400 mb-4">{err}</p>}

        {ctx && !loading && (
          <div className="mb-8 p-4 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-neutral-300 space-y-1 max-w-3xl">
            <p>
              <span className="text-neutral-500">Sprint:</span> {String(ctx.sprint_name ?? '—')}
            </p>
            <p>
              <span className="text-neutral-500">Days left:</span> {String(ctx.days_remaining ?? '—')} ·{' '}
              <span className="text-neutral-500">Velocity:</span> {String(ctx.velocity_pct ?? '—')}% ·{' '}
              <span className="text-neutral-500">Blockers:</span> {ctx.blocker_count ?? 0}
            </p>
            {ctx.refresh_timestamp && <p className="text-neutral-500 text-xs">Context {ctx.refresh_timestamp}</p>}
          </div>
        )}

        <div className="flex-1 flex flex-col items-center justify-center -mt-10">
          <div className="relative flex items-center justify-center mb-8">
            <div className="absolute w-[400px] h-[400px] rounded-full border border-[#22d3ee]/10 animate-[pulse-ring_3s_ease-out_infinite]" />
            <div className="absolute w-[300px] h-[300px] rounded-full border border-[#22d3ee]/15 animate-[pulse-ring_3s_ease-out_infinite_0.5s]" />
            <div className="absolute w-[200px] h-[200px] rounded-full border border-[#22d3ee]/20 animate-[pulse-ring_3s_ease-out_infinite_1s]" />

            <motion.a
              href={telHref}
              className="relative z-10 inline-block text-center select-none"
              aria-label={`Call ${phoneDisplay}`}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
            >
              <span
                className="text-[clamp(2rem,8vw,4rem)] font-bold text-[#22d3ee] font-[family-name:var(--font-syne)] tracking-wide whitespace-nowrap"
                style={{ textShadow: '0 0 40px rgba(34, 211, 238, 0.4)' }}
              >
                {phoneDisplay}
              </span>
            </motion.a>
          </div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="text-neutral-500 text-sm mb-12"
          >
            Powered by ElevenLabs + Twilio
          </motion.p>

          <div className="flex flex-wrap justify-center gap-3 max-w-2xl">
            {suggestionPills.map((pill, index) => (
              <motion.span
                key={pill}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.2 + index * 0.1, duration: 0.3 }}
                className="px-5 py-2.5 rounded-full bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] text-neutral-400 text-sm"
                title="Ask the agent on a live call"
              >
                {pill}
              </motion.span>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="mt-auto"
        >
          <h2 className="text-lg font-semibold text-white mb-4 font-[family-name:var(--font-syne)]">Recent calls</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {rows.length === 0 && !loading && (
              <p className="text-neutral-500 text-sm col-span-full">No calls logged yet. Dial the number to test.</p>
            )}
            {rows.map((transcript, index) => (
              <motion.div
                key={transcript.id || transcript.call_sid || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index, duration: 0.4 }}
                className="p-5 rounded-2xl bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]"
                style={{ boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05)' }}
              >
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  <span className="text-neutral-500 text-sm">{formatWhen(transcript.started_at || transcript.called_at)}</span>
                  <span className="px-2 py-0.5 rounded-full bg-white/[0.06] text-neutral-400 text-xs font-medium">
                    {formatDuration(transcript.duration_seconds)}
                  </span>
                  {transcript.status && (
                    <span className="text-xs text-cyan-500/80">{transcript.status}</span>
                  )}
                </div>
                <p className="text-neutral-300 text-sm leading-relaxed font-[family-name:var(--font-jetbrains-mono)]">
                  {transcript.caller || 'Unknown caller'}
                  {transcript.call_sid && (
                    <span className="block text-neutral-500 text-xs mt-1 truncate">Sid {transcript.call_sid}</span>
                  )}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </main>

      <style jsx global>{`
        @keyframes pulse-ring {
          0% {
            transform: scale(0.8);
            opacity: 0.8;
          }
          100% {
            transform: scale(1.4);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}
