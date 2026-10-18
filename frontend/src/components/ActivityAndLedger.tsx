import React, { useState } from 'react';
import type { LedgerEntry, ActivityLogItem } from '../types';
import { FileText, Bell, AlertTriangle, CheckCircle, Info, ShieldAlert } from 'lucide-react';

interface Props {
  transactions: LedgerEntry[];
  activities: ActivityLogItem[];
}

export const ActivityAndLedger: React.FC<Props> = ({ transactions, activities }) => {
  const [activeTab, setActiveTab] = useState<'activity' | 'ledger'>('activity');

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'SUCCESS':
        return <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />;
      case 'DANGER':
        return <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-sky-400 shrink-0" />;
    }
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'REVENUE':
        return 'bg-emerald-950/70 text-emerald-300 border-emerald-800/40';
      case 'COGS':
        return 'bg-amber-950/70 text-amber-300 border-amber-800/40';
      case 'OPEX':
        return 'bg-rose-950/70 text-rose-300 border-rose-800/40';
      case 'EQUITY_INJECTION':
        return 'bg-indigo-950/70 text-indigo-300 border-indigo-800/40';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('activity')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'activity'
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bell className="w-4 h-4" />
            Activity & Events Feed ({activities.length})
          </button>
          <button
            onClick={() => setActiveTab('ledger')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'ledger'
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            Authoritative Ledger ({transactions.length})
          </button>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">SQLite Persistent Journal</span>
      </div>

      {activeTab === 'activity' ? (
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {activities.length === 0 ? (
            <div className="text-slate-500 text-xs py-4 text-center">No logged events yet.</div>
          ) : (
            activities.map(act => (
              <div
                key={act.id}
                className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60 text-xs hover:border-slate-700/60 transition"
              >
                {getSeverityIcon(act.severity)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Day {act.day} • {act.category}
                    </span>
                  </div>
                  <p className="text-slate-200 mt-0.5 leading-relaxed">{act.message}</p>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="overflow-x-auto max-h-72 pr-1">
          <table className="w-full text-left text-xs font-mono">
            <thead className="text-[11px] text-slate-400 uppercase bg-slate-950/70 border-b border-slate-800 sticky top-0">
              <tr>
                <th className="py-2 px-2.5">Day</th>
                <th className="py-2 px-2.5">Category</th>
                <th className="py-2 px-2.5">Description</th>
                <th className="py-2 px-2.5 text-right">Amount</th>
                <th className="py-2 px-2.5 text-right">Balance After</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {transactions.map(tx => (
                <tr key={tx.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2 px-2.5 text-slate-400">D{tx.day}</td>
                  <td className="py-2 px-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getCategoryBadge(tx.category)}`}>
                      {tx.category}
                    </span>
                  </td>
                  <td className="py-2 px-2.5 text-slate-200 truncate max-w-xs">{tx.description}</td>
                  <td className={`py-2 px-2.5 text-right font-semibold ${tx.amount >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {tx.amount >= 0 ? `+${tx.amount.toFixed(2)}` : tx.amount.toFixed(2)} cr
                  </td>
                  <td className="py-2 px-2.5 text-right font-bold text-slate-100">
                    {tx.balance_after.toFixed(2)} cr
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
