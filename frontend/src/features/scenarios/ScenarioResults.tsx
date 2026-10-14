import React from 'react';
import type { ScenarioRunResponse } from '../../types/api';
import { TimeSeriesChart } from '../../components/TimeSeriesChart';
import { AlertBox } from '../../components/AlertBox';
import { FileJson, FileSpreadsheet, ShieldAlert } from 'lucide-react';

interface Props {
  treatmentResult: ScenarioRunResponse | null;
  controlResult?: ScenarioRunResponse | null;
  onOpenPlayback?: () => void;
}

export const ScenarioResults: React.FC<Props> = ({
  treatmentResult,
  controlResult,
  onOpenPlayback,
}) => {
  if (!treatmentResult) return null;

  const m = treatmentResult.derived_metrics;
  const trtTraj = treatmentResult.trajectory || [];
  const ctrlTraj = controlResult?.trajectory || [];

  // Export JSON handler
  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(treatmentResult, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `vblood_scenario_${treatmentResult.run_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  // Export CSV handler
  const handleExportCsv = () => {
    if (trtTraj.length === 0) return;
    const headers = ['time_s', 'gsh_mM', 'gssg_mM', 'h2o2_mM', 'nadph_mM', 'damage_proxy', 'hemolysis_pct'];
    const rows = trtTraj.map((p) => [
      p.t_s.toFixed(2),
      p.gsh_mM.toFixed(6),
      p.gssg_mM.toFixed(6),
      p.h2o2_mM.toExponential(4),
      p.nadph_mM.toFixed(6),
      p.damage.toFixed(6),
      p.hemolysis_pct.toFixed(2),
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `vblood_trajectory_${treatmentResult.run_id}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-5">
      {/* Run Metadata & Export Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-lg border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Simulation Run:</span>
            <span className="text-xs font-mono text-slate-200 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              {treatmentResult.run_id}
            </span>
            {treatmentResult.has_unverified_compounds && (
              <span className="text-xs font-semibold text-rose-400 flex items-center gap-1 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>UNVERIFIED COMPOUNDS</span>
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Trajectory evaluated at {treatmentResult.trajectory_length} points across{' '}
            {(treatmentResult.scenario_request.duration_s / 60).toFixed(0)} minutes.
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {onOpenPlayback && (
            <button
              onClick={onOpenPlayback}
              className="px-3 py-1.5 text-xs font-semibold bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800 rounded-md transition-colors"
            >
              Play Erythrocyte Animation
            </button>
          )}

          <button
            onClick={handleExportCsv}
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-md flex items-center gap-1.5 transition-colors"
            title="Download simulation time-series as CSV"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={handleExportJson}
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-md flex items-center gap-1.5 transition-colors"
            title="Download complete run payload and provenance as JSON"
          >
            <FileJson className="w-3.5 h-3.5 text-blue-400" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Unverified Alert */}
      {treatmentResult.has_unverified_compounds && (
        <AlertBox type="warning" title="Model Run Includes Unverified Compounds">
          This run incorporated parameters from unverified entries ({treatmentResult.unverified_compounds.join(', ')}).
          Outputs represent exploratory in silico hypothesis generation and are strictly excluded from biological validation scores.
        </AlertBox>
      )}

      {/* Derived Biochemical Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* GSH Nadir */}
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg space-y-1">
          <span className="text-[11px] text-slate-400 block font-medium">GSH Nadir ([GSH]min)</span>
          <div className="text-lg font-bold font-mono text-emerald-400">
            {m.gsh_nadir_mM.toFixed(3)} <span className="text-xs font-sans text-slate-400">mM</span>
          </div>
          <span className="text-[10px] text-slate-500 block">Baseline ref: 2.50 mM</span>
        </div>

        {/* Peak GSSG */}
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg space-y-1">
          <span className="text-[11px] text-slate-400 block font-medium">Peak GSSG ([GSSG]max)</span>
          <div className="text-lg font-bold font-mono text-amber-400">
            {m.gssg_peak_mM.toFixed(3)} <span className="text-xs font-sans text-slate-400">mM</span>
          </div>
          <span className="text-[10px] text-slate-500 block">Baseline ref: 0.025 mM</span>
        </div>

        {/* 90% Recovery Time */}
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg space-y-1">
          <span className="text-[11px] text-slate-400 block font-medium">90% GSH Recovery Time</span>
          <div className="text-lg font-bold font-mono text-blue-400">
            {m.time_to_90pct_recovery_s !== null ? (
              <>
                {m.time_to_90pct_recovery_s.toFixed(0)}{' '}
                <span className="text-xs font-sans text-slate-400">s ({(m.time_to_90pct_recovery_s / 60).toFixed(1)}m)</span>
              </>
            ) : (
              <span className="text-xs text-rose-400 font-sans">No recovery observed</span>
            )}
          </div>
          <span className="text-[10px] text-slate-500 block">Threshold: 90% of baseline</span>
        </div>

        {/* Net Total Glutathione Loss */}
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg space-y-1">
          <span className="text-[11px] text-slate-400 block font-medium">Net Glutathione Loss</span>
          <div className="text-lg font-bold font-mono text-purple-400">
            {m.net_total_glutathione_loss_pct.toFixed(1)}%
          </div>
          <span className="text-[10px] text-slate-500 block">Via export or conjugation</span>
        </div>

        {/* Damage Onset Timestamp */}
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg space-y-1">
          <span className="text-[11px] text-slate-400 block font-medium">Damage Onset (D &gt; 0.05)</span>
          <div className="text-lg font-bold font-mono text-rose-400">
            {m.damage_onset_time_s !== null ? (
              <>
                {m.damage_onset_time_s.toFixed(0)} <span className="text-xs font-sans text-slate-400">s</span>
              </>
            ) : (
              <span className="text-xs text-emerald-400 font-sans">Undetected (&lt; 0.05)</span>
            )}
          </div>
          <span className="text-[10px] text-slate-500 block">Oxidative stress onset</span>
        </div>
      </div>

      {/* Primary Result Time-Series Plots */}
      <TimeSeriesChart
        treatmentTrajectory={trtTraj}
        controlTrajectory={ctrlTraj}
        treatmentLabel={`Treated (${treatmentResult.scenario_request.compounds.map((c) => c.compound_id).join(' + ')})`}
        controlLabel="Untreated Control Baseline"
      />

      {/* Scientific Interaction Assumptions */}
      {treatmentResult.interaction_assumptions.length > 0 && (
        <div className="bg-slate-900/80 rounded-lg border border-slate-800 p-4 space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Simulation Interaction Assumptions
          </h4>
          <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
            {treatmentResult.interaction_assumptions.map((asm, i) => (
              <li key={i}>{asm}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
