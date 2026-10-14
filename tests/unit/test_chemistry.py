"""
Unit tests for chemical structure validation (Milestone 4).
"""

import pytest
from vblood.chemistry.identifiers import validate_inchikey, validate_smiles


class TestChemicalValidation:
    """Tests for SMILES and InChIKey validators."""

    def test_valid_inchikey(self):
        res = validate_inchikey("MHAJPDPJQMAIIY-UHFFFAOYSA-N")
        assert res.is_valid
        assert res.canonical == "MHAJPDPJQMAIIY-UHFFFAOYSA-N"

    def test_lowercase_inchikey_normalized(self):
        res = validate_inchikey("mhajpdpjqmaiiy-uhfffaoysa-n")
        assert res.is_valid
        assert res.canonical == "MHAJPDPJQMAIIY-UHFFFAOYSA-N"

    def test_invalid_inchikey_format_rejected(self):
        res = validate_inchikey("NOT-AN-INCHIKEY")
        assert not res.is_valid
        assert "Invalid InChIKey" in res.error_message

    def test_valid_smiles(self):
        res = validate_smiles("CC1=CC(=O)C2=CC=CC=C2C1=O")  # Menadione
        assert res.is_valid
        assert res.canonical is not None

    def test_empty_smiles_rejected(self):
        res = validate_smiles("")
        assert not res.is_valid

    def test_unbalanced_smiles_rejected(self):
        res = validate_smiles("C1=CC(=O)C2=CC=CC=C2C1(=O")
        assert not res.is_valid
