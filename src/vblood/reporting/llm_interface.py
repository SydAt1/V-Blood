"""
LLM reporting interface contract for V-Blood.

This module defines the data structures that the future LLM scientific
assistant will receive as structured input. The LLM module is NOT
implemented in Milestone 1 — this file defines the interface contract only.

Design principles (to be implemented in a future milestone):
- The LLM receives structured simulation results, never raw text.
- Every numerical claim in the output must map to a specific field here.
- Every mechanistic claim must map to a documented model equation.
- Simulation outputs are clearly distinguished from experimental observations.
- Synthetic parameters are flagged and must not be presented as validated facts.

See docs/project_overview.md §9 for the full LLM assistant specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LLMReportInput(BaseModel):
    """
    Structured input data contract for the future LLM scientific assistant.

    This schema is intentionally complete and strict: the LLM should
    receive this object, not free-form text. This prevents hallucination
    of numerical results or biological mechanisms.

    NOT IMPLEMENTED in Milestone 1.
    """

    # Simulation identity
    run_id: str = Field(description="Unique identifier for the simulation run.")
    model_id: str = Field(description="Biological model identifier.")
    model_version: str = Field(description="Version of the model.")

    # Key endpoint values (for the LLM to summarise)
    final_gsh_mM: float = Field(description="Final [GSH] in mM.")
    final_gssg_mM: float = Field(description="Final [GSSG] in mM.")
    min_gsh_mM: float = Field(description="Minimum [GSH] observed during simulation.")
    max_h2o2_mM: float = Field(description="Maximum [H2O2] observed.")
    final_damage: float = Field(description="Final damage index D.")
    final_hemolysis_pct: float = Field(
        description=(
            "Estimated haemolysis % — synthetic proxy, not experimental observation."
        )
    )

    # Parameter provenance summary
    n_synthetic_params: int = Field(
        description="Number of SYNTHETIC parameters in the parameter set."
    )
    synthetic_param_names: list[str] = Field(
        description="Names of SYNTHETIC parameters."
    )

    # Warnings (model limitations)
    warnings: list[str] = Field(
        description="Scientific and numerical warnings from the simulation.",
        default_factory=list,
    )

    # Model assumptions (the LLM must reference these, not contradict them)
    model_assumptions_summary: str = Field(
        description=(
            "Path or digest of the assumptions document. "
            "The LLM must not claim the model is more accurate than documented."
        )
    )

    # Experimental comparison (empty in Milestone 1)
    experimental_comparisons: list[dict] = Field(
        description=(
            "Available experimental observations for comparison. "
            "Empty in Milestone 1 — no experimental data has been ingested."
        ),
        default_factory=list,
    )


class LLMReportOutput(BaseModel):
    """
    Expected output schema for the LLM scientific assistant response.

    NOT IMPLEMENTED in Milestone 1. This schema defines what the LLM
    module must produce so that it can be validated.
    """

    executive_summary: str = Field(
        description="One-paragraph plain-language summary of the simulation outcome."
    )
    changes_over_time: str = Field(
        description="Description of how each state variable changed."
    )
    pathway_explanation: str = Field(
        description="Explanation of the biochemical pathways that drove the changes."
    )
    distinction_simulation_vs_experiment: str = Field(
        description=(
            "Explicit statement that these are model predictions, not experimental data."
        )
    )
    uncertainty_and_limitations: str = Field(
        description="Summary of model limitations, synthetic parameters, and caveats."
    )
    suggested_follow_up: list[str] = Field(
        description="Suggested follow-up analyses or experiments.",
        default_factory=list,
    )
