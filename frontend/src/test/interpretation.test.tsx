import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { InterpretationPlate } from '../components/InterpretationPlate';
import type {
  PlaygroundInterpretationResponse,
  CohortInterpretationResponse,
} from '../types/api';

const MOCK_PLAYGROUND_INTERPRETATION: PlaygroundInterpretationResponse = {
  executive_summary: 'Single-cell simulation demonstrated moderate redox perturbation under Menadione exposure.',
  nadir_analysis: 'Minimum [GSH] reached 1.15 mM at t = 360 s, representing a 54% reduction from baseline.',
  pathway_flux_breakdown: 'Redox cycler Menadione sustained catalytic electron transfer from NADPH to generate continuous H2O2 flux.',
  control_comparison: 'Compared to untreated control, the scenario produced an excess 42% depletion.',
  uncertainty_and_limitations: 'Isolated in vitro erythrocyte suspension without ADME or whole-body pharmacokinetics.',
  suggested_experiments: [
    'Quantify reduced and oxidized glutathione via DTNB recycling assay.',
    'Perform spectrophotometric NADPH/NADP+ ratio measurements.',
  ],
  provider_used: 'deterministic-biochemical-v1',
  fallback_applied: false,
  fallback_reason: null,
  grounding: {
    passed: true,
    checked_metrics: { gsh_min_mM: 1.15 },
    disclaimers_present: true,
    unverified_compound_warning_present: true,
    flags: [],
  },
  generated_at_utc: '2026-10-15T11:00:00Z',
};

const MOCK_COHORT_INTERPRETATION: CohortInterpretationResponse = {
  executive_summary: 'Monte Carlo simulation of 1000 erythrocytes revealed significant population heterogeneity.',
  tail_risk_analysis: 'While median nadir was 1.50 mM, the vulnerable 5th percentile tail collapsed to 0.45 mM.',
  g6pd_interaction_analysis: 'Severe G6PD deficiency (alpha = 0.2) shifted the population distribution toward prolonged recovery.',
  lysis_risk_evaluation: 'A predicted 8.5% of cells crossed the synthetic membrane damage threshold.',
  uncertainty_and_limitations: 'In vitro cohort priors; bimodal female mosaicism not modeled.',
  suggested_experiments: [
    'Single-cell redox flow cytometry using ThiolTracker Violet.',
  ],
  provider_used: 'deterministic-biochemical-v1',
  fallback_applied: false,
  fallback_reason: null,
  grounding: {
    passed: true,
    checked_metrics: { mean_gsh_nadir_mM: 1.48 },
    disclaimers_present: true,
    unverified_compound_warning_present: true,
    flags: [],
  },
  generated_at_utc: '2026-10-15T11:00:00Z',
};

describe('InterpretationPlate Component (Milestone 6)', () => {
  it('renders single-cell playground interpretation correctly', () => {
    render(
      <InterpretationPlate
        type="playground"
        interpretation={MOCK_PLAYGROUND_INTERPRETATION}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        providerPreference="auto"
        onProviderPreferenceChange={vi.fn()}
        hasUnverifiedCompounds={false}
      />
    );

    // Title & Badge
    expect(screen.getByText(/Biochemical Interpretation Memorandum/i)).toBeInTheDocument();
    expect(screen.getByText('deterministic-biochemical-v1')).toBeInTheDocument();

    // Grounding indicator
    expect(screen.getByText(/Numerical Grounding Verified/i)).toBeInTheDocument();

    // Content sections
    expect(screen.getByText(MOCK_PLAYGROUND_INTERPRETATION.executive_summary)).toBeInTheDocument();
    expect(screen.getByText(MOCK_PLAYGROUND_INTERPRETATION.nadir_analysis)).toBeInTheDocument();
    expect(screen.getByText(MOCK_PLAYGROUND_INTERPRETATION.pathway_flux_breakdown)).toBeInTheDocument();
    expect(screen.getByText(MOCK_PLAYGROUND_INTERPRETATION.control_comparison)).toBeInTheDocument();

    // Suggested experiments
    expect(screen.getByText(/DTNB recycling assay/i)).toBeInTheDocument();
  });

  it('renders cohort interpretation with tail-risk and lysis assessments', () => {
    render(
      <InterpretationPlate
        type="cohort"
        interpretation={MOCK_COHORT_INTERPRETATION}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        providerPreference="auto"
        onProviderPreferenceChange={vi.fn()}
      />
    );

    expect(screen.getByText(MOCK_COHORT_INTERPRETATION.executive_summary)).toBeInTheDocument();
    expect(screen.getByText(MOCK_COHORT_INTERPRETATION.tail_risk_analysis)).toBeInTheDocument();
    expect(screen.getByText(MOCK_COHORT_INTERPRETATION.g6pd_interaction_analysis)).toBeInTheDocument();
    expect(screen.getByText(MOCK_COHORT_INTERPRETATION.lysis_risk_evaluation)).toBeInTheDocument();
  });

  it('handles provider preference switcher and refresh click', () => {
    const handlePrefChange = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <InterpretationPlate
        type="playground"
        interpretation={MOCK_PLAYGROUND_INTERPRETATION}
        isLoading={false}
        error={null}
        onRefresh={handleRefresh}
        providerPreference="auto"
        onProviderPreferenceChange={handlePrefChange}
      />
    );

    // Click Rule Engine button
    const ruleBtn = screen.getByRole('button', { name: /Rule Engine/i });
    fireEvent.click(ruleBtn);
    expect(handlePrefChange).toHaveBeenCalledWith('deterministic');

    // Click Synthesize button
    const synthBtn = screen.getByRole('button', { name: /Synthesize/i });
    fireEvent.click(synthBtn);
    expect(handleRefresh).toHaveBeenCalled();
  });

  it('renders loading and error states properly', () => {
    const { rerender } = render(
      <InterpretationPlate
        type="playground"
        interpretation={null}
        isLoading={true}
        error={null}
        onRefresh={vi.fn()}
        providerPreference="auto"
        onProviderPreferenceChange={vi.fn()}
      />
    );

    expect(screen.getByText(/Evaluating in silico redox kinetics/i)).toBeInTheDocument();

    rerender(
      <InterpretationPlate
        type="playground"
        interpretation={null}
        isLoading={false}
        error="Connection refused"
        onRefresh={vi.fn()}
        providerPreference="auto"
        onProviderPreferenceChange={vi.fn()}
      />
    );

    expect(screen.getByText(/Interpretation Generation Error/i)).toBeInTheDocument();
    expect(screen.getByText('Connection refused')).toBeInTheDocument();
  });
});
