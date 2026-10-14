import React from 'react';
import type { CompoundResponse } from '../../types/api';
import { EvidenceBadge } from '../../components/EvidenceBadge';
import { AlertBox } from '../../components/AlertBox';
import { ExternalLink, X } from 'lucide-react';

interface Props {
  compound: CompoundResponse | null;
  onClose: () => void;
  onSelectForScenario?: (compound: CompoundResponse) => void;
}

export const CompoundModal: React.FC<Props> = ({
  compound,
  onClose,
  onSelectForScenario,
}) => {
  if (!compound) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 sticky top-0 bg-slate-900/95 backdrop-blur z-10">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold text-slate-100">{compound.name}</h2>
              <EvidenceBadge level={compound.evidence_level} />
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">{compound.compound_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 flex-1">
          {/* Unverified Warning */}
          {compound.is_unverified && (
            <AlertBox type="error" title="UNVERIFIED KINETIC MECHANISM">
              This compound is a synthetic probe or unverified research entry. Its kinetic rates
              are hypothetical and not calibrated against experimental human RBC measurements.
              Results generated using this compound are excluded from platform validation scoring.
            </AlertBox>
          )}

          {/* Chemical Identifiers */}
          <div className="bg-slate-950/70 rounded-lg p-4 border border-slate-800 space-y-2.5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Chemical Identifiers</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block">SMILES</span>
                <span className="font-mono text-slate-200 break-all bg-slate-900 px-2 py-1 rounded block mt-0.5 border border-slate-800">
                  {compound.smiles || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">InChIKey</span>
                <span className="font-mono text-slate-200 break-all bg-slate-900 px-2 py-1 rounded block mt-0.5 border border-slate-800">
                  {compound.inchikey || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Mechanism & Units */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-500 block">Mechanism Type</span>
              <span className="text-sm font-semibold text-slate-200 mt-0.5 block">
                {compound.mechanism_type.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-500 block">Exposure Units</span>
              <span className="text-sm font-mono text-slate-200 mt-0.5 block">{compound.exposure_units}</span>
            </div>
            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-500 block">Confidence Score</span>
              <span className="text-sm font-mono text-emerald-400 mt-0.5 block">
                {(compound.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Default Parameters & Bounds */}
          <div className="bg-slate-950/70 rounded-lg p-4 border border-slate-800">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2.5">
              Default Kinetic Parameters & Valid Bounds
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 font-medium">
                    <th className="py-1.5 px-2">Parameter</th>
                    <th className="py-1.5 px-2">Default Value</th>
                    <th className="py-1.5 px-2">Valid Range</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {Object.entries(compound.default_parameters).map(([param, val]) => {
                    const range = compound.parameter_ranges[param];
                    return (
                      <tr key={param} className="text-slate-300">
                        <td className="py-2 px-2 text-slate-400 font-sans">{param}</td>
                        <td className="py-2 px-2 text-emerald-400 font-semibold">{String(val)}</td>
                        <td className="py-2 px-2 text-slate-500">
                          {range ? `[${range[0]}, ${range[1]}]` : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Provenance & Literature */}
          <div className="bg-slate-950/70 rounded-lg p-4 border border-slate-800 space-y-1.5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Literature Provenance</h3>
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "{compound.provenance}"
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/95 sticky bottom-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            Close
          </button>

          {onSelectForScenario && (
            <button
              onClick={() => {
                onSelectForScenario(compound);
                onClose();
              }}
              className="px-4 py-2 text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white rounded-lg shadow transition-colors flex items-center gap-1.5"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Load into Simulation Playground</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
