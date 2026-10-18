import React, { useState } from 'react';
import type { AIAgent } from '../types';
import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  agents: AIAgent[];
  onSubmit: (task: {
    title: string;
    description: string;
    department: string;
    task_type: string;
    assigned_agent_id: string;
    supervisor_id: string;
    priority: string;
    deadline_day: number;
  }) => Promise<void>;
}

export const CreateTaskModal: React.FC<Props> = ({ isOpen, onClose, agents, onSubmit }) => {
  if (!isOpen) return null;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignedAgentId, setAssignedAgentId] = useState(agents[0]?.id || '');
  const [priority, setPriority] = useState('MEDIUM');
  const [deadlineDays, setDeadlineDays] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  const selectedAgent = agents.find(a => a.id === assignedAgentId) || agents[0];
  const supervisor = agents.find(a => a.id === selectedAgent?.supervisor_id) || agents.find(a => a.level === 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit({
        title,
        description,
        department: selectedAgent?.department || 'OPERATIONS',
        task_type: selectedAgent?.allowed_tasks[0] || 'ROUTINE_ANALYSIS',
        assigned_agent_id: selectedAgent?.id || '',
        supervisor_id: supervisor?.id || 'agent_ceo',
        priority,
        deadline_day: deadlineDays,
      });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative text-slate-200">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-slate-200 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-lg font-bold text-slate-100 mb-1">Assign Task to AI Workforce</h3>
        <p className="text-xs text-slate-400 mb-5">
          Delegates an analytical or operational objective down the organizational hierarchy.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Task Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Price Elasticity Study for Micro-Sensors"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description & Objective</label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Specify the analysis parameters, target metric, or constraint..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Assigned Agent</label>
              <select
                value={assignedAgentId}
                onChange={e => setAssignedAgentId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                {agents.map(a => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.title})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
              <select
                value={priority}
                onChange={e => setPriority(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target Deadline (Simulated Days)</label>
            <input
              type="number"
              min={1}
              max={60}
              value={deadlineDays}
              onChange={e => setDeadlineDays(parseInt(e.target.value) || 5)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1">
            <div className="flex justify-between text-slate-400">
              <span>Department:</span>
              <span className="font-semibold text-slate-200">{selectedAgent?.department}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Reviewing Supervisor:</span>
              <span className="font-semibold text-indigo-400">{supervisor?.name || 'CEO'}</span>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md transition disabled:opacity-50"
            >
              {submitting ? 'Assigning...' : 'Assign Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
