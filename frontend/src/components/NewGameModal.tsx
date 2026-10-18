import React, { useState } from 'react';
import { Sparkles, X, Check } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreateGame: (data: {
    company_name: string;
    starting_cash: number;
    initial_product_name: string;
    initial_product_price: number;
    initial_product_cost: number;
    initial_daily_target: number;
  }) => Promise<void>;
}

export const NewGameModal: React.FC<Props> = ({ isOpen, onClose, onCreateGame }) => {
  const [name, setName] = useState("Vanguard Technologies");
  const [startingCash, setStartingCash] = useState(10000.0);
  const [productName, setProductName] = useState("Quantum Core Processor");
  const [price, setPrice] = useState(140.0);
  const [cost, setCost] = useState(50.0);
  const [target, setTarget] = useState(15);
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onCreateGame({
        company_name: name,
        starting_cash: startingCash,
        initial_product_name: productName,
        initial_product_price: price,
        initial_product_cost: cost,
        initial_daily_target: target
      });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Found a New Company</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Company Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Starting Treasury (Credits)</label>
            <input
              type="number"
              min="1000"
              max="100000"
              value={startingCash}
              onChange={e => setStartingCash(parseFloat(e.target.value) || 10000)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
            />
            <span className="text-[10px] text-slate-500 mt-0.5 block">Default standard start is 10,000 cr.</span>
          </div>

          <div className="pt-2 border-t border-slate-800/80">
            <span className="font-semibold text-slate-300 block mb-2">Initial Flagship Product</span>
            <div className="space-y-2">
              <div>
                <label className="text-slate-400 block mb-0.5">Product Name</label>
                <input
                  type="text"
                  required
                  value={productName}
                  onChange={e => setProductName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-slate-400 block mb-0.5">Unit Price (cr)</label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    value={price}
                    onChange={e => setPrice(parseFloat(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-0.5">Unit Cost (cr)</label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    value={cost}
                    onChange={e => setCost(parseFloat(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-0.5">Daily Target</label>
                  <input
                    type="number"
                    min="0"
                    value={target}
                    onChange={e => setTarget(parseInt(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
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
              disabled={submitting}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              Found Company
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
