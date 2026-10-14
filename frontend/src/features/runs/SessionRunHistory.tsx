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
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-purple-400" />
            <span>Session Simulation History</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Local workstation history of scenario and cohort simulations executed during this session.
          </p>
        </div>

        {records.length > 0 && (
          <button
            onClick={onClearHistory}
            className="px-3 py-1.5 text-xs text-slate-400 hover:text-rose-300 hover:bg-rose-950/40 rounded border border-slate-800 hover:border-rose-900 transition-colors flex items-center gap-1.5"
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
        <div className="text-center py-16 border border-dashed border-slate-800 rounded-lg text-slate-500">
          <History className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-60" />
          <p className="text-sm">No simulations executed in this session yet.</p>
          <p className="text-xs text-slate-600 mt-1">Run a single-cell or cohort simulation to log results here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((r) => {
            return (
              <div
                key={r.id}
                className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-all shadow-sm"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5">
                    <span className="text-sm font-bold text-slate-200">{r.title}</span>
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded border ${
                        r.type === 'single'
                          ? 'bg-rose-950 text-rose-300 border-rose-800'
                          : 'bg-blue-950 text-blue-300 border-blue-800'
                      }`}
                    >
                      {r.type === 'single' ? 'Single Cell' : 'Population Cohort'}
                    </span>
                    {r.hasUnverified && (
                      <span className="text-[10px] font-semibold text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" />
                        <span>UNVERIFIED</span>
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center gap-1 text-slate-500 font-mono">
                      <Clock className="w-3 h-3" />
                      <span>{r.timestamp}</span>
                    </span>
                    <span>•</span>
                    <span>Chemicals: <strong className="text-slate-300">{r.compoundNames.join(', ')}</strong></span>
                    <span>•</span>
                    <span>Model: <code className="text-slate-300">{r.modelVersion}</code></span>
                    <span>•</span>
                    <span>G6PD α: <strong className="text-emerald-400 font-mono">{r.g6pdAlpha.toFixed(2)}</strong></span>
                  </div>
                </div>

                {/* Reopen Action */}
                <button
                  onClick={() => onSelectRun(r)}
                  className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5 transition-colors shrink-0"
                >
                  <span>Reopen Results</span>
                  <ArrowRight className="w-3.5 h-3.5 text-rose-400" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
