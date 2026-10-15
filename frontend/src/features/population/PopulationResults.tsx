import React, { useState, useEffect } from 'react';
import type { CohortInterpretationResponse, PopulationRequest, PopulationResult } from '../../types/api';
import { PopulationPercentileChart } from './PopulationPercentileChart';
import { AlertBox } from '../../components/AlertBox';
import { InterpretationPlate } from '../../components/InterpretationPlate';
import { interpretCohort } from '../../api/client';
import { Clock, Users } from 'lucide-react';

interface Props {
  result: PopulationResult | null;
  request?: PopulationRequest | null;
}

export const PopulationResults: React.FC<Props> = ({ result, request }) => {
  const [interpretation, setInterpretation] = useState<CohortInterpretationResponse | null>(null);
  const [interpLoading, setInterpLoading] = useState<boolean>(false);
  const [interpError, setInterpError] = useState<string | null>(null);
  const [providerPreference, setProviderPreference] = useState<'auto' | 'deterministic' | 'llm'>('auto');
  const [interpretationCache, setInterpretationCache] = useState<Record<string, CohortInterpretationResponse>>({});

  const getCohortKey = (res: any, pref: string) => {
    const id = res?.run_id || `${res?.n_cells}_${res?.execution_time_ms}`;
    return `cohort:${id}:${pref}`;
  };

  const fetchInterpretation = async (
    pref: 'auto' | 'deterministic' | 'llm',
    forceRefresh: boolean = false
  ) => {
    if (!result) return;
    const key = getCohortKey(result, pref);

    if (!forceRefresh && interpretationCache[key]) {
      setInterpretation(interpretationCache[key]);
      setInterpLoading(false);
      setInterpError(null);
      return;
    }

    setInterpLoading(true);
    setInterpError(null);

    // Fallback constructed request if not explicitly passed
    const popRequest: PopulationRequest = request || {
      scenario_request: {
        compounds: [],
        exposure_profile: 'BOLUS',
        duration_s: 1800,
        g6pd_alpha: 1.0,
        model_version: 'rbc-g6pd-gsh-v2',
      },
      n_cells: result.n_cells,
    };

    try {
      const resp = await interpretCohort({
        population_request: popRequest,
        population_result: result,
        provider_preference: pref,
        force_refresh: forceRefresh,
      });

      setInterpretationCache((prev) => {
        const next = { ...prev, [key]: resp };
        if (pref === 'auto') {
          const effectiveMode = resp.provider_used.includes('external-llm') ? 'llm' : 'deterministic';
          next[getCohortKey(result, effectiveMode)] = resp;
        } else if (pref === 'llm' && !resp.fallback_applied) {
          next[getCohortKey(result, 'auto')] = resp;
        }
        return next;
      });

      setInterpretation(resp);
    } catch (err: any) {
      setInterpError(err.detail || err.message || 'Cohort interpretation failed.');
    } finally {
      setInterpLoading(false);
    }
  };

  const handleProviderPreferenceChange = (newPref: 'auto' | 'deterministic' | 'llm') => {
    setProviderPreference(newPref);
    if (!result) return;
    const key = getCohortKey(result, newPref);

    if (interpretationCache[key]) {
      setInterpretation(interpretationCache[key]);
      setInterpError(null);
    } else {
      fetchInterpretation(newPref, false);
    }
  };

  useEffect(() => {
    if (result) {
      const key = getCohortKey(result, providerPreference);
      if (interpretationCache[key]) {
        setInterpretation(interpretationCache[key]);
      } else {
        fetchInterpretation(providerPreference, false);
      }
    } else {
      setInterpretation(null);
    }
  }, [result?.n_cells, result?.execution_time_ms]);

  if (!result) return null;

  const bands = result.percentile_bands;
  const n = result.n_cells || 0;
  const nDepleted = result.n_depleted_cells || 0;
  const nLysisRisk = result.n_lysis_risk_cells || 0;

  const minGshP50 =
    bands && Array.isArray(bands.gsh_p50) && bands.gsh_p50.length > 0
      ? Math.min(...bands.gsh_p50)
      : 0;

  const minGshP5 =
    bands && Array.isArray(bands.gsh_p5) && bands.gsh_p5.length > 0
      ? Math.min(...bands.gsh_p5)
      : 0;

  return (
    <div className="space-y-5">
      {/* Run Summary Bar */}
      <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-4 flex flex-wrap items-center justify-between gap-4 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 border border-[#B6CEE0] bg-[#EBF2F7] flex items-center justify-center text-[#2E5875]">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-editorial text-base font-bold text-[#181B18]">
                Cohort of {n.toLocaleString()} Cells Simulated
              </span>
              <span className="text-[10px] font-mono font-semibold text-[#284431] bg-[#EDF3EE] px-2 py-0.5 border border-[#BCD0C1]">
                Vectorized Execution
              </span>
            </div>
            <div className="text-xs text-[#666E65] mt-0.5 flex items-center gap-1.5 font-mono">
              <Clock className="w-3.5 h-3.5 text-[#868E85]" />
              <span>
                Wall-clock runtime:{' '}
                <strong className="text-[#181B18] font-mono">
                  {typeof result.execution_time_ms === 'number'
                    ? result.execution_time_ms.toFixed(1)
                    : '0.0'}{' '}
                  ms
                </strong>
              </span>
            </div>
          </div>
        </div>

        <div className="text-xs text-[#666E65] font-mono bg-[#FAF8F3] px-3 py-1.5 border border-[#EDE8DE]">
          Sampled Parameters:{' '}
          <span className="text-[#181B18]">
            {(result.heterogeneity_parameters_sampled || []).join(', ')}
          </span>
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
        <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-4 space-y-2.5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)]">
          <div className="flex items-center justify-between text-[10.5px] font-mono text-[#767D75]">
            <span className="font-semibold uppercase tracking-wider text-[#181B18]">
              Cells with Depleted GSH (&lt; 1.0 mM)
            </span>
            <span>
              {nDepleted.toLocaleString()} / {n.toLocaleString()} cells
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="font-editorial text-3xl font-bold text-[#8E5A1E]">
              {(result.pct_cells_gsh_depleted || 0).toFixed(1)}%
            </span>
            <span className="text-xs text-[#767D75] font-mono">of simulated cohort</span>
          </div>

          <div className="w-full bg-[#EDE8DE] h-2 border border-[#D8D1C2]">
            <div
              className="bg-[#8E5A1E] h-full transition-all"
              style={{ width: `${Math.min(100, result.pct_cells_gsh_depleted || 0)}%` }}
            />
          </div>
          <span className="text-[10px] text-[#868E85] font-mono block">
            Model definition: Intracellular [GSH] drops below 1.00 mM during simulation window.
          </span>
        </div>

        {/* Lysis Risk Proxy Card */}
        <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-4 space-y-2.5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)]">
          <div className="flex items-center justify-between text-[10.5px] font-mono text-[#767D75]">
            <span className="font-semibold uppercase tracking-wider text-[#181B18]">
              Cells Exceeding Damage Threshold (D &gt; 0.30)
            </span>
            <span>
              {nLysisRisk.toLocaleString()} / {n.toLocaleString()} cells
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="font-editorial text-3xl font-bold text-[#9B332B]">
              {(result.pct_cells_lysis_risk || 0).toFixed(1)}%
            </span>
            <span className="text-xs text-[#767D75] font-mono">of simulated cohort</span>
          </div>

          <div className="w-full bg-[#EDE8DE] h-2 border border-[#D8D1C2]">
            <div
              className="bg-[#9B332B] h-full transition-all"
              style={{ width: `${Math.min(100, result.pct_cells_lysis_risk || 0)}%` }}
            />
          </div>
          <span className="text-[10px] text-[#868E85] font-mono block">
            Model proxy only: Cumulative oxidative damage D exceeds 0.30 (not a validated hemolysis assay).
          </span>
        </div>

        {/* Median Final GSH */}
        <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-4 space-y-2.5 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)]">
          <div className="flex items-center justify-between text-[10.5px] font-mono text-[#767D75]">
            <span className="font-semibold uppercase tracking-wider text-[#181B18]">
              Cohort Median Nadir [GSH]
            </span>
            <span className="font-bold text-[#286345]">p50</span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="font-editorial text-3xl font-bold text-[#286345]">
              {minGshP50.toFixed(3)}
            </span>
            <span className="text-xs text-[#767D75] font-mono">mM</span>
          </div>

          <div className="text-xs text-[#666E65] flex items-center justify-between pt-2 border-t border-[#EDE8DE] font-mono">
            <span>5th percentile (most vulnerable):</span>
            <span className="text-[#9B332B] font-bold">
              {minGshP5.toFixed(3)} mM
            </span>
          </div>
        </div>
      </div>

      {/* Percentile Trajectory Visualizer */}
      {bands && <PopulationPercentileChart bands={bands} />}

      {/* Milestone 6: Scientific Cohort Interpretation Memorandum */}
      <InterpretationPlate
        type="cohort"
        interpretation={interpretation}
        isLoading={interpLoading}
        error={interpError}
        onRefresh={(pref) => fetchInterpretation(pref, true)}
        providerPreference={providerPreference}
        onProviderPreferenceChange={handleProviderPreferenceChange}
        hasUnverifiedCompounds={false}
      />
    </div>
  );
};
