import React from 'react';
import type { ModelDetailResponse } from '../../types/api';
import { AlertBox } from '../../components/AlertBox';
import { BookOpen, CheckCircle, Database } from 'lucide-react';

interface Props {
  models: ModelDetailResponse[];
  loading?: boolean;
  error: string | null;
}

export const ModelInfoView: React.FC<Props> = ({ models, loading = false, error }) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-[#D8D1C2] pb-4">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
            REGISTRY //
          </span>
          <h1 className="font-editorial text-2xl font-bold text-[#181B18] tracking-tight">
            Registered Biological Models & Evidence
          </h1>
        </div>
        <p className="text-xs text-[#666E65] mt-1 font-sans">
          Mechanistic ODE model specifications, parameter evidence grading, and biological boundaries.
        </p>
      </div>

      {loading && models.length === 0 && (
        <div className="text-xs text-[#767D75] py-8 text-center font-mono border border-dashed border-[#D8D1C2] bg-[#FAF7F2]">
          Loading registered biological models from API...
        </div>
      )}

      {error && <AlertBox type="error" title="Failed to Fetch Model Registry">{error}</AlertBox>}

      {/* Model Boundaries & Unmodeled Physics Banner */}
      <AlertBox type="disclaimer" title="Strict Biological Scope & Model Limitations">
        <div className="space-y-2 mt-1">
          <p>
            V-Blood simulates the cytosolic glutathione redox cycle and pentose phosphate pathway in human erythrocytes.
            Researchers must be mindful of the following explicit model boundaries:
          </p>
          <ul className="list-disc list-inside space-y-1 text-[#484E48] font-sans">
            <li>
              <strong>No Glycolysis or ATP Generation:</strong> Glycolytic ATP turnover is not simulated; glucose-6-phosphate
              influx into the PPP is represented via saturating Michaelis-Menten kinetics.
            </li>
            <li>
              <strong>No Physical Membrane Morphology:</strong> The model does not simulate mechanical shear, osmotic swelling,
              or morphological transitions (e.g. echinocyte spiculation, stomatocytes). Damage proxy D is a biochemical index.
            </li>
            <li>
              <strong>No Systemic Pharmacokinetics:</strong> Exposure doses represent direct extracellular fluid concentrations
              at the erythrocyte boundary; ADME (absorption, distribution, hepatic metabolism) is not modeled.
            </li>
          </ul>
        </div>
      </AlertBox>

      {/* Models Grid / Dossiers */}
      <div className="space-y-6">
        {models.map((m) => {
          return (
            <div
              key={m.model_id}
              className="bg-[#FFFFFF] border border-[#D8D1C2] p-6 space-y-5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)]"
            >
              {/* Dossier Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D8D1C2] pb-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="font-editorial text-xl font-bold text-[#181B18]">{m.name}</h2>
                    <span className="font-mono text-[10px] bg-[#FAF7F2] text-[#181B18] px-2 py-0.5 border border-[#B5AC99] font-bold">
                      v{m.version}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-[#666E65] mt-0.5">SPECIFICATION ID: {m.model_id}</p>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-[#767D75]">COMPARTMENT:</span>
                  <span className="text-[#181B18] font-bold bg-[#FAF7F2] px-2.5 py-1 border border-[#B5AC99]">
                    {m.compartment}
                  </span>
                </div>
              </div>

              {/* Description in editorial text */}
              <p className="text-xs text-[#383E38] leading-relaxed bg-[#FAF8F3] p-3.5 border border-[#EDE8DE] font-serif">
                {m.description}
              </p>

              {/* State Variables Table */}
              <div className="space-y-2">
                <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-[#2E5875]" />
                  <span>State Variables ({m.state_variables.length})</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 text-xs">
                  {m.state_variables.map((varName, idx) => (
                    <div
                      key={varName}
                      className="bg-[#FAF7F2] p-2.5 border border-[#EDE8DE] flex flex-col justify-between"
                    >
                      <span className="font-mono font-bold text-[#181B18]">{varName}</span>
                      <span className="text-[10.5px] text-[#767D75] font-mono mt-1">
                        {m.state_variable_units[idx] || 'dimensionless'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Parameter Evidence Provenance Breakdown */}
              <div className="space-y-2">
                <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-[#435E4B]" />
                  <span>Parameter Provenance Breakdown ({m.parameter_count} total parameters)</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
                  <div className="bg-[#EDF3EE] border border-[#BCD0C1] p-3 flex items-center justify-between">
                    <span className="text-xs text-[#284431] font-semibold">Curated Parameters:</span>
                    <span className="font-bold text-[#286345] text-base">
                      {m.evidence_status_summary['curated'] || 0}
                    </span>
                  </div>

                  <div className="bg-[#F8F2E8] border border-[#E2CEB1] p-3 flex items-center justify-between">
                    <span className="text-xs text-[#5C3911] font-semibold">Estimated Parameters:</span>
                    <span className="font-bold text-[#8E5A1E] text-base">
                      {m.evidence_status_summary['estimated'] || 0}
                    </span>
                  </div>

                  <div className="bg-[#F9ECEB] border border-[#DCB0AC] p-3 flex items-center justify-between">
                    <span className="text-xs text-[#7D221C] font-semibold">Unverified Parameters:</span>
                    <span className="font-bold text-[#9B332B] text-base">
                      {m.evidence_status_summary['unverified'] || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Literature Citations */}
              <div className="space-y-2">
                <h3 className="text-[10px] font-mono uppercase tracking-wider text-[#767D75] flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-[#4B466D]" />
                  <span>Literature Sources & Citations</span>
                </h3>
                <ul className="text-xs text-[#484E48] space-y-1 list-disc list-inside bg-[#FAF8F3] p-3.5 border border-[#EDE8DE] font-serif leading-relaxed">
                  {m.literature_sources.map((cit, idx) => (
                    <li key={idx}>{cit}</li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
