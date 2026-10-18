import React, { useState } from 'react';
import type { AIDecisionRecord } from '../types';
import { Bot, Check, X, BrainCircuit, RefreshCw } from 'lucide-react';

interface Props {
  decisions: AIDecisionRecord[];
  onTriggerReview: () => Promise<void>;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onOpenSettings: () => void;
}

export const AIManagerPanel: React.FC<Props> = ({
  decisions,
  onTriggerReview,
  onApprove,
  onReject,
  onOpenSettings
}) => {
  const [reviewing, setReviewing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleReviewNow = async () => {
    setReviewing(true);
    try {
      await onTriggerReview();
    } finally {
      setReviewing(false);
    }
  };

  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await onApprove(id);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: string) => {
    setActionLoading(id);
    try {
      await onReject(id);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'EXECUTED':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/50';
      case 'PENDING':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/50';
      case 'REJECTED':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/50';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              Autonomous Management Suite
              <span className="text-xs font-normal text-indigo-400 bg-indigo-950/60 border border-indigo-800/40 px-2 py-0.5 rounded-full">
                LM Studio / Rule Fallback
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              The AI CEO evaluates cash runway, inventory velocity, and prices to steer corporate strategy.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReviewNow}
            disabled={reviewing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
            title="Force immediate management review"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reviewing ? 'animate-spin' : ''}`} />
            Run Review Now
          </button>
          <button
            onClick={onOpenSettings}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
          >
            <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
            AI Settings
          </button>
        </div>
      </div>

      {/* Decision History Feed */}
      <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
        {decisions.length === 0 ? (
          <div className="text-slate-500 text-xs py-8 text-center bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
            No management decisions recorded yet. As turns advance, the AI CEO will propose and execute strategic adjustments.
          </div>
        ) : (
          decisions.map(d => (
            <div
              key={d.id}
              className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-slate-400">Day {d.day}</span>
                  <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                    {d.manager_role}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(d.status)}`}>
                    {d.status}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    Conf: {(d.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {d.status === 'PENDING' && (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleApprove(d.id)}
                      disabled={actionLoading === d.id}
                      className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold rounded transition disabled:opacity-50"
                    >
                      <Check className="w-3 h-3" />
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(d.id)}
                      disabled={actionLoading === d.id}
                      className="flex items-center gap-1 px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white text-[11px] font-semibold rounded transition disabled:opacity-50"
                    >
                      <X className="w-3 h-3" />
                      Reject
                    </button>
                  </div>
                )}
              </div>

              <div className="text-slate-300 font-medium leading-relaxed">
                {d.reasoning}
              </div>

              {d.result_summary && (
                <div className="text-slate-400 text-[11px] mt-1 bg-slate-900/60 px-2.5 py-1 rounded border border-slate-800/60 font-mono">
                  Result: {d.result_summary}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
