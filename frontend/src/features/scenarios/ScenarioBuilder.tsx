import React, { useState } from 'react';
import type { CompoundExposure, CompoundResponse, ExposureProfile, ScenarioRequest } from '../../types/api';
import { EvidenceBadge } from '../../components/EvidenceBadge';
import { AlertBox } from '../../components/AlertBox';
import { Play, Trash2 } from 'lucide-react';

interface Props {
  compounds: CompoundResponse[];
  onRunScenario: (request: ScenarioRequest, compareWithControl: boolean) => Promise<void>;
  loading: boolean;
  selectedCompoundForAdd?: CompoundResponse | null;
  onClearSelectedCompound?: () => void;
}

export const ScenarioBuilder: React.FC<Props> = ({
  compounds,
  onRunScenario,
  loading,
  selectedCompoundForAdd,
  onClearSelectedCompound,
}) => {
  // Form State
  const [activeCompounds, setActiveCompounds] = useState<CompoundExposure[]>([
    { compound_id: 'cmp_menadione', dose_mM: 0.05 },
  ]);

  const [exposureProfile, setExposureProfile] = useState<ExposureProfile>('BOLUS');
  const [duration_s, setDuration_s] = useState<number>(3600);
  const [g6pd_alpha, setG6pd_alpha] = useState<number>(1.0);
  const [modelVersion, setModelVersion] = useState<string>('rbc-g6pd-gsh-v2');
  const [compareControl, setCompareControl] = useState<boolean>(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  // If a compound was passed from catalog, add it
  React.useEffect(() => {
    if (selectedCompoundForAdd) {
      if (!activeCompounds.some((c) => c.compound_id === selectedCompoundForAdd.compound_id)) {
        setActiveCompounds((prev) => [
          ...prev,
          { compound_id: selectedCompoundForAdd.compound_id, dose_mM: 0.02 },
        ]);
      }
      onClearSelectedCompound?.();
    }
  }, [selectedCompoundForAdd, activeCompounds, onClearSelectedCompound]);

  // Check if any compound in active list is unverified
  const hasUnverified = activeCompounds.some((c) => {
    const entry = compounds.find((lib) => lib.compound_id === c.compound_id);
    return entry?.is_unverified ?? false;
  });

  const handleAddCompound = (id: string) => {
    if (!activeCompounds.some((c) => c.compound_id === id)) {
      setActiveCompounds((prev) => [...prev, { compound_id: id, dose_mM: 0.02 }]);
    }
  };

  const handleRemoveCompound = (index: number) => {
    setActiveCompounds((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpdateDose = (index: number, dose: number) => {
    setActiveCompounds((prev) =>
      prev.map((item, i) => (i === index ? { ...item, dose_mM: dose } : item))
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (activeCompounds.length === 0) {
      setValidationError('Please add at least one chemical compound to simulate.');
      return;
    }

    for (const c of activeCompounds) {
      if (c.dose_mM <= 0) {
        setValidationError(`Dose for '${c.compound_id}' must be strictly greater than 0.`);
        return;
      }
      if (c.dose_mM > 20.0) {
        setValidationError(`Dose for '${c.compound_id}' (${c.dose_mM} mM) exceeds the 20.0 mM upper safety limit.`);
        return;
      }
    }

    if (duration_s <= 0 || duration_s > 86400) {
      setValidationError('Duration must be between 1 second and 86400 seconds (24 hours).');
      return;
    }

    const req: ScenarioRequest = {
      compounds: activeCompounds,
      exposure_profile: exposureProfile,
      duration_s,
      g6pd_alpha,
      model_version: modelVersion,
    };

    onRunScenario(req, compareControl);
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="bg-[#FFFFFF] border border-[#D8D1C2] p-5 space-y-5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)]"
    >
      {/* Header & Experimental Objective */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D8D1C2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#9B332B] inline-block" />
            <h2 className="font-editorial text-lg font-bold text-[#181B18] tracking-tight">
              Single-Cell Chemical Scenario Builder
            </h2>
          </div>
          <p className="text-xs text-[#666E65] mt-0.5 font-sans">
            Configure acute bolus or continuous chemical challenges against human erythrocyte redox ODEs.
          </p>
        </div>

        {/* Control comparison switch */}
        <label className="flex items-center gap-2 cursor-pointer text-xs text-[#383E38] bg-[#F7F4EE] px-2.5 py-1.5 border border-[#D8D1C2] select-none">
          <input
            type="checkbox"
            checked={compareControl}
            onChange={(e) => setCompareControl(e.target.checked)}
            className="rounded-none border-[#B5AC99] text-[#9B332B] focus:ring-0 cursor-pointer accent-[#9B332B]"
          />
          <span className="font-mono text-[11px] font-semibold text-[#181B18]">
            Compare with Baseline Control
          </span>
        </label>
      </div>

      {/* Unverified Warning */}
      {hasUnverified && (
        <AlertBox type="warning" title="Contains Unverified Chemical Compounds">
          One or more selected chemicals (e.g. synthetic probe Xenobiotic X-101) use unverified kinetic
          rates. Output metrics will be explicitly marked as unverified hypotheses and excluded from validation scoring.
        </AlertBox>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <AlertBox type="error" title="Input Validation Error">
          {validationError}
        </AlertBox>
      )}

      {/* Segment 1: Chemical Mixture Formulation */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-[#EDE8DE] pb-1.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
              FORMULATION //
            </span>
            <span className="text-xs font-bold text-[#181B18]">
              Selected Compounds in Mixture ({activeCompounds.length})
            </span>
          </div>

          {/* Quick-add dropdown */}
          <div className="flex items-center gap-1.5">
            <select
              onChange={(e) => {
                if (e.target.value) {
                  handleAddCompound(e.target.value);
                  e.target.value = '';
                }
              }}
              defaultValue=""
              className="bg-[#FAF7F2] border border-[#B5AC99] px-2.5 py-1 text-xs font-mono text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
            >
              <option value="" disabled>
                + Add chemical to mixture...
              </option>
              {compounds.map((c) => (
                <option key={c.compound_id} value={c.compound_id}>
                  {c.name} ({c.mechanism_type.replace(/_/g, ' ')})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Compound rows formatted as laboratory bench ledger */}
        <div className="divide-y divide-[#EDE8DE] border border-[#EDE8DE] bg-[#FAF8F3]">
          {activeCompounds.map((item, idx) => {
            const entry = compounds.find((c) => c.compound_id === item.compound_id);
            return (
              <div
                key={item.compound_id}
                className="flex items-center justify-between gap-4 p-3 hover:bg-[#FFFFFF] transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-[#868E85]">0{idx + 1}.</span>
                    <span className="text-xs font-bold text-[#181B18] truncate">
                      {entry?.name || item.compound_id}
                    </span>
                    {entry && <EvidenceBadge level={entry.evidence_level} />}
                  </div>
                  <div className="text-[11px] text-[#666E65] mt-0.5 font-mono truncate">
                    Mechanism: {entry?.mechanism_type.replace(/_/g, ' ')} • ID: {item.compound_id}
                  </div>
                </div>

                {/* Dose Input with precise units */}
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <label className="text-[9.5px] font-mono text-[#767D75] uppercase tracking-wider block">
                      Dose (mM)
                    </label>
                    <input
                      type="number"
                      step="0.005"
                      min="0.001"
                      max="20.0"
                      value={item.dose_mM}
                      onChange={(e) => handleUpdateDose(idx, parseFloat(e.target.value) || 0)}
                      className="w-24 bg-[#FFFFFF] border border-[#B5AC99] px-2 py-1 text-xs font-mono font-semibold text-[#181B18] text-right focus:outline-none focus:border-[#9B332B]"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveCompound(idx)}
                    className="text-[#868E85] hover:text-[#9B332B] p-1.5 border border-transparent hover:border-[#DCB0AC] hover:bg-[#F9ECEB] transition-colors mt-3"
                    title="Remove compound"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Segment 2: Simulation Parameters Grid */}
      <div className="space-y-2 pt-2 border-t border-[#D8D1C2]">
        <div className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
          PARAMETERS // PHYSICAL & ENZYMATIC CALIBRATION
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Exposure Profile */}
          <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
            <label className="text-[11px] font-semibold text-[#181B18] block">Exposure Waveform</label>
            <select
              value={exposureProfile}
              onChange={(e) => setExposureProfile(e.target.value as ExposureProfile)}
              className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
            >
              <option value="BOLUS">Bolus (Instantaneous at t=0)</option>
              <option value="INFUSION">Continuous Constant Infusion</option>
              <option value="REPEATED_PULSES">Repeated Periodic Pulses</option>
            </select>
          </div>

          {/* Duration */}
          <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
            <label className="text-[11px] font-semibold text-[#181B18] block">
              Duration: <span className="font-mono text-[#9B332B]">{duration_s} s</span> ({(duration_s / 60).toFixed(0)} min)
            </label>
            <select
              value={duration_s}
              onChange={(e) => setDuration_s(parseInt(e.target.value, 10))}
              className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
            >
              <option value={600}>10 minutes (600 s) — Fast transient</option>
              <option value={1800}>30 minutes (1800 s)</option>
              <option value={3600}>1 hour (3600 s) — Recommended</option>
              <option value={7200}>2 hours (7200 s) — Long recovery</option>
              <option value={14400}>4 hours (14400 s)</option>
            </select>
          </div>

          {/* G6PD Alpha */}
          <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
            <label className="text-[11px] font-semibold text-[#181B18] block">
              G6PD Activity (α): <span className="font-mono text-[#435E4B]">{g6pd_alpha.toFixed(2)}</span>
            </label>
            <select
              value={g6pd_alpha}
              onChange={(e) => setG6pd_alpha(parseFloat(e.target.value))}
              className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
            >
              <option value={1.0}>1.00 — Normal Wild-Type (100%)</option>
              <option value={0.5}>0.50 — Mild Deficiency (50%)</option>
              <option value={0.2}>0.20 — G6PD A- Variant (20%)</option>
              <option value={0.05}>0.05 — G6PD Mediterranean Variant (5%)</option>
              <option value={0.01}>0.01 — Severe Chronic Enzymopathy (1%)</option>
            </select>
          </div>

          {/* Biological Model Version */}
          <div className="bg-[#FAF8F3] border border-[#EDE8DE] p-2.5 space-y-1">
            <label className="text-[11px] font-semibold text-[#181B18] block">Model Version</label>
            <select
              value={modelVersion}
              onChange={(e) => setModelVersion(e.target.value)}
              className="w-full bg-[#FFFFFF] border border-[#B5AC99] px-2.5 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer"
            >
              <option value="rbc-g6pd-gsh-v2">rbc-g6pd-gsh-v2 (G6PD Sub-model)</option>
              <option value="rbc-gsh-redox-v1">rbc-gsh-redox-v1 (Baseline Redox)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Execution Control Footer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-[#D8D1C2]">
        <div className="text-[10.5px] font-mono text-[#767D75]">
          SOLVER: SciPy solve_ivp (RK45 Adaptive ODE) • early transient density enabled
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-[#9B332B] hover:bg-[#802821] disabled:bg-[#D8D1C2] disabled:text-[#868E85] text-white font-mono font-semibold text-xs tracking-wider uppercase transition-all shadow-[2px_2px_0px_0px_rgba(24,27,24,0.18)] active:translate-x-[1px] active:translate-y-[1px] flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-none animate-spin" />
              <span>Integrating ODEs...</span>
            </>
          ) : (
            <>
              <Play className="w-3 h-3 fill-current" />
              <span>Execute Simulation</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
