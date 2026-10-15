import React from 'react';
import type { StoredRunRecord } from '../../types/api';
import { AlertBox } from '../../components/AlertBox';
import { ArrowRight, Clock, History, ShieldAlert, Trash2 } from 'lucide-react';

interface Props {
  records: StoredRunRecord[];
  onSelectRun: (record: StoredRunRecord) => void;
  onClearHistory: () => void;
}

export const SessionRunHistory: React.FC<Props> = ({
  records,
  onSelectRun,
  onClearHistory,
}) => {
  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D8D1C2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
              LEDGER //
            </span>
            <h2 className="font-editorial text-2xl font-bold text-[#181B18] tracking-tight">
              Session Simulation History
            </h2>
          </div>
          <p className="text-xs text-[#666E65] mt-0.5 font-sans">
            Local workstation history of scenario and cohort simulations executed during this session.
          </p>
        </div>

        {records.length > 0 && (
          <button
            onClick={onClearHistory}
            className="px-3 py-1.5 text-xs font-mono font-medium text-[#767D75] hover:text-[#9B332B] hover:bg-[#F9ECEB] border border-[#D8D1C2] hover:border-[#DCB0AC] transition-all flex items-center gap-1.5 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Session History</span>
          </button>
        )}
      </div>

      <AlertBox type="info" title="Session Storage Notice">
        In-memory and session records are retained during your browser session. Results can be re-inspected,
        replayed, and exported to JSON or CSV.
      </AlertBox>

      {records.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-[#D8D1C2] bg-[#FAF7F2] text-[#767D75]">
          <History className="w-8 h-8 text-[#B5AC99] mx-auto mb-2 opacity-60" />
          <p className="text-sm font-editorial font-bold text-[#181B18]">
            No simulations executed in this session yet.
          </p>
          <p className="text-xs text-[#666E65] mt-1 font-mono">
            Execute a single-cell or cohort simulation to log results here.
          </p>
        </div>
      ) : (
        <div className="border border-[#D8D1C2] bg-[#FFFFFF] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)] divide-y divide-[#EDE8DE]">
          {records.map((r, idx) => {
            return (
              <div
                key={r.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[#FAF8F3] transition-colors"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-xs text-[#868E85]">#{records.length - idx}</span>
                    <span className="font-editorial text-base font-bold text-[#181B18]">{r.title}</span>
                    <span
                      className={`text-[9.5px] font-mono font-semibold uppercase px-2 py-0.5 border ${
                        r.type === 'single'
                          ? 'bg-[#F9ECEB] text-[#85251E] border-[#DCB0AC]'
                          : 'bg-[#EBF2F7] text-[#2E5875] border-[#B6CEE0]'
                      }`}
                    >
                      {r.type === 'single' ? 'Single Cell' : 'Population Cohort'}
                    </span>
                    {r.hasUnverified && (
                      <span className="text-[9.5px] font-mono font-bold text-[#85251E] bg-[#F7EBEA] px-2 py-0.5 border border-[#962F27] flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" />
                        <span>UNVERIFIED</span>
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-[#666E65] font-mono">
                    <span className="flex items-center gap-1 text-[#484E48]">
                      <Clock className="w-3 h-3 text-[#868E85]" />
                      <span>{r.timestamp}</span>
                    </span>
                    <span>•</span>
                    <span>Chemicals: <strong className="text-[#181B18]">{r.compoundNames.join(', ')}</strong></span>
                    <span>•</span>
                    <span>Model: <code className="text-[#383E38]">{r.modelVersion}</code></span>
                    <span>•</span>
                    <span>G6PD α: <strong className="text-[#435E4B]">{r.g6pdAlpha.toFixed(2)}</strong></span>
                  </div>
                </div>

                {/* Reopen Action */}
                <button
                  onClick={() => onSelectRun(r)}
                  className="px-3.5 py-1.5 text-xs font-mono font-semibold bg-[#FFFFFF] hover:bg-[#FAF7F2] text-[#181B18] border border-[#B5AC99] flex items-center gap-1.5 transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)] shrink-0"
                >
                  <span>Reopen Results</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#9B332B]" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
