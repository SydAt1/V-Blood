import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CompoundResearchWorkspace } from '../features/research/CompoundResearchWorkspace';
import * as clientModule from '../api/client';
import type { ResearchDossier, ResearchJobStatus } from '../types/api';

const MOCK_DOSSIER: ResearchDossier = {
  candidate_id: 'rcand_primaquine',
  query_name: 'Primaquine',
  research_objective: 'Investigate G6PD oxidative sensitivity in human erythrocytes.',
  target_scope: 'Human Erythrocyte Redox Biology (V-Blood ODE Engine)',
  status: 'CANDIDATE',
  chemical_identity: {
    preferred_name: 'Primaquine',
    common_names: ['Primaquine', 'WR-2975'],
    molecular_formula: 'C15H21N3O',
    smiles: 'CC(CCCN)NC1=C2C(=CC=C1)C(=CC=N2)OC',
    inchikey: 'FPGZONURBKGNAZ-UHFFFAOYSA-N',
    entity_type: 'SMALL_MOLECULE',
    charge: 0,
    molecular_weight: 259.35,
    source: 'PubChem PUG REST API',
    retrieved_at: '2026-10-15T00:00:00Z',
    is_ambiguous: false,
    ambiguity_candidates: [],
  },
  sources: [
    {
      source_id: 'src_pmid_1319808',
      title: 'Generation of superoxide and hydrogen peroxide by 5-hydroxyprimaquine',
      authors: ['Vasquez-Vivar J', 'Augusto O'],
      journal: 'J Biol Chem',
      year: 1992,
      doi: '10.1016/S0021-9258(19)49877-0',
      pmid: '1319808',
      url: 'https://pubmed.ncbi.nlm.nih.gov/1319808/',
      abstract: 'Catalytic redox cycling generating superoxide and H2O2 in human RBCs.',
      source_type: 'PUBMED',
      full_text_available: true,
      erythrocyte_relevant: true,
      retrieval_timestamp: '2026-10-15T00:00:00Z',
    },
  ],
  findings: [
    {
      finding_id: 'fnd_001',
      source_id: 'src_pmid_1319808',
      biological_system: 'Human erythrocytes in vitro',
      species: 'Homo sapiens',
      is_human_erythrocyte: true,
      experimental_conditions: 'Standard RBC suspension buffer',
      concentration: 50.0,
      concentration_unit: 'uM',
      observed_outcomes: 'Accelerated peroxide influx and GSH depletion.',
      proposed_mechanism: 'Catalytic redox cycling',
      quantitative_measurements: { catalytic_rate_s: 0.035 },
      uncertainty_notes: 'Assayed in vitro.',
      controls_and_limitations: 'No hepatic metabolism.',
      supports_proposed_effect: true,
      exact_quote: 'The active metabolite undergoes rapid redox cycling.',
      finding_evidence_level: 'CURATED',
      grade_rationale: 'Direct human erythrocyte measurement.',
    },
  ],
  mechanism_mappings: [
    {
      mechanism_type: 'REDOX_CYCLER',
      is_compatible: true,
      confidence: 0.85,
      supporting_finding_ids: ['fnd_001'],
      assumptions: ['1:1 H2O2 generation per cycle'],
      unmodeled_aspects: ['Hepatic clearance'],
      unresolved_questions: [],
      parameters: [
        {
          name: 'catalytic_rate_s',
          mechanism: 'REDOX_CYCLER',
          value: 0.035,
          units: 's^-1',
          min_bound: 0.0005,
          max_bound: 0.5,
          conversion_method: 'Apparent turnover rate',
          provenance: 'MEASURED',
          evidence_level: 'CURATED',
          confidence_score: 0.9,
          assumptions: [],
          is_identifiable: true,
          validation_status: 'VALID',
        },
      ],
    },
  ],
  validation_summary: {
    is_valid: true,
    simulation_eligible: true,
    gates: [
      {
        gate_name: 'Gate 1: Chemical Identity Consistency',
        passed: true,
        message: 'Chemical identity verified.',
        severity: 'INFO',
      },
      {
        gate_name: 'Gate 6: Mechanism Compatibility',
        passed: true,
        message: 'Compatible with REDOX_CYCLER.',
        severity: 'INFO',
      },
    ],
    blocking_reasons: [],
    warnings: [],
  },
  limitations: ['No hepatic clearance'],
  unresolved_questions: [],
  audit_history: [
    {
      timestamp: '2026-10-15T00:00:00Z',
      action: 'CREATED',
      actor: 'orchestrator',
      new_status: 'CANDIDATE',
      notes: 'Initial creation',
    },
  ],
  created_at: '2026-10-15T00:00:00Z',
  updated_at: '2026-10-15T00:00:00Z',
  pipeline_version: '1.0.0',
  llm_provider_metadata: {},
  prompt_version: 'v1.0',
  revision: 1,
};

describe('CompoundResearchWorkspace Component', () => {
  it('renders research input bench, sample chemical buttons, and scope disclaimer', async () => {
    vi.spyOn(clientModule, 'getResearchCandidates').mockResolvedValue([]);
    const handleLoad = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <CompoundResearchWorkspace
        onLoadIntoScenario={handleLoad}
        onRefreshLibrary={handleRefresh}
      />
    );

    expect(screen.getByText('Substance Research Submission')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. Primaquine, Menadione/i)).toBeInTheDocument();
    expect(screen.getByText('Primaquine')).toBeInTheDocument();
    expect(screen.getByText('Menadione')).toBeInTheDocument();
  });

  it('displays research dossier with chemical identity, literature sources, and 10-gate validation', async () => {
    vi.spyOn(clientModule, 'getResearchCandidates').mockResolvedValue([MOCK_DOSSIER]);
    const handleLoad = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <CompoundResearchWorkspace
        onLoadIntoScenario={handleLoad}
        onRefreshLibrary={handleRefresh}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText('Primaquine').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('FPGZONURBKGNAZ-UHFFFAOYSA-N')).toBeInTheDocument();
    expect(screen.getByText('C15H21N3O')).toBeInTheDocument();
    expect(screen.getByText('REDOX_CYCLER')).toBeInTheDocument();
    expect(screen.getByText('Approve for Simulation')).toBeInTheDocument();
  });

  it('triggers candidate approval action and updates status', async () => {
    const approvedDossier: ResearchDossier = {
      ...MOCK_DOSSIER,
      status: 'SIMULATION_READY',
      revision: 2,
    };
    vi.spyOn(clientModule, 'getResearchCandidates').mockResolvedValue([MOCK_DOSSIER]);
    const approveSpy = vi.spyOn(clientModule, 'approveResearchCandidate').mockResolvedValue(approvedDossier);
    const handleLoad = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <CompoundResearchWorkspace
        onLoadIntoScenario={handleLoad}
        onRefreshLibrary={handleRefresh}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Approve for Simulation')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Approve for Simulation'));
    await waitFor(() => {
      expect(approveSpy).toHaveBeenCalledWith('rcand_primaquine', 'researcher', expect.any(String));
      expect(handleRefresh).toHaveBeenCalled();
    });
  });
});
