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
  height = 360,
}) => {
  const [metric, setMetric] = useState<SelectedMetric>('gsh');
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const timePoints = bands?.time_points_s || [];
  const maxTime_s = timePoints[timePoints.length - 1] || 1;

  // Extract selected bands safely
  const { p5, p25, p50, p75, p95, label, unit, color } = useMemo(() => {
    switch (metric) {
      case 'damage':
        return {
          p5: bands?.damage_p5 || [],
          p25: bands?.damage_p25 || [],
          p50: bands?.damage_p50 || [],
          p75: bands?.damage_p75 || [],
          p95: bands?.damage_p95 || [],
          label: 'Cumulative Damage Index [D]',
          unit: '[0, 1]',
          color: '#9B332B', // Oxidized crimson
        };
      case 'nadph':
        return {
          p5: bands?.nadph_p5 || [],
          p25: bands?.nadph_p25 || [],
          p50: bands?.nadph_p50 || [],
          p75: bands?.nadph_p75 || [],
          p95: bands?.nadph_p95 || [],
          label: 'Intracellular [NADPH]',
          unit: 'mM',
          color: '#4B466D', // Slate indigo
        };
      case 'gsh':
      default:
        return {
          p5: bands?.gsh_p5 || [],
          p25: bands?.gsh_p25 || [],
          p50: bands?.gsh_p50 || [],
          p75: bands?.gsh_p75 || [],
          p95: bands?.gsh_p95 || [],
          label: 'Reduced Glutathione [GSH]',
          unit: 'mM',
          color: '#286345', // Deep physiological sage
        };
    }
  }, [bands, metric]);

  // Compute Y bounds safely
  const { minY, maxY } = useMemo(() => {
    let min = 0;
    let max = 0.05;
    (p95 || []).forEach((v) => {
      if (typeof v === 'number' && v > max) max = v;
    });
    (p5 || []).forEach((v) => {
      if (typeof v === 'number' && v < min) min = v;
    });
    return { minY: min, maxY: max * 1.05 };
  }, [p5, p95]);

  const width = 860;
  const padding = { top: 25, right: 35, bottom: 45, left: 65 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const scaleX = (t: number) => padding.left + (t / maxTime_s) * plotWidth;
  const scaleY = (v: number) =>
    padding.top + plotHeight - ((v - minY) / (maxY - minY || 1)) * plotHeight;

  // Build area polygons
  const outerAreaPath = useMemo(() => {
    if (!timePoints || timePoints.length === 0 || !p95 || !p5) return '';
    const upper = timePoints.map((t, i) => `${scaleX(t).toFixed(1)},${scaleY(p95[i] || 0).toFixed(1)}`).join(' ');
    const lower = timePoints
      .slice()
      .reverse()
      .map((t, i) => {
        const revIdx = timePoints.length - 1 - i;
        return `${scaleX(t).toFixed(1)},${scaleY(p5[revIdx] || 0).toFixed(1)}`;
      })
      .join(' ');
    return `M ${upper} L ${lower} Z`;
  }, [timePoints, p5, p95, maxY, minY]);

  const innerAreaPath = useMemo(() => {
    if (!timePoints || timePoints.length === 0 || !p75 || !p25) return '';
    const upper = timePoints.map((t, i) => `${scaleX(t).toFixed(1)},${scaleY(p75[i] || 0).toFixed(1)}`).join(' ');
    const lower = timePoints
      .slice()
      .reverse()
      .map((t, i) => {
        const revIdx = timePoints.length - 1 - i;
        return `${scaleX(t).toFixed(1)},${scaleY(p25[revIdx] || 0).toFixed(1)}`;
      })
      .join(' ');
    return `M ${upper} L ${lower} Z`;
  }, [timePoints, p25, p75, maxY, minY]);

  const medianPath = useMemo(() => {
    if (!timePoints || timePoints.length === 0 || !p50) return '';
    return timePoints.reduce((acc, t, i) => {
      const x = scaleX(t).toFixed(1);
      const y = scaleY(p50[i] || 0).toFixed(1);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');
  }, [timePoints, p50, maxY, minY]);

  // Hover state
  const hoveredTime = hoverIndex !== null && timePoints ? timePoints[hoverIndex] : null;

  return (
    <div className="space-y-3 bg-[#FFFFFF] border border-[#D8D1C2] p-4 shadow-[2px_2px_0px_0px_rgba(24,27,24,0.08)]">
      {/* Header & Metric Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D8D1C2] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9.5px] uppercase tracking-wider text-[#767D75]">
              COHORT SPREAD //
            </span>
            <h3 className="font-editorial text-base font-bold text-[#181B18] tracking-tight">
              {title}
            </h3>
          </div>
          <p className="text-xs text-[#666E65] font-sans mt-0.5">
            Median trajectory (p50) with interquartile band (p25–p75) and 90% simulated cohort envelope (p5–p95).
          </p>
        </div>

        {/* Variable Channel Switcher */}
        <div className="flex items-center gap-1.5 bg-[#FAF7F2] p-1 border border-[#D8D1C2]">
          <button
            onClick={() => setMetric('gsh')}
            className={`px-3 py-1 text-xs font-mono transition-colors border ${
              metric === 'gsh'
                ? 'bg-[#FFFFFF] text-[#286345] border-[#286345] font-bold shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]'
                : 'bg-transparent border-transparent text-[#666E65] hover:text-[#181B18]'
            }`}
          >
            Glutathione [GSH]
          </button>
          <button
            onClick={() => setMetric('damage')}
            className={`px-3 py-1 text-xs font-mono transition-colors border ${
              metric === 'damage'
                ? 'bg-[#FFFFFF] text-[#9B332B] border-[#9B332B] font-bold shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]'
                : 'bg-transparent border-transparent text-[#666E65] hover:text-[#181B18]'
            }`}
          >
            Damage Proxy [D]
          </button>
          <button
            onClick={() => setMetric('nadph')}
            className={`px-3 py-1 text-xs font-mono transition-colors border ${
              metric === 'nadph'
                ? 'bg-[#FFFFFF] text-[#4B466D] border-[#4B466D] font-bold shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]'
                : 'bg-transparent border-transparent text-[#666E65] hover:text-[#181B18]'
            }`}
          >
            NADPH Pool
          </button>
        </div>
      </div>

      {/* SVG Container */}
      <div className="relative bg-[#FCFBF9] border border-[#EDE8DE]">
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
            fill="#484E48"
            fontSize="10"
            fontFamily="'Plus Jakarta Sans', sans-serif"
            fontWeight="600"
            letterSpacing="0.02em"
          >
            SIMULATION ELAPSED TIME (MINUTES)
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
            {label.toUpperCase()} ({unit})
          </text>

          {/* Shaded Outer Percentile Interval: p5 to p95 */}
          <path d={outerAreaPath} fill={color} fillOpacity="0.10" />

          {/* Shaded Interquartile Interval: p25 to p75 */}
          <path d={innerAreaPath} fill={color} fillOpacity="0.22" />

          {/* Median Trajectory: p50 */}
          <path d={medianPath} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" />

          {/* Boundary stroke for p5 and p95 */}
          {timePoints.length > 0 && p95 && p5 && (
            <>
              <path
                d={timePoints
                  .map((t, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(t).toFixed(1)} ${scaleY(p95[i] || 0).toFixed(1)}`)
                  .join(' ')}
                fill="none"
                stroke={color}
                strokeWidth="1"
                strokeDasharray="3 2"
                opacity="0.45"
              />
              <path
                d={timePoints
                  .map((t, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(t).toFixed(1)} ${scaleY(p5[i] || 0).toFixed(1)}`)
                  .join(' ')}
                fill="none"
                stroke={color}
                strokeWidth="1"
                strokeDasharray="3 2"
                opacity="0.45"
              />
            </>
          )}

          {/* Hover Crosshair & Data Dot */}
          {hoverIndex !== null && hoveredTime !== null && p50 && (
            <g>
              <line
                x1={scaleX(hoveredTime)}
                y1={padding.top}
                x2={scaleX(hoveredTime)}
                y2={padding.top + plotHeight}
                stroke="#181B18"
                strokeWidth="1"
                strokeDasharray="3 2"
              />
              <circle
                cx={scaleX(hoveredTime)}
                cy={scaleY(p50[hoverIndex] || 0)}
                r="4"
                fill={color}
                stroke="#FFFFFF"
                strokeWidth="2"
              />
            </g>
          )}
        </svg>

        {/* Hover Tooltip Box */}
        {hoverIndex !== null && hoveredTime !== null && p50 && p95 && p75 && p25 && p5 && (
          <div className="absolute top-3 right-3 bg-[#FFFFFF] border border-[#181B18] p-3 shadow-[3px_3px_0px_0px_rgba(24,27,24,0.15)] text-xs space-y-1.5 pointer-events-none min-w-[210px]">
            <div className="font-mono text-[10px] text-[#484E48] border-b border-[#D8D1C2] pb-1 flex justify-between uppercase">
              <span>t = {(hoveredTime / 60).toFixed(1)} min</span>
              <span className="text-[#868E85]">({hoveredTime.toFixed(0)}s)</span>
            </div>

            <div className="space-y-1 font-mono text-[11px]">
              <div className="flex justify-between text-[#767D75]">
                <span>95th percentile:</span>
                <span className="text-[#181B18]">{(p95[hoverIndex] || 0).toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-[#767D75]">
                <span>75th percentile:</span>
                <span className="text-[#181B18]">{(p75[hoverIndex] || 0).toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between font-bold" style={{ color }}>
                <span>Median (p50):</span>
                <span>{(p50[hoverIndex] || 0).toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-[#767D75]">
                <span>25th percentile:</span>
                <span className="text-[#181B18]">{(p25[hoverIndex] || 0).toFixed(3)} {unit}</span>
              </div>
              <div className="flex justify-between text-[#767D75]">
                <span>5th percentile:</span>
                <span className="text-[#181B18]">{(p5[hoverIndex] || 0).toFixed(3)} {unit}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend & Calibration Reference */}
      <div className="flex flex-wrap items-center justify-between text-[10.5px] font-mono text-[#666E65] bg-[#FAF8F3] p-2.5 border border-[#EDE8DE]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-current rounded-none" style={{ color }} />
            <span className="font-semibold text-[#181B18]">Median (p50)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-2 border border-[#B5AC99]" style={{ backgroundColor: color, opacity: 0.22 }} />
            <span>Interquartile (p25–p75)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-2 border border-[#B5AC99]" style={{ backgroundColor: color, opacity: 0.10 }} />
            <span>90% Envelope (p5–p95)</span>
          </span>
        </div>
        <span className="italic text-[#868E85]">
          Sampled over prior enzymatic heterogeneity (G6PD, GR, GPx capacities).
        </span>
      </div>
    </div>
  );
};
