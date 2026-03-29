import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Pencil, X, Check } from 'lucide-react';
import React from 'react';

export type ActionType = 'SLACK_MESSAGE' | 'MONDAY_BOARD' | 'GMAIL_SEND' | 'CALENDAR_EVENT';

export interface ReviewQueueCardProps {
  id: string;
  type: ActionType;
  title: string;
  content: string;
  reasoning: string[];
  isExpanded: boolean;
  isEditing: boolean;
  isBusy: boolean;
  currentContent: string;
  index: number;
  onToggleExpand: () => void;
  onApprove: () => void;
  onReject: () => void;
  onEditToggle: () => void;
  onContentChange: (val: string) => void;
}

const typeConfig: Record<ActionType, { label: string; color: string; bg: string; icon: string }> = {
  SLACK_MESSAGE: { label: 'SLACK', color: 'text-cyan-400', bg: 'bg-cyan-500/20', icon: 'chat' },
  MONDAY_BOARD: { label: 'MONDAY', color: 'text-blue-400', bg: 'bg-blue-500/20', icon: 'view_kanban' },
  GMAIL_SEND: { label: 'GMAIL', color: 'text-red-400', bg: 'bg-red-500/20', icon: 'mail' },
  CALENDAR_EVENT: { label: 'CALENDAR', color: 'text-emerald-400', bg: 'bg-emerald-500/20', icon: 'event' },
};

export function ReviewQueueCard({
  id,
  type,
  title,
  reasoning,
  isExpanded,
  isEditing,
  isBusy,
  currentContent,
  index,
  onToggleExpand,
  onApprove,
  onReject,
  onEditToggle,
  onContentChange
}: ReviewQueueCardProps) {
  const config = typeConfig[type] || typeConfig.SLACK_MESSAGE;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{
        opacity: 0,
        x: 100,
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        transition: { duration: 0.3 },
      }}
      transition={{ delay: index * 0.1 }}
      className="glass-card rounded-3xl p-8 glow-hover transition-all duration-500 border border-white/5 flex flex-col group overflow-hidden relative"
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#22d3ee]/5 blur-[80px] rounded-full pointer-events-none"></div>

      <div className="flex items-start justify-between mb-8 z-10 relative">
        <div className="space-y-1">
          <span className={`font-mono text-[10px] ${config.color} tracking-widest uppercase`}>Proposed Action</span>
          <h3 className="text-xl font-bold tracking-tight text-white" style={{ fontFamily: 'var(--font-syne)' }}>{title}</h3>
        </div>
        <div className={`w-12 h-12 rounded-full border ${config.bg.replace('/20', '/30')} flex items-center justify-center ${config.bg.replace('/20', '/10')}`}>
          <span className={`material-symbols-outlined ${config.color}`} data-icon={config.icon}>{config.icon}</span>
        </div>
      </div>

      <div className="space-y-4 mb-4 flex-grow z-10 relative">
          <div
            className={`relative rounded-2xl bg-black/40 border p-4 transition-colors ${
              isEditing ? 'border-[#22d3ee]/50 shadow-[0_0_20px_rgba(34,211,238,0.1)]' : 'border-white/[0.06]'
            }`}
          >
            <span className="font-label text-[10px] text-on-surface-variant uppercase tracking-widest block mb-2" style={{ fontFamily: 'var(--font-mono)' }}>Content / Payload</span>
            <textarea
              value={currentContent}
              onChange={(e) => onContentChange(e.target.value)}
              className="w-full bg-transparent text-neutral-300 font-mono text-sm resize-none outline-none min-h-[80px]"
              style={{ caretColor: '#22d3ee', fontFamily: 'var(--font-mono)' }}
              disabled={isBusy}
              readOnly={!isEditing}
            />
            {isEditing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute bottom-2 right-2 text-xs text-[#22d3ee]/60 bg-black/50 px-2 py-1 rounded"
              >
                Editing...
              </motion.div>
            )}
          </div>
          
          <button
            type="button"
            onClick={onToggleExpand}
            className="flex items-center gap-2 text-sm text-[#22d3ee] opacity-70 hover:opacity-100 transition-opacity font-mono tracking-wide"
          >
            <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="w-4 h-4" />
            </motion.div>
            Agent Reasoning
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="rounded-xl bg-black/60 border border-white/[0.04] p-4 mt-2">
                  {reasoning.length ? (
                    reasoning.map((line, i) => (
                      <p key={i} className="text-sm text-neutral-400 font-mono leading-relaxed flex gap-4">
                        <span className="text-[#22d3ee] opacity-50">[{i+1}]</span> 
                        {line}
                      </p>
                    ))
                  ) : (
                    <p className="text-sm text-neutral-500 font-mono">No telemetry stored.</p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
      </div>

      <div className="grid grid-cols-4 gap-3 mt-4 z-10 relative">
        <button
          type="button"
          onClick={onApprove}
          disabled={isBusy}
          className="col-span-2 py-4 rounded-2xl bg-[#22d3ee] text-[#020817] font-bold text-sm tracking-wide shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isBusy ? (
             <div className="w-4 h-4 border-2 border-[#020817]/30 border-t-[#020817] rounded-full animate-spin"></div>
          ) : (
            <>Approve Action</>
          )}
        </button>

        <button
          type="button"
          onClick={onEditToggle}
          disabled={isBusy}
          className={`py-3 rounded-xl border font-medium text-xs hover:scale-[1.02] transition-all col-span-1 ${isEditing ? 'bg-[#22d3ee]/10 text-[#22d3ee] border-[#22d3ee]/30' : 'bg-white/[0.04] text-white border-white/5'}`}
        >
          {isEditing ? 'Done' : 'Edit'}
        </button>

        <button
          type="button"
          onClick={onReject}
          disabled={isBusy}
          className="py-3 rounded-xl border border-red-500/30 text-red-400 font-medium text-xs hover:bg-red-500/10 hover:scale-[1.02] transition-all col-span-1"
        >
          Reject
        </button>
      </div>
    </motion.div>
  );
}
