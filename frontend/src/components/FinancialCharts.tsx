import React from 'react';
import type { DailySnapshot } from '../types';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';

interface Props {
  snapshots: DailySnapshot[];
}

export const FinancialCharts: React.FC<Props> = ({ snapshots }) => {
  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
        Awaiting simulation data... Advance days to see financial trajectories.
      </div>
    );
  }

  const chartData = snapshots.map(s => ({
    day: `Day ${s.day}`,
    cash: Math.round(s.cash_balance),
    revenue: Math.round(s.revenue),
    profit: Math.round(s.net_profit),
    cogs: Math.round(s.cogs),
    units: s.total_units_sold,
    unmet: s.unmet_demand,
    valuation: Math.round(s.total_valuation)
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Cash Reserves & Net Valuation Chart */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-slate-100">Capital & Valuation Trajectory</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">SQLite Snapshot History</span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
              />
              <Area type="monotone" dataKey="cash" stroke="#10b981" fillOpacity={1} fill="url(#colorCash)" name="Cash Reserves (cr)" />
              <Area type="monotone" dataKey="valuation" stroke="#6366f1" fillOpacity={1} fill="url(#colorVal)" name="Est. Valuation (cr)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Revenue & Net Profit Chart */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-slate-100">Revenue & Net Profit</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Real-time P&L</span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
              />
              <Line type="monotone" dataKey="revenue" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} name="Daily Revenue (cr)" />
              <Line type="monotone" dataKey="profit" stroke="#a855f7" strokeWidth={2} dot={{ r: 3 }} name="Net Profit (cr)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
