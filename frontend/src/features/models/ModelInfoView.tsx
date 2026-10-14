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
      <div className="border-b border-slate-800 pb-3">
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">Registered Biological Models & Evidence</h1>
        <p className="text-xs text-slate-400 mt-1">
          Mechanistic ODE model specifications, parameter evidence grading, and biological boundaries.
        </p>
      </div>

      {loading && models.length === 0 && (
        <div className="text-xs text-slate-400 py-6 text-center">
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
          <ul className="list-disc list-inside space-y-1 text-slate-400">
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

      {/* Models Grid */}
      <div className="grid grid-cols-1 gap-6">
        {models.map((m) => {
          return (
            <div key={m.model_id} className="bg-slate-900/90 rounded-xl border border-slate-800 p-6 space-y-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-base font-bold text-slate-100">{m.name}</h2>
                    <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                      v{m.version}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">Model ID: {m.model_id}</p>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400 font-mono">Compartment:</span>
                  <span className="text-slate-200 font-semibold bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
                    {m.compartment}
                  </span>
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                {m.description}
              </p>

              {/* State Variables Table */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-blue-400" />
                  <span>State Variables ({m.state_variables.length})</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 text-xs">
                  {m.state_variables.map((varName, idx) => (
                    <div
                      key={varName}
                      className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex flex-col justify-between"
                    >
                      <span className="font-mono font-semibold text-slate-200">{varName}</span>
                      <span className="text-[11px] text-slate-500 font-mono mt-1">
                        {m.state_variable_units[idx] || 'dimensionless'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Parameter Evidence Breakdown */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Parameter Provenance Breakdown ({m.parameter_count} total parameters)</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-emerald-950/30 border border-emerald-800/80 p-3 rounded-lg flex items-center justify-between">
                    <span className="text-xs text-emerald-300 font-medium">Curated Parameters:</span>
                    <span className="font-mono font-bold text-emerald-400 text-sm">
                      {m.evidence_status_summary['curated'] || 0}
                    </span>
                  </div>

                  <div className="bg-amber-950/30 border border-amber-800/80 p-3 rounded-lg flex items-center justify-between">
                    <span className="text-xs text-amber-300 font-medium">Estimated Parameters:</span>
                    <span className="font-mono font-bold text-amber-400 text-sm">
                      {m.evidence_status_summary['estimated'] || 0}
                    </span>
                  </div>

                  <div className="bg-rose-950/30 border border-rose-800/80 p-3 rounded-lg flex items-center justify-between">
                    <span className="text-xs text-rose-300 font-medium">Unverified Parameters:</span>
                    <span className="font-mono font-bold text-rose-400 text-sm">
                      {m.evidence_status_summary['unverified'] || 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Literature Citations */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-purple-400" />
                  <span>Literature Sources & Citations</span>
                </h3>
                <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 font-serif leading-relaxed">
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
