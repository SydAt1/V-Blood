import React, { useMemo, useState } from 'react';
import type { TrajectoryPoint } from '../types/api';

export interface SeriesConfig {
  key: keyof TrajectoryPoint;
  label: string;
  chemicalFormula: string;
  unit: string;
  color: string;
  scale?: number;
}

const DEFAULT_SERIES: SeriesConfig[] = [
  {
    key: 'gsh_mM',
    label: 'Reduced Glutathione',
    chemicalFormula: '[GSH]',
    unit: 'mM',
    color: '#286345', // Deep physiological sage
  },
  {
    key: 'gssg_mM',
    label: 'Glutathione Disulfide',
    chemicalFormula: '[GSSG]',
    unit: 'mM',
    color: '#8F5C1E', // Oxidized amber
  },
  {
    key: 'nadph_mM',
    label: 'NADPH Cofactor Pool',
    chemicalFormula: '[NADPH]',
    unit: 'mM',
    color: '#4B466D', // Slate indigo
  },
  {
    key: 'h2o2_mM',
    label: 'Hydrogen Peroxide',
    chemicalFormula: '[H₂O₂]',
    unit: 'mM',
    color: '#2A5A6E', // Prussian steel
  },
  {
    key: 'damage',
    label: 'Oxidative Damage Index',
    chemicalFormula: '[D]',
    unit: '[0, 1]',
    color: '#9B332B', // Oxidized crimson
  },
];

interface Props {
  treatmentTrajectory?: TrajectoryPoint[];
  controlTrajectory?: TrajectoryPoint[];
  treatmentLabel?: string;
  controlLabel?: string;
  title?: string;
  height?: number;
}

