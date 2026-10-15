"""
Pydantic schemas for LLM-powered scientific interpretation (Milestone 6).

Defines structured inputs, response payloads, provider options,
and guardrail verification metadata for single-cell and cohort reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from vblood.scenarios.engine import ScenarioRequest, ScenarioResult
from vblood.scenarios.population import PopulationRequest, PopulationResult


class GroundingEvaluation(BaseModel):
    """Integrity and grounding validation status for an interpretation."""

    model_config = ConfigDict(frozen=True)

    passed: bool = Field(description="True if all numerical and scientific checks passed.")
    checked_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of simulation metrics verified against interpretation text.",
    )
    disclaimers_present: bool = Field(
        description="True if mandatory scientific boundaries and disclaimers are present.",
    )
    unverified_compound_warning_present: bool = Field(
        description="True if unverified compound warning is present when applicable.",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Validation flags, warnings, or notes raised during guardrail inspection.",
    )


class PlaygroundInterpretationRequest(BaseModel):
    """Input request for interpreting a single-cell playground scenario run."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "provider_preference": "auto",
            }
        },
    )

    scenario_request: Any = Field(
        description="The chemical scenario configuration that was executed.",
    )
    scenario_result: Any = Field(
        description="The resulting simulation trajectory and derived metrics.",
    )
    control_result: Any | None = Field(
        default=None,
        description="Optional unperturbed vehicle control result for comparative delta analysis.",
    )
    provider_preference: Literal["auto", "deterministic", "llm"] = Field(
        default="auto",
        description="Preferred provider: 'auto' (use LLM if configured, else fallback), 'deterministic', or 'llm'.",
    )
    force_refresh: bool = Field(
        default=False,
        description="If True, bypasses cache and regenerates a fresh interpretation.",
    )


class PlaygroundInterpretationResponse(BaseModel):
    """Scientific interpretation memorandum for a single-cell simulation."""

    model_config = ConfigDict(frozen=True)

    executive_summary: str = Field(
        description="One-paragraph synthesis of the simulation outcome and biological findings.",
    )
    nadir_analysis: str = Field(
        description="Detailed analysis of the minimum [GSH] nadir, time to nadir, and recovery kinetics.",
    )
    pathway_flux_breakdown: str = Field(
        description="Mechanistic breakdown of enzymatic fluxes (GPx, GR, G6PD) driving the response.",
    )
    control_comparison: str = Field(
        description="Comparative analysis against unperturbed baseline or vehicle control.",
    )
    uncertainty_and_limitations: str = Field(
        description="Explicit catalogue of model assumptions, synthetic parameters, and unmodeled physics.",
    )
    suggested_experiments: list[str] = Field(
        default_factory=list,
        description="Concrete in vitro assays or follow-up simulations to test the generated hypothesis.",
    )
    provider_used: str = Field(
        description="Provider identifier that generated this interpretation (e.g. 'deterministic-v1', 'llm-gpt-4o').",
    )
    fallback_applied: bool = Field(
        default=False,
        description="True if fallback to deterministic engine occurred due to LLM unavailability or failure.",
    )
    fallback_reason: str | None = Field(
        default=None,
        description="Reason for provider fallback, if applicable.",
    )
    grounding: GroundingEvaluation | None = Field(
        default=None,
        description="Guardrail verification metadata confirming numerical grounding and disclaimers.",
    )
    generated_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of report generation in UTC ISO format.",
    )


class CohortInterpretationRequest(BaseModel):
    """Input request for interpreting a heterogeneous population cohort simulation."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "provider_preference": "auto",
            }
        },
    )

    population_request: Any = Field(
        description="The cohort simulation request configuration.",
    )
    population_result: Any = Field(
        description="The aggregated Monte Carlo simulation result and percentile bands.",
    )
    provider_preference: Literal["auto", "deterministic", "llm"] = Field(
        default="auto",
        description="Preferred provider: 'auto', 'deterministic', or 'llm'.",
    )
    force_refresh: bool = Field(
        default=False,
        description="If True, bypasses cache and regenerates a fresh interpretation.",
    )


class CohortInterpretationResponse(BaseModel):
    """Scientific interpretation memorandum for a heterogeneous cohort experiment."""

    model_config = ConfigDict(frozen=True)

    executive_summary: str = Field(
        description="Population-level synthesis of cohort vulnerability and oxidative response.",
    )
    tail_risk_analysis: str = Field(
        description="Analysis of biological variance, comparing the median (p50) against vulnerable tails (p5, p25).",
    )
    g6pd_interaction_analysis: str = Field(
        description="Assessment of enzymatic G6PD capacity and genetic deficiency interaction under chemical stress.",
    )
    lysis_risk_evaluation: str = Field(
        description="Evaluation of predicted crisis fraction and mechanistic proxy for membrane collapse.",
    )
    uncertainty_and_limitations: str = Field(
        description="Explicit catalogue of population prior assumptions and unmodeled in vivo factors.",
    )
    suggested_experiments: list[str] = Field(
        default_factory=list,
        description="Suggested cohort assays (e.g. flow cytometry redox tracking, clinical fragility tests).",
    )
    provider_used: str = Field(
        description="Provider identifier that generated this report.",
    )
    fallback_applied: bool = Field(
        default=False,
        description="True if fallback to deterministic engine occurred.",
    )
    fallback_reason: str | None = Field(default=None)
    grounding: GroundingEvaluation | None = Field(
        default=None,
        description="Guardrail verification metadata.",
    )
    generated_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class InterpretationStatusResponse(BaseModel):
    """System health and capabilities of the scientific interpretation engine."""

    model_config = ConfigDict(frozen=True)

    providers_available: list[str] = Field(
        description="List of available providers (e.g. ['deterministic', 'llm']).",
    )
    default_provider: str = Field(
        description="Default provider selected when preference is 'auto'.",
    )
    llm_configured: bool = Field(
        description="True if a valid external LLM API key / endpoint is configured.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Identifier of configured external LLM model if available.",
    )
    guardrails_active: bool = Field(
        default=True,
        description="True if numerical grounding and disclaimer guardrails are enforced.",
    )
    unmodeled_physics_declared: list[str] = Field(
        description="Standard catalogue of biological processes explicitly excluded from interpretation.",
    )
