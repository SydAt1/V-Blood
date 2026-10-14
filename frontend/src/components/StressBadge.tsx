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
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-800 ${className}`}
        >
          Healthy
        </span>
      );

    case 'stressed':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-950/70 text-amber-300 border border-amber-800 ${className}`}
        >
          Stressed
        </span>
      );

    case 'severely_stressed':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-orange-950/80 text-orange-300 border border-orange-700 ${className}`}
        >
          Severely Stressed
        </span>
      );

    case 'lysis_risk':
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-700 ${className}`}
        >
          Lysis Risk (Model Proxy)
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700 ${className}`}
        >
          {state}
        </span>
      );
  }
};
