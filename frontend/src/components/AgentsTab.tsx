import React, { useState } from 'react';
import type { AIAgent, AITask } from '../types';
import {
  GitBranch,
  Search,
  Filter,
  Play
} from 'lucide-react';

interface Props {
  agents: AIAgent[];
  tasks: AITask[];
  selectedAgentId: string | null;
  onSelectAgent: (id: string) => void;
  onTriggerCycle: () => void;
  onCreateTaskModal: () => void;
}

export const AgentsTab: React.FC<Props> = ({
  agents,
  tasks,
  selectedAgentId,
  onSelectAgent,
  onTriggerCycle,
  onCreateTaskModal
}) => {
  const [viewMode, setViewMode] = useState<'hierarchy' | 'directory' | 'tasks'>('hierarchy');
  const [deptFilter, setDeptFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [collapsedDepts, setCollapsedDepts] = useState<Record<string, boolean>>({});

  const toggleDept = (dept: string) => {
    setCollapsedDepts(prev => ({ ...prev, [dept]: !prev[dept] }));
  };

  const selectedAgent = agents.find(a => a.id === selectedAgentId) || agents[0];
  const agentTasks = tasks.filter(
    t => t.assigned_agent_id === selectedAgent?.id || t.supervisor_id === selectedAgent?.id
  );

  const filteredAgents = agents.filter(a => {
    const matchesDept = deptFilter === 'ALL' || a.department === deptFilter;
    const matchesQuery =
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.specialization.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDept && matchesQuery;
  });

  const ceo = agents.find(a => a.level === 0);
  const managers = agents.filter(a => a.level === 1);
  const specialists = agents.filter(a => a.level === 2);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'WORKING':
      case 'IN_PROGRESS':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/60">WORKING</span>;
      case 'AWAITING_REVIEW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-900/60 text-amber-300 border border-amber-700/60">AWAITING REVIEW</span>;
      case 'AWAITING_APPROVAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-900/60 text-purple-300 border border-purple-700/60">AWAITING APPROVAL</span>;
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-900/60 text-emerald-300 border border-emerald-700/60">COMPLETED</span>;
      case 'BLOCKED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-900/60 text-rose-300 border border-rose-700/60">BLOCKED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">IDLE</span>;
    }
  };

  const getDeptColor = (dept: string) => {
    switch (dept) {
      case 'EXECUTIVE':
        return 'border-amber-500/70 text-amber-400 bg-amber-950/20';
      case 'FINANCE':
        return 'border-emerald-500/70 text-emerald-400 bg-emerald-950/20';
      case 'OPERATIONS':
        return 'border-blue-500/70 text-blue-400 bg-blue-950/20';
      case 'MARKETING':
        return 'border-purple-500/70 text-purple-400 bg-purple-950/20';
      case 'RESEARCH':
        return 'border-cyan-500/70 text-cyan-400 bg-cyan-950/20';
      default:
        return 'border-slate-700 text-slate-300 bg-slate-900/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls & Navigation Header */}
      <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-700/60 text-indigo-400">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              AI Workforce & Organizational Hierarchy
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-700/50 font-mono">
                {agents.length} Specialized Agents
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Autonomous multi-tier workforce with supervisor reviews, escalation chains, and auditable deliverables.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('hierarchy')}
              className={`px-3 py-1.5 rounded font-medium transition ${
                viewMode === 'hierarchy' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Org Hierarchy
            </button>
            <button
              onClick={() => setViewMode('directory')}
              className={`px-3 py-1.5 rounded font-medium transition ${
                viewMode === 'directory' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Directory
            </button>
            <button
              onClick={() => setViewMode('tasks')}
              className={`px-3 py-1.5 rounded font-medium transition ${
                viewMode === 'tasks' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Work Tasks ({tasks.length})
            </button>
          </div>

          <button
            onClick={onTriggerCycle}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-700/80 hover:bg-emerald-600 text-emerald-100 text-xs font-semibold shadow transition"
            title="Execute workforce analysis, review, and execution cycle"
          >
            <Play className="w-3.5 h-3.5" /> Run Work Cycle
          </button>

          <button
            onClick={onCreateTaskModal}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-700/80 hover:bg-indigo-600 text-indigo-100 text-xs font-semibold shadow transition"
          >
            + Assign Task
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Views (Hierarchy / Directory / Task Board) */}
        <div className="lg:col-span-2 space-y-6">
          {viewMode === 'hierarchy' && (
            <div className="space-y-6">
              {/* Level 0: CEO Card */}
              {ceo && (
                <div className="flex flex-col items-center">
                  <div
                    onClick={() => onSelectAgent(ceo.id)}
                    className={`cursor-pointer w-full max-w-md p-4 rounded-xl border bg-gradient-to-r from-amber-950/40 via-slate-900 to-amber-950/30 transition shadow-lg hover:border-amber-400 ${
                      selectedAgentId === ceo.id ? 'ring-2 ring-amber-400 border-amber-400' : 'border-amber-600/50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-amber-900/60 border border-amber-500 flex items-center justify-center text-amber-300 font-bold text-sm shadow">
                          CEO
                        </div>
                        <div>
                          <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                            {ceo.name}
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-900/80 text-amber-300 font-mono">
                              LEVEL 0
                            </span>
                          </div>
                          <div className="text-xs text-amber-400/90 font-medium">{ceo.title}</div>
                        </div>
                      </div>
                      {getStatusBadge(ceo.current_status)}
                    </div>
                    <p className="mt-2.5 text-xs text-slate-300 line-clamp-2 leading-relaxed">
                      {ceo.specialization}
                    </p>
                  </div>
                  {/* Stem line */}
                  <div className="w-0.5 h-6 bg-slate-700 my-1"></div>
                </div>
              )}

              {/* Level 1 & 2: Department Branches */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {managers.map(mgr => {
                  const deptSpecs = specialists.filter(s => s.supervisor_id === mgr.id);
                  const isCollapsed = collapsedDepts[mgr.department];

                  return (
                    <div
                      key={mgr.id}
                      className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col space-y-3"
                    >
                      {/* Department Manager Card */}
                      <div
                        onClick={() => onSelectAgent(mgr.id)}
                        className={`cursor-pointer p-3 rounded-lg border transition ${getDeptColor(mgr.department)} ${
                          selectedAgentId === mgr.id ? 'ring-2 ring-indigo-400' : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="text-xs font-bold text-slate-100">{mgr.name}</div>
                            <div className="text-[11px] font-medium opacity-90">{mgr.title}</div>
                          </div>
                          {getStatusBadge(mgr.current_status)}
                        </div>
                        <div className="mt-2 text-[11px] text-slate-300 line-clamp-2">
                          {mgr.specialization}
                        </div>
                      </div>

                      {/* Subordinates Toggle & Tree */}
                      <div className="pl-3 border-l-2 border-slate-800 space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>Specialists ({deptSpecs.length})</span>
                          <button
                            onClick={() => toggleDept(mgr.department)}
                            className="hover:text-slate-200 underline"
                          >
                            {isCollapsed ? 'Expand' : 'Collapse'}
                          </button>
                        </div>

                        {!isCollapsed && (
                          <div className="space-y-2">
                            {deptSpecs.map(spec => (
                              <div
                                key={spec.id}
                                onClick={() => onSelectAgent(spec.id)}
                                className={`cursor-pointer p-2.5 rounded-lg border bg-slate-950/80 transition hover:border-slate-600 ${
                                  selectedAgentId === spec.id
                                    ? 'border-indigo-400 ring-1 ring-indigo-400'
                                    : 'border-slate-800'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="text-xs font-semibold text-slate-200">{spec.name}</div>
                                    <div className="text-[10px] text-slate-400">{spec.title}</div>
                                  </div>
                                  {getStatusBadge(spec.current_status)}
                                </div>
                                <div className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                                  {spec.specialization}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {viewMode === 'directory' && (
            <div className="space-y-4">
              {/* Filter & Search Bar */}
              <div className="flex flex-wrap items-center gap-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search agents by name, title, or skill..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <Filter className="w-3.5 h-3.5 text-slate-500" />
                  {['ALL', 'EXECUTIVE', 'FINANCE', 'OPERATIONS', 'MARKETING', 'RESEARCH'].map(dept => (
                    <button
                      key={dept}
                      onClick={() => setDeptFilter(dept)}
                      className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                        deptFilter === dept
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {dept}
                    </button>
                  ))}
                </div>
              </div>

              {/* Agent Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredAgents.map(a => (
                  <div
                    key={a.id}
                    onClick={() => onSelectAgent(a.id)}
                    className={`cursor-pointer p-3.5 rounded-xl border bg-slate-900/60 transition hover:border-indigo-500/60 ${
                      selectedAgentId === a.id ? 'border-indigo-500 ring-1 ring-indigo-500 bg-indigo-950/20' : 'border-slate-800'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-sm font-bold text-slate-100">{a.name}</div>
                        <div className="text-xs text-indigo-400 font-medium">{a.title}</div>
                      </div>
                      {getStatusBadge(a.current_status)}
                    </div>
                    <div className="text-xs text-slate-400 mt-2 line-clamp-2">
                      {a.specialization}
                    </div>
                    <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Supervisor: {agents.find(sup => sup.id === a.supervisor_id)?.name || 'Board of Directors'}</span>
                      <span className="font-mono text-emerald-400">Score: {a.performance_score.toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {viewMode === 'tasks' && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400 mb-2">
                All company tasks across the delegation pipeline.
              </div>
              {tasks.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
                  No tasks created yet. Click "Run Work Cycle" or "Assign Task" to generate work.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {tasks.map(t => {
                    const assigned = agents.find(a => a.id === t.assigned_agent_id);
                    const sup = agents.find(a => a.id === t.supervisor_id);

                    return (
                      <div
                        key={t.id}
                        className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/70 hover:border-slate-700 transition space-y-2"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                              {t.title}
                              <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                                t.priority === 'HIGH' || t.priority === 'URGENT'
                                  ? 'bg-rose-900/70 text-rose-300'
                                  : 'bg-slate-800 text-slate-400'
                              }`}>
                                {t.priority}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5">{t.description}</div>
                          </div>
                          {getStatusBadge(t.status)}
                        </div>

                        {/* Deliverable snippet if available */}
                        {t.deliverable && (
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800/80 text-[11px] font-mono text-slate-300">
                            <span className="text-indigo-400 font-semibold block mb-0.5">Deliverable Output:</span>
                            {JSON.stringify(t.deliverable, null, 2).slice(0, 160)}...
                          </div>
                        )}

                        <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                          <span>Assignee: <strong className="text-slate-300">{assigned?.name || t.assigned_agent_id}</strong></span>
                          <span>Reviewer: <strong className="text-slate-300">{sup?.name || t.supervisor_id}</strong></span>
                          <span>Review: <strong className="text-indigo-400">{t.review_status}</strong></span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right 1 Column: Agent Detail Panel */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl backdrop-blur-md space-y-5 h-fit">
          <div className="flex items-start justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700/60 text-indigo-300">
                Level {selectedAgent?.level} • {selectedAgent?.department}
              </span>
              <h3 className="text-lg font-bold text-slate-100 mt-2">{selectedAgent?.name}</h3>
              <div className="text-xs text-indigo-400 font-medium">{selectedAgent?.title}</div>
            </div>
            {getStatusBadge(selectedAgent?.current_status || 'IDLE')}
          </div>

          {/* Reporting Structure */}
          <div className="space-y-1.5 text-xs">
            <span className="text-slate-400 block font-semibold">Reporting Hierarchy</span>
            <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-300 flex items-center justify-between">
              <span>Direct Supervisor:</span>
              <strong className="text-slate-100 font-medium">
                {agents.find(a => a.id === selectedAgent?.supervisor_id)?.name || 'Board of Directors'}
              </strong>
            </div>
          </div>

          {/* Specialization & Objective */}
          <div className="space-y-2 text-xs">
            <span className="text-slate-400 block font-semibold">Specialization & Scope</span>
            <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
              {selectedAgent?.specialization}
            </p>
            <span className="text-slate-400 block font-semibold mt-2">Current Strategic Objective</span>
            <p className="text-indigo-300 text-[11px] leading-relaxed bg-indigo-950/30 p-2.5 rounded-lg border border-indigo-800/40">
              {selectedAgent?.current_objective}
            </p>
          </div>

          {/* Metrics & Performance */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Performance</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                {selectedAgent?.performance_score.toFixed(0)}%
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Completed</span>
              <span className="text-sm font-bold text-slate-200 font-mono">
                {selectedAgent?.tasks_completed}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Failed</span>
              <span className="text-sm font-bold text-rose-400 font-mono">
                {selectedAgent?.tasks_failed}
              </span>
            </div>
          </div>

          {/* Permitted Task Types */}
          <div className="space-y-1.5 text-xs">
            <span className="text-slate-400 block font-semibold">Permitted Responsibilities</span>
            <div className="flex flex-wrap gap-1">
              {selectedAgent?.allowed_tasks.map(t => (
                <span
                  key={t}
                  className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 font-mono border border-slate-700/60"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Agent's Recent Work Assignments */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <span className="text-xs text-slate-400 font-semibold block">Active & Recent Assignments</span>
            {agentTasks.length === 0 ? (
              <div className="text-[11px] text-slate-500 italic">No assigned tasks currently.</div>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {agentTasks.slice(0, 4).map(t => (
                  <div key={t.id} className="p-2 rounded bg-slate-950/70 border border-slate-800/80 text-[11px] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200 truncate">{t.title}</span>
                      {getStatusBadge(t.status)}
                    </div>
                    {t.review_feedback && (
                      <div className="text-[10px] text-amber-400/90 italic">
                        Feedback: {t.review_feedback}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
