import { motion } from 'framer-motion';

export interface BlockerRadarCardProps {
  id?: string | null;
  severity?: string;
  type?: string;
  engineer?: string;
  description?: string;
  blocked_for?: string;
  draft_ping?: string;
  resolver?: string;
  onDismiss: () => void;
  index: number;
}

export function BlockerRadarCard({
  id,
  severity,
  type,
  engineer,
  description,
  blocked_for,
  draft_ping,
  resolver,
  onDismiss,
  index
}: BlockerRadarCardProps) {

  const uSev = (severity || '').toUpperCase();
  const isCritical = uSev.includes('CRITICAL') || uSev === 'HIGH';
  const isWatch = uSev.includes('WATCH') || uSev === 'LOW';

  const sevConfig = {
    CRITICAL: {
      label: 'HIGH SEVERITY',
      bgClass: 'bg-red-500/20',
      textClass: 'text-red-400',
      borderClass: 'border-red-500/30',
      glow: 'shadow-[0_0_20px_rgba(239,68,68,0.3)]'
    },
    MEDIUM: {
      label: 'MEDIUM SEVERITY',
      bgClass: 'bg-amber-500/20',
      textClass: 'text-amber-400',
      borderClass: 'border-amber-500/30',
      glow: 'shadow-[0_0_12px_rgba(245,158,11,0.2)]'
    },
    WATCH: {
      label: 'LOW SEVERITY',
      bgClass: 'bg-blue-500/20',
      textClass: 'text-blue-400',
      borderClass: 'border-blue-500/30',
      glow: 'shadow-[0_0_12px_rgba(59,130,246,0.2)]'
    }
  };

  const config = isCritical ? sevConfig.CRITICAL : isWatch ? sevConfig.WATCH : sevConfig.MEDIUM;
  const displayId = id || `BLK-${Math.floor(Math.random() * 900) + 100}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 300 }}
      whileHover={{ y: -4, scale: 1.01 }}
      className={`glass-card rounded-3xl p-8 transition-all duration-500 flex flex-col border border-white/5 relative overflow-hidden group ${isCritical ? 'shadow-[0_0_30px_rgba(239,68,68,0.05)]' : ''}`}
    >
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#22d3ee]/10 blur-[60px] rounded-full"></div>
      
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-[#1a263c] flex items-center justify-center group-hover:bg-[#22d3ee]/20 transition-colors border border-white/5">
          {/* Material icon fallback */}
          <div className="w-4 h-4 rounded-full border-2 border-[#22d3ee] animate-pulse"></div>
        </div>
        <h3 className="text-lg text-white tracking-tight font-bold" style={{ fontFamily: 'var(--font-syne)' }}>Blocker Radar</h3>
      </div>

      <div className="flex-grow space-y-6">
        <div className="flex justify-between items-center">
          <span className="text-xs text-[#a3abc0]" style={{ fontFamily: 'var(--font-mono)' }}>ID: {displayId}</span>
          <span className={`px-2 py-0.5 rounded ${config.bgClass} ${config.textClass} border ${config.borderClass} text-[10px] font-black tracking-tighter uppercase`} style={{ fontFamily: 'var(--font-mono)' }}>
            {config.label}
          </span>
        </div>

        <div>
          <p className="text-[#dde5fb] text-lg font-medium leading-snug">
            {description}
          </p>
          
          <div className="mt-4 flex flex-wrap items-center gap-4 text-[#a3abc0]">
            <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-[#1a263c] border border-white/10 flex items-center justify-center">
                    <span className="text-[10px]">👤</span>
                </div>
                <span className="text-xs" style={{ fontFamily: 'var(--font-inter)' }}>Assigned to: <strong className="text-white font-medium">{engineer || 'Unassigned'}</strong></span>
            </div>
            
            {blocked_for && (
                <span className="px-2 py-0.5 rounded-md text-[10px] bg-white/[0.06] text-neutral-400 border border-white/[0.08]" style={{ fontFamily: 'var(--font-mono)' }}>
                    Blocked for: {blocked_for}
                </span>
            )}
            
            {type && (
                 <span className="px-2 py-0.5 rounded-md text-[10px] bg-white/[0.06] text-[#22d3ee] border border-[#22d3ee]/20" style={{ fontFamily: 'var(--font-mono)' }}>
                    {type}
                 </span>
            )}
          </div>
        </div>
        
        {draft_ping && (
            <div className="p-4 rounded-xl bg-black/30 border border-white/[0.06] mt-4 relative overflow-hidden group/draft">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#22d3ee]/40 group-hover/draft:bg-[#22d3ee] transition-colors"></div>
                <p className="text-sm text-neutral-300" style={{ fontFamily: 'var(--font-mono)' }}>{draft_ping}</p>
            </div>
        )}
      </div>

      <div className="mt-8 flex gap-3">
          <motion.button 
              className="flex-1 py-4 rounded-2xl bg-[#00cbe6]/10 text-[#22d3ee] font-bold tracking-tight text-sm shadow-[0_0_20px_rgba(58,223,250,0.1)] hover:bg-[#00cbe6]/20 border border-[#22d3ee]/30 transition-all flex items-center justify-center gap-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled
          >
              <span className="text-lg">🔔</span>
              Ping {resolver || 'resolver'}
          </motion.button>
          
          <motion.button 
              className="px-6 py-4 rounded-2xl bg-transparent text-neutral-400 text-sm font-bold border border-white/[0.08] hover:bg-white/[0.04] transition-all"
              onClick={onDismiss}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
          >
              Dismiss
          </motion.button>
      </div>
    </motion.div>
  );
}
