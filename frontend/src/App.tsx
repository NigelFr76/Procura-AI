import { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Database, 
  GitBranch, 
  Layers, 
  CheckCircle2, 
  Activity,
  ArrowRight
} from 'lucide-react';

interface HealthStatus {
  status: string;
  service: string;
  environment: string;
  version: string;
  timestamp: string;
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                ProcureAI Intelligence
              </span>
              <span className="text-xs block text-slate-400">Enterprise Multi-Agent Platform</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>Phase 9 Active: REST Endpoints & Real-Time SSE Streaming</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-10 w-full space-y-10">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/90 to-slate-900/40 p-8 md:p-12 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="max-w-3xl space-y-4">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Multi-Agent LangGraph Architecture</span>
            </div>
            <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
              AI Procurement & <br className="hidden md:block" />
              <span className="bg-gradient-to-r from-sky-400 via-indigo-300 to-emerald-400 bg-clip-text text-transparent">
                Vendor Intelligence Platform
              </span>
            </h1>
            <p className="text-slate-400 text-base md:text-lg leading-relaxed">
              Transparent, evidence-based purchasing decisions through specialized multi-agent workflows,
              deterministic multi-criteria scoring, and what-if scenario simulations.
            </p>
          </div>
        </div>

        {/* System Core Health & Readiness */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">FastAPI Backend</span>
              <Activity className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>{loading ? "Checking..." : error ? "Offline (Local)" : "Healthy"}</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {health?.version ? `API v${health.version}` : 'FastAPI 0.111.0'}
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">PostgreSQL 16 + pgvector</span>
              <Database className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>Configured</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Docker Compose Port 5432</p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">LangGraph Engine</span>
              <Cpu className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>v1.2.15 Ready</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Stateful Graph & Checkpointing</p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Scenario Engine</span>
              <GitBranch className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>Stateless Python</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Deterministic Pure Math</p>
          </div>
        </div>

        {/* Implementation Status Grid */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Execution Roadmap: Phases 1 to 12</h2>
              <p className="text-xs text-slate-400">Strictly following IMPLEMENTATION_PLAN.md</p>
            </div>
            <span className="text-xs text-sky-400 font-mono">9 of 12 Complete</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 1: Infra & Scaffold</span>
              </div>
              <p className="text-xs text-slate-400">
                Docker Compose, PostgreSQL pgvector init, uv backend virtualenv, FastAPI app, and React Vite.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 2: Database & Models</span>
              </div>
              <p className="text-xs text-slate-400">
                SQLAlchemy 2.x async models, tenant isolation context, Alembic migrations for 16 core entities.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 3: Scoring Engine</span>
              </div>
              <p className="text-xs text-slate-400">
                Landed cost, bounded criterion normalizers, eligibility gate, and deterministic tie-breaking.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 4: Ingestion & OCR</span>
              </div>
              <p className="text-xs text-slate-400">
                PyMuPDF parser, normalized coordinate bounding boxes, prompt injection detection, and RRF retrieval.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 5: Intake Agents (1, 2, 3)</span>
              </div>
              <p className="text-xs text-slate-400">
                Requirement Analysis, Vendor Discovery, and Quotation Analysis Agents with evidence coordinate citations.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 6: Compliance & Risk (4, 5)</span>
              </div>
              <p className="text-xs text-slate-400">
                Deterministic compliance rule gating + clause verification; multi-dimensional risk telemetry with sparse data penalties.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 7: LangGraph Multi-Agent (8, 9)</span>
              </div>
              <p className="text-xs text-slate-400">
                StateGraph orchestration, parallel vendor evaluation fan-out/fan-in, guarded Decision Explanation Agent (8), Decision Coordinator (9), and HITL interrupt gate.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 8: Negotiation & Scenarios (6, 7)</span>
              </div>
              <p className="text-xs text-slate-400">
                Negotiation Simulation Agent (6) with cost floors; What-If Scenario Simulation Engine (7) with immutable deep copies and winner displacement analysis.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-400 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Phase 9: REST APIs & Event Streaming</span>
              </div>
              <p className="text-xs text-slate-400">
                FastAPI v1 endpoints for evaluations, scenarios, negotiations, requests, uploads; real-time SSE streaming broadcaster and async background worker.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-sky-500/40 bg-sky-950/20 space-y-2 relative overflow-hidden">
            <div className="flex items-center space-x-2 text-sky-400 font-medium">
              <ArrowRight className="w-4 h-4 text-sky-400 animate-pulse" />
              <span>Next Up: Phase 10 (Frontend Foundation, Design System, Intake & Extraction Review)</span>
            </div>
            <p className="text-xs text-slate-400">
              Modern enterprise React design system, multi-tenant workspace, dynamic requirement intake form with validation, quotation upload dropzone, and side-by-side PDF coordinate highlighter.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-6">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 space-y-2 md:space-y-0">
          <p>AI Procurement & Vendor Intelligence Platform • Phase 1 Scaffold</p>
          <p className="font-mono">LangGraph • FastAPI • PostgreSQL 16 pgvector • React Vite</p>
        </div>
      </footer>
    </div>
  );
}
