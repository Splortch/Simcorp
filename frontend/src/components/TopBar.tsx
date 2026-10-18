import React, { useState } from 'react';
import type { GameClock, CompanyState } from '../types';
import { Play, Pause, Calendar, ShieldCheck, Plus } from 'lucide-react';

interface Props {
  clock: GameClock;
  company: CompanyState;
  cash: number;
  onControlClock: (action: string, speed?: number) => Promise<void>;
  onNewGameModal: () => void;
}

export const TopBar: React.FC<Props> = ({
  clock,
  company,
  cash,
  onControlClock,
  onNewGameModal
}) => {
  const [loadingAction, setLoadingAction] = useState(false);

  const handleAction = async (action: string, speed?: number) => {
    setLoadingAction(true);
    try {
      await onControlClock(action, speed);
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <header className="bg-slate-900/90 border-b border-slate-800 px-6 py-3.5 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Left: Branding & Company Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center font-black text-white text-lg tracking-wider shadow-md shadow-indigo-500/20">
              SC
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-100 tracking-tight text-base">{company.name}</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full font-medium bg-slate-800 text-slate-300 border border-slate-700">
                  {company.industry}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Reputation: <strong className="text-slate-200">{company.reputation.toFixed(1)}/100</strong>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Clock Controls */}
        <div className="flex items-center gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800/80 shadow-inner">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-900 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 mr-1">
            <Calendar className="w-3.5 h-3.5 text-indigo-400" />
            <span>DAY <strong className="text-slate-100 font-bold">{clock.current_day}</strong></span>
          </div>

          {/* Pause / Resume */}
          {clock.is_paused ? (
            <button
              onClick={() => handleAction('resume')}
              disabled={loadingAction}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
              title="Resume simulation"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Resume
            </button>
          ) : (
            <button
              onClick={() => handleAction('pause')}
              disabled={loadingAction}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
              title="Pause simulation"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              Pause
            </button>
          )}

          {/* Step 1 Day */}
          <button
            onClick={() => handleAction('step')}
            disabled={loadingAction}
            className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
            title="Advance exactly 1 day"
          >
            +1 Day
          </button>

          {/* Speed Presets */}
          <div className="flex items-center gap-1 pl-1 border-l border-slate-800">
            <button
              onClick={() => handleAction('set_speed', 3.0)}
              className={`px-2 py-1 text-[11px] font-mono rounded transition ${
                clock.tick_speed_seconds === 3.0
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              1x
            </button>
            <button
              onClick={() => handleAction('set_speed', 1.5)}
              className={`px-2 py-1 text-[11px] font-mono rounded transition ${
                clock.tick_speed_seconds === 1.5
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              2x
            </button>
            <button
              onClick={() => handleAction('set_speed', 0.5)}
              className={`px-2 py-1 text-[11px] font-mono rounded transition ${
                clock.tick_speed_seconds === 0.5
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              5x
            </button>
          </div>
        </div>

        {/* Right: Cash Reserves & New Game */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800 flex items-center gap-2">
            <div className="text-right">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Cash Balance</div>
              <div className={`text-base font-extrabold font-mono ${cash < 1000 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-xs font-normal text-slate-400">cr</span>
              </div>
            </div>
          </div>

          <button
            onClick={onNewGameModal}
            className="flex items-center gap-1 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition"
          >
            <Plus className="w-3.5 h-3.5 text-indigo-400" />
            New Game
          </button>
        </div>
      </div>
    </header>
  );
};
