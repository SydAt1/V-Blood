import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ErythrocyteViewer } from '../features/visualization/ErythrocyteViewer';
import * as client from '../api/client';
import type { VisualTrajectoryResponse } from '../types/api';

const MOCK_VISUAL_RESPONSE: VisualTrajectoryResponse = {
  run_id: 'test_run_456',
  total_frames: 3,
  playback_duration_s: 3600,
  model_notes: 'Model-derived biochemical state.',
  frames: [
    {
      t_s: 0,
      normalized_gsh: 1.0,
      normalized_nadph: 1.0,
      damage: 0.0,
      hemolysis_pct: 0.0,
      cell_state: 'healthy',
      state_classification_type: 'MODEL_DERIVED',
      morphology_simulated: false,
    },
    {
      t_s: 1800,
      normalized_gsh: 0.55,
      normalized_nadph: 0.45,
      damage: 0.22,
      hemolysis_pct: 1.2,
      cell_state: 'severely_stressed',
      state_classification_type: 'MODEL_DERIVED',
      morphology_simulated: false,
    },
    {
      t_s: 3600,
      normalized_gsh: 0.2,
      normalized_nadph: 0.2,
      damage: 0.55,
      hemolysis_pct: 6.8,
      cell_state: 'lysis_risk',
      state_classification_type: 'MODEL_DERIVED',
      morphology_simulated: false,
    },
  ],
};

describe('ErythrocyteViewer Component', () => {
  beforeEach(() => {
    vi.spyOn(client, 'getVisualTrajectory').mockResolvedValue(MOCK_VISUAL_RESPONSE);
  });

  it('renders visual frame state and explicit morphology disclaimer', async () => {
    render(<ErythrocyteViewer runId="test_run_456" />);

    // Wait for frames to load
    await waitFor(() => {
      expect(screen.getByText('Erythrocyte State Playback')).toBeInTheDocument();
    });

    // Check mandatory illustrative morphology notice
    expect(
      screen.getByText(/Physical membrane deformations \(echinocytosis, spiculation, crenation, or swelling\) are/i)
    ).toBeInTheDocument();

    // Check initial frame status
    expect(screen.getByText(/Healthy/i)).toBeInTheDocument();
  });

  it('scrubs to frame 2 and updates biochemical meters and lysis risk badge', async () => {
    render(<ErythrocyteViewer runId="test_run_456" />);

    await waitFor(() => {
      expect(screen.getByText('Frame 1 / 3')).toBeInTheDocument();
    });

    const slider = screen.getByRole('slider');
    // Scrub to last frame (index 2)
    fireEvent.change(slider, { target: { value: '2' } });

    // Should now reflect frame 3: lysis_risk
    expect(screen.getByText(/Lysis Risk \(Model Proxy\)/i)).toBeInTheDocument();
    expect(screen.getByText('0.550')).toBeInTheDocument(); // damage D
    expect(screen.getByText('6.8%')).toBeInTheDocument(); // lysis proxy
  });
});
