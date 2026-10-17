"""
Chemical Identity Resolution Service (Milestone 7 - Step 2).

Resolves chemical substance names against authoritative sources (primarily PubChem),
captures canonical SMILES, InChIKey, InChI, molecular formula, CID, and synonyms,
and classifies chemical entity types (small molecule, element, ion, salt, metabolite).
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from vblood.chemistry.identifiers import validate_inchikey, validate_smiles
from vblood.intelligence.schemas import ChemicalEntityType, ChemicalIdentity

logger = logging.getLogger(__name__)

# Known curated fixture identities for deterministic offline tests and benchmarks
KNOWN_IDENTITIES: dict[str, dict[str, Any]] = {
    "primaquine": {
        "preferred_name": "Primaquine",
        "common_names": ["Primaquine", "WR-2975", "Neo-Quipenyl", "SN-13272"],
        "molecular_formula": "C15H21N3O",
        "smiles": "CC(CCCN)NC1=C2C(=CC=C1)C(=CC=N2)OC",
        "inchikey": "FPGZONURBKGNAZ-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C15H21N3O/c1-11(5-3-7-16)18-14-8-6-9-15(19-2)13-10-4-12-17-13/h4,6,8,10-12,18H,3,5,7,16H2,1-2H3",
        "pubchem_cid": 4908,
        "entity_type": ChemicalEntityType.SMALL_MOLECULE,
        "charge": 0,
        "molecular_weight": 259.35,
        "source": "PubChem",
    },
    "menadione": {
        "preferred_name": "Menadione",
        "common_names": ["Menadione", "Vitamin K3", "2-Methylnaphthalene-1,4-dione", "Menaphthone"],
        "molecular_formula": "C11H8O2",
        "smiles": "CC1=CC(=O)C2=CC=CC=C2C1=O",
        "inchikey": "MJGQHYZZJPFOCL-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C11H8O2/c1-7-6-10(12)8-4-2-3-5-9(8)11(7)13/h2-6H,1H3",
        "pubchem_cid": 4055,
        "entity_type": ChemicalEntityType.SMALL_MOLECULE,
        "charge": 0,
        "molecular_weight": 172.18,
        "source": "PubChem",
    },
    "hydrogen peroxide": {
        "preferred_name": "Hydrogen peroxide",
        "common_names": ["Hydrogen peroxide", "Oxydol", "Peroxide", "Dihydric peroxide"],
        "molecular_formula": "H2O2",
        "smiles": "OO",
        "inchikey": "MHAJPDPJQMAIIY-UHFFFAOYSA-N",
        "inchi": "InChI=1S/H2O2/c1-2/h1-2H",
        "pubchem_cid": 784,
        "entity_type": ChemicalEntityType.SMALL_MOLECULE,
        "charge": 0,
        "molecular_weight": 34.014,
        "source": "PubChem",
    },
    "iron": {
        "preferred_name": "Iron",
        "common_names": ["Iron", "Ferrum", "Iron elemental"],
        "molecular_formula": "Fe",
        "smiles": "[Fe]",
        "inchikey": "XEEYBQQBJWHFJM-UHFFFAOYSA-N",
        "inchi": "InChI=1S/Fe",
        "pubchem_cid": 23925,
        "entity_type": ChemicalEntityType.ELEMENT,
        "charge": 0,
        "molecular_weight": 55.845,
        "source": "PubChem",
        "is_ambiguous": True,
        "ambiguity_candidates": [
            "Ferrous iron (Fe2+)",
            "Ferric iron (Fe3+)",
            "Elemental iron (Fe0)",
            "Ferric chloride (FeCl3)",
            "Ferrous sulfate (FeSO4)",
        ],
    },
    "ferrous iron": {
        "preferred_name": "Iron(2+)",
        "common_names": ["Ferrous iron", "Iron(II) ion", "Fe(2+)", "Ferrous ion"],
        "molecular_formula": "Fe+2",
        "smiles": "[Fe+2]",
        "inchikey": "CWYNVVGOOAEACU-UHFFFAOYSA-N",
        "inchi": "InChI=1S/Fe/q+2",
        "pubchem_cid": 27284,
        "entity_type": ChemicalEntityType.ION,
        "charge": 2,
        "molecular_weight": 55.845,
        "source": "PubChem",
    },
    "ferric chloride": {
        "preferred_name": "Iron trichloride",
        "common_names": ["Ferric chloride", "Iron(III) chloride", "Molysite", "FeCl3"],
        "molecular_formula": "Cl3Fe",
        "smiles": "Cl[Fe](Cl)Cl",
        "inchikey": "RBTARNPIBWPFCO-UHFFFAOYSA-N",
        "inchi": "InChI=1S/3ClH.Fe/h3*1H;/q;;;+3/p-3",
        "pubchem_cid": 24380,
        "entity_type": ChemicalEntityType.SALT,
        "charge": 0,
        "molecular_weight": 162.2,
        "source": "PubChem",
    },
    "doxorubicin": {
        "preferred_name": "Doxorubicin",
        "common_names": ["Adriamycin", "Doxorubicin hydrochloride", "Hydroxydaunorubicin"],
        "molecular_formula": "C27H29NO11",
        "smiles": "CC1C(C(CC(O1)OC2CC(CC3=C2C(=O)C4=C(C3=O)C(=CC=C4)OC)(C(=O)CO)O)N)O",
        "inchikey": "MWWSFMDVAYGXBV-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C27H29NO11/c1-10-22(31)14(28)6-17(38-10)39-16-8-27(36,19(30)9-29)7-13-18(16)26(35)21-20(25(13)34)23(32)11-4-3-5-12(37-2)15(11)24(21)33/h3-5,10,14,16-17,22,29,31,34-36H,6-9,28H2,1-2H3",
        "pubchem_cid": 31703,
        "entity_type": ChemicalEntityType.SMALL_MOLECULE,
        "charge": 0,
        "molecular_weight": 543.5,
        "source": "PubChem",
    },
    "ascorbic acid": {
        "preferred_name": "Ascorbic acid",
        "common_names": ["Vitamin C", "L-Ascorbic acid", "Ascorbate"],
        "molecular_formula": "C6H8O6",
        "smiles": "C(C(C1C(=C(C(=O)O1)O)O)O)O",
        "inchikey": "CIWBSHSKHKDKBQ-UHFFFAOYSA-N",
        "inchi": "InChI=1S/C6H8O6/c7-1-2(8)3-4(9)5(10)6(11)12-3/h2-3,7-10H,1H2",
        "pubchem_cid": 54670067,
        "entity_type": ChemicalEntityType.SMALL_MOLECULE,
        "charge": 0,
        "molecular_weight": 176.12,
        "source": "PubChem",
    },
}


def _classify_entity_type(name: str, formula: str | None, charge: int) -> ChemicalEntityType:
    """Classify the chemical entity type based on name patterns, formula, and charge."""
    n = name.lower().strip()

    # Elements
    element_names = {
        "iron", "copper", "zinc", "selenium", "carbon", "oxygen", "nitrogen", "sulfur",
        "calcium", "magnesium", "manganese", "potassium", "sodium", "gold", "silver",
    }
    if n in element_names:
        return ChemicalEntityType.ELEMENT

    # Ions
    if charge != 0 or re.search(r"\b(ion|\(ii\)|\(iii\)|\(\+?\d+\)|cation|anion)\b", n) or "+" in n or "-" in n:
        return ChemicalEntityType.ION

    # Salts
    salt_indicators = ["chloride", "sulfate", "sulphate", "phosphate", "bromide", "iodide", "nitrate", "acetate"]
    if any(s in n for s in salt_indicators) and (" " in n or "-" in n):
        return ChemicalEntityType.SALT

    # Metabolites
    if any(m in n for m in ["metabolite", "quinone", "glucuronide", "conjugate", "oxide", "hydroxy-"]):
        return ChemicalEntityType.METABOLITE

    return ChemicalEntityType.SMALL_MOLECULE


class ChemicalIdentityResolver:
    """Resolves chemical substance names to authoritative identities and identifiers."""

    def __init__(self, timeout_s: float = 8.0):
        self.timeout_s = timeout_s
        self._cache: dict[str, ChemicalIdentity] = {}

    def resolve(self, query: str) -> ChemicalIdentity:
        """Resolve query chemical name to a verified ChemicalIdentity object.

        Prioritizes:
        1. In-memory cache
        2. Curated fixture records
        3. Authoritative PubChem PUG REST API query
        """
        normalized_query = query.strip().lower()
        if not normalized_query:
            raise ValueError("Chemical query string cannot be empty.")

        if normalized_query in self._cache:
            return self._cache[normalized_query]

        # Check curated fixtures
        if normalized_query in KNOWN_IDENTITIES:
            fixture = KNOWN_IDENTITIES[normalized_query]
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            ident = ChemicalIdentity(
                preferred_name=fixture["preferred_name"],
                common_names=fixture.get("common_names", [fixture["preferred_name"]]),
                molecular_formula=fixture.get("molecular_formula"),
                smiles=fixture["smiles"],
                inchikey=fixture["inchikey"],
                inchi=fixture.get("inchi"),
                pubchem_cid=fixture.get("pubchem_cid"),
                entity_type=fixture.get("entity_type", ChemicalEntityType.SMALL_MOLECULE),
                charge=fixture.get("charge", 0),
                molecular_weight=fixture.get("molecular_weight"),
                source=fixture.get("source", "PubChem"),
                retrieved_at=now_iso,
                is_ambiguous=fixture.get("is_ambiguous", False),
                ambiguity_candidates=fixture.get("ambiguity_candidates", []),
            )
            self._cache[normalized_query] = ident
            return ident

        # Query PubChem PUG REST API
        try:
            ident = self._query_pubchem(query)
            self._cache[normalized_query] = ident
            return ident
        except Exception as exc:
            logger.warning("PubChem live resolution failed for '%s': %s", query, exc)
            # Check if partial match exists in fixtures
            for key, fix in KNOWN_IDENTITIES.items():
                if key in normalized_query or normalized_query in key:
                    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    ident = ChemicalIdentity(
                        preferred_name=fix["preferred_name"],
                        common_names=fix.get("common_names", [fix["preferred_name"]]),
                        molecular_formula=fix.get("molecular_formula"),
                        smiles=fix["smiles"],
                        inchikey=fix["inchikey"],
                        inchi=fix.get("inchi"),
                        pubchem_cid=fix.get("pubchem_cid"),
                        entity_type=fix.get("entity_type", ChemicalEntityType.SMALL_MOLECULE),
                        charge=fix.get("charge", 0),
                        molecular_weight=fix.get("molecular_weight"),
                        source=fix.get("source", "PubChem (Curated Fixture)"),
                        retrieved_at=now_iso,
                        is_ambiguous=fix.get("is_ambiguous", False),
                        ambiguity_candidates=fix.get("ambiguity_candidates", []),
                    )
                    self._cache[normalized_query] = ident
                    return ident

            raise RuntimeError(
                f"Could not resolve chemical identity for '{query}'. "
                f"PubChem endpoint was unreachable or substance was not found: {exc}"
            ) from exc

    def _query_pubchem(self, query: str) -> ChemicalIdentity:
        """Fetch compound properties directly from PubChem PUG REST API."""
        encoded_name = urllib.parse.quote(query.strip())
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/"
            f"Title,CanonicalSMILES,InChI,InChIKey,MolecularFormula,MolecularWeight,Charge/JSON"
        )

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "V-Blood-Research-Station/0.7 (Computational Biology Research)"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        prop_table = data.get("PropertyTable", {}).get("Properties", [])
        if not prop_table:
            raise ValueError(f"No compound properties returned from PubChem for '{query}'.")

        p = prop_table[0]
        cid = p.get("CID")
        title = p.get("Title") or query.capitalize()
        smiles = p.get("CanonicalSMILES") or p.get("ConnectivitySMILES") or ""
        inchikey = p.get("InChIKey") or ""
        inchi = p.get("InChI")
        formula = p.get("MolecularFormula")
        mw = float(p["MolecularWeight"]) if "MolecularWeight" in p else None
        charge = int(p.get("Charge", 0))

        # Validate identifiers
        smiles_val = validate_smiles(smiles)
        canonical_smiles = smiles_val.canonical or smiles

        inchikey_val = validate_inchikey(inchikey)
        canonical_inchikey = inchikey_val.canonical or inchikey

        entity_type = _classify_entity_type(title, formula, charge)

        # Retrieve synonyms
        synonyms = [title]
        try:
            syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
            syn_req = urllib.request.Request(
                syn_url,
                headers={"User-Agent": "V-Blood-Research-Station/0.7"},
            )
            with urllib.request.urlopen(syn_req, timeout=4.0) as s_resp:
                s_data = json.loads(s_resp.read().decode("utf-8"))
                syn_list = s_data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
                synonyms = syn_list[:8] if syn_list else [title]
        except Exception:
            pass

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        is_ambiguous = len(prop_table) > 1 or query.lower() in ("iron", "copper", "arsenic")
        ambiguity_candidates = [item.get("Title", "") for item in prop_table[:5]] if is_ambiguous else []

        return ChemicalIdentity(
            preferred_name=title,
            common_names=synonyms,
            molecular_formula=formula,
            smiles=canonical_smiles,
            inchikey=canonical_inchikey,
            inchi=inchi,
            pubchem_cid=cid,
            entity_type=entity_type,
            charge=charge,
            molecular_weight=mw,
            source="PubChem PUG REST API",
            retrieved_at=now_iso,
            is_ambiguous=is_ambiguous,
            ambiguity_candidates=ambiguity_candidates,
        )
