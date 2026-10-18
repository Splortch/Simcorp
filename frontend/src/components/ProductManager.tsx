import React, { useState } from 'react';
import type { Product } from '../types';
import { Package, TrendingUp, AlertTriangle, Check, Sliders } from 'lucide-react';

interface Props {
  products: Product[];
  onUpdateProduct: (id: string, price: number, target: number) => Promise<void>;
}

export const ProductManager: React.FC<Props> = ({ products, onUpdateProduct }) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPrice, setEditPrice] = useState<number>(0);
  const [editTarget, setEditTarget] = useState<number>(0);
  const [saving, setSaving] = useState(false);

  const startEdit = (p: Product) => {
    setEditingId(p.id);
    setEditPrice(p.selling_price);
    setEditTarget(p.daily_production_target);
  };

  const handleSave = async (id: string) => {
    setSaving(true);
    try {
      await onUpdateProduct(id, editPrice, editTarget);
      setEditingId(null);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">Production & Catalog</h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">Active Lines: {products.filter(p => p.status === 'ACTIVE').length}</span>
      </div>

      <div className="space-y-4">
        {products.map(p => {
          const isEditing = editingId === p.id;
          const unitMargin = p.selling_price - p.production_cost;
          const marginPercent = ((unitMargin / p.selling_price) * 100).toFixed(1);

          return (
            <div key={p.id} className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-colors">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100 text-base">{p.name}</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/50">
                      {p.status}
                    </span>
                    <span className="text-xs text-slate-400">Category: {p.category}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex gap-4">
                    <span>Quality Rating: <strong className="text-slate-200">{p.quality}/100</strong></span>
                    <span>Total Sold: <strong className="text-slate-200">{p.total_units_sold.toLocaleString()}</strong></span>
                    <span>Cumulative Revenue: <strong className="text-slate-200">{p.total_revenue.toLocaleString()} cr</strong></span>
                  </div>
                </div>

                {!isEditing ? (
                  <button
                    onClick={() => startEdit(p)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
                  >
                    <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                    Configure Line
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSave(p.id)}
                      disabled={saving}
                      className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {/* Stats & Controls */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/50 p-3 rounded-lg border border-slate-800/50 text-xs">
                <div>
                  <div className="text-slate-400 mb-1">Selling Price</div>
                  {isEditing ? (
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={editPrice}
                      onChange={e => setEditPrice(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-indigo-500/50 rounded px-2 py-1 text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  ) : (
                    <div className="text-slate-200 font-mono font-semibold text-sm">
                      {p.selling_price.toFixed(2)} cr
                    </div>
                  )}
                  <div className="text-[10px] text-slate-500 mt-0.5">Unit Cost: {p.production_cost.toFixed(2)} cr</div>
                </div>

                <div>
                  <div className="text-slate-400 mb-1">Daily Target</div>
                  {isEditing ? (
                    <input
                      type="number"
                      min="0"
                      value={editTarget}
                      onChange={e => setEditTarget(parseInt(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-indigo-500/50 rounded px-2 py-1 text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  ) : (
                    <div className="text-slate-200 font-mono font-semibold text-sm">
                      {p.daily_production_target} units/day
                    </div>
                  )}
                  <div className="text-[10px] text-slate-500 mt-0.5">Max batch per day</div>
                </div>

                <div>
                  <div className="text-slate-400 mb-1">Inventory / Stock</div>
                  <div className="text-slate-200 font-mono font-semibold text-sm flex items-center gap-1.5">
                    {p.inventory_units} units
                    {p.inventory_units === 0 && (
                      <span className="text-rose-400 flex items-center gap-0.5 text-[10px]">
                        <AlertTriangle className="w-3 h-3" /> Out of stock
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Holding Val: {(p.inventory_units * p.production_cost).toFixed(0)} cr
                  </div>
                </div>

                <div>
                  <div className="text-slate-400 mb-1">Unit Margin & Performance</div>
                  <div className="text-slate-200 font-mono font-semibold text-sm flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    +{unitMargin.toFixed(1)} cr ({marginPercent}%)
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Last day: sold {p.units_sold_last_day} | unmet: {p.unmet_demand_last_day}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
