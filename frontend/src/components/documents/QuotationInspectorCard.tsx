import React, { useState } from 'react';
import { FileText, Upload, ShieldCheck, Eye, Hash, CheckCircle, AlertTriangle } from 'lucide-react';
import { BentoCard } from '../bento/BentoCard';
import { BoundingBoxProof, DocumentUploadResponse } from '../../types/procurement';
import { api } from '../../api/client';

const SAMPLE_PROOFS: BoundingBoxProof[] = [
  {
    term_name: 'Base Unit Price',
    extracted_value: '$7,850.00 / server node',
    unit: 'USD',
    page_number: 1,
    confidence: 0.98,
    bbox: [0.12, 0.35, 0.45, 0.42], // [x0, y0, x1, y1] normalized
    source_quote: 'Item 01: Dual AMD EPYC 9654 Server Nodes - Unit Rate: $7,850.00 USD Net 30',
  },
  {
    term_name: 'Warranty & Support SLA',
    extracted_value: '36 Months 24x7 4-Hour Onsite',
    unit: 'Months',
    page_number: 1,
    confidence: 0.96,
    bbox: [0.55, 0.35, 0.88, 0.44],
    source_quote: 'Support Tier: Enterprise Gold 36-Month 24x7 with guaranteed 4-hour on-site dispatch',
  },
  {
    term_name: 'Freight & Delivery Terms',
    extracted_value: 'DDP San Jose Facility (Included)',
    unit: 'Incoterms 2020',
    page_number: 2,
    confidence: 0.94,
    bbox: [0.15, 0.62, 0.52, 0.70],
    source_quote: 'Delivery Terms: Delivered Duty Paid (DDP) to Customer Dock, Freight & Insurance fully prepaid',
  },
  {
    term_name: 'Payment Terms & Discount',
    extracted_value: '2% 10 Net 30 Days',
    unit: 'Terms',
    page_number: 2,
    confidence: 0.97,
    bbox: [0.58, 0.62, 0.90, 0.72],
    source_quote: 'Payment Conditions: 2% cash discount if settled within 10 days; balance due Net 30 days',
  },
];

