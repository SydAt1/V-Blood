import React from 'react';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  FlaskConical,
  Info,
  Layers,
} from 'lucide-react';
import type {
  PlaygroundInterpretationResponse,
  CohortInterpretationResponse,
} from '../types/api';

interface InterpretationPlateProps {
  type: 'playground' | 'cohort';
  interpretation: PlaygroundInterpretationResponse | CohortInterpretationResponse | null;
  isLoading: boolean;
  error: string | null;
  onRefresh: (preference: 'auto' | 'deterministic' | 'llm') => void;
  providerPreference: 'auto' | 'deterministic' | 'llm';
  onProviderPreferenceChange: (pref: 'auto' | 'deterministic' | 'llm') => void;
  hasUnverifiedCompounds?: boolean;
}

export const InterpretationPlate: React.FC<InterpretationPlateProps> = ({
  type,
  interpretation,
  isLoading,
  error,
  onRefresh,
  providerPreference,
  onProviderPreferenceChange,
  hasUnverifiedCompounds = false,
}) => {
  const isPlayground = type === 'playground';
  const playgroundInterp = isPlayground
    ? (interpretation as PlaygroundInterpretationResponse)
    : null;
  const cohortInterp = !isPlayground
    ? (interpretation as CohortInterpretationResponse)
    : null;

  return (
    <div
      className="mt-6 border border-[#DDD7CD] rounded-md bg-[#FAF8F5] shadow-sm overflow-hidden"
      data-testid="interpretation-plate"
    >
      {/* Plate Dossier Header */}
      <div className="border-b border-[#DDD7CD] bg-[#F3EFE6] px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-[#E4DDD0] border border-[#DDD7CD] flex items-center justify-center text-[#9E2A2B]">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] tracking-widest uppercase text-[#736B63] font-semibold">
                Scientific Dossier · {isPlayground ? 'Single-Cell Run' : 'Cohort Analysis'}
              </span>
              {interpretation?.provider_used && (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#EAE4D9] text-[#4A443C] border border-[#DDD7CD]">
                  {interpretation.provider_used}
                </span>
              )}
            </div>
            <h3 className="font-serif text-lg font-semibold text-[#1F1E1C] tracking-tight leading-tight">
              Biochemical Interpretation Memorandum
            </h3>
          </div>
        </div>

        {/* Action & Mode Controls */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center bg-[#E8E2D5] rounded border border-[#DDD7CD] p-0.5 font-sans">
            <button
              type="button"
              onClick={() => onProviderPreferenceChange('auto')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                providerPreference === 'auto'
                  ? 'bg-white text-[#1F1E1C] shadow-xs'
                  : 'text-[#736B63] hover:text-[#1F1E1C]'
              }`}
            >
              Auto
            </button>
            <button
              type="button"
              onClick={() => onProviderPreferenceChange('deterministic')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                providerPreference === 'deterministic'
                  ? 'bg-white text-[#1F1E1C] shadow-xs'
                  : 'text-[#736B63] hover:text-[#1F1E1C]'
              }`}
            >
              Rule Engine
            </button>
            <button
              type="button"
              onClick={() => onProviderPreferenceChange('llm')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                providerPreference === 'llm'
                  ? 'bg-white text-[#1F1E1C] shadow-xs'
                  : 'text-[#736B63] hover:text-[#1F1E1C]'
              }`}
            >
              Live LLM
            </button>
          </div>

          <button
            type="button"
            onClick={() => onRefresh(providerPreference)}
            disabled={isLoading}
            title={interpretation ? "Regenerate fresh interpretation" : "Synthesize interpretation"}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#2D2A26] hover:bg-[#433F39] text-[#F5F2EB] font-sans font-medium text-xs transition-colors shadow-xs disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Interpreting...' : 'Synthesize'}</span>
          </button>
        </div>
      </div>

      {/* Grounding & Verification Telemetry Banner */}
      {interpretation && (
        <div className="border-b border-[#E8E2D5] bg-[#F7F4ED] px-5 py-2 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-[#5C554D]">
          <div className="flex items-center gap-3">
            {interpretation.grounding?.passed ? (
              <span className="flex items-center gap-1 text-[#2D5A4C] font-semibold">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Numerical Grounding Verified (±1% tolerance)</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[#B3541E] font-semibold">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Guardrail Verification Flag Raised</span>
              </span>
            )}

            {interpretation.fallback_applied && (
              <span className="px-1.5 py-0.5 rounded bg-[#FAF0E6] text-[#B3541E] border border-[#E8C5A5]">
                Fallback to Rule Engine applied
              </span>
            )}
          </div>

          <div className="text-[11px] text-[#736B63]">
            Generated: {new Date(interpretation.generated_at_utc).toLocaleTimeString()} UTC
          </div>
        </div>
      )}

      {/* Main Body */}
      <div className="p-5 space-y-6">
        {error && (
          <div className="p-3.5 rounded bg-[#FBEBEB] border border-[#E8A5A5] text-[#9E2A2B] text-xs flex items-start gap-2 font-sans">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Interpretation Generation Error</p>
              <p>{error}</p>
            </div>
          </div>
        )}

        {isLoading && !interpretation && (
          <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-10 h-10 rounded-full border-2 border-[#DDD7CD] border-t-[#9E2A2B] animate-spin" />
            <p className="font-serif text-[#1F1E1C] text-base font-medium">
              Evaluating in silico redox kinetics and metabolic fluxes...
            </p>
            <p className="text-xs text-[#736B63] font-mono">
              Grounding endpoints against ODE trajectory and evidence registers
            </p>
          </div>
        )}

        {!isLoading && !interpretation && !error && (
          <div className="py-10 text-center space-y-2">
            <Sparkles className="w-8 h-8 text-[#B3541E] mx-auto opacity-70" />
            <p className="font-serif text-base text-[#1F1E1C]">
              No scientific memorandum generated yet.
            </p>
            <p className="text-xs text-[#736B63] font-sans max-w-md mx-auto">
              Click &quot;Synthesize&quot; to produce an evidence-grounded interpretation of this simulation run using the biochemical rule engine or active LLM.
            </p>
          </div>
        )}

        {interpretation && (
          <>
            {/* Executive Summary Block */}
            <div className="bg-white border border-[#DDD7CD] rounded-md p-4 shadow-xs">
              <span className="font-mono text-[10px] tracking-wider uppercase text-[#736B63] font-semibold block mb-1">
                Executive Finding
              </span>
              <p className="font-serif text-[#1F1E1C] text-base leading-relaxed">
                {interpretation.executive_summary}
              </p>
            </div>

            {/* Structured Analytical Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Box 1: Kinetic Nadir & Trajectory (Playground) OR Tail Risk (Cohort) */}
              <div className="bg-white border border-[#DDD7CD] rounded-md p-4 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 font-mono text-[10px] tracking-wider uppercase text-[#736B63] font-semibold mb-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#B3541E]" />
                    <span>
                      {isPlayground ? 'Nadir & Clearance Kinetics' : 'Population Tail-Risk Dispersion'}
                    </span>
                  </div>
                  <p className="text-xs font-sans text-[#2D2A26] leading-relaxed">
                    {isPlayground
                      ? playgroundInterp?.nadir_analysis
                      : cohortInterp?.tail_risk_analysis}
                  </p>
                </div>
              </div>

              {/* Box 2: Pathway Breakdown (Playground) OR G6PD Interaction (Cohort) */}
              <div className="bg-white border border-[#DDD7CD] rounded-md p-4 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 font-mono text-[10px] tracking-wider uppercase text-[#736B63] font-semibold mb-1.5">
                    <FlaskConical className="w-3.5 h-3.5 text-[#2D5A4C]" />
                    <span>
                      {isPlayground ? 'Enzymatic Flux & Reaction Laws' : 'G6PD Enzymatic Capacity Coupling'}
                    </span>
                  </div>
                  <p className="text-xs font-sans text-[#2D2A26] leading-relaxed">
                    {isPlayground
                      ? playgroundInterp?.pathway_flux_breakdown
                      : cohortInterp?.g6pd_interaction_analysis}
                  </p>
                </div>
              </div>
            </div>

            {/* Differential Control (Playground) OR Lysis Risk Evaluation (Cohort) */}
            <div className="bg-white border border-[#DDD7CD] rounded-md p-4 shadow-xs">
              <span className="font-mono text-[10px] tracking-wider uppercase text-[#736B63] font-semibold block mb-1">
                {isPlayground ? 'Comparative Baseline Control Analysis' : 'Membrane Integrity & Lysis Assessment'}
              </span>
              <p className="text-xs font-sans text-[#2D2A26] leading-relaxed">
                {isPlayground
                  ? playgroundInterp?.control_comparison
                  : cohortInterp?.lysis_risk_evaluation}
              </p>
            </div>

            {/* Suggested Wet-Lab Experiments */}
            {interpretation.suggested_experiments && interpretation.suggested_experiments.length > 0 && (
              <div className="border border-[#E4DDD0] bg-[#F7F4ED] rounded-md p-4">
                <div className="flex items-center gap-1.5 font-mono text-[10px] tracking-wider uppercase text-[#736B63] font-semibold mb-2">
                  <FlaskConical className="w-3.5 h-3.5 text-[#9E2A2B]" />
                  <span>Actionable Wet-Lab Experimental Follow-ups</span>
                </div>
                <ul className="space-y-1.5">
                  {interpretation.suggested_experiments.map((exp, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs font-sans text-[#2D2A26]">
                      <span className="w-4 h-4 rounded-full bg-[#EAE4D9] text-[#736B63] font-mono text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span>{exp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimers & Model Boundaries Plate */}
            <div className="border-t border-[#DDD7CD] pt-4 space-y-2">
              <div className="flex items-start gap-2 text-xs text-[#736B63] font-sans">
                <Info className="w-4 h-4 shrink-0 mt-0.5 text-[#B3541E]" />
                <p className="leading-relaxed">
                  <span className="font-semibold text-[#4A443C]">Scientific Limitations & Model Boundaries: </span>
                  {interpretation.uncertainty_and_limitations}
                </p>
              </div>

              {hasUnverifiedCompounds && (
                <div className="p-3 rounded bg-[#FAF0E6] border border-[#E8C5A5] text-[#B3541E] text-xs flex items-start gap-2 font-sans">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <p>
                    <span className="font-semibold">Unverified Chemical Parameters: </span>
                    One or more compounds in this scenario belong to the UNVERIFIED evidence tier. Numerical conclusions are exploratory hypotheses and excluded from formal validation scoring.
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
