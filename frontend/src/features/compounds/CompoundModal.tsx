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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in">
      <div className="bg-[#FFFFFF] border-2 border-[#181B18] shadow-[6px_6px_0px_0px_rgba(24,27,24,0.2)] max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
        {/* Monograph Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#D8D1C2] sticky top-0 bg-[#FAF7F2] z-10">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
                MONOGRAPH //
              </span>
              <h2 className="font-editorial text-xl font-bold text-[#181B18]">{compound.name}</h2>
              <EvidenceBadge level={compound.evidence_level} />
            </div>
            <p className="text-xs font-mono text-[#666E65] mt-0.5">SPECIMEN ID: {compound.compound_id}</p>
          </div>

          <button
            onClick={onClose}
            className="text-[#767D75] hover:text-[#181B18] p-1.5 border border-[#D8D1C2] hover:bg-[#F2ECE1] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Monograph Content */}
        <div className="p-6 space-y-5 flex-1 bg-[#FCFBF9]">
          {/* Unverified Warning */}
          {compound.is_unverified && (
            <AlertBox type="error" title="UNVERIFIED KINETIC MECHANISM">
              This compound is a synthetic probe or unverified research entry. Its kinetic rates
              are hypothetical and not calibrated against experimental human RBC measurements.
              Results generated using this compound are excluded from platform validation scoring.
            </AlertBox>
          )}

          {/* Chemical Identifiers Plate */}
          <div className="bg-[#FAF8F3] p-4 border border-[#D8D1C2] space-y-2.5">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75]">
              Chemical Structure & Identifiers
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[#666E65] font-mono text-[11px] block">SMILES Notation</span>
                <span className="font-mono text-[#181B18] break-all bg-[#FFFFFF] px-2 py-1 block mt-0.5 border border-[#D8D1C2]">
                  {compound.smiles || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-[#666E65] font-mono text-[11px] block">InChIKey Hash</span>
                <span className="font-mono text-[#181B18] break-all bg-[#FFFFFF] px-2 py-1 block mt-0.5 border border-[#D8D1C2]">
                  {compound.inchikey || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Mechanism & Units */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-[#FAF8F3] p-3 border border-[#D8D1C2]">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] block">
                Mechanism Type
              </span>
              <span className="text-xs font-bold text-[#181B18] mt-1 block">
                {compound.mechanism_type.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="bg-[#FAF8F3] p-3 border border-[#D8D1C2]">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] block">
                Exposure Units
              </span>
              <span className="text-xs font-mono font-bold text-[#181B18] mt-1 block">
                {compound.exposure_units}
              </span>
            </div>
            <div className="bg-[#FAF8F3] p-3 border border-[#D8D1C2]">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] block">
                Confidence Score
              </span>
              <span className="text-xs font-mono font-bold text-[#286345] mt-1 block">
                {(compound.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Default Parameters & Bounds Table */}
          <div className="bg-[#FAF8F3] p-4 border border-[#D8D1C2] space-y-2">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75]">
              Default Kinetic Parameters & Valid Bounds
            </h3>
            <div className="overflow-x-auto border border-[#EDE8DE] bg-[#FFFFFF]">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-[#D8D1C2] text-[#666E65] font-mono bg-[#FAF7F2]">
                    <th className="py-2 px-3 font-semibold">Parameter</th>
                    <th className="py-2 px-3 font-semibold">Default Value</th>
                    <th className="py-2 px-3 font-semibold">Valid Range</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EDE8DE] font-mono">
                  {Object.entries(compound.default_parameters).map(([param, val]) => {
                    const range = compound.parameter_ranges[param];
                    return (
                      <tr key={param} className="hover:bg-[#FAF8F3]">
                        <td className="py-2 px-3 text-[#181B18] font-sans font-medium">{param}</td>
                        <td className="py-2 px-3 text-[#286345] font-bold">{String(val)}</td>
                        <td className="py-2 px-3 text-[#767D75]">
                          {range ? `[${range[0]}, ${range[1]}]` : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Provenance & Literature Citation */}
          <div className="bg-[#FAF8F3] p-4 border border-[#D8D1C2] space-y-1.5">
            <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75]">
              Literature Provenance
            </h3>
            <p className="text-xs text-[#383E38] leading-relaxed italic font-serif bg-[#FFFFFF] p-3 border border-[#EDE8DE]">
              "{compound.provenance}"
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#D8D1C2] flex items-center justify-between bg-[#FAF7F2] sticky bottom-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-mono font-medium text-[#484E48] hover:text-[#181B18] hover:bg-[#FFFFFF] border border-[#B5AC99] transition-colors shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]"
          >
            Close Monograph
          </button>

          {onSelectForScenario && (
            <button
              onClick={() => {
                onSelectForScenario(compound);
                onClose();
              }}
              className="px-4 py-2 text-xs font-mono font-semibold bg-[#9B332B] hover:bg-[#802821] text-white border border-[#9B332B] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.15)] transition-all flex items-center gap-1.5"
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
