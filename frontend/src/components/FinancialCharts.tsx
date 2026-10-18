import React, { useState } from 'react';
import type { DailySnapshot } from '../types';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import {
  TrendingUp,
  BarChart3,
  Package,
  Layers,
  Award,
  Zap
} from 'lucide-react';

interface Props {
  snapshots: DailySnapshot[];
}

export const FinancialCharts: React.FC<Props> = ({ snapshots }) => {
  const [timeRange, setTimeRange] = useState<'7' | '14' | '30' | 'all'>('all');
  const [chartView, setChartView] = useState<'financial' | 'operations' | 'valuation'>('financial');

  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-500 backdrop-blur-md">
        Awaiting simulation data... Unpause or advance clock to see financial trajectories.
      </div>
    );
  }

  // Filter based on time range
  const filteredSnapshots = (() => {
    if (timeRange === 'all') return snapshots;
    const daysLimit = parseInt(timeRange);
    return snapshots.slice(-daysLimit);
  })();

  const chartData = filteredSnapshots.map(s => ({
    day: `Day ${s.day}`,
    dayNum: s.day,
    cash: Math.round(s.cash_balance),
    revenue: Math.round(s.revenue),
    profit: Math.round(s.net_profit),
    cogs: Math.round(s.cogs),
    opex: Math.round(s.operating_expenses),
    unitsSold: s.total_units_sold,
    unmetDemand: s.unmet_demand,
    inventoryVal: Math.round(s.inventory_value),
    valuation: Math.round(s.total_valuation),
    reputation: Number(s.reputation.toFixed(1)),
  }));

  // Summary Metrics for the visible window
  const latest = snapshots[snapshots.length - 1];
  const totalRevenue = chartData.reduce((acc, d) => acc + d.revenue, 0);
  const totalProfit = chartData.reduce((acc, d) => acc + d.profit, 0);
  const totalUnits = chartData.reduce((acc, d) => acc + d.unitsSold, 0);
  const avgMargin = totalRevenue > 0 ? ((totalProfit / totalRevenue) * 100).toFixed(1) : '0.0';

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-950/95 border border-slate-700/80 rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs space-y-1.5 min-w-[170px]">
          <div className="font-bold text-slate-200 border-b border-slate-800 pb-1 flex items-center justify-between">
            <span>{label}</span>
            <span className="text-[10px] text-slate-500 font-mono">SimCorp Log</span>
          </div>
          {payload.map((entry: any, index: number) => (
            <div key={`item-${index}`} className="flex items-center justify-between gap-3 text-[11px]">
              <span className="flex items-center gap-1.5" style={{ color: entry.color }}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                {entry.name}:
              </span>
              <span className="font-mono font-bold text-slate-100">
                {typeof entry.value === 'number'
                  ? entry.name.toLowerCase().includes('units') || entry.name.toLowerCase().includes('rep')
                    ? entry.value.toLocaleString()
                    : `${entry.value.toLocaleString()} cr`
                  : entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md space-y-5">
      {/* Chart Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-slate-100">Financial Performance & Analytics</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Interactive multi-horizon telemetry recorded from authoritative SQLite ledger snapshots.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Chart Type Selector */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setChartView('financial')}
              className={`px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5 ${
                chartView === 'financial' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" /> P&L & Cash
            </button>
            <button
              onClick={() => setChartView('operations')}
              className={`px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5 ${
                chartView === 'operations' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Package className="w-3.5 h-3.5" /> Volume & Demand
            </button>
            <button
              onClick={() => setChartView('valuation')}
              className={`px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5 ${
                chartView === 'valuation' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" /> Asset Valuation
            </button>
          </div>

          {/* Time Range Selector */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {(['7', '14', '30', 'all'] as const).map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                  timeRange === range ? 'bg-slate-800 text-indigo-300' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {range === 'all' ? 'All Days' : `${range}D`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Snapshot KPI Highlights Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 text-xs">
        <div>
          <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Visible Revenue</span>
          <span className="font-mono font-bold text-slate-200 text-sm">{totalRevenue.toLocaleString()} cr</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Visible Profit</span>
          <span className={`font-mono font-bold text-sm ${totalProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {totalProfit >= 0 ? '+' : ''}{totalProfit.toLocaleString()} cr
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Net Margin (Window)</span>
          <span className="font-mono font-bold text-indigo-300 text-sm">{avgMargin}%</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase tracking-wider">Total Units Output</span>
          <span className="font-mono font-bold text-cyan-400 text-sm">{totalUnits.toLocaleString()} units</span>
        </div>
      </div>

      {/* Main Charts View Area */}
      {chartView === 'financial' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Cash Reserves & Net Profit Trajectory */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-emerald-400" /> Cash Reserves & Cumulative Balance
              </span>
              <span className="font-mono text-emerald-400 text-[11px]">
                Current: {latest ? Math.round(latest.cash_balance).toLocaleString() : 0} cr
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="cash"
                    stroke="#10b981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorCash)"
                    name="Liquid Cash"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Revenue vs Cost of Goods & Profit */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-cyan-400" /> Daily Revenue vs. Cost Breakdown
              </span>
              <span className="font-mono text-cyan-400 text-[11px]">
                Net Profit: {latest ? (latest.net_profit >= 0 ? '+' : '') + Math.round(latest.net_profit) : 0} cr
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="revenue" fill="#38bdf8" name="Revenue" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="cogs" fill="#f43f5e" name="COGS" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="profit" fill="#a855f7" name="Net Profit" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {chartView === 'operations' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Sales Volume vs Unmet Market Demand */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Package className="w-4 h-4 text-purple-400" /> Units Sold vs. Unmet Demand
              </span>
              <span className="text-[11px] text-amber-400 font-mono">
                Unmet (last): {latest ? latest.unmet_demand : 0}
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorUnits" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#c084fc" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#c084fc" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorUnmet" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#fbbf24" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Area
                    type="monotone"
                    dataKey="unitsSold"
                    stroke="#c084fc"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorUnits)"
                    name="Units Sold"
                  />
                  <Area
                    type="monotone"
                    dataKey="unmetDemand"
                    stroke="#fbbf24"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorUnmet)"
                    name="Unmet Demand"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Market Reputation & Brand Strength */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-amber-400" /> Company Reputation Trend
              </span>
              <span className="font-mono text-amber-400 text-[11px]">
                Score: {latest ? latest.reputation.toFixed(1) : 50}/100
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="reputation"
                    stroke="#fbbf24"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#fbbf24' }}
                    name="Reputation"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {chartView === 'valuation' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Total Enterprise Valuation */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-indigo-400" /> Total Enterprise Valuation
              </span>
              <span className="font-mono text-indigo-400 text-[11px]">
                {latest ? Math.round(latest.total_valuation).toLocaleString() : 0} cr
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorValuation" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="valuation"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorValuation)"
                    name="Enterprise Valuation"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Liquid Cash vs. Warehoused Inventory Assets */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="font-bold text-slate-200 flex items-center gap-1.5">
                <Package className="w-4 h-4 text-cyan-400" /> Cash vs. Inventory Asset Split
              </span>
              <span className="font-mono text-slate-300 text-[11px]">
                Inv: {latest ? Math.round(latest.inventory_value).toLocaleString() : 0} cr
              </span>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Area
                    type="monotone"
                    dataKey="cash"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                    name="Liquid Cash"
                  />
                  <Area
                    type="monotone"
                    dataKey="inventoryVal"
                    stackId="1"
                    stroke="#38bdf8"
                    fill="#38bdf8"
                    fillOpacity={0.6}
                    name="Inventory Value"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
