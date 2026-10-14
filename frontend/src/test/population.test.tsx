import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PopulationResults } from '../features/population/PopulationResults';
import { PopulationPercentileChart } from '../features/population/PopulationPercentileChart';
import type { PopulationResult } from '../types/api';

const MOCK_POPULATION_RESULT: PopulationResult = {
  n_cells: 1000,
  execution_time_ms: 1245.8,
  pct_cells_gsh_depleted: 14.2,
  pct_cells_lysis_risk: 3.5,
  n_depleted_cells: 142,
  n_lysis_risk_cells: 35,
  heterogeneity_parameters_sampled: ['vmax_g6pd', 'k_gr', 'k_gpx', 'total_glutathione_pool'],
  research_disclaimer: 'Research cohort hypothesis generation only.',
  percentile_bands: {
    time_points_s: [0, 600, 1800],
    gsh_p5: [2.1, 0.85, 1.2],
    gsh_p25: [2.3, 1.2, 1.8],
    gsh_p50: [2.5, 1.5, 2.2],
    gsh_p75: [2.7, 1.9, 2.4],
    gsh_p95: [2.9, 2.3, 2.6],
    nadph_p5: [0.02, 0.008, 0.015],
    nadph_p25: [0.025, 0.012, 0.022],
    nadph_p50: [0.03, 0.018, 0.028],
    nadph_p75: [0.035, 0.022, 0.032],
    nadph_p95: [0.04, 0.028, 0.038],
    damage_p5: [0.0, 0.01, 0.02],
    damage_p25: [0.0, 0.02, 0.05],
    damage_p50: [0.0, 0.05, 0.12],
    damage_p75: [0.0, 0.15, 0.28],
    damage_p95: [0.0, 0.32, 0.45],
  },
};

describe('PopulationResults and Percentile Chart Components', () => {
  it('displays correct cohort counts, percentage fractions, and runtime', () => {
    render(<PopulationResults result={MOCK_POPULATION_RESULT} />);

    // Cohort size
    expect(screen.getByText(/1,000 Cells Simulated/i)).toBeInTheDocument();

    // Wall-clock runtime
    expect(screen.getByText('1245.8 ms')).toBeInTheDocument();

    // Depleted fraction
    expect(screen.getByText('14.2%')).toBeInTheDocument();
    expect(screen.getByText(/142 \/ 1,000 cells/i)).toBeInTheDocument();

    // Lysis risk fraction
    expect(screen.getByText('3.5%')).toBeInTheDocument();
    expect(screen.getByText(/35 \/ 1,000 cells/i)).toBeInTheDocument();
  });

  it('switches between GSH, Damage, and NADPH channels in percentile chart', () => {
    render(<PopulationPercentileChart bands={MOCK_POPULATION_RESULT.percentile_bands} />);

    // Default is GSH
    expect(screen.getByText(/Reduced Glutathione \[GSH\]/i)).toBeInTheDocument();

    // Switch to Damage Proxy
    const damageBtn = screen.getByText('Damage Proxy [D]');
    fireEvent.click(damageBtn);
    expect(screen.getByText(/Cumulative Damage Index \[D\]/i)).toBeInTheDocument();

    // Switch to NADPH
    const nadphBtn = screen.getByText('NADPH Pool');
    fireEvent.click(nadphBtn);
    expect(screen.getByText(/Intracellular \[NADPH\]/i)).toBeInTheDocument();
  });
});
