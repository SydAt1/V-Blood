"""
Visual-State Contract for Frontend Blood Playground (Milestone 4 - Task 5).

Converts numerical simulation trajectories into standardized, frontend-ready
per-frame visual states with biochemical health classifications.

CRITICAL MODEL INTEGRITY NOTICE:
States and thresholds are strictly derived from modeled biochemical variables
(GSH, NADPH, D). No morphological distortions (e.g. echinocyte spiculation,
crenation) are simulated or implied.
"""

from __future__ import annotations

from enum import Enum
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from vblood.schemas.simulation import TrajectoryPoint


class CellVisualState(str, Enum):
    """Categorical biochemical health status of the simulated erythrocyte."""

    HEALTHY = "healthy"
    STRESSED = "stressed"
    SEVERELY_STRESSED = "severely_stressed"
    LYSIS_RISK = "lysis_risk"


class VisualFrame(BaseModel):
    """A single animation frame for frontend rendering."""

    model_config = ConfigDict(frozen=True)

    t_s: float = Field(description="Simulation timestamp in seconds.")
    normalized_gsh: float = Field(
        ge=0.0,
        description="Current [GSH] normalized to baseline reference (2.5 mM). Clamped to [0.0, 1.5].",
    )
    normalized_nadph: float = Field(
        ge=0.0,
        description="Current [NADPH] normalized to baseline reference (0.030 mM). Clamped to [0.0, 1.5].",
    )
    damage: float = Field(
        ge=0.0,
        le=1.0,
        description="Cumulative oxidative damage index D in [0.0, 1.0].",
    )
    hemolysis_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Estimated cell lysis percentage proxy.",
    )
    cell_state: CellVisualState = Field(
        description="Derived biochemical status: healthy, stressed, severely_stressed, or lysis_risk.",
    )
    state_classification_type: str = Field(
        default="MODEL_DERIVED",
        description="Indicates whether state is 'MODEL_DERIVED' (biochemical ODE output) vs 'ILLUSTRATIVE'.",
    )
    morphology_simulated: bool = Field(
        default=False,
        description="Always False. The model simulates cytosolic biochemistry, not physical membrane shape.",
    )


class VisualTrajectoryResponse(BaseModel):
    """Sequence of visual state frames for frontend playground animation."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    total_frames: int
    playback_duration_s: float
    frames: list[VisualFrame]
    model_notes: str = Field(
        default=(
            "Model-derived biochemical state. Thresholds: Healthy ([GSH] >= 1.5 mM, D < 0.05); "
            "Stressed ([GSH] 0.8-1.5 mM, D 0.05-0.20); Severely Stressed ([GSH] 0.25-0.8 mM, D 0.20-0.50); "
            "Lysis Risk ([GSH] < 0.25 mM or D >= 0.50). Cell morphology (crenation/echinocytosis) is NOT modeled."
        )
    )


def classify_cell_state(gsh_mM: float, damage: float) -> CellVisualState:
    """Classify cell biochemical health from modeled state variables.

    Criteria:
    - LYSIS_RISK: [GSH] < 0.25 mM (oxidative crisis) or damage >= 0.50.
    - SEVERELY_STRESSED: [GSH] in [0.25, 0.80) mM or damage in [0.20, 0.50).
    - STRESSED: [GSH] in [0.80, 1.50) mM or damage in [0.05, 0.20).
    - HEALTHY: [GSH] >= 1.50 mM and damage < 0.05.
    """
    if gsh_mM < 0.25 or damage >= 0.50:
        return CellVisualState.LYSIS_RISK
    if gsh_mM < 0.80 or damage >= 0.20:
        return CellVisualState.SEVERELY_STRESSED
    if gsh_mM < 1.50 or damage >= 0.05:
        return CellVisualState.STRESSED
    return CellVisualState.HEALTHY


def trajectory_to_visual_frames(
    trajectory: list[TrajectoryPoint],
    max_frames: int = 300,
    ref_gsh_mM: float = 2.50,
    ref_nadph_mM: float = 0.030,
) -> list[VisualFrame]:
    """Convert an ODE simulation trajectory into a sequence of frontend VisualFrame objects.

    Downsamples long trajectories evenly to max_frames for responsive frontend rendering.
    """
    if not trajectory:
        return []

    # Downsample if trajectory exceeds max_frames
    n_pts = len(trajectory)
    if n_pts <= max_frames:
        selected_points = trajectory
    else:
        indices = np.linspace(0, n_pts - 1, max_frames, dtype=int)
        selected_points = [trajectory[i] for i in indices]

    frames: list[VisualFrame] = []
    for pt in selected_points:
        norm_gsh = float(min(1.5, max(0.0, pt.gsh_mM / max(1e-6, ref_gsh_mM))))
        norm_nadph = float(min(1.5, max(0.0, pt.nadph_mM / max(1e-6, ref_nadph_mM))))
        dam = float(min(1.0, max(0.0, pt.damage)))
        state = classify_cell_state(pt.gsh_mM, dam)

        frames.append(
            VisualFrame(
                t_s=round(pt.t_s, 3),
                normalized_gsh=round(norm_gsh, 4),
                normalized_nadph=round(norm_nadph, 4),
                damage=round(dam, 4),
                hemolysis_pct=round(pt.hemolysis_pct, 2),
                cell_state=state,
                state_classification_type="MODEL_DERIVED",
                morphology_simulated=False,
            )
        )

    return frames
