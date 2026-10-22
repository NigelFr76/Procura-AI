import React from 'react';
import { Layers, Building2, RefreshCw } from 'lucide-react';

interface HeaderProps {
  tenantName?: string;
  isSSEConnected?: boolean;
  onRefresh?: () => void;
  activePhase?: string;
}

export const Header: React.FC<HeaderProps> = ({
  tenantName = 'Global Manufacturing & Tech Corp',
  isSSEConnected = true,
  onRefresh,
  activePhase = 'Phase 10 & 11: Bento Grid Decision Studio',
}) => {
  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#FAD4C0] via-amber-200 to-[#80A1C1] flex items-center justify-center shadow-glow-peach">
            <Layers className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-white via-slate-100 to-[#FAD4C0] bg-clip-text text-transparent">
                Sourcyn
              </span>
              <span className="bento-badge-peach text-[10px] py-0.5 px-2">
                Bento v2.0
              </span>
            </div>
            <span className="text-[11px] block text-slate-400">
              {activePhase}
            </span>
          </div>
        </div>

        {/* Tenant & Telemetry Badges */}
        <div className="flex items-center space-x-3">
          {/* Tenant */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
            <Building2 className="w-3.5 h-3.5 text-[#80A1C1]" />
            <span className="truncate max-w-[180px]">{tenantName}</span>
          </div>

          {/* SSE Pulse */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
            <span className="relative flex h-2 w-2">
              {isSSEConnected ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
              )}
            </span>
            <span className="hidden md:inline font-mono text-[11px]">
              {isSSEConnected ? 'SSE Live Stream' : 'Reconnecting...'}
            </span>
          </div>

          {/* Refresh Action */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition"
              title="Refresh Workspace State"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
