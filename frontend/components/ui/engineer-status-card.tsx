import { motion } from 'framer-motion';

export interface EngineerStatusCardProps {
  engineer: string;
  status: string; // 'blocked' | 'check_in' | 'on_track'
  did?: string;
  working_on?: string;
  blocker?: string | null;
  sources?: string[];
  index: number;
}

export function EngineerStatusCard({ 
  engineer, 
  status, 
  did, 
  working_on, 
  blocker, 
  sources, 
  index 
}: EngineerStatusCardProps) {
  
  const isBlocked = status === 'blocked';
  const isCheckIn = status === 'check_in';
  
  const statusConfig = {
    blocked: {
      label: 'BLOCKED',
      color: '#ef4444',
      bgClass: 'bg-red-500/20',
      borderClass: 'border-red-500/30',
      textClass: 'text-red-500',
      glow: 'shadow-[0_0_12px_rgba(239,68,68,0.4)]',
      icon: 'block'
    },
    check_in: {
      label: 'CHECK IN',
      color: '#f59e0b',
      bgClass: 'bg-amber-500/20',
      borderClass: 'border-amber-500/30',
      textClass: 'text-amber-500',
      glow: '',
      icon: 'warning'
    },
    on_track: {
      label: 'ON TRACK',
      color: '#10b981',
      bgClass: 'bg-emerald-500/20',
      borderClass: 'border-emerald-500/30',
      textClass: 'text-emerald-500',
      glow: '',
      icon: 'check_circle'
    }
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.on_track;

  // Generate a deterministic but random-looking avatar
  const avatarId = engineer.length % 10;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      whileHover={{ y: -4, scale: 1.01 }}
      className="glass-card rounded-3xl p-6 glow-hover transition-all duration-500 flex flex-col justify-between group border border-white/5"
    >
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img 
                alt={engineer} 
                className="w-14 h-14 rounded-2xl border-2 border-[#1a263c] object-cover" 
                src={`https://api.dicebear.com/9.x/notionists/svg?seed=${engineer}`}
            />
            {isBlocked && (
                <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-red-500 border-2 border-[#020817] shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse"></span>
            )}
            {!isBlocked && (
                 <span className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-[#020817] ${isCheckIn ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white tracking-tight" style={{ fontFamily: 'var(--font-syne)' }}>{engineer}</h3>
            <p className="text-xs text-[#a3abc0]" style={{ fontFamily: 'var(--font-inter)' }}>Software Engineer</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full ${config.bgClass} border ${config.borderClass} flex items-center gap-1.5 ${config.glow}`}>
            {/* Fallback to simple circle if material icons not loaded */}
            <span className={`w-2 h-2 rounded-full`} style={{ background: config.color }}></span>
            <span className={`text-[10px] font-bold ${config.textClass} tracking-widest uppercase`} style={{ fontFamily: 'var(--font-mono)' }}>
                {config.label}
            </span>
        </div>
      </div>
      
      <div className="space-y-4 flex-grow">
        {(working_on || did) && (
            <div className="bg-[#0a1324]/50 rounded-2xl p-4 border border-white/5 h-full">
                {working_on && (
                    <div className="mb-3">
                        <span className="text-[10px] text-[#22d3ee] uppercase tracking-widest block mb-1 font-bold" style={{ fontFamily: 'var(--font-mono)' }}>Working On</span>
                        <p className="text-sm font-medium text-neutral-200 leading-relaxed">{working_on}</p>
                    </div>
                )}
                
                {did && (
                    <div>
                        <span className="text-[10px] text-neutral-500 uppercase tracking-widest block mb-1 font-bold" style={{ fontFamily: 'var(--font-mono)' }}>Did</span>
                        <p className="text-sm font-medium text-neutral-400 leading-relaxed line-clamp-2">{did}</p>
                    </div>
                )}
            </div>
        )}

        {blocker && (
             <div className="bg-red-500/10 rounded-2xl p-4 border border-red-500/20 text-red-300 text-sm mt-2">
                 <span className="text-[10px] uppercase tracking-widest block mb-1 font-bold text-red-400" style={{ fontFamily: 'var(--font-mono)' }}>Blocker</span>
                 {blocker}
             </div>
        )}
      </div>

      {sources && sources.length > 0 && (
          <div className="flex items-center justify-between pt-4 mt-auto border-t border-white/5">
              <div className="flex flex-wrap gap-2">
                {sources.map((s, i) => (
                  <span
                    key={i}
                    className="text-[10px] px-2 py-1 rounded-lg border border-[#22d3ee]/20"
                    style={{ background: 'rgba(34,211,238,0.05)', color: '#22d3ee', fontFamily: 'var(--font-mono)' }}
                  >
                    {s}
                  </span>
                ))}
              </div>
          </div>
      )}
    </motion.div>
  );
}
