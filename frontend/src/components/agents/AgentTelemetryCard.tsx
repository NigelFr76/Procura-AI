import React from 'react';
import { Cpu, CheckCircle2, Clock, PlayCircle, Activity } from 'lucide-react';
import { BentoCard } from '../bento/BentoCard';

export interface AgentNodeStatus {
  id: string;
  name: string;
  agentLabel: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'INTERRUPTED' | 'FAILED';
  executionMs?: number;
  outputSummary?: string;
}

interface AgentTelemetryCardProps {
  currentStatus: string;
  threadId?: string;
  nodes?: AgentNodeStatus[];
  liveLogs?: string[];
}

const DEFAULT_NODES: AgentNodeStatus[] = [
  {
    id: 'intake',
    name: 'Requirement Analysis',
    agentLabel: 'Agent 1 (LLM Structured)',
    status: 'COMPLETED',
    executionMs: 1420,
    outputSummary: 'Parsed 3 items, ISO 9001 constraint, $450K budget ceiling',
  },
  {
    id: 'discovery',
    name: 'Vendor Discovery',
    agentLabel: 'Agent 2 (Hybrid SQL/Vector)',
    status: 'COMPLETED',
    executionMs: 820,
    outputSummary: 'Shortlisted 3 eligible vendors from enterprise registry',
  },
  {
    id: 'quotation',
    name: 'Quotation Layout Ingestion',
    agentLabel: 'Agent 3 (PyMuPDF OCR)',
    status: 'COMPLETED',
    executionMs: 2150,
    outputSummary: 'Extracted 18 commercial clauses, verified bounding boxes',
  },
  {
    id: 'parallel_eval',
    name: 'Compliance & Risk Gating',
    agentLabel: 'Agents 4 & 5 (Parallel Fan-Out)',
    status: 'COMPLETED',
    executionMs: 1890,
    outputSummary: 'Zero policy violations, evaluated financial and delivery risk',
  },
  {
    id: 'scoring',
    name: 'Deterministic Scoring',
    agentLabel: 'Python Scoring Engine',
    status: 'COMPLETED',
    executionMs: 45,
    outputSummary: 'Computed landed costs, applied normalized weights, generated SHA fingerprint',
  },
  {
    id: 'explanation',
    name: 'Decision Explanation',
    agentLabel: 'Agent 8 (Anti-Hallucination LLM)',
    status: 'COMPLETED',
    executionMs: 1650,
    outputSummary: 'Grounded rationale synthesized with zero unverified claims',
  },
  {
    id: 'approval_gate',
    name: 'HITL Human Approval Gate',
    agentLabel: 'LangGraph Interrupt() Gate',
    status: 'INTERRUPTED',
    executionMs: 0,
    outputSummary: 'Waiting for authorized Human Officer sign-off',
  },
];

export const AgentTelemetryCard: React.FC<AgentTelemetryCardProps> = ({
  currentStatus = 'AWAITING_APPROVAL',
  threadId = 'eval-thread-live-01',
  nodes = DEFAULT_NODES,
  liveLogs = [
    '[10:45:01] LangGraph state graph compiled with PostgresSaver checkpointing.',
    '[10:45:02] Agent 1 extracted structured RFP spec and validated policy bounds.',
    '[10:45:03] Parallel fan-out initiated for 3 shortlisted suppliers.',
    '[10:45:05] Deterministic scoring finalized: Apex Technologies ranked #1 (91.50).',
    '[10:45:06] LangGraph interrupt() triggered at approval_gate node. Awaiting officer sign-off.',
  ],
}) => {
  const getNodeColor = (status: AgentNodeStatus['status']) => {
    switch (status) {
      case 'COMPLETED':
        return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400';
      case 'RUNNING':
        return 'border-[#FAD4C0] bg-[#FAD4C0]/20 text-[#FAD4C0] animate-pulse';
      case 'INTERRUPTED':
        return 'border-amber-500/60 bg-amber-500/10 text-amber-300';
      case 'FAILED':
        return 'border-rose-500/40 bg-rose-500/10 text-rose-400';
      case 'PENDING':
      default:
        return 'border-slate-800 bg-slate-950/40 text-slate-500';
    }
  };

  return (
    <BentoCard
      title="Multi-Agent LangGraph Workflow Telemetry"
      subtitle="Real-time parallel agent execution, cyclic clarification loops, and interrupt checkpoints"
      icon={Cpu}
      badge={currentStatus}
      badgeColor={currentStatus.includes('APPROVAL') ? 'warning' : 'success'}
      colSpan="col-span-1"
      className="md:col-span-2 lg:col-span-4"
      headerAction={
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-spin" />
          <span>Thread: {threadId.slice(0, 18)}...</span>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Node Stepper Pipeline */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
          {nodes.map((node, index) => {
            const isCompleted = node.status === 'COMPLETED';
            const isInterrupted = node.status === 'INTERRUPTED';
            const isRunning = node.status === 'RUNNING';

            return (
              <div
                key={node.id}
                className={`relative rounded-xl border p-2.5 transition flex flex-col justify-between ${getNodeColor(
                  node.status
                )}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono text-slate-400 font-bold">
                      0{index + 1}
                    </span>
                    {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                    {isInterrupted && <Clock className="w-3.5 h-3.5 text-amber-400 animate-bounce" />}
                    {isRunning && <PlayCircle className="w-3.5 h-3.5 text-[#FAD4C0] animate-spin" />}
                  </div>
                  <h4 className="text-xs font-bold tracking-tight text-white line-clamp-1">
                    {node.name}
                  </h4>
                  <p className="text-[10px] text-slate-400 mt-0.5 truncate">{node.agentLabel}</p>
                </div>

                <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[9px] font-mono">
                  <span className="text-slate-400 truncate">{node.status}</span>
                  {node.executionMs !== undefined && node.executionMs > 0 && (
                    <span className="text-[#80A1C1]">{node.executionMs}ms</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Live SSE Execution Log Console */}
        <div className="rounded-xl border border-slate-800/90 bg-slate-950 p-3 space-y-1.5 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 pb-1 border-b border-slate-800/60 text-[11px]">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>SSE Real-Time Orchestration Feed</span>
            </span>
            <span className="text-[10px] text-slate-500">PostgreSQL Durable Checkpoint</span>
          </div>
          <div className="max-h-24 overflow-y-auto space-y-1 pr-1 text-[11px]">
            {liveLogs.map((log, i) => (
              <div key={i} className="text-slate-300 leading-relaxed truncate">
                <span className="text-[#80A1C1] mr-1.5">›</span>
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </BentoCard>
  );
};
