import React from 'react';
import type { ScenarioRunResponse } from '../../types/api';
import { TimeSeriesChart } from '../../components/TimeSeriesChart';
import { AlertBox } from '../../components/AlertBox';
import { FileJson, FileSpreadsheet, Film, ShieldAlert } from 'lucide-react';

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
      {/* Run Metadata & Instrument Action Bar */}
      <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-4 flex flex-wrap items-center justify-between gap-4 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#767D75]">
              RUN IDENTIFIER:
            </span>
            <span className="font-mono text-xs font-bold text-[#181B18] bg-[#FAF7F2] px-2 py-0.5 border border-[#B5AC99]">
              {treatmentResult.run_id}
            </span>
            {treatmentResult.has_unverified_compounds && (
              <span className="text-[10px] font-mono font-bold text-[#85251E] flex items-center gap-1 bg-[#F7EBEA] px-2 py-0.5 border border-[#962F27]">
                <ShieldAlert className="w-3 h-3" />
                <span>UNVERIFIED COMPOUNDS INCLUDED</span>
              </span>
            )}
          </div>
          <div className="text-xs text-[#666E65] mt-1 font-mono">
            Evaluated at {treatmentResult.trajectory_length} points across{' '}
            {(treatmentResult.scenario_request.duration_s / 60).toFixed(0)} minutes simulation window.
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {onOpenPlayback && (
            <button
              onClick={onOpenPlayback}
              className="px-3 py-1.5 text-xs font-mono font-semibold bg-[#FAF7F2] hover:bg-[#F2ECE1] text-[#9B332B] border border-[#DCB0AC] transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)] flex items-center gap-1.5"
            >
              <Film className="w-3.5 h-3.5" />
              <span>Play Erythrocyte Animation</span>
            </button>
          )}

          <button
            onClick={handleExportCsv}
            className="px-3 py-1.5 text-xs font-mono font-medium bg-[#FFFFFF] hover:bg-[#FAF7F2] text-[#181B18] border border-[#B5AC99] transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)] flex items-center gap-1.5"
            title="Download simulation time-series as CSV"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-[#435E4B]" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={handleExportJson}
            className="px-3 py-1.5 text-xs font-mono font-medium bg-[#FFFFFF] hover:bg-[#FAF7F2] text-[#181B18] border border-[#B5AC99] transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)] flex items-center gap-1.5"
            title="Download complete run payload and provenance as JSON"
          >
            <FileJson className="w-3.5 h-3.5 text-[#2E5875]" />
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

      {/* Asymmetric Derived Biochemical Metrics Readout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
        {/* Primary Critical Readout: GSH Nadir (Hero Column 4 cols) */}
        <div className="md:col-span-4 bg-[#FFFFFF] border-2 border-[#181B18] p-4 flex flex-col justify-between shadow-[3px_3px_0px_0px_rgba(24,27,24,0.12)]">
          <div>
            <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-[#767D75]">
              <span>PRIMARY KINETIC NADIR</span>
              <span className="text-[#435E4B] font-semibold">[GSH]min</span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-editorial text-3xl font-bold text-[#181B18] tracking-tight">
                {m.gsh_nadir_mM.toFixed(3)}
              </span>
              <span className="font-mono text-sm text-[#767D75]">mM</span>
            </div>
          </div>

          <div className="mt-4 pt-2.5 border-t border-[#EDE8DE] text-[10.5px] font-mono text-[#666E65] flex items-center justify-between">
            <span>Baseline Ref: 2.500 mM</span>
            <span
              className={
                m.gsh_nadir_mM < 1.0
                  ? 'text-[#9B332B] font-semibold'
                  : 'text-[#435E4B] font-semibold'
              }
            >
              {m.gsh_nadir_mM < 1.0 ? 'Depletion Risk' : 'Physiological Buffer'}
            </span>
          </div>
        </div>

        {/* Secondary Metric Grid (8 cols) */}
        <div className="md:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Peak GSSG */}
          <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-3 flex flex-col justify-between shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]">
            <span className="text-[10px] font-mono text-[#767D75] uppercase tracking-wider block">
              Peak GSSG ([GSSG]max)
            </span>
            <div className="my-1.5 text-xl font-bold font-mono text-[#8F5C1E]">
              {m.gssg_peak_mM.toFixed(3)} <span className="text-xs font-sans text-[#767D75]">mM</span>
            </div>
            <span className="text-[10px] font-mono text-[#868E85] block">Ref: 0.025 mM</span>
          </div>

          {/* 90% Recovery Time */}
          <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-3 flex flex-col justify-between shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]">
            <span className="text-[10px] font-mono text-[#767D75] uppercase tracking-wider block">
              90% Recovery
            </span>
            <div className="my-1.5 text-xl font-bold font-mono text-[#2E5875]">
              {m.time_to_90pct_recovery_s !== null ? (
                <>
                  {m.time_to_90pct_recovery_s.toFixed(0)}{' '}
                  <span className="text-xs font-sans text-[#767D75]">
                    s ({(m.time_to_90pct_recovery_s / 60).toFixed(1)}m)
                  </span>
                </>
              ) : (
                <span className="text-xs text-[#9B332B] font-sans font-semibold">No recovery</span>
              )}
            </div>
            <span className="text-[10px] font-mono text-[#868E85] block">T to 90% GSH</span>
          </div>

          {/* Net Glutathione Loss */}
          <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-3 flex flex-col justify-between shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]">
            <span className="text-[10px] font-mono text-[#767D75] uppercase tracking-wider block">
              Glutathione Loss
            </span>
            <div className="my-1.5 text-xl font-bold font-mono text-[#4B466D]">
              {m.net_total_glutathione_loss_pct.toFixed(1)}%
            </div>
            <span className="text-[10px] font-mono text-[#868E85] block">Conjugation / Export</span>
          </div>

          {/* Damage Onset Time */}
          <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-3 flex flex-col justify-between shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]">
            <span className="text-[10px] font-mono text-[#767D75] uppercase tracking-wider block">
              Damage Onset (D &gt; 0.05)
            </span>
            <div className="my-1.5 text-xl font-bold font-mono text-[#9B332B]">
              {m.damage_onset_time_s !== null ? (
                <>
                  {m.damage_onset_time_s.toFixed(0)} <span className="text-xs font-sans text-[#767D75]">s</span>
                </>
              ) : (
                <span className="text-xs text-[#435E4B] font-sans font-semibold">Undetected</span>
              )}
            </div>
            <span className="text-[10px] font-mono text-[#868E85] block">D &gt; 0.05 threshold</span>
          </div>
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
        <div className="bg-[#FAF8F3] border border-[#D8D1C2] p-4 space-y-2 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.04)]">
          <div className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
            MEMORANDUM // SIMULATION INTERACTION ASSUMPTIONS
          </div>
          <ul className="text-xs text-[#383E38] space-y-1 list-disc list-inside font-sans leading-relaxed">
            {treatmentResult.interaction_assumptions.map((asm, i) => (
              <li key={i}>{asm}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
