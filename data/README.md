# Data Directory — V-Blood

## Structure

```
data/
├── raw/         Original data files as downloaded (never modified)
├── processed/   Cleaned, normalised versions with explicit schema
└── README.md    This file
```

## Data principles

1. **Preserve originals.** Raw data files are never modified. All transformations produce files in `processed/`.
2. **Separate measurement types.** Whole-blood, plasma, and isolated-RBC measurements are stored separately and never silently merged.
3. **Record provenance.** Every processed file is accompanied by a metadata record (study ID, source publication, license, extraction method, quality flag).
4. **No fabricated data.** No experimental values are invented. Synthetic data used for software tests is clearly labelled and stored outside this directory.
5. **License compliance.** No copyrighted experimental data is committed without explicit permission.

## Current status (Milestone 1)

No experimental data has been ingested yet. This directory contains only placeholder files.

## Planned datasets (Milestone 2)

| Dataset | Type | Source | License | Priority |
|---|---|---|---|---|
| Normal RBC GSH/GSSG reference ranges | Steady-state | Giustarini et al. 2013 | Review/extract from paper | High |
| H2O2 clearance kinetics | Time-series | Gaetani et al. 1994 | Review/extract | High |
| AAPH haemolysis dose-response | Endpoint | Multiple (ToxCast/OpenTox) | Check per source | Medium |
| G6PD-deficient RBC GSH trajectories | Time-series | Nakayama 2005 (simulated) | Available in paper | Medium |

## Data schema (planned)

Each experimental record will capture (where available):
- Study and experiment IDs
- Chemical identifier (InChIKey, SMILES, CAS)
- Concentration and units
- Exposure duration (s)
- Temperature and pH
- Sample type (whole blood, plasma, isolated RBC, packed RBC)
- Donor characteristics (if available)
- Assay method
- Endpoint name and definition
- Measured value and units
- Replicate information (n, SD)
- Measurement uncertainty
- Source publication (DOI)
- Data quality status (raw / validated / suspect)
