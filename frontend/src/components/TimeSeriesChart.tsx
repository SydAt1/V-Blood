import React, { useMemo, useState } from 'react';
import type { TrajectoryPoint } from '../types/api';

export interface SeriesConfig {
  key: keyof TrajectoryPoint;
  label: string;
  unit: string;
  color: string;
  scale?: number; // Optional visual multiplier for trace readability
}

const DEFAULT_SERIES: SeriesConfig[] = [
  { key: 'gsh_mM', label: 'Reduced Glutathione [GSH]', unit: 'mM', color: '#10b981' },
  { key: 'gssg_mM', label: 'Glutathione Disulfide [GSSG]', unit: 'mM', color: '#f59e0b' },
  { key: 'nadph_mM', label: 'NADPH Pool [NADPH]', unit: 'mM', color: '#a855f7' },
  { key: 'h2o2_mM', label: 'Intracellular [H₂O₂]', unit: 'mM', color: '#06b6d4' },
  { key: 'damage', label: 'Oxidative Damage Index [D]', unit: '[0, 1]', color: '#f43f5e' },
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
  treatmentLabel = 'Treated',
  controlLabel = 'Control (Untreated Baseline)',
  title = 'Intracellular Biochemical Dynamics',
  height = 340,
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

  const width = 800;
  const padding = { top: 25, right: 30, bottom: 45, left: 60 };
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
      <div className="flex flex-col items-center justify-center h-80 rounded-lg border border-dashed border-slate-800 bg-slate-900/40 text-slate-400 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-500 mb-3 font-mono text-lg">
          📈
        </div>
        <div className="text-sm font-medium text-slate-300">No Simulation Trajectory Available</div>
        <div className="text-xs text-slate-500 max-w-sm mt-1">
          Configure chemical compounds, dosage profile, and model version above, then click "Run Simulation" to visualize intracellular dynamics.
        </div>
      </div>
    );
  }

  // Hover position & values
  const hoveredPoint = hoverIndex !== null ? primaryTraj[hoverIndex] : null;
  const hoveredControl = hoverIndex !== null && controlTrajectory.length > hoverIndex ? controlTrajectory[hoverIndex] : null;

  return (
    <div className="space-y-3 bg-slate-900/90 rounded-lg border border-slate-800 p-4">
      {/* Chart Header & Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
          <p className="text-xs text-slate-400">
            Solid line = {treatmentLabel} {controlTrajectory.length > 0 && `• Dashed line = ${controlLabel}`}
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
                className={`px-2.5 py-1 rounded text-xs font-medium border flex items-center gap-1.5 transition-all ${
                  active
                    ? 'bg-slate-800 border-slate-600 text-slate-100 shadow-sm'
                    : 'bg-slate-950/60 border-slate-800 text-slate-500 hover:text-slate-400'
                }`}
                title={`Toggle ${s.label} (${s.unit})`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full inline-block"
                  style={{ backgroundColor: active ? s.color : '#475569' }}
                />
                <span>{s.label.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* SVG Container */}
      <div className="relative">
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
                  stroke="#1e293b"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
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
                  stroke="#1e293b"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={x}
                  y={padding.top + plotHeight + 18}
                  textAnchor="middle"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
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
            fill="#94a3b8"
            fontSize="11"
            fontWeight="500"
          >
            {timeUnit.label}
          </text>

          <text
            transform={`rotate(-90)`}
            x={-(padding.top + plotHeight / 2)}
            y={16}
            textAnchor="middle"
            fill="#94a3b8"
            fontSize="11"
            fontWeight="500"
          >
            Concentration (mM) / Damage Index
          </text>

          {/* Control Trajectory Paths (Dashed) */}
          {controlTrajectory.length > 0 &&
            DEFAULT_SERIES.map((s) => {
              if (!activeSeries[s.key as string]) return null;
              const pathD = buildPath(controlTrajectory, s.key);
              return (
                <path
                  key={`ctrl-${s.key as string}`}
                  d={pathD}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="1.5"
                  strokeDasharray="5 4"
                  opacity="0.6"
                />
              );
            })}

          {/* Treatment Trajectory Paths (Solid) */}
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

          {/* Interactive Hover Crosshair */}
          {hoveredPoint && (
            <g>
              <line
                x1={scaleX(hoveredPoint.t_s)}
                y1={padding.top}
                x2={scaleX(hoveredPoint.t_s)}
                y2={padding.top + plotHeight}
                stroke="#e2e8f0"
                strokeWidth="1.2"
                strokeDasharray="3 3"
              />
              {DEFAULT_SERIES.map((s) => {
                if (!activeSeries[s.key as string]) return null;
                const val = Number(hoveredPoint[s.key]) || 0;
                return (
                  <circle
                    key={`dot-${s.key as string}`}
                    cx={scaleX(hoveredPoint.t_s)}
                    cy={scaleY(val)}
                    r="4"
                    fill={s.color}
                    stroke="#0f172a"
                    strokeWidth="1.5"
                  />
                );
              })}
            </g>
          )}
        </svg>

        {/* Floating Tooltip Card */}
        {hoveredPoint && (
          <div
            className="absolute top-3 right-3 bg-slate-950/95 border border-slate-700/80 rounded-md p-2.5 shadow-xl text-xs space-y-1.5 pointer-events-none min-w-[210px] backdrop-blur"
          >
            <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1 flex justify-between">
              <span>t = {(hoveredPoint.t_s / timeUnit.divisor).toFixed(timeUnit.precision)} {timeUnit.label.split(' ')[1].replace(/[()]/g, '')}</span>
              <span className="text-slate-400 font-mono">({hoveredPoint.t_s.toFixed(0)}s)</span>
            </div>

            <div className="space-y-1">
              {DEFAULT_SERIES.map((s) => {
                if (!activeSeries[s.key as string]) return null;
                const trtVal = Number(hoveredPoint[s.key]) || 0;
                const ctrlVal = hoveredControl ? Number(hoveredControl[s.key]) : null;

                return (
                  <div key={s.key as string} className="flex items-center justify-between gap-3 text-[11px]">
                    <span className="flex items-center gap-1.5" style={{ color: s.color }}>
                      <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: s.color }} />
                      <span>{s.label.split(' ')[0]}:</span>
                    </span>
                    <span className="font-mono text-slate-200">
                      {trtVal >= 0.01 ? trtVal.toFixed(3) : trtVal.toExponential(2)} {s.unit}
                      {ctrlVal !== null && (
                        <span className="text-slate-500 ml-1">
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
    </div>
  );
};
