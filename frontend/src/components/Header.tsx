import React from 'react';
import { Activity, Database, FlaskConical, History, Info, Users } from 'lucide-react';
import type { HealthResponse } from '../types/api';

export type ActiveTab = 'playground' | 'compounds' | 'population' | 'history' | 'models';

interface Props {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: string | null;
  onRetryHealth: () => void;
}

export const Header: React.FC<Props> = ({
  activeTab,
  onTabChange,
  health,
  healthLoading,
  healthError,
  onRetryHealth,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/95 sticky top-0 z-40 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Info */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-rose-950 border border-rose-700/60 flex items-center justify-center text-rose-400 font-bold shadow-inner">
              <FlaskConical className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-100 tracking-tight text-lg">V-Blood</span>
                <span className="text-xs font-mono uppercase bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">
                  v0.4.0
                </span>
              </div>
              <div className="text-xs text-slate-400">Blood Playground • Mechanistic In Silico Research</div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => onTabChange('playground')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'playground'
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Activity className="w-4 h-4 text-rose-400" />
              <span>Playground</span>
            </button>

            <button
              onClick={() => onTabChange('compounds')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'compounds'
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Compound Library</span>
            </button>

            <button
              onClick={() => onTabChange('population')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'population'
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Users className="w-4 h-4 text-blue-400" />
              <span>Population Cohort</span>
            </button>

            <button
              onClick={() => onTabChange('history')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'history'
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <History className="w-4 h-4 text-purple-400" />
              <span>Run History</span>
            </button>

            <button
              onClick={() => onTabChange('models')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'models'
                  ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Info className="w-4 h-4 text-amber-400" />
              <span>Model & Evidence</span>
            </button>
          </nav>

          {/* Backend Status */}
          <div className="flex items-center gap-3">
            {healthLoading ? (
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                Connecting API...
              </span>
            ) : health ? (
              <span
                className="text-xs text-emerald-400 flex items-center gap-1.5 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/60"
                title={`API ${health.status.toUpperCase()} • ${health.registered_models_count} models registered.`}
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Backend Connected</span>
              </span>
            ) : (
              <button
                onClick={onRetryHealth}
                className="text-xs text-rose-400 flex items-center gap-1.5 bg-rose-950/40 px-2 py-1 rounded border border-rose-800/80 hover:bg-rose-900/60 transition-colors"
                title={healthError || 'Backend unreachable'}
              >
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                <span>Backend Offline (Retry)</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Persistent Research Use Notice */}
      <div className="bg-slate-900/90 border-t border-slate-800/80 px-4 py-1 text-center text-[11px] text-slate-400 flex items-center justify-center gap-2">
        <span className="font-semibold text-amber-400/90 uppercase tracking-wider">Research Prototype Notice:</span>
        <span>Simulations generate mechanistic hypotheses only. NOT for clinical diagnostics, patient therapy, or real-world dosing.</span>
      </div>
    </header>
  );
};
