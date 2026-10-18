import React, { useEffect, useState } from 'react';
import type { AIConfig, AIHealthStatus } from '../types';
import { X, Check, Cpu, Radio } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const AISettingsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState<AIConfig>({
    enabled: true,
    provider: 'lm_studio',
    base_url: 'http://localhost:1234/v1',
    model_id: 'google/gemma-4-e4b',
    autonomy_mode: 'autonomous',
    review_frequency_days: 2,
    timeout_seconds: 8.0
  });

  const [health, setHealth] = useState<AIHealthStatus | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadData = async () => {
    try {
      const cfgRes = await fetch('/api/ai/config');
      if (cfgRes.ok) {
        const data = await cfgRes.json();
        setConfig(data);
      }
      checkHealth();
    } catch (err) {
      console.error(err);
    }
  };

  const checkHealth = async () => {
    setCheckingHealth(true);
    try {
      const res = await fetch('/api/ai/health');
      if (res.ok) {
        const h: AIHealthStatus = await res.json();
        setHealth(h);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await fetch('/api/ai/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-100">Local AI / LM Studio Configuration</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Health Status Box */}
        <div className="mb-4 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Radio className={`w-4 h-4 ${health?.connected ? 'text-emerald-400 animate-pulse' : 'text-rose-500'}`} />
            <div>
              <div className="font-semibold text-slate-200">
                {health?.connected ? 'Connected to LM Studio' : 'LM Studio Disconnected'}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {health?.connected
                  ? `${health.models_available.length} models detected on local host`
                  : health?.error_message || 'Verify LM Studio local server is running on port 1234'}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={checkHealth}
            disabled={checkingHealth}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 font-medium transition"
          >
            {checkingHealth ? 'Pinging...' : 'Test Connection'}
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
            <div>
              <span className="font-semibold text-slate-200 block">Enable AI Management</span>
              <span className="text-[11px] text-slate-400">If disabled, company runs purely on player inputs.</span>
            </div>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={e => setConfig({ ...config, enabled: e.target.checked })}
              className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">LM Studio API Base URL</label>
            <input
              type="text"
              value={config.base_url}
              onChange={e => setConfig({ ...config, base_url: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
            />
            <span className="text-[10px] text-slate-500 mt-0.5 block">Default OpenAI-compatible URL: http://localhost:1234/v1</span>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Active Model ID</label>
            {health?.models_available && health.models_available.length > 0 ? (
              <select
                value={config.model_id}
                onChange={e => setConfig({ ...config, model_id: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
              >
                {health.models_available.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={config.model_id}
                onChange={e => setConfig({ ...config, model_id: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
              />
            )}
            <span className="text-[10px] text-slate-500 mt-0.5 block">Select any loaded model from your local LM Studio session.</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Autonomy Policy</label>
              <select
                value={config.autonomy_mode}
                onChange={e => setConfig({ ...config, autonomy_mode: e.target.value as any })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
              >
                <option value="autonomous">Autonomous (Auto-executes)</option>
                <option value="oversight">Oversight (Requires Player Approval)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Review Frequency</label>
              <select
                value={config.review_frequency_days}
                onChange={e => setConfig({ ...config, review_frequency_days: parseInt(e.target.value) || 2 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
              >
                <option value="1">Every 1 in-game day</option>
                <option value="2">Every 2 in-game days</option>
                <option value="5">Every 5 in-game days</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              Save Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
