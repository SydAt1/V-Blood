"""
Explicit unit conversion utilities for biological measurements (Task 4).

Only conversions with well-defined mathematical conversion factors are performed.
Ambiguous conversions (e.g. mg/dL without molecular weight) raise explicit errors.
"""

from __future__ import annotations

import re


# Canonical conversion factors to model standard units (mM for concentrations, % for hemolysis)
_CONCENTRATION_TO_MM: dict[str, float] = {
    "mm": 1.0,
    "millimolar": 1.0,
    "mmol/l": 1.0,
    "um": 1e-3,
    "µm": 1e-3,
    "micromolar": 1e-3,
    "umol/l": 1e-3,
    "µmol/l": 1e-3,
    "nm": 1e-6,
    "nanomolar": 1e-6,
    "nmol/l": 1e-6,
    "m": 1e3,
    "molar": 1e3,
    "mol/l": 1e3,
}

_PERCENTAGE_TO_PCT: dict[str, float] = {
    "%": 1.0,
    "pct": 1.0,
    "percent": 1.0,
    "percentage": 1.0,
    "fraction": 100.0,
}

_DIMENSIONLESS_UNITS = {"dimensionless", "ratio", "unitless", ""}


def normalize_unit_string(unit: str) -> str:
    """Clean and normalize unit string for lookup."""
    return unit.strip().lower().replace(" ", "")


def convert_measurement(
    value: float,
    original_unit: str,
    target_endpoint: str,
) -> tuple[float, str]:
    """Convert an experimental value to its canonical model unit.

    Args:
        value: Original numeric measurement.
        original_unit: Original unit string from publication.
        target_endpoint: Target endpoint string (e.g. 'GSH', 'HEMOLYSIS').

    Returns:
        Tuple of (normalized_value, normalized_unit).

    Raises:
        ValueError: If unit is unsupported or conversion is ambiguous.
    """
    cleaned = normalize_unit_string(original_unit)
    ep_upper = target_endpoint.upper()

    if ep_upper in ("HEMOLYSIS",):
        if cleaned in _PERCENTAGE_TO_PCT:
            norm_val = value * _PERCENTAGE_TO_PCT[cleaned]
            return float(norm_val), "%"
        raise ValueError(
            f"Unsupported hemolysis unit '{original_unit}'. Expected '%', 'pct', or 'fraction'."
        )

    if ep_upper in ("GSH_GSSG_RATIO", "OXIDATIVE_DAMAGE"):
        if cleaned in _DIMENSIONLESS_UNITS:
            return float(value), "dimensionless"
        raise ValueError(
            f"Unsupported dimensionless unit '{original_unit}'. Expected 'dimensionless' or 'ratio'."
        )

    # General metabolite concentrations (GSH, GSSG, H2O2, NADPH)
    if cleaned in _CONCENTRATION_TO_MM:
        factor = _CONCENTRATION_TO_MM[cleaned]
        return float(value * factor), "mM"

    raise ValueError(
        f"Unsupported unit '{original_unit}' for endpoint '{target_endpoint}'. "
        f"Supported concentration units: {list(_CONCENTRATION_TO_MM.keys())}."
    )
