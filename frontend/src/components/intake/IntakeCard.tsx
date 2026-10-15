import React, { useState } from 'react';
import { Sparkles, Calendar, DollarSign, Award, AlertCircle, ArrowRight, Loader2, RefreshCw } from 'lucide-react';
import { BentoCard } from '../bento/BentoCard';

export interface IntakeFormData {
  text: string;
  budget_ceiling: number;
  target_delivery_date: string;
  currency: string;
  required_certifications: string[];
}

interface IntakeCardProps {
  onStartEvaluation: (data: IntakeFormData) => Promise<void>;
  isLoading: boolean;
  clarificationQuestions?: string[];
  onSubmitClarification?: (answers: Record<string, string>) => void;
}

const PRESETS = [
  {
    title: '50 HPC Compute Servers',
    desc: 'Procure 50 high-density dual AMD EPYC server nodes with 512GB ECC DDR5, redundant 1600W PSUs, and 3-year on-site 4-hour NBD SLA.',
    budget: 450000,
    certs: ['ISO 9001', 'ISO 27001', 'RoHS'],
  },
  {
    title: 'Industrial 5-Axis CNC Mill',
    desc: 'Precision 5-axis vertical machining center with high-torque spindle, linear glass scales, Renishaw probe, and CE/OSHA safety certification.',
    budget: 320000,
    certs: ['ISO 9001', 'CE', 'OSHA'],
  },
  {
    title: 'Enterprise SIEM & SOC Platform',
    desc: 'Cloud-native Security Information and Event Management platform with multi-tenant log ingestion, automated SOAR playbooks, and 99.99% uptime guarantee.',
    budget: 180000,
    certs: ['SOC 2', 'HIPAA', 'ISO 27001'],
  },
];

const AVAILABLE_CERTS = ['ISO 9001', 'ISO 27001', 'SOC 2', 'HIPAA', 'CE', 'RoHS', 'ITAR'];

export const IntakeCard: React.FC<IntakeCardProps> = ({
  onStartEvaluation,
  isLoading,
  clarificationQuestions = [],
  onSubmitClarification,
}) => {
  const [text, setText] = useState<string>(PRESETS[0].desc);
  const [budget, setBudget] = useState<number>(PRESETS[0].budget);
  const [deliveryDate, setDeliveryDate] = useState<string>('2026-12-15');
  const [currency, setCurrency] = useState<string>('USD');
  const [selectedCerts, setSelectedCerts] = useState<string[]>(PRESETS[0].certs);
  const [clarificationAnswers, setClarificationAnswers] = useState<Record<string, string>>({});

  const toggleCert = (cert: string) => {
    setSelectedCerts((prev) =>
      prev.includes(cert) ? prev.filter((c) => c !== cert) : [...prev, cert]
    );
  };

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    setText(preset.desc);
    setBudget(preset.budget);
    setSelectedCerts(preset.certs);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    onStartEvaluation({
      text,
      budget_ceiling: budget,
      target_delivery_date: deliveryDate,
      currency,
      required_certifications: selectedCerts,
    });
  };

  return (
    <BentoCard
      title="Requirement Intake & Analysis"
      subtitle="Agent 1: Structured LLM parsing & policy constraint gating"
      icon={Sparkles}
      badge="Agent 1 Active"
      badgeColor="peach"
      colSpan="col-span-1"
      className="lg:col-span-2"
      glow="peach"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Preset Selector */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300">Quick-Load RFP Templates</label>
            <span className="text-[11px] text-slate-500">Auto-populates parameters</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.title}
                type="button"
                onClick={() => handleApplyPreset(p)}
                className="text-left px-2.5 py-1.5 rounded-xl border border-slate-800 bg-slate-950/50 hover:bg-slate-800/60 hover:border-slate-700 transition text-xs font-medium text-slate-300 truncate"
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        {/* Natural Language RFP Spec */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Natural Language Specification & Commercial Terms
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            className="w-full rounded-xl bg-slate-950/70 border border-slate-800 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-[#FAD4C0]/60 focus:ring-1 focus:ring-[#FAD4C0]/40 transition"
            placeholder="Describe the items, technical requirements, SLAs, warranties, and delivery constraints..."
            required
          />
        </div>

        {/* Financial Ceiling & Target Date */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-300">
                Budget Ceiling
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded text-[11px] font-mono text-slate-300 px-1.5 py-0.5 focus:outline-none"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="CAD">CAD ($)</option>
              </select>
            </div>
            <div className="relative">
              <DollarSign className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full rounded-xl bg-slate-950/70 border border-slate-800 pl-9 pr-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#FAD4C0]/60 focus:ring-1 focus:ring-[#FAD4C0]/40 transition"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Required Delivery By
            </label>
            <div className="relative">
              <Calendar className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="date"
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                className="w-full rounded-xl bg-slate-950/70 border border-slate-800 pl-9 pr-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#FAD4C0]/60 focus:ring-1 focus:ring-[#FAD4C0]/40 transition"
                required
              />
            </div>
          </div>
        </div>

        {/* Required Certifications Multi-select */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-[#80A1C1]" />
            <span>Mandatory Compliance Certifications</span>
          </label>
          <div className="flex flex-wrap gap-1.5">
            {AVAILABLE_CERTS.map((cert) => {
              const isSelected = selectedCerts.includes(cert);
              return (
                <button
                  key={cert}
                  type="button"
                  onClick={() => toggleCert(cert)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                    isSelected
                      ? 'bg-[#80A1C1]/20 text-[#80A1C1] border border-[#80A1C1]/40'
                      : 'bg-slate-950/60 text-slate-400 border border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {cert}
                </button>
              );
            })}
          </div>
        </div>

        {/* Clarification Loop (Agent 1 Cyclic Feedback) */}
        {clarificationQuestions.length > 0 && (
          <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 space-y-3">
            <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
              <AlertCircle className="w-4 h-4" />
              <span>Agent 1 Flagged Missing Requirement Specifics</span>
            </div>
            <p className="text-[11px] text-amber-200/80">
              The requirement analysis agent identified ambiguities in the request. Please provide clarification:
            </p>
            {clarificationQuestions.map((q, idx) => (
              <div key={idx} className="space-y-1">
                <span className="text-[11px] text-slate-300 font-medium block">Q{idx + 1}: {q}</span>
                <input
                  type="text"
                  placeholder="Provide clarification details..."
                  onChange={(e) =>
                    setClarificationAnswers((prev) => ({ ...prev, [q]: e.target.value }))
                  }
                  className="w-full rounded-lg bg-slate-900 border border-amber-500/30 px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>
            ))}
            {onSubmitClarification && (
              <button
                type="button"
                onClick={() => onSubmitClarification(clarificationAnswers)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 text-slate-950 text-xs font-bold hover:bg-amber-400 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Submit Clarifications & Resume Graph
              </button>
            )}
          </div>
        )}

        {/* Action Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#FAD4C0] via-amber-200 to-[#80A1C1] text-slate-950 font-bold text-xs tracking-wide shadow-lg shadow-[#FAD4C0]/20 hover:opacity-95 transition disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Orchestrating 9-Agent Pipeline...</span>
              </>
            ) : (
              <>
                <span>Execute Multi-Agent Procurement Evaluation</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </BentoCard>
  );
};
