"""
Deterministic Biochemical Rule-Based Interpretation Provider (Milestone 6).

Generates evidence-grounded, mathematically verified scientific memoranda
for single-cell playground simulations and heterogeneous cohort experiments
using domain-specific biochemical diagnostic rules.
"""

from __future__ import annotations

from typing import Any

from vblood.interpretation.guardrails import (
    GroundingGuardrail,
    UNVERIFIED_COMPOUND_NOTICE,
)
from vblood.interpretation.providers.base import InterpretationProvider
from vblood.interpretation.schemas import (
    CohortInterpretationResponse,
    PlaygroundInterpretationResponse,
)


class DeterministicBiochemicalProvider(InterpretationProvider):
    """Rule-based biochemical interpretation provider."""

    def __init__(self) -> None:
        self.guardrail = GroundingGuardrail()

    @property
    def provider_id(self) -> str:
        return "deterministic-biochemical-v1"

    async def interpret_playground(
        self,
        context: dict[str, Any],
    ) -> PlaygroundInterpretationResponse:
        """Synthesize a scientific interpretation memorandum for a single-cell run."""
        endpoints = context["endpoints"]
        gsh_min = endpoints["gsh_min_mM"]
        gsh_depleted = endpoints["gsh_depleted_pct"]
        time_to_nadir = endpoints["time_to_nadir_s"]
        recovery_time = endpoints["recovery_time_s"]
        h2o2_max = endpoints["h2o2_max_mM"]
        nadph_min = endpoints["nadph_min_mM"]
        status_label = endpoints["status_label"]
        duration_s = context["duration_s"]
        g6pd_alpha = context["g6pd_alpha"]
        compounds = context["compounds"]
        has_unverified = context["has_unverified_compounds"]

        # 1. Executive Summary
        compound_names = ", ".join([f"{c['name']} ({c['dose_mM']} mM)" for c in compounds]) if compounds else "vehicle control"
        if gsh_min >= 1.50:
            severity_desc = (
                f"Erythrocyte cytosolic glutathione remained well-buffered above 1.50 mM (minimum observed: {gsh_min:.2f} mM, "
                f"{gsh_depleted:.1f}% depletion). The physiological redox reserve absorbed the challenge with minimal perturbation."
            )
        elif gsh_min >= 0.80:
            severity_desc = (
                f"Moderate oxidative perturbation occurred, driving [GSH] down to a nadir of {gsh_min:.2f} mM ({gsh_depleted:.1f}% depletion) "
                f"at t = {time_to_nadir:.1f} s. Frontline antioxidant reserves were taxed but prevented catastrophic thiol loss."
            )
        elif gsh_min >= 0.25:
            severity_desc = (
                f"Severe redox exhaustion was observed: [GSH] collapsed to {gsh_min:.2f} mM ({gsh_depleted:.1f}% depletion) "
                f"at t = {time_to_nadir:.1f} s. Glutathione regeneration kinetics were outpaced by the oxidative rate law."
            )
        else:
            severity_desc = (
                f"Critical oxidative crisis occurred. Cytosolic [GSH] collapsed to {gsh_min:.2f} mM ({gsh_depleted:.1f}% depletion), "
                f"crossing the critical hemolytic risk threshold. NADPH supply was severely decoupled from glutathione reductase demand."
            )

        exec_summary = (
            f"Simulation of in vitro erythrocyte exposure to {compound_names} under {context['exposure_profile']} delivery "
            f"(G6PD capacity α = {g6pd_alpha:.2f}) over {duration_s:.0f} s produced a physiological classification of '{status_label}'. "
            f"{severity_desc}"
        )

        # 2. Nadir & Dynamic Trajectory Analysis
        if recovery_time is not None:
            rec_str = f"The cell achieved 90% glutathione replenishment within {recovery_time:.1f} s."
        else:
            rec_str = f"The cell failed to achieve 90% recovery within the {duration_s:.0f} s observation window."

        nadir_text = (
            f"The minimum intracellular [GSH] reached {gsh_min:.4f} mM at t = {time_to_nadir:.1f} s, representing a {gsh_depleted:.2f}% "
            f"reduction from baseline. Peak cytosolic [H2O2] reached {h2o2_max:.6f} mM, while the NADPH reducing pool reached a nadir of "
            f"{nadph_min:.5f} mM. {rec_str}"
        )

        # 3. Mechanistic Pathway Breakdown
        mech_notes: list[str] = []
        for c in compounds:
            mtype = c.get("mechanism_type", "")
            if mtype == "DIRECT_OXIDANT":
                mech_notes.append(
                    f"Direct oxidant delivery elevated [H2O2], accelerating glutathione peroxidase (GPx1) flux: "
                    f"v_GPx = k_gpx · [H2O2] · [GSH], converting 2 GSH into GSSG."
                )
            elif mtype == "GSH_CONJUGATOR":
                mech_notes.append(
                    f"Electrophilic conjugation via {c['name']} directly consumed GSH (v_conj = k_conj · [C] · [GSH]) "
                    f"without GSSG generation, bypassing glutathione reductase recycling and permanently depleting the intracellular thiol pool."
                )
            elif mtype == "REDOX_CYCLER":
                mech_notes.append(
                    f"Redox cycler {c['name']} sustained catalytic electron transfer from NADPH to generate continuous H2O2 flux, "
                    f"creating a dual drain on both cofactor synthesis and antioxidant buffer."
                )
            elif mtype == "ENZYME_INHIBITOR":
                mech_notes.append(
                    f"Enzymatic inhibition by {c['name']} reduced effective turnover capacity of the targeted catalyst."
                )

        if g6pd_alpha < 0.5:
            mech_notes.append(
                f"Simulated G6PD enzymatic restriction (α = {g6pd_alpha:.2f}) throttled pentose phosphate pathway turnover, "
                f"capping the rate of NADPH regeneration and causing glutathione reductase (GR) to become cofactor-limited."
            )
        elif not mech_notes:
            mech_notes.append("Basal steady-state redox balance maintained by endogenous autoxidation and PPP turnover.")

        pathway_text = " ".join(mech_notes)

        # 4. Control Comparison
        ctrl = context.get("control_comparison")
        if ctrl is not None:
            control_text = (
                f"Compared to unperturbed vehicle control (minimum [GSH]: {ctrl['control_min_gsh_mM']:.2f} mM, "
                f"depletion: {ctrl['control_percent_depleted']:.1f}%), this scenario caused an excess [GSH] depression of "
                f"{abs(ctrl['delta_min_gsh_mM']):.2f} mM ({ctrl['delta_depleted_pct']:.1f}% relative difference)."
            )
        else:
            control_text = "No vehicle control scenario was provided for comparative differential analysis."

        # 5. Uncertainty & Limitations
        limitations: list[str] = [
            "This simulation represents an isolated in vitro suspension of human erythrocytes.",
            "No whole-body pharmacokinetics (ADME), hepatic metabolism, plasma protein binding, or renal clearance are simulated.",
            "Embden-Meyerhof glycolysis, ATP maintenance, and membrane deformability are unmodeled.",
            "Damage index (D) and hemolysis estimates are synthetic mathematical proxies, not clinical assays.",
        ]
        if has_unverified:
            limitations.append(UNVERIFIED_COMPOUND_NOTICE)

        uncertainty_text = " ".join(limitations)

        # 6. Suggested Experiments
        suggested: list[str] = [
            "Quantify reduced (GSH) and oxidized (GSSG) glutathione via HPLC or DTNB (Ellman's reagent) recycling assay.",
            "Measure intracellular NADPH/NADP+ ratios using enzymatic cycling spectrophotometry.",
            "Evaluate in vitro erythrocyte osmotic fragility or hemoglobin release under identical compound exposure.",
        ]
        if g6pd_alpha < 1.0:
            suggested.append("Perform G6PD quantitative enzymatic activity assay on patient hemolysates to validate α scaling.")

        resp = PlaygroundInterpretationResponse(
            executive_summary=exec_summary,
            nadir_analysis=nadir_text,
            pathway_flux_breakdown=pathway_text,
            control_comparison=control_text,
            uncertainty_and_limitations=uncertainty_text,
            suggested_experiments=suggested,
            provider_used=self.provider_id,
            fallback_applied=False,
            fallback_reason=None,
            grounding=self.guardrail.verify_playground(
                response=PlaygroundInterpretationResponse.model_construct(
                    executive_summary=exec_summary,
                    nadir_analysis=nadir_text,
                    pathway_flux_breakdown=pathway_text,
                    control_comparison=control_text,
                    uncertainty_and_limitations=uncertainty_text,
                    suggested_experiments=suggested,
                    provider_used=self.provider_id,
                    grounding=None,  # type: ignore
                ),
                context=context,
            ),
        )
        return resp

    async def interpret_cohort(
        self,
        context: dict[str, Any],
    ) -> CohortInterpretationResponse:
        """Synthesize a scientific interpretation memorandum for a cohort experiment."""
        endpoints = context["distribution_endpoints"]
        n_cells = context["n_cells"]
        g6pd_alpha = context["g6pd_alpha"]
        compounds = context["compounds"]
        has_unverified = context["has_unverified_compounds"]

        mean_nadir = endpoints["mean_gsh_nadir_mM"]
        median_nadir = endpoints["median_gsh_nadir_mM"]
        pct_mild = endpoints["pct_below_mild_gsh"]
        pct_crisis = endpoints["pct_below_crisis_gsh"]
        pct_lysis = endpoints["pct_cells_lysis_risk"]
        p5_nadir = endpoints["p5_nadir_mM"]
        p95_nadir = endpoints["p95_nadir_mM"]

        comp_str = ", ".join([f"{c['name']} ({c['dose_mM']} mM)" for c in compounds]) if compounds else "vehicle control"

        # 1. Executive Summary
        exec_summary = (
            f"Monte Carlo simulation of a heterogeneous cohort (N = {n_cells} erythrocytes, G6PD α = {g6pd_alpha:.2f}) "
            f"exposed to {comp_str} revealed significant biological dispersion. Across the population, {pct_mild:.1f}% of cells "
            f"experienced mild-to-moderate depletion, while {pct_crisis:.1f}% crossed into critical oxidative crisis ([GSH] < 0.25 mM). "
            f"Mean nadir was {mean_nadir:.2f} mM with a median of {median_nadir:.2f} mM."
        )

        # 2. Tail Risk Analysis
        tail_text = (
            f"Biological parameter variance (CV ~ 15-25% across GR, GPx, and G6PD) produced a wide response envelope: "
            f"the 95th percentile resilient subpopulation maintained [GSH] above {p95_nadir:.2f} mM, whereas the vulnerable 5th percentile "
            f"tail collapsed to {p5_nadir:.2f} mM. This spread highlights that population tail-risk is substantially more severe than "
            f"indicated by bulk mean or median metrics alone."
        )

        # 3. G6PD Interaction
        if g6pd_alpha < 0.5:
            g6pd_text = (
                f"Enzymatic restriction (α = {g6pd_alpha:.2f}) compounded chemical vulnerability, shifting the entire population distribution "
                f"toward prolonged recovery times and markedly expanding the crisis fraction ({pct_crisis:.1f}% of cells below 0.25 mM)."
            )
        else:
            g6pd_text = (
                f"At normal G6PD capacity (α = {g6pd_alpha:.2f}), the majority of cells regenerated NADPH sufficiently to limit crisis "
                f"fraction to {pct_crisis:.1f}%."
            )

        # 4. Lysis Risk
        lysis_text = (
            f"A predicted {pct_lysis:.1f}% of cells exceeded the synthetic membrane damage threshold (hemolysis proxy > 5%), "
            f"identifying the subset of erythrocytes at elevated risk of premature clearance or intravascular lysis."
        )

        # 5. Uncertainty & Limitations
        limitations = [
            "Cohort simulation samples log-normal parameter priors for isolated erythrocytes in an aqueous suspension.",
            "In vivo whole-body pharmacokinetics (ADME), vascular shear stress, and splenic macrophage filtration are not simulated.",
            "Uniform G6PD scaling α is applied; lyonization in heterozygous females produces bimodal mosaics which require multi-population modeling.",
        ]
        if has_unverified:
            limitations.append(UNVERIFIED_COMPOUND_NOTICE)
        uncertainty_text = " ".join(limitations)

        # 6. Suggested Experiments
        suggested = [
            "Perform single-cell redox flow cytometry (e.g. roGFP or ThiolTracker Violet) to assess cell-to-cell heterogeneity.",
            "Compare in vitro challenge sensitivity across G6PD-deficient and wild-type donor blood samples.",
            "Conduct automated osmotic fragility testing on exposed cohorts.",
        ]

        resp = CohortInterpretationResponse(
            executive_summary=exec_summary,
            tail_risk_analysis=tail_text,
            g6pd_interaction_analysis=g6pd_text,
            lysis_risk_evaluation=lysis_text,
            uncertainty_and_limitations=uncertainty_text,
            suggested_experiments=suggested,
            provider_used=self.provider_id,
            fallback_applied=False,
            fallback_reason=None,
            grounding=self.guardrail.verify_cohort(
                response=CohortInterpretationResponse.model_construct(
                    executive_summary=exec_summary,
                    tail_risk_analysis=tail_text,
                    g6pd_interaction_analysis=g6pd_text,
                    lysis_risk_evaluation=lysis_text,
                    uncertainty_and_limitations=uncertainty_text,
                    suggested_experiments=suggested,
                    provider_used=self.provider_id,
                    grounding=None,  # type: ignore
                ),
                context=context,
            ),
        )
        return resp
