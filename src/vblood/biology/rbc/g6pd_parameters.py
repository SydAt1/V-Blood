"""
Parameter definitions and provenance for the G6PD kinetic sub-model (Task 6).

Scientific Provenance:
- Yoshida, A. (1973) Hemolytic anemia and G6PD deficiency. Science 179:532-537.
- Kirkman, H. N. & Gaetani, G. F. (1986) Catalase: a tetrameric enzyme with four tightly
  bound molecules of NADPH. J. Biol. Chem. 261:4033-4038.
- Gaetani, G. F. et al. (1994) Catalase and glutathione peroxidase are equally active in
  detoxification of hydrogen peroxide in human erythrocytes. Blood 84:2018-2024.
- Mulquiney, P. J. & Kuchel, P. W. (1999) Model of red blood cell metabolism: glycolysis,
  the pentose phosphate pathway and the Rapoport-Luebering shunt. Biochem. J. 342:567-584.
- Minakami, S. et al. (1965) Studies on erythrocyte glycolysis. I. Determination of glycolytic
  intermediates in human erythrocytes. Biochem. Biophys. Res. Commun. 19:422-427.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vblood.biology.rbc.parameters import EvidenceStatus, Parameter


@dataclass
class G6PDParameters:
    """Parameters for the evidence-grounded erythrocyte G6PD kinetic rate law.

    Models ordered/rapid-equilibrium Bi-Bi kinetics with competitive product
    inhibition by NADPH against NADP+ (Option A).
    """

    # Maximum G6PD velocity in normal human erythrocyte cytosol
    vmax_g6pd: Parameter = field(
        default_factory=lambda: Parameter(
            name="vmax_g6pd",
            value=0.008,  # mM/s = 8 µM/s
            units="mM s⁻¹",
            source="Gaetani et al. (1994) Blood 84:2018; Kirkman & Gaetani (1986) JBC 261:4033",
            conditions="Normal adult human erythrocytes, pH 7.4, 37°C",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.5,
            notes="Vmax of G6PD in normal erythrocytes under physiological conditions.",
            assumption_id="P-G6PD-01",
        )
    )

    # Michaelis constant for G6P
    km_g6p: Parameter = field(
        default_factory=lambda: Parameter(
            name="km_g6p",
            value=0.040,  # mM = 40 µM
            units="mM",
            source="Yoshida (1973) Science 179:532; Mulquiney & Kuchel (1999) Biochem. J. 342:567",
            conditions="Purified human erythrocyte G6PD",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.3,
            notes="Affinity constant for glucose-6-phosphate substrate.",
            assumption_id="P-G6PD-02",
        )
    )

    # Michaelis constant for NADP+
    km_nadp: Parameter = field(
        default_factory=lambda: Parameter(
            name="km_nadp",
            value=0.008,  # mM = 8 µM
            units="mM",
            source="Yoshida (1973) Science 179:532; Kirkman et al. (1986)",
            conditions="Purified human erythrocyte G6PD",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.3,
            notes="Affinity constant for NADP+ cofactor.",
            assumption_id="P-G6PD-03",
        )
    )

    # Competitive inhibition constant for NADPH against NADP+
    ki_nadph: Parameter = field(
        default_factory=lambda: Parameter(
            name="ki_nadph",
            value=0.012,  # mM = 12 µM
            units="mM",
            source="Kirkman & Gaetani (1986) JBC 261:4033; Gaetani et al. (1989)",
            conditions="Human erythrocyte cytosol, competitive inhibition vs NADP+",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.4,
            notes="NADPH competitively inhibits G6PD binding of NADP+.",
            assumption_id="P-G6PD-04",
        )
    )

    # Total intracellular NADP(H) pool concentration: [NADP+] + [NADPH]
    nadp_total: Parameter = field(
        default_factory=lambda: Parameter(
            name="nadp_total",
            value=0.040,  # mM = 40 µM
            units="mM",
            source="Gaetani et al. (1994) Blood 84:2018; Kirkman et al. (1986)",
            conditions="Resting human erythrocytes (total [NADP+] + [NADPH])",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.2,
            notes="Total pyridine nucleotide pool conserved in mature erythrocytes.",
            assumption_id="P-G6PD-05",
        )
    )

    # Steady-state concentration of glucose-6-phosphate
    g6p_conc: Parameter = field(
        default_factory=lambda: Parameter(
            name="g6p_conc",
            value=0.040,  # mM = 40 µM
            units="mM",
            source="Minakami et al. (1965) BBRC 19:422; Mulquiney & Kuchel (1999)",
            conditions="Resting human erythrocyte intracellular water",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.5,
            notes="Intracellular G6P maintained by steady-state glycolysis.",
            assumption_id="P-G6PD-06",
        )
    )

    # Relative G6PD enzyme activity multiplier (alpha): 1.0 = normal, 0.0-0.9 = reduced
    g6pd_activity_fraction: Parameter = field(
        default_factory=lambda: Parameter(
            name="g6pd_activity_fraction",
            value=1.0,
            units="dimensionless",
            source="Mathematical scaling multiplier for deficiency scenarios",
            conditions="1.0 = normal (100%), 0.5 = 50% activity, 0.1 = 10% activity",
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=1.0,
            notes="Enables simulating reduced G6PD enzyme activity without altering intrinsic kinetic constants.",
            assumption_id="P-G6PD-07",
        )
    )

    def to_dict(self) -> dict[str, float]:
        """Return dict of parameter name -> numeric value."""
        return {
            "vmax_g6pd": self.vmax_g6pd.value,
            "km_g6p": self.km_g6p.value,
            "km_nadp": self.km_nadp.value,
            "ki_nadph": self.ki_nadph.value,
            "nadp_total": self.nadp_total.value,
            "g6p_conc": self.g6p_conc.value,
            "g6pd_activity_fraction": self.g6pd_activity_fraction.value,
        }

    def all_parameters(self) -> dict[str, Parameter]:
        """Return dict of parameter_name -> Parameter object."""
        return {
            p.name: p
            for p in self.__dict__.values()
            if isinstance(p, Parameter)
        }


DEFAULT_G6PD_PARAMETERS = G6PDParameters()
