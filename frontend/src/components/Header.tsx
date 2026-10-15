import React, { useState } from 'react';
import { Activity, Database, History, Info, Menu, RefreshCw, Users, X } from 'lucide-react';
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

const NAV_ITEMS: Array<{
  id: ActiveTab;
  number: string;
  label: string;
  descriptor: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  {
    id: 'playground',
    number: '01',
    label: 'Blood Playground',
    descriptor: 'Single-cell ODE solver & kinetics',
    icon: Activity,
  },
  {
    id: 'compounds',
    number: '02',
    label: 'Compound Library',
    descriptor: 'Curated biochemical index & SMILES',
    icon: Database,
  },
  {
    id: 'population',
    number: '03',
    label: 'Population Cohort',
    descriptor: 'Vectorized Monte Carlo priors',
    icon: Users,
  },
  {
    id: 'history',
    number: '04',
    label: 'Run History',
    descriptor: 'Session workstation logbook',
    icon: History,
  },
  {
    id: 'models',
    number: '05',
    label: 'Model & Evidence',
    descriptor: 'Kinetic boundaries & provenance',
    icon: Info,
  },
];

export const Header: React.FC<Props> = ({
  activeTab,
  onTabChange,
  health,
  healthLoading,
  healthError,
  onRetryHealth,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSelectTab = (tab: ActiveTab) => {
    onTabChange(tab);
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Top Masthead */}
      <header className="lg:hidden bg-[#FAF7F2] border-b border-[#D8D1C2] px-4 py-3 flex items-center justify-between sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-[#9B332B] text-white flex items-center justify-center font-mono font-bold text-xs shadow-[1px_1px_0px_0px_rgba(24,27,24,0.2)]">
            V•B
          </div>
          <div>
            <div className="font-editorial text-base font-bold text-[#181B18] tracking-tight flex items-center gap-2">
              <span>V-Blood</span>
              <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">v0.4.0</span>
            </div>
            <div className="text-[10px] text-[#767D75] font-mono">Field Station // Erythrocyte Kinetics</div>
          </div>
        </div>

        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 border border-[#D8D1C2] bg-[#FFFFFF] text-[#484E48] hover:text-[#181B18]"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* Navigation Rail (Sidebar on lg+, collapsible drawer on mobile) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#FAF7F2] border-r border-[#D8D1C2] flex flex-col justify-between transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Top Masthead & Station Identification */}
        <div className="p-5 border-b border-[#D8D1C2] bg-[#F4EFE6]/60">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 border border-[#9B332B] bg-[#9B332B] text-white flex flex-col items-center justify-center font-mono font-bold text-sm shadow-[2px_2px_0px_0px_rgba(24,27,24,0.15)]">
                <span>VB</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="font-editorial text-xl font-bold tracking-tight text-[#181B18]">
                    V-Blood
                  </h1>
                  <span className="font-mono text-[9px] uppercase tracking-wider px-1 py-0.5 border border-[#B5AC99] bg-[#EDE8DE] text-[#484E48] font-semibold">
                    v0.4.0
                  </span>
                </div>
                <div className="text-[10.5px] font-mono text-[#666E65] tracking-tight">
                  In Silico Erythrocyte Station
                </div>
              </div>
            </div>

            {/* Close button for mobile */}
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden p-1 text-[#767D75] hover:text-[#181B18]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 pt-2.5 border-t border-[#D8D1C2]/80 flex items-center justify-between text-[10px] font-mono text-[#767D75]">
            <span>STATION: FIELD-RED-04</span>
            <span className="text-[#435E4B] font-medium">ODE SOLVER RK4</span>
          </div>
        </div>

        {/* Primary Scientific Navigation Rail */}
        <nav className="flex-1 py-3 px-3 space-y-1 overflow-y-auto">
          <div className="px-2 py-1 text-[9.5px] font-mono uppercase tracking-widest text-[#868E85]">
            Instrumentation Modules
          </div>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelectTab(item.id)}
                className={`w-full text-left p-2.5 transition-all flex items-start gap-3 border ${
                  isActive
                    ? 'bg-[#FFFFFF] border-[#B5AC99] text-[#181B18] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)] relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-[#9B332B]'
                    : 'bg-transparent border-transparent text-[#484E48] hover:bg-[#F2ECE1] hover:border-[#DDD6C8] hover:text-[#181B18]'
                }`}
              >
                <span
                  className={`font-mono text-[11px] font-semibold mt-0.5 ${
                    isActive ? 'text-[#9B332B]' : 'text-[#868E85]'
                  }`}
                >
                  {item.number}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-xs font-semibold tracking-tight ${
                        isActive ? 'text-[#181B18]' : 'text-[#383E38]'
                      }`}
                    >
                      {item.label}
                    </span>
                    <Icon
                      className={`w-3.5 h-3.5 ${
                        isActive ? 'text-[#9B332B]' : 'text-[#9CA49C]'
                      }`}
                    />
                  </div>
                  <div className="text-[10px] text-[#767D75] truncate mt-0.5">
                    {item.descriptor}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>

        {/* Telemetry, Backend Status & Research Boundary */}
        <div className="p-3.5 border-t border-[#D8D1C2] bg-[#F2ECE1]/70 space-y-3">
          {/* Real Backend Status */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-mono text-[#767D75]">
              <span>CORE API TELEMETRY</span>
              <span className="text-[9px]">PORT 8000</span>
            </div>

            {healthLoading ? (
              <div className="flex items-center justify-between p-2 border border-[#D8D1C2] bg-[#FCFAF6] text-[11px] font-mono text-[#767D75]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-none bg-[#8E5A1E] animate-pulse" />
                  <span>Polling backend...</span>
                </div>
                <RefreshCw className="w-3 h-3 animate-spin text-[#8E5A1E]" />
              </div>
            ) : health ? (
              <div
                className="p-2 border border-[#BCD0C1] bg-[#EDF3EE] text-[11px] font-mono text-[#284431] space-y-1 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.04)]"
                title={`FastAPI ${health.status.toUpperCase()} • ${health.registered_models_count} models registered.`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-semibold">
                    <span className="w-2 h-2 rounded-none bg-[#3E5C46]" />
                    <span>SYSTEM ONLINE</span>
                  </div>
                  <span className="text-[10px] text-[#435E4B]">2 MODELS</span>
                </div>
                <div className="text-[9.5px] text-[#4F6856] truncate">
                  Mass conservation active
                </div>
              </div>
            ) : (
              <div className="p-2 border border-[#DCB0AC] bg-[#F9ECEB] text-[11px] font-mono text-[#7D221C] space-y-1.5 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.04)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-semibold">
                    <span className="w-2 h-2 rounded-none bg-[#9B332B] animate-pulse" />
                    <span>OFFLINE</span>
                  </div>
                  <button
                    onClick={onRetryHealth}
                    className="px-1.5 py-0.5 text-[9px] uppercase tracking-wider bg-[#FFFFFF] border border-[#DCB0AC] hover:bg-[#F2ECE1] text-[#7D221C] transition-colors"
                  >
                    Retry
                  </button>
                </div>
                <div className="text-[9.5px] text-[#9B332B] truncate">
                  {healthError || '127.0.0.1:8000 unreachable'}
                </div>
              </div>
            )}
          </div>

          {/* Research Inscription */}
          <div className="border border-[#D8D1C2] bg-[#FFFFFF] p-2 text-[9.5px] leading-tight text-[#666E65]">
            <strong className="font-mono text-[9px] text-[#9B332B] block mb-0.5 uppercase tracking-wider">
              Research Notice:
            </strong>
            Mechanistic in silico models simulate redox hypotheses only. NOT for clinical dosing or medical decisions.
          </div>
        </div>
      </aside>

      {/* Backdrop for mobile drawer */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs lg:hidden"
        />
      )}
    </>
  );
};
