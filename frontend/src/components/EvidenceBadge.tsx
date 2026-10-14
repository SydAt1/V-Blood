import React from 'react';
import type { EvidenceLevel } from '../types/api';
import { AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';

interface Props {
  level: EvidenceLevel;
  className?: string;
}

export const EvidenceBadge: React.FC<Props> = ({ level, className = '' }) => {
  switch (level) {
    case 'CURATED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800 ${className}`}
          title="Curated: Peer-reviewed human erythrocyte experimental data with documented provenance."
        >
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>CURATED</span>
        </span>
      );

    case 'ESTIMATED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-800 ${className}`}
          title="Estimated: Calibrated or approximated from analogous biological systems or preliminary assays."
        >
          <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
          <span>ESTIMATED</span>
        </span>
      );

    case 'UNVERIFIED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-200 border border-rose-700 animate-pulse-slow ${className}`}
          title="UNVERIFIED: Synthetic or unverified kinetics. Excluded from biological validation scoring."
        >
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          <span>UNVERIFIED</span>
        </span>
      );
  }
};