export const TimeSeriesChart: React.FC<Props> = ({
  treatmentTrajectory = [],
  controlTrajectory = [],
  treatmentLabel = 'Treatment Challenge',
  controlLabel = 'Untreated Baseline Control',
  title = 'Intracellular Biochemical Dynamics & Redox Kinetics',
  height = 360,
}) => {
  const [activeSeries, setActiveSeries] = useState<Record<string, boolean>>({
    gsh_mM: true,
    gssg_mM: true,
    nadph_mM: true,
    h2o2_mM: false,
    damage: true,
  });

  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const hasData = treatmentTrajectory.length > 0 || controlTrajectory.length > 0;
  const primaryTraj = treatmentTrajectory.length > 0 ? treatmentTrajectory : controlTrajectory;

  // Compute time bounds & optimal unit (s, min, or h)
  const maxTime_s = useMemo(() => {
    if (!hasData) return 3600;
    const tMax1 = treatmentTrajectory[treatmentTrajectory.length - 1]?.t_s || 0;
    const tMax2 = controlTrajectory[controlTrajectory.length - 1]?.t_s || 0;
    return Math.max(tMax1, tMax2, 1);
  }, [treatmentTrajectory, controlTrajectory, hasData]);

  const timeUnit = useMemo(() => {
    if (maxTime_s >= 7200) return { label: 'Time (hours)', divisor: 3600, precision: 2 };
    if (maxTime_s >= 180) return { label: 'Time (minutes)', divisor: 60, precision: 1 };
    return { label: 'Time (seconds)', divisor: 1, precision: 0 };
  }, [maxTime_s]);

  // Compute Y bounds for active series
  const { minY, maxY } = useMemo(() => {
    let min = 0;
    let max = 0.1;

    const evalSeries = (traj: TrajectoryPoint[]) => {
      traj.forEach((pt) => {
        DEFAULT_SERIES.forEach((s) => {
          if (activeSeries[s.key as string]) {
            const val = Number(pt[s.key]) || 0;
            if (val > max) max = val;
            if (val < min) min = val;
          }
        });
      });
    };

    if (treatmentTrajectory.length > 0) evalSeries(treatmentTrajectory);
    if (controlTrajectory.length > 0) evalSeries(controlTrajectory);

    return { minY: min, maxY: max * 1.05 };
  }, [treatmentTrajectory, controlTrajectory, activeSeries]);

  const width = 860;
  const padding = { top: 25, right: 35, bottom: 45, left: 65 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const scaleX = (t: number) => padding.left + (t / maxTime_s) * plotWidth;
  const scaleY = (v: number) =>
    padding.top + plotHeight - ((v - minY) / (maxY - minY || 1)) * plotHeight;

  // Build SVG path strings
  const buildPath = (traj: TrajectoryPoint[], key: keyof TrajectoryPoint) => {
    if (!traj || traj.length === 0) return '';
    return traj.reduce((acc, pt, idx) => {
      const x = scaleX(pt.t_s);
      const y = scaleY(Number(pt[key]) || 0);
      return idx === 0 ? `M ${x.toFixed(1)} ${y.toFixed(1)}` : `${acc} L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }, '');
  };

  const toggleSeries = (key: string) => {
    setActiveSeries((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (!hasData) {
    return (
      <div className="flex flex-col items-center justify-center h-80 border border-dashed border-[#D8D1C2] bg-[#FAF7F2] text-[#767D75] p-8 text-center shadow-[1px_1px_0px_0px_rgba(24,27,24,0.04)]">
        <div className="w-10 h-10 border border-[#B5AC99] bg-[#EDE8DE] flex items-center justify-center text-[#484E48] mb-3 font-mono text-sm">
          FIG.1
        </div>
        <div className="font-editorial text-base font-bold text-[#181B18]">
          Awaiting Numerical Trajectory Integration
        </div>
        <div className="text-xs text-[#666E65] max-w-md mt-1 leading-relaxed">
          Select chemical compounds and exposure parameters in the scenario builder above, then click{' '}
          <strong className="text-[#9B332B]">"Execute Simulation"</strong> to evaluate the ODE system.
        </div>
      </div>
    );
  }

  // Hover position & values
  const hoveredPoint = hoverIndex !== null ? primaryTraj[hoverIndex] : null;
  const hoveredControl =
    hoverIndex !== null && controlTrajectory.length > hoverIndex ? controlTrajectory[hoverIndex] : null;

  return (
    <div className="space-y-3 bg-[#FFFFFF] border border-[#D8D1C2] p-4 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)]">
      {/* Chart Masthead & Calibrated Series Selector */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D8D1C2] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9.5px] uppercase tracking-wider text-[#767D75]">
              INSTRUMENT READOUT //
            </span>
            <h3 className="font-editorial text-base font-bold text-[#181B18] tracking-tight">
              {title}
            </h3>
          </div>
          <p className="text-[11px] text-[#666E65] mt-0.5 font-mono">
            Solid line = <span className="font-semibold text-[#181B18]">{treatmentLabel}</span>
            {controlTrajectory.length > 0 && (
              <>
                {' '}• Dashed line = <span className="text-[#767D75]">{controlLabel}</span>
              </>
            )}
          </p>
        </div>

        {/* Series Visibility Toggles */}
        <div className="flex flex-wrap items-center gap-1.5">
          {DEFAULT_SERIES.map((s) => {
            const active = activeSeries[s.key as string];
            return (
              <button
                key={s.key as string}
                onClick={() => toggleSeries(s.key as string)}
                className={`px-2 py-1 text-xs font-mono transition-all border flex items-center gap-1.5 ${
                  active
                    ? 'bg-[#FAF7F2] border-[#181B18] text-[#181B18] font-semibold shadow-[1px_1px_0px_0px_rgba(24,27,24,0.1)]'
                    : 'bg-[#FCFAF6] border-[#D8D1C2] text-[#868E85] hover:border-[#B5AC99] hover:text-[#484E48]'
                }`}
                title={`Toggle ${s.label} (${s.unit})`}
              >
                <span
                  className="w-2 h-2 inline-block rounded-none"
                  style={{ backgroundColor: active ? s.color : '#B5AC99' }}
                />
                <span>{s.chemicalFormula}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* SVG Plate Container */}
      <div className="relative bg-[#FCFBF9] border border-[#EDE8DE]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseLeave={() => setHoverIndex(null)}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clientX = e.clientX - rect.left;
            const normX = (clientX / rect.width) * width;
            if (normX >= padding.left && normX <= padding.left + plotWidth && primaryTraj.length > 0) {
              const rel = (normX - padding.left) / plotWidth;
              const idx = Math.min(
                Math.max(0, Math.round(rel * (primaryTraj.length - 1))),
                primaryTraj.length - 1
              );
              setHoverIndex(idx);
            } else {
              setHoverIndex(null);
            }
          }}
        >
          {/* Plot Background Tint */}
          <rect
            x={padding.left}
            y={padding.top}
            width={plotWidth}
            height={plotHeight}
            fill="#FAF8F3"
            stroke="#D8D1C2"
            strokeWidth="1"
          />

          {/* Y-Axis Gridlines & Ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const val = minY + ratio * (maxY - minY);
            const y = scaleY(val);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + plotWidth}
                  y2={y}
                  stroke="#E8E2D5"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  fill="#767D75"
                  fontSize="9.5"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {val >= 1 ? val.toFixed(1) : val.toExponential(1).replace('e-0', 'e-')}
                </text>
              </g>
            );
          })}

          {/* X-Axis Gridlines & Ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const t = ratio * maxTime_s;
            const x = scaleX(t);
            const displayTime = (t / timeUnit.divisor).toFixed(timeUnit.precision);
            return (
              <g key={ratio}>
                <line
                  x1={x}
                  y1={padding.top}
                  x2={x}
                  y2={padding.top + plotHeight}
                  stroke="#E8E2D5"
                  strokeWidth="1"
                  strokeDasharray="2 2"
                />
                <text
                  x={x}
                  y={padding.top + plotHeight + 16}
                  textAnchor="middle"
                  fill="#767D75"
                  fontSize="9.5"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {displayTime}
                </text>
              </g>
            );
          })}

          {/* Axis Labels */}
          <text
            x={padding.left + plotWidth / 2}
            y={height - 8}
            textAnchor="middle"
            fill="#484E48"
            fontSize="10"
            fontFamily="'Plus Jakarta Sans', sans-serif"
            fontWeight="600"
            letterSpacing="0.02em"
          >
            {timeUnit.label.toUpperCase()}
          </text>

          <text
            transform="rotate(-90)"
            x={-(padding.top + plotHeight / 2)}
            y={16}
            textAnchor="middle"
            fill="#484E48"
            fontSize="10"
            fontFamily="'Plus Jakarta Sans', sans-serif"
            fontWeight="600"
            letterSpacing="0.02em"
          >
            CONCENTRATION (mM) / DAMAGE INDEX [D]
          </text>

          {/* Control Trajectory Paths (Subtle Charcoal Dashed) */}
          {controlTrajectory.length > 0 &&
            DEFAULT_SERIES.map((s) => {
              if (!activeSeries[s.key as string]) return null;
              const pathD = buildPath(controlTrajectory, s.key);
              return (
                <path
                  key={`ctrl-${s.key as string}`}
                  d={pathD}
                  fill="none"
                  stroke="#7A8279"
                  strokeWidth="1.5"
                  strokeDasharray="4 3"
                  opacity="0.85"
                />
              );
            })}

          {/* Treatment Trajectory Paths (Crisp Calibrated Series) */}
          {treatmentTrajectory.length > 0 &&
            DEFAULT_SERIES.map((s) => {
              if (!activeSeries[s.key as string]) return null;
              const pathD = buildPath(treatmentTrajectory, s.key);
              return (
                <path
                  key={`trt-${s.key as string}`}
                  d={pathD}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                />
              );
            })}

          {/* Precision Hover Crosshair */}
          {hoveredPoint && (
            <g>
              <line
                x1={scaleX(hoveredPoint.t_s)}
                y1={padding.top}
                x2={scaleX(hoveredPoint.t_s)}
                y2={padding.top + plotHeight}
                stroke="#181B18"
                strokeWidth="1"
                strokeDasharray="3 2"
              />
              {DEFAULT_SERIES.map((s) => {
                if (!activeSeries[s.key as string]) return null;
                const val = Number(hoveredPoint[s.key]) || 0;
                return (
                  <circle
                    key={`dot-${s.key as string}`}
                    cx={scaleX(hoveredPoint.t_s)}
                    cy={scaleY(val)}
                    r="3.5"
                    fill={s.color}
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                );
              })}
            </g>
          )}
        </svg>

        {/* Floating Laboratory Annotation Card */}
        {hoveredPoint && (
          <div className="absolute top-3 right-3 bg-[#FFFFFF] border border-[#181B18] p-3 shadow-[3px_3px_0px_0px_rgba(24,27,24,0.15)] text-xs space-y-1.5 pointer-events-none min-w-[220px]">
            <div className="font-mono text-[10px] text-[#484E48] border-b border-[#D8D1C2] pb-1 flex justify-between uppercase">
              <span>t = {(hoveredPoint.t_s / timeUnit.divisor).toFixed(timeUnit.precision)} {timeUnit.label.split(' ')[1].replace(/[()]/g, '')}</span>
              <span className="text-[#868E85]">({hoveredPoint.t_s.toFixed(0)}s)</span>
            </div>

            <div className="space-y-1 font-mono text-[11px]">
              {DEFAULT_SERIES.map((s) => {
                if (!activeSeries[s.key as string]) return null;
                const trtVal = Number(hoveredPoint[s.key]) || 0;
                const ctrlVal = hoveredControl ? Number(hoveredControl[s.key]) : null;

                return (
                  <div key={s.key as string} className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-1.5" style={{ color: s.color }}>
                      <span className="w-1.5 h-1.5 inline-block" style={{ backgroundColor: s.color }} />
                      <span className="font-semibold">{s.chemicalFormula}:</span>
                    </span>
                    <span className="text-[#181B18]">
                      {trtVal >= 0.01 ? trtVal.toFixed(3) : trtVal.toExponential(2)} {s.unit}
                      {ctrlVal !== null && (
                        <span className="text-[#868E85] ml-1">
                          (ctrl: {ctrlVal >= 0.01 ? ctrlVal.toFixed(3) : ctrlVal.toExponential(1)})
                        </span>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Calibrated Footnote / Legend Reference */}
      <div className="flex flex-wrap items-center justify-between text-[10.5px] font-mono text-[#666E65] pt-1 border-t border-[#EDE8DE]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#286345]" />
            <span>GSH (Reduced)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#8F5C1E]" />
            <span>GSSG (Disulfide)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#4B466D]" />
            <span>NADPH</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#9B332B]" />
            <span>Damage [D]</span>
          </span>
        </div>
        <span>Units: Intracellular mM // Trajectory points: {primaryTraj.length}</span>
      </div>
    </div>
  );
};