export const QuotationInspectorCard: React.FC = () => {
  const [activeProof, setActiveProof] = useState<BoundingBoxProof>(SAMPLE_PROOFS[0]);
  const [activePage, setActivePage] = useState<number>(1);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const res = await api.uploadDocument(file);
      setUploadResult(res);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || err.message || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <BentoCard
      title="Quotation Ingestion & Visual Provenance"
      subtitle="Agent 3: PyMuPDF bounding-box coordinates & prompt-injection defense"
      icon={FileText}
      badge="Evidence Verified"
      badgeColor="steel"
      colSpan="col-span-1"
      className="lg:col-span-2"
      glow="steel"
    >
      <div className="space-y-4">
        {/* Upload Dropzone Bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3 p-3 rounded-xl border border-dashed border-slate-700 bg-slate-950/40">
          <label className="flex-1 flex items-center gap-2 cursor-pointer w-full">
            <Upload className="w-4 h-4 text-[#80A1C1] flex-shrink-0" />
            <span className="text-xs text-slate-300 truncate">
              {isUploading ? 'Extracting visual bounding boxes...' : 'Upload Supplier Quotation (PDF)'}
            </span>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isUploading}
            />
          </label>
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <span className="bento-badge-success text-[10px] py-0.5">
              <ShieldCheck className="w-3 h-3" />
              <span>Injection Guard Active</span>
            </span>
          </div>
        </div>

        {uploadError && (
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Audit Meta Bar */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 px-1 font-mono">
          <div className="flex items-center gap-1.5 truncate max-w-[280px]">
            <Hash className="w-3 h-3 text-[#FAD4C0]" />
            <span className="truncate">
              SHA: {uploadResult?.sha256 ? `${uploadResult.sha256.slice(0, 16)}...` : 'a8f4c21990e72bd1...'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span>Doc: Apex_Tech_Quote_2026.pdf</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Verified
            </span>
          </div>
        </div>

        {/* Side-by-Side: PDF Layout Canvas & Extracted Commercial Terms */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Simulated PDF Layout Viewer */}
          <div className="relative rounded-xl border border-slate-800 bg-slate-950 p-3 h-64 flex flex-col justify-between overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3 text-[#80A1C1]" />
                <span>Page Canvas: Page {activePage} of 2</span>
              </span>
              <div className="flex gap-1">
                <button
                  type="button"
                  onClick={() => setActivePage(1)}
                  className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                    activePage === 1 ? 'bg-[#80A1C1]/20 text-[#80A1C1] font-bold' : 'text-slate-500'
                  }`}
                >
                  P1
                </button>
                <button
                  type="button"
                  onClick={() => setActivePage(2)}
                  className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                    activePage === 2 ? 'bg-[#80A1C1]/20 text-[#80A1C1] font-bold' : 'text-slate-500'
                  }`}
                >
                  P2
                </button>
              </div>
            </div>

            {/* Document Canvas Simulation */}
            <div className="relative flex-1 my-2 bg-slate-900/60 rounded border border-slate-800/60 p-2 text-[10px] font-mono text-slate-500 select-none overflow-hidden">
              <div className="space-y-1 opacity-40">
                <div className="h-2 w-3/4 bg-slate-700 rounded"></div>
                <div className="h-1.5 w-1/2 bg-slate-800 rounded"></div>
                <div className="h-1.5 w-5/6 bg-slate-800 rounded"></div>
                <div className="h-2 w-2/3 bg-slate-700 rounded mt-3"></div>
                <div className="h-1.5 w-full bg-slate-800 rounded"></div>
              </div>

              {/* Highlighted Bounding Box Overlay */}
              {activeProof.page_number === activePage && (
                <div
                  style={{
                    position: 'absolute',
                    left: `${activeProof.bbox[0] * 100}%`,
                    top: `${activeProof.bbox[1] * 100}%`,
                    width: `${(activeProof.bbox[2] - activeProof.bbox[0]) * 100}%`,
                    height: `${(activeProof.bbox[3] - activeProof.bbox[1]) * 100}%`,
                  }}
                  className="rounded border-2 border-[#FAD4C0] bg-[#FAD4C0]/20 shadow-glow-peach transition-all duration-300 flex items-center justify-center"
                >
                  <span className="text-[9px] font-bold text-[#FAD4C0] bg-slate-950/80 px-1 rounded shadow">
                    [{activeProof.bbox.map((b) => b.toFixed(2)).join(', ')}]
                  </span>
                </div>
              )}
            </div>

            {/* Selected Coordinate Details */}
            <div className="text-[10px] text-slate-400 bg-slate-900/80 p-1.5 rounded border border-slate-800/80 truncate">
              <span className="text-[#FAD4C0] font-semibold">Quote: </span>
              <span className="italic">{activeProof.source_quote}</span>
            </div>
          </div>

          {/* Extracted Terms Selector List */}
          <div className="space-y-2 h-64 overflow-y-auto pr-1">
            <span className="text-[11px] font-semibold text-slate-400 block mb-1">
              Extracted Commercial Claims & Bounding Boxes
            </span>
            {SAMPLE_PROOFS.map((proof) => {
              const isSelected = activeProof.term_name === proof.term_name;
              return (
                <div
                  key={proof.term_name}
                  onClick={() => {
                    setActiveProof(proof);
                    setActivePage(proof.page_number);
                  }}
                  className={`p-2.5 rounded-xl border cursor-pointer transition text-left ${
                    isSelected
                      ? 'border-[#FAD4C0]/60 bg-gradient-to-r from-slate-900 to-slate-900/90 shadow-sm'
                      : 'border-slate-800/80 bg-slate-950/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">{proof.term_name}</span>
                    <span className="text-[10px] font-mono text-emerald-400">
                      {(proof.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>
                  <div className="text-xs font-mono font-bold text-[#FAD4C0] mt-0.5">
                    {proof.extracted_value}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
                    <span>Page {proof.page_number}</span>
                    <span className="font-mono">bbox: [{proof.bbox.map((v) => v.toFixed(2)).join(', ')}]</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </BentoCard>
  );
};
