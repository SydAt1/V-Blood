import React from 'react';
import type { CellVisualState } from '../types/api';

interface Props {
  state: CellVisualState;
  className?: string;
}

export const StressBadge: React.FC<Props> = ({ state, className = '' }) => {
  switch (state) {
    case 'healthy':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 border border-[#3E5C46] bg-[#EDF4EE] text-[#284431] font-mono text-[11px] font-semibold tracking-wide ${className}`}
        >
          Healthy
        </span>
      );

    case 'stressed':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 border border-[#8C5D23] bg-[#F8F2E8] text-[#5C3911] font-mono text-[11px] font-semibold tracking-wide ${className}`}
        >
          Stressed
        </span>
      );

    case 'severely_stressed':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 border border-[#9A421D] bg-[#FAEDE6] text-[#6E2C0F] font-mono text-[11px] font-semibold tracking-wide ${className}`}
        >
          Severely Stressed
        </span>
      );

    case 'lysis_risk':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 border border-[#962F27] bg-[#F7EBEA] text-[#82241D] font-mono text-[11px] font-bold tracking-wide shadow-[1px_1px_0px_0px_rgba(150,47,39,0.2)] ${className}`}
        >
          Lysis Risk (Model Proxy)
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 border border-[#C8C1B2] bg-[#EFECE3] text-[#474D46] font-mono text-[11px] ${className}`}
        >
          {state}
        </span>
      );
  }
};
