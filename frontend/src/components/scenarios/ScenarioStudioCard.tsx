import React, { useState } from 'react';
import { Sliders, Zap, AlertTriangle, ArrowUpRight, ArrowDownRight, Minus, RefreshCw, Sparkles } from 'lucide-react';
import { BentoCard } from '../bento/BentoCard';
import { Scorecard, ScenarioRunResult } from '../../types/procurement';
import { api } from '../../api/client';

interface ScenarioStudioCardProps {
  scorecard: Scorecard;
}

export const ScenarioStudioCard: React.FC<ScenarioStudioCardProps> = ({ scorecard }) => {
  const [priceWeight, setPriceWeight] = useState<number>(40);
  const [techWeight, setTechWeight] = useState<number>(40);
  const [riskWeight, setRiskWeight] = useState<number>(20);
  const [costShockPct, setCostShockPct] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [scenarioResult, setScenarioResult] = useState<ScenarioRunResult | null>(null);

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const totalWeight = priceWeight + techWeight + riskWeight;
      const normalizedWeights = {
        financial: priceWeight / totalWeight,
        technical: techWeight / totalWeight,
        risk: riskWeight / totalWeight,
      };

      // Cost adjustments per vendor if costShockPct != 0
      const costAdjustments: Record<string, number> = {};
      if (costShockPct !== 0) {
        scorecard.ranking.forEach((v) => {
          const base = Number(v.landed_cost);
          costAdjustments[v.vendor_id] = base * (1 + costShockPct / 100);
        });
      }

      const res = await api.simulateScenario({
        scenario_name: `What-If Price Sensitivity ${priceWeight}% & Cost Shift ${costShockPct}%`,
        description: 'Simulated parameter shift against immutable baseline evaluation.',
        baseline_scorecard: scorecard,
        criteria_weights_override: normalizedWeights,
        landed_cost_adjustments: Object.keys(costAdjustments).length > 0 ? costAdjustments : undefined,
      });

      setScenarioResult(res);
    } catch (err) {
      console.error('Scenario simulation error', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const renderDelta = (delta: number | string, isCost: boolean = false) => {
    const num = Number(delta);
    if (num > 0) {
      return (
        <span className={`inline-flex items-center text-xs font-mono font-bold ${isCost ? 'text-rose-400' : 'text-emerald-400'}`}>
          <ArrowUpRight className="w-3 h-3 mr-0.5" />
          {isCost ? `+$${num.toLocaleString()}` : `+${num.toFixed(2)}`}
        </span>
      );
    }
    if (num < 0) {
      return (
        <span className={`inline-flex items-center text-xs font-mono font-bold ${isCost ? 'text-emerald-400' : 'text-rose-400'}`}>
          <ArrowDownRight className="w-3 h-3 mr-0.5" />
          {isCost ? `-$${Math.abs(num).toLocaleString()}` : num.toFixed(2)}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center text-xs font-mono text-slate-500">
        <Minus className="w-3 h-3 mr-0.5" /> 0.00
      </span>
    );
  };

  return (
    <BentoCard
      title="What-If Scenario Simulation Studio"
      subtitle="Agent 7 & Python Simulation Engine: Deep differential analysis & winner displacement detection"
      icon={Sliders}
      badge="Zero Side-Effects"
      badgeColor="steel"
      colSpan="col-span-1"
      className="lg:col-span-2"
      glow="steel"
    >
      <div className="space-y-4">
        {/* Sliders Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-3 rounded-xl border border-slate-800 bg-slate-950/60">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-semibold">Price Sensitivity Weight</span>
              <span className="font-mono text-[#FAD4C0] font-bold">{priceWeight}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={80}
              step={5}
              value={priceWeight}
              onChange={(e) => setPriceWeight(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#FAD4C0]"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-semibold">Technical SLA Weight</span>
              <span className="font-mono text-[#80A1C1] font-bold">{techWeight}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={80}
              step={5}
              value={techWeight}
              onChange={(e) => setTechWeight(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#80A1C1]"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-semibold">Risk Penalty Weight</span>
              <span className="font-mono text-amber-400 font-bold">{riskWeight}%</span>
            </div>
            <input
              type="range"
              min={5}
              max={50}
              step={5}
              value={riskWeight}
              onChange={(e) => setRiskWeight(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-semibold">Supply Chain Cost Shock</span>
              <span className={`font-mono font-bold ${costShockPct > 0 ? 'text-rose-400' : costShockPct < 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                {costShockPct > 0 ? `+${costShockPct}%` : `${costShockPct}%`}
              </span>
            </div>
            <input
              type="range"
              min={-20}
              max={30}
              step={5}
              value={costShockPct}
              onChange={(e) => setCostShockPct(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-slate-400"
            />
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSimulate}
            disabled={isSimulating}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold text-xs tracking-wide transition disabled:opacity-50"
          >
            {isSimulating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#FAD4C0]" />
                <span>Simulating Differentials...</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 text-[#FAD4C0]" />
                <span>Simulate Scenario Branch</span>
              </>
            )}
          </button>
        </div>

        {/* Winner Displacement Alert Banner */}
        {scenarioResult && scenarioResult.winner_displaced && (
          <div className="p-3 rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-500/10 to-amber-500/5 text-amber-200 text-xs space-y-1.5">
            <div className="flex items-center gap-2 font-bold text-amber-300">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Winner Displacement Alert!</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              <strong>{scenarioResult.new_winner_name}</strong> displaces{' '}
              <strong>{scenarioResult.baseline_winner_name}</strong> as the #1 ranked supplier under
              these shifted sensitivity constraints.
            </p>
          </div>
        )}

        {/* Differentials Comparison Table */}
        {scenarioResult && (
          <div className="rounded-xl border border-slate-800/80 bg-slate-950 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-[10px] font-mono text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Vendor</th>
                  <th className="py-2 px-2 text-center">Score</th>
                  <th className="py-2 px-2 text-center">Δ Score</th>
                  <th className="py-2 px-2 text-center">Rank</th>
                  <th className="py-2 px-3 text-right">Δ Landed Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {scenarioResult.differentials.map((diff) => (
                  <tr key={diff.vendor_id} className="hover:bg-slate-900/40 transition">
                    <td className="py-2 px-3 font-sans font-semibold text-white">
                      {diff.vendor_name}
                    </td>
                    <td className="py-2 px-2 text-center text-slate-300">
                      {Number(diff.scenario_score).toFixed(1)}
                    </td>
                    <td className="py-2 px-2 text-center">{renderDelta(diff.delta_score)}</td>
                    <td className="py-2 px-2 text-center text-slate-300">
                      #{diff.scenario_rank}{' '}
                      <span className="text-[9px] text-slate-500 font-normal">
                        ({diff.baseline_rank !== diff.scenario_rank ? `was #${diff.baseline_rank}` : 'unchanged'})
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right">{renderDelta(diff.delta_cost, true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Agent 7 Qualitative Trade-off Synthesis */}
        {scenarioResult && scenarioResult.trade_off_analysis && (
          <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 text-xs space-y-1">
            <div className="flex items-center gap-1.5 text-slate-300 font-semibold text-[11px]">
              <Sparkles className="w-3.5 h-3.5 text-[#80A1C1]" />
              <span>Agent 7 Trade-off Rationale:</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {scenarioResult.trade_off_analysis}
            </p>
          </div>
        )}
      </div>
    </BentoCard>
  );
};
