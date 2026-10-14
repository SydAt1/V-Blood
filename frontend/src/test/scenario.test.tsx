import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ScenarioBuilder } from '../features/scenarios/ScenarioBuilder';
import { ScenarioResults } from '../features/scenarios/ScenarioResults';
import type { CompoundResponse, ScenarioRunResponse } from '../types/api';

const MOCK_COMPOUNDS: CompoundResponse[] = [
  {
    compound_id: 'cmp_menadione',
    name: 'Menadione',
    smiles: 'CC1=C(C(=O)c2ccccc2C1=O)',
    inchikey: 'MJVBLLDWVPNLAN-UHFFFAOYSA-N',
    mechanism_type: 'REDOX_CYCLER',
    default_parameters: { k_cycle: 0.015 },
    parameter_ranges: { k_cycle: [0.001, 0.1] },
    exposure_units: 'mM',
    evidence_level: 'CURATED',
    is_unverified: false,
    provenance: 'Winterbourn 1987',
    confidence_score: 0.9,
  },
];

const MOCK_SCENARIO_RESULT: ScenarioRunResponse = {
  run_id: 'scen_test_123',
  scenario_request: {
    compounds: [{ compound_id: 'cmp_menadione', dose_mM: 0.05 }],
    exposure_profile: 'BOLUS',
    duration_s: 3600,
    g6pd_alpha: 1.0,
    model_version: 'rbc-g6pd-gsh-v2',
  },
  derived_metrics: {
    gsh_nadir_mM: 1.425,
    gssg_peak_mM: 0.285,
    time_to_90pct_recovery_s: 1420,
    net_total_glutathione_loss_pct: 4.8,
    damage_onset_time_s: 180,
  },
  has_unverified_compounds: false,
  unverified_compounds: [],
  compound_summaries: [
    {
      compound_id: 'cmp_menadione',
      name: 'Menadione',
      mechanism: 'REDOX_CYCLER',
      evidence_level: 'CURATED',
      is_unverified: false,
      provenance: 'Winterbourn 1987',
    },
  ],
  interaction_assumptions: ['Additive oxidant generation.'],
  trajectory_length: 50,
  research_disclaimer: 'Research simulation only.',
  trajectory: [
    {
      t_s: 0,
      gsh_mM: 2.5,
      gssg_mM: 0.025,
      h2o2_mM: 0.0001,
      nadph_mM: 0.03,
      damage: 0.0,
      hemolysis_pct: 0.0,
      gsh_gssg_ratio: 100,
    },
    {
      t_s: 100,
      gsh_mM: 1.425,
      gssg_mM: 0.285,
      h2o2_mM: 0.0025,
      nadph_mM: 0.015,
      damage: 0.06,
      hemolysis_pct: 0.2,
      gsh_gssg_ratio: 5,
    },
    {
      t_s: 3600,
      gsh_mM: 2.38,
      gssg_mM: 0.026,
      h2o2_mM: 0.0001,
      nadph_mM: 0.029,
      damage: 0.065,
      hemolysis_pct: 0.25,
      gsh_gssg_ratio: 91,
    },
  ],
};

describe('ScenarioBuilder Component', () => {
  it('validates dose bounds and rejects negative or zero dose', async () => {
    const handleRun = vi.fn().mockResolvedValue(undefined);

    render(
      <ScenarioBuilder
        compounds={MOCK_COMPOUNDS}
        onRunScenario={handleRun}
        loading={false}
      />
    );

    const doseInput = screen.getByRole('spinbutton');
    fireEvent.change(doseInput, { target: { value: '0' } });

    const submitBtn = screen.getByText('Execute Simulation');
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/must be strictly greater than 0/i)).toBeInTheDocument();
    expect(handleRun).not.toHaveBeenCalled();
  });

  it('rejects dose exceeding upper 20.0 mM safety boundary', async () => {
    const handleRun = vi.fn().mockResolvedValue(undefined);

    render(
      <ScenarioBuilder
        compounds={MOCK_COMPOUNDS}
        onRunScenario={handleRun}
        loading={false}
      />
    );

    const doseInput = screen.getByRole('spinbutton');
    fireEvent.change(doseInput, { target: { value: '25.0' } });

    const submitBtn = screen.getByText('Execute Simulation');
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/exceeds the 20.0 mM upper safety limit/i)).toBeInTheDocument();
    expect(handleRun).not.toHaveBeenCalled();
  });

  it('submits valid scenario request and prevents duplicate execution during loading', async () => {
    const handleRun = vi.fn().mockResolvedValue(undefined);

    const { rerender } = render(
      <ScenarioBuilder
        compounds={MOCK_COMPOUNDS}
        onRunScenario={handleRun}
        loading={false}
      />
    );

    const submitBtn = screen.getByText('Execute Simulation');
    fireEvent.click(submitBtn);

    expect(handleRun).toHaveBeenCalledTimes(1);

    // When loading is true, button should be disabled
    rerender(
      <ScenarioBuilder
        compounds={MOCK_COMPOUNDS}
        onRunScenario={handleRun}
        loading={true}
      />
    );

    const integratingBtn = screen.getByText(/Integrating ODEs/i);
    expect(integratingBtn.closest('button')).toBeDisabled();
  });
});

describe('ScenarioResults Component', () => {
  it('displays calculated derived metrics accurately', () => {
    render(<ScenarioResults treatmentResult={MOCK_SCENARIO_RESULT} />);

    // Check GSH nadir
    expect(screen.getByText('1.425')).toBeInTheDocument();
    // Check peak GSSG
    expect(screen.getByText('0.285')).toBeInTheDocument();
    // Check 90% recovery time
    expect(screen.getByText(/1420/)).toBeInTheDocument();
    // Check net total glutathione loss
    expect(screen.getByText('4.8%')).toBeInTheDocument();
  });
});
