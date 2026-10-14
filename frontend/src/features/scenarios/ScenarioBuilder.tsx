import React, { useState } from 'react';
import type { CompoundExposure, CompoundResponse, ExposureProfile, ScenarioRequest } from '../../types/api';
import { EvidenceBadge } from '../../components/EvidenceBadge';
import { AlertBox } from '../../components/AlertBox';
import { Activity, Play, Trash2 } from 'lucide-react';

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
    <form onSubmit={handleSubmit} noValidate className="bg-slate-900/90 rounded-lg border border-slate-800 p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-rose-400" />
            <span>Single-Cell Chemical Scenario Builder</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure acute bolus or continuous chemical challenges against human erythrocyte redox models.
          </p>
        </div>

        {/* Control comparison switch */}
        <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
          <input
            type="checkbox"
            checked={compareControl}
            onChange={(e) => setCompareControl(e.target.checked)}
            className="rounded border-slate-700 bg-slate-950 text-rose-500 focus:ring-0 cursor-pointer"
          />
          <span className="font-medium">Compare with Baseline Control</span>
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

      {/* Compound Selection List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Selected Chemical Compounds ({activeCompounds.length})
          </label>

          {/* Quick-add dropdown */}
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => {
                if (e.target.value) {
                  handleAddCompound(e.target.value);
                  e.target.value = '';
                }
              }}
              defaultValue=""
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-slate-700 cursor-pointer"
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

        {/* Compound rows */}
        <div className="space-y-2">
          {activeCompounds.map((item, idx) => {
            const entry = compounds.find((c) => c.compound_id === item.compound_id);
            return (
              <div
                key={item.compound_id}
                className="flex items-center justify-between gap-3 p-3 bg-slate-950/70 rounded-lg border border-slate-800/80"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-200 truncate">
                      {entry?.name || item.compound_id}
                    </span>
                    {entry && <EvidenceBadge level={entry.evidence_level} />}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5 truncate font-mono">
                    {entry?.mechanism_type.replace(/_/g, ' ')} • ID: {item.compound_id}
                  </div>
                </div>

                {/* Dose Input */}
                <div className="flex items-center gap-2 shrink-0">
                  <div className="text-right">
                    <label className="text-[10px] text-slate-400 uppercase tracking-wider block">Dose (mM)</label>
                    <input
                      type="number"
                      step="0.005"
                      min="0.001"
                      max="20.0"
                      value={item.dose_mM}
                      onChange={(e) => handleUpdateDose(idx, parseFloat(e.target.value) || 0)}
                      className="w-24 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs font-mono text-slate-100 text-right focus:outline-none focus:border-rose-500"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveCompound(idx)}
                    className="text-slate-500 hover:text-rose-400 p-1.5 rounded hover:bg-slate-900 transition-colors mt-3"
                    title="Remove compound"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Simulation Parameters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-slate-800">
        {/* Exposure Profile */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">Exposure Waveform</label>
          <select
            value={exposureProfile}
            onChange={(e) => setExposureProfile(e.target.value as ExposureProfile)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value="BOLUS">Bolus (Instantaneous at t=0)</option>
            <option value="INFUSION">Continuous Constant Infusion</option>
            <option value="REPEATED_PULSES">Repeated Periodic Pulses</option>
          </select>
        </div>

        {/* Duration */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">
            Duration: <span className="font-mono text-slate-300">{duration_s} s</span> ({(duration_s / 60).toFixed(0)} min)
          </label>
          <select
            value={duration_s}
            onChange={(e) => setDuration_s(parseInt(e.target.value, 10))}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value={600}>10 minutes (600 s) — Fast transient</option>
            <option value={1800}>30 minutes (1800 s)</option>
            <option value={3600}>1 hour (3600 s) — Recommended</option>
            <option value={7200}>2 hours (7200 s) — Long recovery</option>
            <option value={14400}>4 hours (14400 s)</option>
          </select>
        </div>

        {/* G6PD Alpha */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-slate-400">
              G6PD Activity (α): <span className="font-mono text-emerald-400">{g6pd_alpha.toFixed(2)}</span>
            </label>
          </div>
          <select
            value={g6pd_alpha}
            onChange={(e) => setG6pd_alpha(parseFloat(e.target.value))}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value={1.0}>1.00 — Normal Wild-Type (100%)</option>
            <option value={0.5}>0.50 — Mild Deficiency (50%)</option>
            <option value={0.2}>0.20 — G6PD A- Variant (20%)</option>
            <option value={0.05}>0.05 — G6PD Mediterranean Variant (5%)</option>
            <option value={0.01}>0.01 — Severe Chronic Enzymopathy (1%)</option>
          </select>
        </div>

        {/* Biological Model Version */}
        <div>
          <label className="text-xs font-medium text-slate-400 block mb-1">Model Version</label>
          <select
            value={modelVersion}
            onChange={(e) => setModelVersion(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-700 cursor-pointer"
          >
            <option value="rbc-g6pd-gsh-v2">rbc-g6pd-gsh-v2 (G6PD Sub-model)</option>
            <option value="rbc-gsh-redox-v1">rbc-gsh-redox-v1 (Baseline Redox)</option>
          </select>
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800">
        <div className="text-[11px] text-slate-500">
          Numerical solver: Adaptive Runge-Kutta 4th order (SciPy solve_ivp) with dense early transient sampling.
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Integrating ODEs...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Execute Simulation</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
