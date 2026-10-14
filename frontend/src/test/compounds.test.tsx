import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CompoundCatalog } from '../features/compounds/CompoundCatalog';
import type { CompoundResponse } from '../types/api';

const MOCK_COMPOUNDS: CompoundResponse[] = [
  {
    compound_id: 'cmp_menadione',
    name: 'Menadione',
    smiles: 'CC1=C(C(=O)c2ccccc2C1=O)',
    inchikey: 'MJVBLLDWVPNLAN-UHFFFAOYSA-N',
    mechanism_type: 'REDOX_CYCLER',
    default_parameters: { k_cycle: 0.015, km_nadph: 0.01 },
    parameter_ranges: { k_cycle: [0.001, 0.1] },
    exposure_units: 'mM',
    evidence_level: 'CURATED',
    is_unverified: false,
    provenance: 'Winterbourn & Stern (1987) Clin Chim Acta 168:145-152.',
    confidence_score: 0.9,
  },
  {
    compound_id: 'cmp_cdnb',
    name: '1-Chloro-2,4-dinitrobenzene (CDNB)',
    smiles: 'C1=CC(=C(C=C1[N+](=O)[O-])[N+](=O)[O-])Cl',
    inchikey: 'FDFUODIDABPFIL-UHFFFAOYSA-N',
    mechanism_type: 'GSH_CONJUGATOR',
    default_parameters: { k_conj: 0.05 },
    parameter_ranges: { k_conj: [0.005, 0.5] },
    exposure_units: 'mM',
    evidence_level: 'CURATED',
    is_unverified: false,
    provenance: 'Awasthi et al. (1981) Blood 58(4):733-738.',
    confidence_score: 0.92,
  },
  {
    compound_id: 'cmp_xenobiotic_x101',
    name: 'Xenobiotic X-101 (Synthetic Probe)',
    smiles: 'C1=CC=C2C(=C1)C=CC=C2',
    inchikey: 'UFWIBSMAOFPBAB-UHFFFAOYSA-N',
    mechanism_type: 'NADPH_DRAIN',
    default_parameters: { k_drain: 0.05 },
    parameter_ranges: { k_drain: [0.001, 0.2] },
    exposure_units: 'mM',
    evidence_level: 'UNVERIFIED',
    is_unverified: true,
    provenance: 'SYNTHETIC TEST PROBE: Hypothetical probe parameters.',
    confidence_score: 0.15,
  },
];

describe('CompoundCatalog Component', () => {
  it('renders all compounds and displays evidence badges correctly', () => {
    const handleSelect = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <CompoundCatalog
        compounds={MOCK_COMPOUNDS}
        loading={false}
        error={null}
        onRefresh={handleRefresh}
        onSelectForScenario={handleSelect}
      />
    );

    expect(screen.getByText('Menadione')).toBeInTheDocument();
    expect(screen.getByText('1-Chloro-2,4-dinitrobenzene (CDNB)')).toBeInTheDocument();
    expect(screen.getByText('Xenobiotic X-101 (Synthetic Probe)')).toBeInTheDocument();

    // Verify evidence badges
    const curatedBadges = screen.getAllByText('CURATED');
    expect(curatedBadges.length).toBe(2);

    const unverifiedBadges = screen.getAllByText('UNVERIFIED');
    expect(unverifiedBadges.length).toBeGreaterThanOrEqual(1);
  });

  it('filters compounds by text search query', () => {
    render(
      <CompoundCatalog
        compounds={MOCK_COMPOUNDS}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
        onSelectForScenario={vi.fn()}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search by compound name, ID, SMILES...');
    fireEvent.change(searchInput, { target: { value: 'CDNB' } });

    expect(screen.getByText('1-Chloro-2,4-dinitrobenzene (CDNB)')).toBeInTheDocument();
    expect(screen.queryByText('Menadione')).not.toBeInTheDocument();
    expect(screen.queryByText('Xenobiotic X-101 (Synthetic Probe)')).not.toBeInTheDocument();
  });

  it('filters compounds by mechanism type', () => {
    render(
      <CompoundCatalog
        compounds={MOCK_COMPOUNDS}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
        onSelectForScenario={vi.fn()}
      />
    );

    const selects = screen.getAllByRole('combobox');
    const mechanismSelect = selects[0]; // First select is mechanism
    fireEvent.change(mechanismSelect, { target: { value: 'REDOX_CYCLER' } });

    expect(screen.getByText('Menadione')).toBeInTheDocument();
    expect(screen.queryByText('1-Chloro-2,4-dinitrobenzene (CDNB)')).not.toBeInTheDocument();
  });

  it('opens compound inspection modal on inspect button click', () => {
    render(
      <CompoundCatalog
        compounds={MOCK_COMPOUNDS}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
        onSelectForScenario={vi.fn()}
      />
    );

    const inspectButtons = screen.getAllByText('Inspect Details');
    fireEvent.click(inspectButtons[0]);

    // Modal should now be open displaying literature provenance
    expect(screen.getByText('Literature Provenance')).toBeInTheDocument();
    expect(screen.getAllByText(/Winterbourn & Stern/i).length).toBeGreaterThanOrEqual(1);
  });
});
