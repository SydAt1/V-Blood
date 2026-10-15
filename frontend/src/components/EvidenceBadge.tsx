import React from 'react';
import type { EvidenceLevel } from '../types/api';
import { AlertTriangle, Check, HelpCircle } from 'lucide-react';

interface Props {
  level: EvidenceLevel;
  className?: string;
}

export const EvidenceBadge: React.FC<Props> = ({ level, className = '' }) => {
  switch (level) {
    case 'CURATED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 border border-[#3E5C46] bg-[#EDF4EE] text-[#294231] font-mono text-[10px] font-semibold tracking-wider ${className}`}
          title="Curated: Peer-reviewed human erythrocyte experimental data with documented provenance."
        >
          <Check className="w-2.5 h-2.5 text-[#33533B] stroke-[2.5]" />
          <span>CURATED</span>
        </span>
      );

    case 'ESTIMATED':
      return (
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 border border-[#8C5D23] bg-[#F8F2E8] text-[#5C3911] font-mono text-[10px] font-semibold tracking-wider ${className}`}
          title="Estimated: Calibrated or approximated from analogous biological systems or preliminary assays."
        >
          <HelpCircle className="w-2.5 h-2.5 text-[#7A4E1A] stroke-[2]" />
          <span>ESTIMATED</span>
        </span>
      );

    case 'UNVERIFIED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 border border-[#962F27] bg-[#F7EBEA] text-[#85251E] font-mono font-bold text-[10px] tracking-wider animate-pulse-slow shadow-[1px_1px_0px_0px_rgba(150,47,39,0.2)] ${className}`}
          title="UNVERIFIED: Synthetic or unverified kinetics. Excluded from biological validation scoring."
        >
          <AlertTriangle className="w-2.5 h-2.5 text-[#85251E] stroke-[2.5]" />
          <span>UNVERIFIED</span>
        </span>
      );
  }
};
