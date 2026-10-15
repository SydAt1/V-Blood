import React, { useState } from 'react';
import type { CompoundResponse, PopulationRequest, ScenarioRequest } from '../../types/api';
import { AlertBox } from '../../components/AlertBox';
import { Play } from 'lucide-react';

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
    <form
      onSubmit={handleSubmit}
      noValidate
      className="bg-[#FFFFFF] border border-[#D8D1C2] p-5 space-y-5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)]"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D8D1C2] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#2E5875] inline-block" />
            <h2 className="font-editorial text-lg font-bold text-[#181B18] tracking-tight">
              Heterogeneous Population Cohort Simulator
            </h2>
          </div>
          <p className="text-xs text-[#666E65] mt-0.5 font-sans">
            Simulate thousands of heterogeneous red blood cells sampled across biological priors in seconds.
          </p>
        </div>

        <span className="text-[10px] font-mono text-[#2E5875] bg-[#EBF2F7] px-2.5 py-1 border border-[#B6CEE0] font-semibold">
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
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Compound Selector */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            Challenge Compound
          </label>
          <select
            value={selectedCompoundId}
            onChange={(e) => setSelectedCompoundId(e.target.value)}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
          >
            {compounds.map((c) => (
              <option key={c.compound_id} value={c.compound_id}>
                {c.name} {c.is_unverified ? '(UNVERIFIED)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Dose (mM) */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            Dose (mM)
          </label>
          <input
            type="number"
            step="0.005"
            min="0.001"
            max="10.0"
            value={dose_mM}
            onChange={(e) => setDose_mM(parseFloat(e.target.value) || 0)}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1 text-xs font-mono font-semibold text-[#181B18] focus:outline-none focus:border-[#2E5875]"
          />
        </div>

        {/* Population Size N */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            Cohort Size: <strong className="text-[#2E5875] font-mono">{n_cells.toLocaleString()}</strong>
          </label>
          <select
            value={n_cells}
            onChange={(e) => setN_cells(parseInt(e.target.value, 10))}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
          >
            <option value={100}>100 cells (Fast preview ~0.1s)</option>
            <option value={500}>500 cells (~0.5s)</option>
            <option value={1000}>1,000 cells (Standard cohort)</option>
            <option value={2500}>2,500 cells (~3.0s)</option>
            <option value={5000}>5,000 cells (High resolution)</option>
          </select>
        </div>

        {/* Duration */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            Duration: <strong className="text-[#181B18] font-mono">{(duration_s / 60).toFixed(0)}m</strong>
          </label>
          <select
            value={duration_s}
            onChange={(e) => setDuration_s(parseInt(e.target.value, 10))}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
          >
            <option value={600}>10 minutes (600s)</option>
            <option value={1800}>30 minutes (1800s)</option>
            <option value={3600}>1 hour (3600s)</option>
          </select>
        </div>

        {/* G6PD Activity Multiplier */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            G6PD α: <strong className="text-[#435E4B] font-mono">{g6pd_alpha.toFixed(2)}</strong>
          </label>
          <select
            value={g6pd_alpha}
            onChange={(e) => setG6pd_alpha(parseFloat(e.target.value))}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
          >
            <option value={1.0}>1.00 (Normal Wild-Type)</option>
            <option value={0.5}>0.50 (Mild Deficiency)</option>
            <option value={0.2}>0.20 (G6PD A- Variant)</option>
            <option value={0.05}>0.05 (Mediterranean)</option>
            <option value={0.01}>0.01 (Severe Chronic)</option>
          </select>
        </div>

        {/* Reproducibility Seed */}
        <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
          <label className="text-[10.5px] font-mono uppercase tracking-wider text-[#767D75] block">
            RNG Seed
          </label>
          <input
            type="number"
            value={randomSeed}
            onChange={(e) => setRandomSeed(parseInt(e.target.value, 10) || 0)}
            className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1 text-xs font-mono font-semibold text-[#181B18] focus:outline-none focus:border-[#2E5875]"
          />
        </div>
      </div>

      {/* Submit Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-[#D8D1C2]">
        <span className="text-[10.5px] font-mono text-[#767D75]">
          PRIORS: Log-normal distributions on Vmax_G6PD, k_GR, k_GPx, and pool volumes.
        </span>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-[#2E5875] hover:bg-[#23465E] disabled:bg-[#D8D1C2] disabled:text-[#868E85] text-white font-mono font-semibold text-xs tracking-wider uppercase transition-all shadow-[2px_2px_0px_0px_rgba(24,27,24,0.18)] active:translate-x-[1px] active:translate-y-[1px] flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-none animate-spin" />
              <span>Simulating {n_cells.toLocaleString()} cells...</span>
            </>
          ) : (
            <>
              <Play className="w-3 h-3 fill-current" />
              <span>Run Cohort Simulation</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
