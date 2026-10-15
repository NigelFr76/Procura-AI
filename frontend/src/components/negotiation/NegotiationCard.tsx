import React, { useState } from 'react';
import { MessageSquareText, TrendingDown, Shield, RefreshCw } from 'lucide-react';
import { BentoCard } from '../bento/BentoCard';
import { NegotiationSimResult } from '../../types/procurement';
import { api } from '../../api/client';

export const NegotiationCard: React.FC = () => {
  const vendorName = 'Apex Technologies';
  const initialPrice = 392500;
  const [targetDiscount, setTargetDiscount] = useState<number>(12);
  const [strategy, setStrategy] = useState<'BALANCED' | 'AGGRESSIVE' | 'CONSERVATIVE'>('BALANCED');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [negotiationResult, setNegotiationResult] = useState<NegotiationSimResult | null>(null);

  const handleSimulateNegotiation = async () => {
    setIsSimulating(true);
    try {
      const res = await api.simulateNegotiation({
        vendor_id: 'vendor-apex-01',
        vendor_name: vendorName,
        baseline_quoted_price: initialPrice,
        target_discount_pct: targetDiscount,
        max_rounds: 3,
        concession_strategy: strategy,
        cost_floor_margin: 0.15,
      });
      setNegotiationResult(res);
    } catch (err) {
      console.error('Negotiation sim error', err);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <BentoCard
      title="Autonomous Negotiation Simulation"
      subtitle="Agent 6: Counteroffer elasticity frontier & bounded concession rounds"
      icon={MessageSquareText}
      badge="Agent 6 Active"
      badgeColor="peach"
      colSpan="col-span-1"
      className="lg:col-span-2"
      glow="peach"
    >
      <div className="space-y-4">
        {/* Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-xl border border-slate-800 bg-slate-950/60">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Target Discount: <span className="text-[#FAD4C0] font-mono">{targetDiscount}%</span>
            </label>
            <input
              type="range"
              min={3}
              max={25}
              step={1}
              value={targetDiscount}
              onChange={(e) => setTargetDiscount(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#FAD4C0]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Tactic</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as any)}
              className="w-full rounded-lg bg-slate-900 border border-slate-800 px-2 py-1.5 text-xs text-white"
            >
              <option value="BALANCED">Balanced Compromise</option>
              <option value="AGGRESSIVE">Aggressive Price-First</option>
              <option value="CONSERVATIVE">Conservative / SLA Focus</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="button"
              onClick={handleSimulateNegotiation}
              disabled={isSimulating}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold text-white transition disabled:opacity-50"
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Simulating...</span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-3.5 h-3.5 text-[#FAD4C0]" />
                  <span>Run Counteroffer Sim</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {negotiationResult && (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10">
              <div>
                <span className="text-xs text-emerald-300 font-semibold block">
                  Simulated Outcome: {negotiationResult.outcome}
                </span>
                <span className="text-[11px] text-emerald-200/80">
                  Negotiated savings of ${(negotiationResult.initial_price - negotiationResult.final_price).toLocaleString()} ({negotiationResult.achieved_discount_pct.toFixed(1)}%)
                </span>
              </div>
              <div className="text-right font-mono">
                <span className="text-sm font-extrabold text-white">
                  ${negotiationResult.final_price.toLocaleString()}
                </span>
                <span className="text-[10px] text-slate-400 block line-through">
                  ${negotiationResult.initial_price.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Concession Rounds Timeline */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 block">
                Concession Rounds & Elasticity Response
              </span>
              {negotiationResult.rounds.map((round) => (
                <div
                  key={round.round_number}
                  className="p-2 rounded-lg border border-slate-800/80 bg-slate-950/60 flex items-center justify-between text-xs font-mono"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-[10px] text-slate-300 flex items-center justify-center font-bold">
                      R{round.round_number}
                    </span>
                    <span className="text-slate-300">
                      Buyer: ${round.buyer_target_price.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[#FAD4C0]">
                      Counter: ${round.seller_counteroffer.toLocaleString()}
                    </span>
                    <span className="text-emerald-400 text-[11px]">
                      -${round.concession_amount.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Cost Floor Safeguard note */}
            <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
              <Shield className="w-3 h-3 text-[#80A1C1]" />
              <span>Cost Floor Protected: ${negotiationResult.cost_floor.toLocaleString()} (Vendor Margin Invariant Enforced)</span>
            </div>
          </div>
        )}
      </div>
    </BentoCard>
  );
};
