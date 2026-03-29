import { motion } from 'framer-motion';

export interface UiTicket {
  id: string;
  k2Score: number;
  title: string;
  assignee: string;
  storyPoints: number;
  included: boolean;
}

export interface SprintTicketRowProps {
  ticket: UiTicket;
  index: number;
  onToggle: (id: string) => void;
}

export function SprintTicketRow({ ticket, index, onToggle }: SprintTicketRowProps) {
  const getScoreBadgeStyle = (score: number) => {
    if (score >= 90) return 'text-[#22d3ee] shadow-[0_0_15px_rgba(34,211,238,0.2)] bg-[#22d3ee]/10 border-[#22d3ee]/20';
    if (score >= 70) return 'text-[#10b981] shadow-[0_0_15px_rgba(16,185,129,0.1)] bg-[#10b981]/10 border-[#10b981]/20';
    return 'text-neutral-400 bg-white/5 border-white/10';
  };

  const getScoreIconStyle = (score: number) => {
    if (score >= 90) return 'text-[#22d3ee]';
    if (score >= 70) return 'text-[#10b981]';
    return 'text-neutral-400';
  };

  const displayId = ticket.id.length > 8 ? `ST-${ticket.id.substring(0, 5).toUpperCase()}` : ticket.id;
  const avatarSeed = ticket.assignee || 'Unassigned';

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + index * 0.08 }}
      whileHover={{ scale: 1.005, backgroundColor: 'rgba(255,255,255,0.02)' }}
      onClick={() => onToggle(ticket.id)}
      className="glass-card rounded-3xl p-1 glow-hover transition-all duration-500 border border-white/5 overflow-hidden cursor-pointer mb-3 group"
    >
      <div className="flex flex-col md:flex-row items-center gap-4 md:gap-8 px-6 py-5">
        <div className="flex items-center gap-4 w-full md:w-auto min-w-[300px]">
          <div className="px-3 py-1.5 rounded-lg bg-[#1a263c]/80 border border-white/10">
            <span className="font-mono text-xs font-bold tracking-widest text-[#a3abc0] group-hover:text-[#22d3ee] transition-colors">{displayId}</span>
          </div>
          <h4 className={`text-lg transition-colors truncate max-w-[400px] ${ticket.included ? 'text-white' : 'text-neutral-500'}`} style={{ fontFamily: 'var(--font-syne)', letterSpacing: '-0.02em', fontWeight: 600 }}>
             {ticket.title}
          </h4>
        </div>

        <div className="hidden xl:flex items-center gap-4 flex-grow px-8">
            <div className="w-8 h-8 rounded-full border-2 border-[#1a263c] overflow-hidden flex-shrink-0">
                <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${avatarSeed}&backgroundColor=020817`} alt={avatarSeed} />
            </div>
            <span className={`text-sm ${ticket.included ? 'text-[#dde5fb]' : 'text-neutral-600'}`} style={{ fontFamily: 'var(--font-inter)'}}>{ticket.assignee}</span>
        </div>

        <div className="flex items-center gap-6 w-full md:w-auto justify-between md:justify-end min-w-[300px]">
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end">
              <span className="text-[9px] uppercase tracking-widest text-[#a3abc0] font-bold" style={{ fontFamily: 'var(--font-mono)'}}>K2 Score</span>
              <span className={`text-xl font-black tracking-tighter ${getScoreIconStyle(ticket.k2Score)}`} style={{ fontFamily: 'var(--font-syne)'}}>
                 {ticket.k2Score}<span className="text-xs font-medium opacity-50">/100</span>
              </span>
            </div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${getScoreBadgeStyle(ticket.k2Score)}`}>
              <span className="text-xl">✨</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                   <span className="text-[9px] uppercase tracking-widest text-[#a3abc0] font-bold" style={{ fontFamily: 'var(--font-mono)'}}>Story Pts</span>
                   <span className={`font-mono font-medium ${ticket.included ? 'text-white' : 'text-neutral-600'}`}>{ticket.storyPoints}</span>
              </div>
          </div>

          <div className="flex justify-center flex-shrink-0 ml-4">
            <motion.button
              type="button"
              whileTap={{ scale: 0.9 }}
              onClick={(e) => {
                e.stopPropagation();
                onToggle(ticket.id);
              }}
              className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
                ticket.included
                  ? 'bg-[#22d3ee] text-[#020817] shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                  : 'bg-white/5 border border-white/10 text-transparent group-hover:border-white/20'
              }`}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </motion.button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
