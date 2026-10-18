import React, { useEffect, useState, useCallback } from 'react';
import type { FullGameState, AIAgent, AITask } from './types';
import { TopBar } from './components/TopBar';
import { ProductManager } from './components/ProductManager';
import { FinancialCharts } from './components/FinancialCharts';
import { ActivityAndLedger } from './components/ActivityAndLedger';
import { AIManagerPanel } from './components/AIManagerPanel';
import { AISettingsModal } from './components/AISettingsModal';
import { NewGameModal } from './components/NewGameModal';
import { AgentsTab } from './components/AgentsTab';
import { CreateTaskModal } from './components/CreateTaskModal';
import {
  TrendingUp,
  DollarSign,
  Package,
  Layers,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  LayoutDashboard,
  Users,
  Boxes,
  Receipt
} from 'lucide-react';

export const App: React.FC = () => {
  const [gameState, setGameState] = useState<FullGameState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'operations' | 'ledger'>('overview');
  
  // AI Workforce State
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [tasks, setTasks] = useState<AITask[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);

  // Modals
  const [showNewGameModal, setShowNewGameModal] = useState(false);
  const [showAISettings, setShowAISettings] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);

  const fetchWorkforce = useCallback(async () => {
    try {
      const [agentsRes, tasksRes] = await Promise.all([
        fetch('/api/ai/agents'),
        fetch('/api/ai/tasks')
      ]);
      if (agentsRes.ok) {
        const agentData: AIAgent[] = await agentsRes.json();
        setAgents(agentData);
        if (!selectedAgentId && agentData.length > 0) {
          setSelectedAgentId(agentData[0].id);
        }
      }
      if (tasksRes.ok) {
        const taskData: AITask[] = await tasksRes.json();
        setTasks(taskData);
      }
    } catch (err) {
      console.error('Failed to load AI workforce:', err);
    }
  }, [selectedAgentId]);

  const handleTriggerAIReview = async () => {
    try {
      await fetch('/api/ai/review-now', { method: 'POST' });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTriggerWorkCycle = async () => {
    try {
      await fetch('/api/ai/workforce/cycle', { method: 'POST' });
      await Promise.all([fetchState(), fetchWorkforce()]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignTask = async (taskData: any) => {
    await fetch('/api/ai/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskData)
    });
    await fetchWorkforce();
  };

  const handleApproveAIDecision = async (id: string) => {
    try {
      await fetch(`/api/ai/decisions/${id}/approve`, { method: 'POST' });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRejectAIDecision = async (id: string) => {
    try {
      await fetch(`/api/ai/decisions/${id}/reject`, { method: 'POST' });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  // Fetch full authoritative game state from local FastAPI backend
  const fetchState = useCallback(async () => {
    try {
      const res = await fetch('/api/state');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to reach simulation engine`);
      }
      const data: FullGameState = await res.json();
      setGameState(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Unable to connect to SimCorp simulation backend');
    } finally {
      setLoading(false);
    }
  }, []);

  // Poll state every 1.5 seconds to reflect clock ticks and background steps
  useEffect(() => {
    fetchState();
    fetchWorkforce();
    const interval = setInterval(() => {
      fetchState();
      fetchWorkforce();
    }, 1500);
    return () => clearInterval(interval);
  }, [fetchState, fetchWorkforce]);

  const handleControlClock = async (action: string, speed?: number) => {
    try {
      await fetch('/api/clock/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, speed_seconds: speed })
      });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateProduct = async (id: string, price: number, target: number) => {
    try {
      await fetch(`/api/products/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selling_price: price, daily_production_target: target })
      });
      await fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateGame = async (gameData: any) => {
    try {
      await fetch('/api/new-game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameData)
      });
      await fetchState();
      await fetchWorkforce();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && !gameState) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center text-slate-300">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
        <h2 className="text-lg font-bold">Initializing SimCorp Engine...</h2>
        <p className="text-xs text-slate-500 mt-1">Connecting to SQLite simulation state</p>
      </div>
    );
  }

  if (error && !gameState) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md bg-slate-900 border border-rose-900/50 p-6 rounded-2xl shadow-xl">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-base font-bold text-slate-100">Engine Connection Disconnected</h2>
          <p className="text-xs text-slate-400 mt-2 mb-4 leading-relaxed">
            Ensure the local Python backend is active at <code className="bg-slate-950 px-1 py-0.5 rounded text-indigo-400">127.0.0.1:8000</code>.
          </p>
          <button
            onClick={fetchState}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const latest = gameState?.latest_snapshot;
  const totalInventoryVal = gameState?.products.reduce((acc, p) => acc + (p.inventory_units * p.production_cost), 0) || 0;
  const totalUnitsSold = gameState?.products.reduce((acc, p) => acc + p.total_units_sold, 0) || 0;

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200 flex flex-col font-sans">
      {gameState && (
        <TopBar
          clock={gameState.clock}
          company={gameState.company}
          cash={gameState.cash_balance}
          onControlClock={handleControlClock}
          onNewGameModal={() => setShowNewGameModal(true)}
        />
      )}

      {/* Primary Navigation Bar */}
      <div className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-[61px] z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-bold transition ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" /> Overview & Financials
          </button>

          <button
            onClick={() => setActiveTab('agents')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-bold transition ${
              activeTab === 'agents'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Users className="w-4 h-4" /> AI Workforce & Agents ({agents.length})
          </button>

          <button
            onClick={() => setActiveTab('operations')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-bold transition ${
              activeTab === 'operations'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Boxes className="w-4 h-4" /> Products & Operations
          </button>

          <button
            onClick={() => setActiveTab('ledger')}
            className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-bold transition ${
              activeTab === 'ledger'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <Receipt className="w-4 h-4" /> Ledger & System Logs
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Onboarding / Tutorial Banner */}
        {showTutorial && (
          <div className="bg-gradient-to-r from-indigo-950/70 to-slate-900/90 border border-indigo-800/60 rounded-xl p-4 flex items-start justify-between gap-4 shadow-lg">
            <div className="flex items-start gap-3">
              <HelpCircle className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <span className="font-bold text-indigo-200 block text-sm">Welcome to SimCorp Executive Dashboard</span>
                <p className="text-slate-300 leading-relaxed">
                  You are running an autonomous commercial enterprise. Inspect the dedicated AI Workforce & Agents tab to explore
                  the multi-tier org hierarchy (CEO &rarr; Department Managers &rarr; Specialists), assign tasks, and monitor reviews and deliverables.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowTutorial(false)}
              className="text-xs text-slate-400 hover:text-slate-200 underline shrink-0"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Executive KPI Stat Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Revenue Last Day */}
          <div className="bg-slate-900/80 border border-slate-800/80 p-4 rounded-xl shadow-md backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Day Revenue</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100 font-mono">
              {latest ? latest.revenue.toFixed(2) : '0.00'} <span className="text-xs font-normal text-slate-400">cr</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              COGS: -{latest ? latest.cogs.toFixed(2) : '0.00'} cr
            </div>
          </div>

          {/* Daily Net Profit */}
          <div className="bg-slate-900/80 border border-slate-800/80 p-4 rounded-xl shadow-md backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Net Profit</span>
              <TrendingUp className="w-4 h-4 text-cyan-400" />
            </div>
            <div className={`text-2xl font-extrabold font-mono ${(latest?.net_profit || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {(latest?.net_profit || 0) >= 0 ? '+' : ''}{latest ? latest.net_profit.toFixed(2) : '0.00'} <span className="text-xs font-normal text-slate-400">cr</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Fixed Overhead: -{gameState?.daily_fixed_opex} cr
            </div>
          </div>

          {/* Asset Valuation */}
          <div className="bg-slate-900/80 border border-slate-800/80 p-4 rounded-xl shadow-md backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Est. Valuation</span>
              <Layers className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100 font-mono">
              {latest ? latest.total_valuation.toLocaleString(undefined, { maximumFractionDigits: 0 }) : '0'} <span className="text-xs font-normal text-slate-400">cr</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Inventory Value: {totalInventoryVal.toFixed(0)} cr
            </div>
          </div>

          {/* Total Output */}
          <div className="bg-slate-900/80 border border-slate-800/80 p-4 rounded-xl shadow-md backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Total Sales Volume</span>
              <Package className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-100 font-mono">
              {totalUnitsSold.toLocaleString()} <span className="text-xs font-normal text-slate-400">units</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Unmet Demand (last): {latest ? latest.unmet_demand : 0}
            </div>
          </div>
        </div>

        {/* Tab 1: Overview & Financials */}
        {activeTab === 'overview' && gameState && (
          <div className="space-y-6">
            <FinancialCharts snapshots={gameState.historical_snapshots} />
            <AIManagerPanel
              decisions={gameState.ai_decisions || []}
              onTriggerReview={handleTriggerAIReview}
              onApprove={handleApproveAIDecision}
              onReject={handleRejectAIDecision}
              onOpenSettings={() => setShowAISettings(true)}
            />
          </div>
        )}

        {/* Tab 2: Dedicated Agents Tab */}
        {activeTab === 'agents' && (
          <AgentsTab
            agents={agents}
            tasks={tasks}
            selectedAgentId={selectedAgentId}
            onSelectAgent={setSelectedAgentId}
            onTriggerCycle={handleTriggerWorkCycle}
            onCreateTaskModal={() => setShowCreateTaskModal(true)}
          />
        )}

        {/* Tab 3: Products & Operations */}
        {activeTab === 'operations' && gameState && (
          <ProductManager
            products={gameState.products}
            onUpdateProduct={handleUpdateProduct}
          />
        )}

        {/* Tab 4: Authoritative Ledger & Activity Feed */}
        {activeTab === 'ledger' && gameState && (
          <ActivityAndLedger
            transactions={gameState.recent_transactions}
            activities={gameState.recent_activities}
          />
        )}
      </main>

      {/* Footer / Status bar */}
      <footer className="border-t border-slate-800/80 py-3 px-6 bg-slate-950/60 text-xs text-slate-500 flex items-center justify-between">
        <div>SimCorp AI Workforce Management System • Level 0-2 Active</div>
        <div className="flex items-center gap-4">
          <button onClick={() => setShowAISettings(true)} className="hover:text-slate-300">AI Config</button>
          <button onClick={() => setShowTutorial(true)} className="hover:text-slate-300">Quick Guide</button>
          <span>Engine: Local SQLite Authoritative Journal</span>
        </div>
      </footer>

      {/* New Game Dialog Modal */}
      <NewGameModal
        isOpen={showNewGameModal}
        onClose={() => setShowNewGameModal(false)}
        onCreateGame={handleCreateGame}
      />

      {/* AI Settings Modal */}
      <AISettingsModal
        isOpen={showAISettings}
        onClose={() => setShowAISettings(false)}
      />

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateTaskModal}
        onClose={() => setShowCreateTaskModal(false)}
        agents={agents}
        onSubmit={handleAssignTask}
      />
    </div>
  );
};

export default App;

