import React from 'react';
import type { PopulationResult } from '../../types/api';
import { PopulationPercentileChart } from './PopulationPercentileChart';
import { AlertBox } from '../../components/AlertBox';
import { Clock, Users } from 'lucide-react';

interface Props {
  result: PopulationResult | null;
}

export const PopulationResults: React.FC<Props> = ({ result }) => {
  if (!result) return null;

  const bands = result.percentile_bands;
  const n = result.n_cells;
  const nDepleted = result.n_depleted_cells;
  const nLysisRisk = result.n_lysis_risk_cells;

  return (
    <div className="space-y-5">
      {/* Run Summary Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-lg border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-950/80 border border-blue-800 flex items-center justify-center text-blue-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-100">
                Cohort of {n.toLocaleString()} Cells Simulated
              </span>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/80">
                Vectorized Execution
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Wall-clock runtime: <strong className="text-slate-200 font-mono">{result.execution_time_ms.toFixed(1)} ms</strong></span>
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Sampled Parameters: {result.heterogeneity_parameters_sampled.join(', ')}
        </div>
      </div>

      {/* Model Limitation Banner */}
      <AlertBox type="disclaimer" title="Cohort Heterogeneity Interpretation Standard">
        Percentile trajectories represent distributions resulting strictly from simulated biological
        prior sampling (log-normal distributions on Vmax_G6PD, k_GR, k_GPx). These are model-defined stress
        indicators and do NOT constitute clinically validated risk predictions or clinical trial statistics.
      </AlertBox>

      {/* Primary Population Threshold Fraction Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* GSH Depletion Card */}
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Cells with Depleted GSH (&lt; 1.0 mM)
            </span>
            <span className="text-xs font-mono text-slate-400">
              {nDepleted.toLocaleString()} / {n.toLocaleString()} cells
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {result.pct_cells_gsh_depleted.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500">of simulated cohort</span>
          </div>

          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-amber-500 h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, result.pct_cells_gsh_depleted)}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-500 block">
            Model definition: Intracellular [GSH] drops below 1.00 mM during simulation window.
          </span>
        </div>

        {/* Lysis Risk Proxy Card */}
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Cells Exceeding Damage Threshold (D &gt; 0.30)
            </span>
            <span className="text-xs font-mono text-slate-400">
              {nLysisRisk.toLocaleString()} / {n.toLocaleString()} cells
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-rose-400">
              {result.pct_cells_lysis_risk.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500">of simulated cohort</span>
          </div>

          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-rose-500 h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, result.pct_cells_lysis_risk)}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-500 block">
            Model proxy only: Cumulative oxidative damage D exceeds 0.30 (not a validated hemolysis assay).
          </span>
        </div>

        {/* Median Final GSH */}
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Cohort Median Nadir [GSH]
            </span>
            <span className="text-xs font-mono text-slate-400">p50</span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {(Math.min(...bands.gsh_p50) || 0).toFixed(3)}
            </span>
            <span className="text-xs text-slate-400">mM</span>
          </div>

          <div className="text-xs text-slate-400 flex items-center justify-between pt-2 border-t border-slate-800/80">
            <span>5th percentile (most vulnerable):</span>
            <span className="font-mono text-rose-400 font-semibold">
              {(Math.min(...bands.gsh_p5) || 0).toFixed(3)} mM
            </span>
          </div>
        </div>
      </div>

      {/* Percentile Trajectory Visualizer */}
      <PopulationPercentileChart bands={bands} />
    </div>
  );
};
