import React, { useState } from 'react';
import type { CompoundResponse, PopulationRequest, ScenarioRequest } from '../../types/api';
import { AlertBox } from '../../components/AlertBox';
import { Play, Users } from 'lucide-react';

interface Props {
  compounds: CompoundResponse[];
  onRunPopulation: (request: PopulationRequest) => Promise<void>;
  loading: boolean;
}

export const PopulationBuilder: React.FC<Props> = ({
  compounds,
  onRunPopulation,
  loading,
}) => {
  const [selectedCompoundId, setSelectedCompoundId] = useState<string>('cmp_menadione');
  const [dose_mM, setDose_mM] = useState<number>(0.03);
  const [n_cells, setN_cells] = useState<number>(1000);
  const [g6pd_alpha, setG6pd_alpha] = useState<number>(0.2);
  const [duration_s, setDuration_s] = useState<number>(1800);
  const [randomSeed, setRandomSeed] = useState<number>(42);
  const [validationError, setValidationError] = useState<string | null>(null);

  const selectedCompound = compounds.find((c) => c.compound_id === selectedCompoundId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (n_cells < 10 || n_cells > 5000) {
      setValidationError('Cohort population size must be between 10 and 5,000 cells.');
      return;
    }

    if (dose_mM <= 0 || dose_mM > 20.0) {
      setValidationError('Exposure dose must be greater than 0 and at most 20.0 mM.');
      return;
    }

    const scenReq: ScenarioRequest = {
      compounds: [{ compound_id: selectedCompoundId, dose_mM }],
      exposure_profile: 'BOLUS',
      duration_s,
      g6pd_alpha,
      model_version: 'rbc-g6pd-gsh-v2',
    };

    const popReq: PopulationRequest = {
      scenario_request: scenReq,
      n_cells,
      random_seed: randomSeed,
      gsh_mild_threshold_mM: 1.0,
      gsh_crisis_threshold_mM: 0.25,
      hemolysis_proxy_threshold_pct: 5.0,
    };

    onRunPopulation(popReq);
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="bg-slate-900/90 rounded-lg border border-slate-800 p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-400" />
            <span>Heterogeneous Population Cohort Simulator</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Simulate thousands of heterogeneous red blood cells sampled across biological priors in seconds.
          </p>
        </div>

        <span className="text-xs font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
          Vectorized RK4 Engine
        </span>
      </div>

      {validationError && (
        <AlertBox type="error" title="Input Validation Error">
          {validationError}
        </AlertBox>
      )}

      {selectedCompound?.is_unverified && (
        <AlertBox type="warning" title="Simulating Unverified Compound">
          The selected compound ({selectedCompound.name}) contains unverified kinetic parameters.
          Cohort percentiles reflect hypothesis exploration only and cannot be scored for validation.
        </AlertBox>
      )}

      {/* Grid Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Compound Selector */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">Challenge Compound</label>
          <select
            value={selectedCompoundId}
            onChange={(e) => setSelectedCompoundId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            {compounds.map((c) => (
              <option key={c.compound_id} value={c.compound_id}>
                {c.name} {c.is_unverified ? '(UNVERIFIED)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Dose (mM) */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">Dose (mM)</label>
          <input
            type="number"
            step="0.005"
            min="0.001"
            max="10.0"
            value={dose_mM}
            onChange={(e) => setDose_mM(parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Population Size N */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">
            Cohort Size (N): <span className="font-mono text-blue-400">{n_cells.toLocaleString()} cells</span>
          </label>
          <select
            value={n_cells}
            onChange={(e) => setN_cells(parseInt(e.target.value, 10))}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value={100}>100 cells (Fast preview ~0.1s)</option>
            <option value={500}>500 cells (~0.5s)</option>
            <option value={1000}>1,000 cells (Standard cohort ~1.2s)</option>
            <option value={2500}>2,500 cells (~3.0s)</option>
            <option value={5000}>5,000 cells (High resolution ~6.0s)</option>
          </select>
        </div>

        {/* Duration */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">
            Duration: <span className="font-mono text-slate-300">{duration_s}s</span> ({(duration_s / 60).toFixed(0)}m)
          </label>
          <select
            value={duration_s}
            onChange={(e) => setDuration_s(parseInt(e.target.value, 10))}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value={600}>10 minutes (600s)</option>
            <option value={1800}>30 minutes (1800s)</option>
            <option value={3600}>1 hour (3600s)</option>
          </select>
        </div>

        {/* G6PD Activity Multiplier */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">
            G6PD Activity (α): <span className="font-mono text-emerald-400">{g6pd_alpha.toFixed(2)}</span>
          </label>
          <select
            value={g6pd_alpha}
            onChange={(e) => setG6pd_alpha(parseFloat(e.target.value))}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value={1.0}>1.00 (Normal Wild-Type)</option>
            <option value={0.5}>0.50 (Mild Deficiency)</option>
            <option value={0.2}>0.20 (G6PD A- Variant)</option>
            <option value={0.05}>0.05 (G6PD Mediterranean)</option>
            <option value={0.01}>0.01 (Severe Chronic)</option>
          </select>
        </div>

        {/* Reproducibility Seed */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">RNG Seed (Reproducibility)</label>
          <input
            type="number"
            value={randomSeed}
            onChange={(e) => setRandomSeed(parseInt(e.target.value, 10) || 0)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Submit Bar */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800">
        <span className="text-[11px] text-slate-500">
          Samples log-normal distributions for Vmax_G6PD, k_GR, k_GPx, and pool volumes.
        </span>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Simulating {n_cells.toLocaleString()} cells...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Run Cohort Simulation</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
