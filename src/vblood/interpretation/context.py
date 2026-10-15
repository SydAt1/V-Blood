"""
Structured Context Builder for Scientific Interpretation (Milestone 6).

Extracts, normalizes, and aggregates numerical endpoints, biochemical mechanisms,
parameter provenance, and model boundaries from raw simulation trajectories.
"""

from __future__ import annotations

from typing import Any
import numpy as np

from vblood.scenarios.compounds import get_compound_library
from vblood.scenarios.engine import ScenarioRequest, ScenarioResult
from vblood.scenarios.population import PopulationRequest, PopulationResult

UNMODELED_PHYSICS_CATALOGUE: list[str] = [
    "No in vivo whole-body pharmacokinetics (ADME) — isolated in vitro erythrocyte suspension only.",
    "No Embden-Meyerhof glycolysis, ATP, 2,3-BPG, or ion-pump energetics modeled.",
    "No physical membrane deformability, echinocytic spiculation, or morphological swelling modeled.",
    "Damage index (D) and hemolysis estimates are synthetic mathematical proxies, not clinical assays.",
]


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Safe attribute/key extractor handling both Pydantic models and dictionaries."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def build_playground_context(
    request: ScenarioRequest | dict[str, Any],
    result: ScenarioResult | dict[str, Any],
    control_result: ScenarioResult | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble structured biochemical and numerical context for a single-cell playground run.

    Returns a comprehensive dictionary with exact numerical endpoints,
    pathway mechanisms, evidence tiers, and boundary notes.
    """
    library = get_compound_library()

    metrics = _get_val(result, "derived_metrics")
    sim_res = _get_val(result, "simulation_result")
    traj = _get_val(sim_res, "trajectory") or _get_val(result, "trajectory") or []

    # GSH initial
    gsh_0 = 2.5
    if traj and len(traj) > 0:
        p0 = traj[0]
        gsh_0 = float(_get_val(p0, "gsh_mM", 2.5))

    gsh_min = float(_get_val(metrics, "gsh_nadir_mM", 2.0))
    gsh_depleted_pct = float(
        _get_val(metrics, "net_total_glutathione_loss_pct", _get_val(metrics, "percent_gsh_depleted", 0.0))
    )
    time_to_nadir = float(_get_val(metrics, "gsh_nadir_time_s", 0.0))
    rec_time_raw = _get_val(metrics, "time_to_90pct_recovery_s", _get_val(metrics, "recovery_time_s", None))
    recovery_time = float(rec_time_raw) if rec_time_raw is not None else None
    h2o2_max = float(_get_val(metrics, "max_h2o2_mM", 0.0))
    nadph_min = float(_get_val(metrics, "nadph_nadir_mM", 0.0))

    damage_max = 0.0
    if traj:
        damage_max = max([float(_get_val(p, "damage", 0.0)) for p in traj])

    final_hemolysis_pct = float(
        _get_val(sim_res, "final_hemolysis_pct", _get_val(result, "final_hemolysis_pct", 0.0))
    )

    # Classify biochemical status label
    if gsh_min < 0.25 or damage_max >= 0.50:
        status_label = "lysis_risk"
    elif gsh_min < 0.80 or damage_max >= 0.20:
        status_label = "severely_stressed"
    elif gsh_min < 1.50 or damage_max >= 0.05:
        status_label = "stressed"
    else:
        status_label = "healthy"

    # Compound inspection & evidence
    compounds_info: list[dict[str, Any]] = []
    has_unverified = False
    unverified_ids: list[str] = []

    req_compounds = _get_val(request, "compounds", [])
    for comp in req_compounds:
        cid = _get_val(comp, "compound_id")
        dose = float(_get_val(comp, "dose_mM", 0.0))
        entry = library.get(cid) if cid else None
        if entry is not None:
            comp_data = {
                "id": entry.compound_id,
                "name": entry.name,
                "dose_mM": dose,
                "mechanism_type": entry.mechanism_type.value,
                "evidence_level": entry.evidence_level.value,
                "citation": entry.provenance,
            }
            if entry.is_unverified:
                has_unverified = True
                unverified_ids.append(entry.compound_id)
        else:
            comp_data = {
                "id": cid or "unknown",
                "name": cid or "Unknown Chemical",
                "dose_mM": dose,
                "mechanism_type": "unknown",
                "evidence_level": "UNVERIFIED",
                "citation": "Unverified chemical entity",
            }
            has_unverified = True
            if cid:
                unverified_ids.append(cid)
        compounds_info.append(comp_data)

    # Control delta analysis
    control_info: dict[str, Any] | None = None
    if control_result is not None:
        c_metrics = _get_val(control_result, "derived_metrics")
        c_min_gsh = float(_get_val(c_metrics, "gsh_nadir_mM", 2.5))
        c_depleted = float(
            _get_val(c_metrics, "net_total_glutathione_loss_pct", _get_val(c_metrics, "percent_gsh_depleted", 0.0))
        )
        c_rec = _get_val(c_metrics, "time_to_90pct_recovery_s", _get_val(c_metrics, "recovery_time_s", None))
        control_info = {
            "control_min_gsh_mM": c_min_gsh,
            "control_percent_depleted": c_depleted,
            "control_recovery_time_s": float(c_rec) if c_rec is not None else None,
            "delta_min_gsh_mM": round(gsh_min - c_min_gsh, 4),
            "delta_depleted_pct": round(gsh_depleted_pct - c_depleted, 2),
        }

    has_unv_flag = _get_val(result, "has_unverified_compounds", False)
    unv_list = _get_val(result, "unverified_compounds", [])

    model_ver = _get_val(request, "model_version", "rbc-g6pd-gsh-v2")
    alpha_val = float(_get_val(request, "g6pd_alpha", 1.0))
    profile_val = _get_val(request, "exposure_profile", "BOLUS")
    if hasattr(profile_val, "value"):
        profile_val = profile_val.value
    duration_val = float(_get_val(request, "duration_s", 3600.0))

    return {
        "model_version": model_ver,
        "g6pd_alpha": alpha_val,
        "exposure_profile": str(profile_val),
        "duration_s": duration_val,
        "compounds": compounds_info,
        "has_unverified_compounds": bool(has_unverified or has_unv_flag),
        "unverified_compounds": list(set(unverified_ids + unv_list)),
        "endpoints": {
            "gsh_initial_mM": round(gsh_0, 4),
            "gsh_min_mM": round(gsh_min, 4),
            "gsh_depleted_pct": round(gsh_depleted_pct, 2),
            "time_to_nadir_s": round(time_to_nadir, 2),
            "recovery_time_s": round(recovery_time, 2) if recovery_time is not None else None,
            "h2o2_max_mM": round(h2o2_max, 6),
            "nadph_min_mM": round(nadph_min, 5),
            "damage_max": round(damage_max, 4),
            "final_hemolysis_pct": round(final_hemolysis_pct, 2),
            "status_label": status_label,
            "gsh_recovered": recovery_time is not None,
        },
        "control_comparison": control_info,
        "unmodeled_physics": UNMODELED_PHYSICS_CATALOGUE,
    }


def build_cohort_context(
    request: PopulationRequest | dict[str, Any],
    result: PopulationResult | dict[str, Any],
) -> dict[str, Any]:
    """Assemble structured context for a heterogeneous population cohort experiment.

    Returns population-scale distribution endpoints, percentile spreads,
    subpopulation crisis fractions, and genetic parameters.
    """
    library = get_compound_library()
    scenario_req = _get_val(request, "scenario_request", {})

    compounds_info: list[dict[str, Any]] = []
    has_unverified = False
    unverified_ids: list[str] = []

    req_compounds = _get_val(scenario_req, "compounds", [])
    for comp in req_compounds:
        cid = _get_val(comp, "compound_id")
        dose = float(_get_val(comp, "dose_mM", 0.0))
        entry = library.get(cid) if cid else None
        if entry is not None:
            compounds_info.append({
                "id": entry.compound_id,
                "name": entry.name,
                "dose_mM": dose,
                "mechanism_type": entry.mechanism_type.value,
                "evidence_level": entry.evidence_level.value,
            })
            if entry.is_unverified:
                has_unverified = True
                unverified_ids.append(entry.compound_id)
        else:
            compounds_info.append({
                "id": cid or "unknown",
                "name": cid or "Unknown Chemical",
                "dose_mM": dose,
                "mechanism_type": "unknown",
                "evidence_level": "UNVERIFIED",
            })
            has_unverified = True
            if cid:
                unverified_ids.append(cid)

    bands = _get_val(result, "percentile_bands")
    gsh_p5 = _get_val(bands, "gsh_p5", [])
    gsh_p25 = _get_val(bands, "gsh_p25", [])
    gsh_p50 = _get_val(bands, "gsh_p50", [])
    gsh_p75 = _get_val(bands, "gsh_p75", [])
    gsh_p95 = _get_val(bands, "gsh_p95", [])

    p5_min = float(min(gsh_p5)) if gsh_p5 else 0.0
    p25_min = float(min(gsh_p25)) if gsh_p25 else 0.0
    p50_min = float(min(gsh_p50)) if gsh_p50 else 0.0
    p75_min = float(min(gsh_p75)) if gsh_p75 else 0.0
    p95_min = float(min(gsh_p95)) if gsh_p95 else 0.0

    exec_time = float(
        _get_val(result, "execution_time_s", float(_get_val(result, "execution_time_ms", 0.0)) / 1000.0)
    )
    mean_nadir = float(_get_val(result, "mean_gsh_nadir_mM", p50_min))
    median_nadir = float(_get_val(result, "median_gsh_nadir_mM", p50_min))
    pct_mild = float(
        _get_val(result, "pct_cells_below_mild_gsh", _get_val(result, "pct_cells_gsh_depleted", 0.0))
    )
    pct_crisis = float(_get_val(result, "pct_cells_below_crisis_gsh", 0.0))
    pct_lysis = float(_get_val(result, "pct_cells_lysis_risk", 0.0))

    has_unv_flag = _get_val(result, "has_unverified_compounds", False)
    unv_list = _get_val(result, "unverified_compounds", [])

    model_ver = _get_val(scenario_req, "model_version", "rbc-g6pd-gsh-v2")
    alpha_val = float(_get_val(scenario_req, "g6pd_alpha", 1.0))
    profile_val = _get_val(scenario_req, "exposure_profile", "BOLUS")
    if hasattr(profile_val, "value"):
        profile_val = profile_val.value
    duration_val = float(_get_val(scenario_req, "duration_s", 1800.0))

    return {
        "n_cells": int(_get_val(result, "n_cells", 1000)),
        "execution_time_s": round(exec_time, 3),
        "g6pd_alpha": alpha_val,
        "model_version": model_ver,
        "exposure_profile": str(profile_val),
        "duration_s": duration_val,
        "compounds": compounds_info,
        "has_unverified_compounds": bool(has_unverified or has_unv_flag),
        "unverified_compounds": list(set(unverified_ids + unv_list)),
        "distribution_endpoints": {
            "mean_gsh_nadir_mM": round(mean_nadir, 4),
            "median_gsh_nadir_mM": round(median_nadir, 4),
            "pct_below_mild_gsh": round(pct_mild, 2),
            "pct_below_crisis_gsh": round(pct_crisis, 2),
            "pct_cells_lysis_risk": round(pct_lysis, 2),
            "p5_nadir_mM": round(p5_min, 4),
            "p25_nadir_mM": round(p25_min, 4),
            "p50_nadir_mM": round(p50_min, 4),
            "p75_nadir_mM": round(p75_min, 4),
            "p95_nadir_mM": round(p95_min, 4),
        },
        "unmodeled_physics": UNMODELED_PHYSICS_CATALOGUE,
    }
