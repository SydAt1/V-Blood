"""
Chemical identifier validation and normalization utilities.

Provides verification for SMILES and InChIKey representations.
Uses RDKit when installed, with standard syntax fallbacks.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# Standard IUPAC InChIKey regex: 14 uppercase chars, hyphen, 10 uppercase chars, hyphen, 1 uppercase char
INCHIKEY_PATTERN = re.compile(r"^[A-Z]{14}-[A-Z]{10}-[A-Z]$")


class ValidationResult(NamedTuple):
    is_valid: bool
    error_message: str | None = None
    canonical: str | None = None


def validate_inchikey(inchikey: str) -> ValidationResult:
    """Validate an InChIKey string format.

    Args:
        inchikey: IUPAC InChIKey string.

    Returns:
        ValidationResult indicating validity and error details.
    """
    if not isinstance(inchikey, str):
        return ValidationResult(False, "InChIKey must be a string.")

    cleaned = inchikey.strip().upper()
    if not INCHIKEY_PATTERN.match(cleaned):
        return ValidationResult(
            False,
            f"Invalid InChIKey format '{inchikey}'. Must match standard pattern 'XXXXXXXXXXXXXX-XXXXXXXXXX-X'.",
        )
    return ValidationResult(True, canonical=cleaned)


def validate_smiles(smiles: str) -> ValidationResult:
    """Validate a SMILES string.

    Uses RDKit if available, otherwise performs structural syntax checks.

    Args:
        smiles: Simplified Molecular Input Line Entry System string.

    Returns:
        ValidationResult with canonical SMILES if valid.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return ValidationResult(False, "SMILES string must be non-empty.")

    cleaned = smiles.strip()

    # Attempt RDKit validation if available
    try:
        from rdkit import Chem

        mol = Chem.MolFromSmiles(cleaned)
        if mol is None:
            return ValidationResult(False, f"Invalid SMILES string '{cleaned}' rejected by RDKit parser.")
        canonical = Chem.MolToSmiles(mol, canonical=True)
        return ValidationResult(True, canonical=canonical)
    except ImportError:
        pass

    # Fallback syntactic validation: balanced brackets, parentheses, valid characters
    brackets = 0
    parens = 0
    for char in cleaned:
        if char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
            if brackets < 0:
                return ValidationResult(False, f"Unbalanced brackets in SMILES '{cleaned}'.")
        elif char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
            if parens < 0:
                return ValidationResult(False, f"Unbalanced parentheses in SMILES '{cleaned}'.")

    if brackets != 0:
        return ValidationResult(False, f"Unclosed square bracket in SMILES '{cleaned}'.")
    if parens != 0:
        return ValidationResult(False, f"Unclosed parenthesis in SMILES '{cleaned}'.")

    # Reject obviously illegal characters
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789=#%-+@:\\[]()/.")
    if not set(cleaned).issubset(valid_chars):
        return ValidationResult(False, f"SMILES '{cleaned}' contains illegal characters.")

    return ValidationResult(True, canonical=cleaned)
