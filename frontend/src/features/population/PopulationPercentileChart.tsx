import React, { useMemo, useState } from 'react';
import type { PopulationPercentileBands } from '../../types/api';

interface Props {
  bands: PopulationPercentileBands;
  title?: string;
  height?: number;
}

type SelectedMetric = 'gsh' | 'damage' | 'nadph';

export const PopulationPercentileChart: React.FC<Props> = ({
  bands,
  title = 'Simulated Population Cohort Distribution Over Time',
  height = 340,
}) => {
  const [metric, setMetric] = useState<SelectedMetric>('gsh');
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const timePoints = bands.time_points_s || [];
  const maxTime_s = timePoints[timePoints.length - 1] || 1;

  // Extract selected bands
  const { p5, p25, p50, p75, p95, label, unit, color } = useMemo(() => {
    switch (metric) {
      case 'damage':
        return {
          p5: bands.damage_p5,
          p25: bands.damage_p25,
          p50: bands.damage_p50,
          p75: bands.damage_p75,
          p95: bands.damage_p95,
          label: 'Cumulative Damage Index [D]',
          unit: '[0, 1]',
          color: '#f43f5e',
        };
      case 'nadph':
        return {
          p5: bands.nadph_p5,
          p25: bands.nadph_p25,
          p50: bands.nadph_p50,
          p75: bands.nadph_p75,
          p95: bands.nadph_p95,
          label: 'Intracellular [NADPH]',
          unit: 'mM',
          color: '#a855f7',
        };
      case 'gsh':
      default:
        return {
          p5: bands.gsh_p5,
          p25: bands.gsh_p25,
          p50: bands.gsh_p50,
          p75: bands.gsh_p75,
          p95: bands.gsh_p95,
          label: 'Reduced Glutathione [GSH]',
          unit: 'mM',
          color: '#10b981',
        };
    }
  }, [bands, metric]);

  // Compute Y bounds
  const { minY, maxY } = useMemo(() => {
    let min = 0;
    let max = 0.05;
    p95.forEach((v) => {
      if (v > max) max = v;
    });
    p5.forEach((v) => {
      if (v < min) min = v;
    });
    return { minY: min, maxY: max * 1.05 };
  }, [p5, p95]);

  const width = 800;
  const padding = { top: 25, right: 30, bottom: 45, left: 60 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const scaleX = (t: number) => padding.left + (t / maxTime_s) * plotWidth;
  const scaleY = (v: number) =>
    padding.top + plotHeight - ((v - minY) / (maxY - minY || 1)) * plotHeight;

  // Build area polygons
  const outerAreaPath = useMemo(() => {
    if (timePoints.length === 0) return '';
    const upper = timePoints.map((t, i) => `${scaleX(t).toFixed(1)},${scaleY(p95[i]).toFixed(1)}`).join(' ');
    const lower = timePoints
      .slice()
      .reverse()
      .map((t, i) => {
        const revIdx = timePoints.length - 1 - i;
        return `${scaleX(t).toFixed(1)},${scaleY(p5[revIdx]).toFixed(1)}`;
      })
      .join(' ');
    return `M ${upper} L ${lower} Z`;
  }, [timePoints, p5, p95, maxY, minY]);

  const innerAreaPath = useMemo(() => {
    if (timePoints.length === 0) return '';
    const upper = timePoints.map((t, i) => `${scaleX(t).toFixed(1)},${scaleY(p75[i]).toFixed(1)}`).join(' ');
    const lower = timePoints
      .slice()
      .reverse()
      .map((t, i) => {
        const revIdx = timePoints.length - 1 - i;
        return `${scaleX(t).toFixed(1)},${scaleY(p25[revIdx]).toFixed(1)}`;
      })
      .join(' ');
    return `M ${upper} L ${lower} Z`;
  }, [timePoints, p25, p75, maxY, minY]);

  const medianPath = useMemo(() => {
    if (timePoints.length === 0) return '';
    return timePoints.reduce((acc, t, i) => {
      const x = scaleX(t).toFixed(1);
      const y = scaleY(p50[i]).toFixed(1);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');
  }, [timePoints, p50, maxY, minY]);

  // Hover state
  const hoveredTime = hoverIndex !== null ? timePoints[hoverIndex] : null;

  return (
    <div className="space-y-3 bg-slate-900/90 rounded-lg border border-slate-800 p-4">
      {/* Header & Metric Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
          <p className="text-xs text-slate-400">
            Median trajectory (p50) with interquartile band (p25–p75) and 90% simulated cohort envelope (p5–p95).
          </p>
        </div>

        {/* Variable Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setMetric('gsh')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              metric === 'gsh' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Glutathione [GSH]
          </button>
          <button
            onClick={() => setMetric('damage')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              metric === 'damage' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Damage Proxy [D]
          </button>
          <button
            onClick={() => setMetric('nadph')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              metric === 'nadph' ? 'bg-purple-950 text-purple-300 border border-purple-800' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NADPH Pool
          </button>
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
            if (normX >= padding.left && normX <= padding.left + plotWidth && timePoints.length > 0) {
              const rel = (normX - padding.left) / plotWidth;
              const idx = Math.min(
                Math.max(0, Math.round(rel * (timePoints.length - 1))),
                timePoints.length - 1
              );
              setHoverIndex(idx);
            } else {
              setHoverIndex(null);
            }
          }}
        >
          {/* Y-Axis Gridlines */}
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
                  {val >= 1 ? val.toFixed(1) : val.toFixed(3)}
                </text>
              </g>
            );
          })}

          {/* X-Axis Gridlines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const t = ratio * maxTime_s;
            const x = scaleX(t);
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
                  {(t / 60).toFixed(0)}m
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
            Simulation Elapsed Time (minutes)
          </text>

          <text
            transform="rotate(-90)"
            x={-(padding.top + plotHeight / 2)}
            y={16}
            textAnchor="middle"
            fill="#94a3b8"
            fontSize="11"
            fontWeight="500"
          >
            {label} ({unit})
          </text>

          {/* Shaded Outer Percentile Interval: p5 to p95 */}
          <path d={outerAreaPath} fill={color} fillOpacity="0.12" />

          {/* Shaded Interquartile Interval: p25 to p75 */}
          <path d={innerAreaPath} fill={color} fillOpacity="0.25" />

          {/* Median Trajectory: p50 */}
          <path d={medianPath} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" />

          {/* Boundary stroke for p5 and p95 */}
          {timePoints.length > 0 && (
            <>
              <path
                d={timePoints
                  .map((t, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(t).toFixed(1)} ${scaleY(p95[i]).toFixed(1)}`)
                  .join(' ')}
                fill="none"
                stroke={color}
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.4"
              />
              <path
                d={timePoints
                  .map((t, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(t).toFixed(1)} ${scaleY(p5[i]).toFixed(1)}`)
                  .join(' ')}
                fill="none"
                stroke={color}
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.4"
              />
            </>
          )}

          {/* Hover Crosshair & Points */}
          {hoverIndex !== null && hoveredTime !== null && (
            <g>
              <line
                x1={scaleX(hoveredTime)}
                y1={padding.top}
                x2={scaleX(hoveredTime)}
                y2={padding.top + plotHeight}
                stroke="#cbd5e1"
                strokeWidth="1.2"
                strokeDasharray="3 3"
              />
              <circle
                cx={scaleX(hoveredTime)}
                cy={scaleY(p50[hoverIndex])}
                r="4.5"
                fill={color}
                stroke="#0f172a"
                strokeWidth="2"
              />
            </g>
          )}
        </svg>

        {/* Hover Tooltip Box */}
        {hoverIndex !== null && hoveredTime !== null && (
          <div className="absolute top-3 right-3 bg-slate-950/95 border border-slate-700/80 rounded-md p-3 shadow-xl text-xs space-y-1.5 pointer-events-none min-w-[210px] backdrop-blur">
            <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1 flex justify-between">
              <span>t = {(hoveredTime / 60).toFixed(1)} min</span>
              <span className="font-mono text-slate-400">({hoveredTime.toFixed(0)}s)</span>
            </div>

            <div className="space-y-1 font-mono text-[11px]">
              <div className="flex justify-between text-slate-400">
                <span>95th percentile:</span>
                <span className="text-slate-200">{p95[hoverIndex].toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>75th percentile:</span>
                <span className="text-slate-200">{p75[hoverIndex].toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-emerald-300 font-bold">
                <span>Median (p50):</span>
                <span>{p50[hoverIndex].toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>25th percentile:</span>
                <span className="text-slate-200">{p25[hoverIndex].toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>5th percentile:</span>
                <span className="text-slate-200">{p5[hoverIndex].toFixed(3)} {unit}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend & Interpretation */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-current rounded-full" style={{ color }} />
            <span>Median (p50)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: color, opacity: 0.25 }} />
            <span>Interquartile range (p25–p75)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: color, opacity: 0.12 }} />
            <span>90% Cohort interval (p5–p95)</span>
          </span>
        </div>
        <span className="italic text-slate-500">
          Sampled over prior enzymatic heterogeneity (G6PD, GR, GPx capacities).
        </span>
      </div>
    </div>
  );
};
