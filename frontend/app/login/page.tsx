'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { apiUrl, getApiBase } from '@/lib/api';
import { setToken } from '@/lib/auth';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/dashboard';

  const [email, setEmail] = useState('pm@pilotpm.demo');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const res = await fetch(apiUrl('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(typeof data.detail === 'string' ? data.detail : 'Invalid credentials');
        setIsLoading(false);
        return;
      }
      const token = data.access_token as string | undefined;
      if (!token) {
        setError('No token in response');
        setIsLoading(false);
        return;
      }
      setToken(token);
      setIsSuccess(true);
      setTimeout(() => {
        router.push(redirectTo);
      }, 600);
    } catch (err) {
      const base = getApiBase();
      const hint = err instanceof Error && err.message ? ` ${err.message}` : '';
      let port = '8001';
      try {
        const u = new URL(base);
        if (u.port) port = u.port;
        const host = u.hostname;
        const isLocal =
          host === 'localhost' || host === '127.0.0.1' || host === '::1';
        if (!isLocal) {
          const appOrigin =
            typeof window !== 'undefined' ? window.location.origin : 'https://your-app.vercel.app';
          setError(
            `Cannot reach API at ${base}.${hint} If the API is up (open ${base}/health in a new tab), add your frontend origin to CORS_ORIGINS on the API host — e.g. ["${appOrigin}","http://localhost:3000"] as JSON — then redeploy the API.`,
          );
          setIsLoading(false);
          return;
        }
      } catch {
        /* keep default */
      }
      setError(
        `Cannot reach API at ${base}.${hint} From repo root run: uv run uvicorn app.main:app --reload --host 127.0.0.1 --port ${port}`,
      );
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#020817]">
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute -top-1/2 -left-1/2 w-full h-full rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(34,211,238,0.05) 0%, transparent 70%)',
          }}
          animate={{
            x: [0, 100, 50, 0],
            y: [0, 50, 100, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      </div>

      <AnimatePresence>
        {!isSuccess && (
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="relative z-10 w-full max-w-[420px] mx-4"
          >
            <div
              className="rounded-2xl p-8"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                backdropFilter: 'blur(40px)',
                WebkitBackdropFilter: 'blur(40px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 0 80px rgba(34, 211, 238, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
              }}
            >
              <div className="flex flex-col items-center mb-8">
                <div
                  className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
                  style={{
                    border: '2px solid #22d3ee',
                    background: 'rgba(34, 211, 238, 0.1)',
                  }}
                >
                  <span
                    className="text-xl font-bold"
                    style={{ fontFamily: 'var(--font-syne)', color: '#22d3ee' }}
                  >
                    PM
                  </span>
                </div>
                <h1
                  className="text-2xl font-bold text-white"
                  style={{ fontFamily: 'var(--font-syne)' }}
                >
                  PilotPM
                </h1>
                <p className="text-sm mt-1" style={{ color: 'rgba(34, 211, 238, 0.7)' }}>
                  AI PM Orchestrator
                </p>
              </div>

              <div className="w-full h-px mb-6" style={{ background: 'rgba(255, 255, 255, 0.1)' }} />

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full h-11 px-4 rounded-lg text-white outline-none"
                    style={{
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: error ? '1px solid #EF4444' : '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter password"
                      className="w-full h-11 px-4 pr-12 rounded-lg text-white outline-none"
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: error ? '1px solid #EF4444' : '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {error && <p className="text-sm text-red-400">{error}</p>}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-11 text-base font-semibold"
                  style={{
                    background: '#22d3ee',
                    color: '#020817',
                  }}
                >
                  {isLoading ? <Spinner className="size-5 text-[#020817]" /> : 'Sign in'}
                </Button>
              </form>

              <p className="text-center text-xs mt-6" style={{ color: 'rgba(255, 255, 255, 0.4)' }}>
                Demo: pm@pilotpm.demo / pilotpm2026
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isSuccess && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
            <p className="text-white font-medium">Welcome back!</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#020817] flex items-center justify-center text-neutral-500">Loading…</div>}>
      <LoginForm />
    </Suspense>
  );
}
