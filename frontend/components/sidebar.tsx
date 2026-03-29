'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  Zap,
  FileText,
  Phone,
  CheckSquare,
} from 'lucide-react';
import { apiJson } from '@/lib/api';

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/dashboard/standup', icon: Users, label: 'Standup Feed' },
  { href: '/dashboard/blockers', icon: AlertTriangle, label: 'Blocker Radar' },
  { href: '/dashboard/sprint', icon: Zap, label: 'Sprint Planner' },
  { href: '/dashboard/reports', icon: FileText, label: 'Status Reports' },
  { href: '/dashboard/voice', icon: Phone, label: 'Voice Agent' },
  { href: '/dashboard/review', icon: CheckSquare, label: 'Review Queue', badgeKey: true as const },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [pending, setPending] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const items = await apiJson<unknown[]>('/api/v1/review');
        if (!cancelled) setPending(Array.isArray(items) ? items.length : 0);
      } catch {
        if (!cancelled) setPending(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-[260px] z-50 flex flex-col"
      style={{
        background: 'rgba(2, 8, 23, 0.8)',
        backdropFilter: 'blur(30px)',
        WebkitBackdropFilter: 'blur(30px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      <div className="p-6 flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{
            border: '1.5px solid #22d3ee',
            background: 'rgba(34, 211, 238, 0.1)',
          }}
        >
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-syne)', color: '#22d3ee' }}>
            PM
          </span>
        </div>
        <span className="text-xl font-semibold text-white" style={{ fontFamily: 'var(--font-syne)' }}>
          PilotPM
        </span>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            const badge = item.badgeKey && pending !== null && pending > 0 ? pending : item.badgeKey ? undefined : undefined;

            return (
              <li key={item.href}>
                <Link href={item.href}>
                  <motion.div
                    className="relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer group"
                    style={{
                      borderLeft: isActive ? '2px solid #22d3ee' : '2px solid transparent',
                      background: isActive ? 'rgba(34, 211, 238, 0.08)' : 'transparent',
                    }}
                    whileHover={{ x: 4 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  >
                    <Icon
                      size={18}
                      className={isActive ? 'text-[#22d3ee]' : 'text-neutral-400 group-hover:text-white'}
                    />
                    <span
                      className={`text-sm ${isActive ? 'text-white font-medium' : 'text-neutral-400 group-hover:text-white'}`}
                    >
                      {item.label}
                    </span>
                    {item.badgeKey && pending !== null && pending > 0 && (
                      <span
                        className="ml-auto text-xs font-medium px-1.5 py-0.5 rounded-full"
                        style={{ background: '#EF4444', color: 'white' }}
                      >
                        {pending}
                      </span>
                    )}
                  </motion.div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div
        className="p-4 mx-3 mb-4 rounded-lg flex items-center gap-3 cursor-pointer hover:bg-white/5"
        style={{
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        }}
        onClick={() => router.push('/login')}
        role="presentation"
      >
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-medium"
          style={{
            background: 'linear-gradient(135deg, #22d3ee 0%, #0ea5e9 100%)',
            color: '#020817',
          }}
        >
          A
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">Alex Chen</p>
          <p className="text-xs text-neutral-500">Product Manager</p>
        </div>
        <span
          className="text-xs font-medium px-2 py-0.5 rounded"
          style={{ background: 'rgba(34, 211, 238, 0.15)', color: '#22d3ee' }}
        >
          PM
        </span>
      </div>
    </aside>
  );
}
