import React, { useEffect, useRef, useState } from 'react';
import type { VisualFrame } from '../../types/api';
import { StressBadge } from '../../components/StressBadge';
import { AlertBox } from '../../components/AlertBox';
import { getVisualTrajectory, subscribeVisualFrames } from '../../api/client';
import { Pause, Play, Radio, RotateCcw, X } from 'lucide-react';

interface Props {
  runId: string | null;
  onClose?: () => void;
}

export const ErythrocyteViewer: React.FC<Props> = ({ runId, onClose }) => {
  const [frames, setFrames] = useState<VisualFrame[]>([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  const animationRef = useRef<number | null>(null);
  const streamCleanupRef = useRef<(() => void) | null>(null);

  // Fetch static frames when runId changes
  useEffect(() => {
    if (!runId) return;

    let mounted = true;
    setLoading(true);
    setError(null);
    setIsPlaying(false);
    setCurrentFrameIndex(0);

    getVisualTrajectory(runId, 250)
      .then((res) => {
        if (!mounted) return;
        setFrames(res.frames);
        setLoading(false);
        if (res.frames.length > 0) {
          setIsPlaying(true);
        }
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err.detail || 'Failed to load visual animation frames.');
        setLoading(false);
      });

    return () => {
      mounted = false;
      if (streamCleanupRef.current) {
        streamCleanupRef.current();
        streamCleanupRef.current = null;
      }
    };
  }, [runId]);

  // Animation Loop
  useEffect(() => {
    if (!isPlaying || frames.length === 0) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      return;
    }

    let lastTime = performance.now();
    const frameIntervalMs = 1000 / (30 * playbackSpeed);

    const step = (now: number) => {
      if (now - lastTime >= frameIntervalMs) {
        lastTime = now;
        setCurrentFrameIndex((prev) => {
          if (prev >= frames.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }
      animationRef.current = requestAnimationFrame(step);
    };

    animationRef.current = requestAnimationFrame(step);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    };
  }, [isPlaying, frames, playbackSpeed]);

  // Connect to real-time SSE stream
  const handleStartSSEStream = () => {
    if (!runId) return;

    if (streamCleanupRef.current) {
      streamCleanupRef.current();
      streamCleanupRef.current = null;
    }

    setIsStreaming(true);
    setIsPlaying(false);
    setFrames([]);
    setCurrentFrameIndex(0);

    const cleanup = subscribeVisualFrames(
      runId,
      (newFrame) => {
        setFrames((prev) => {
          const next = [...prev, newFrame];
          setCurrentFrameIndex(next.length - 1);
          return next;
        });
      },
      () => {
        setIsStreaming(false);
      },
      (err) => {
        setIsStreaming(false);
        setError(err.message);
      },
      150
    );

    streamCleanupRef.current = cleanup;
  };

  const currentFrame = frames[currentFrameIndex] || null;

  if (!runId) {
    return (
      <div className="bg-slate-900/90 rounded-lg border border-slate-800 p-8 text-center text-slate-400">
        <p className="text-sm">Select or execute a simulation run to view animated erythrocyte dynamics.</p>
      </div>
    );
  }

  // Cytosolic color calculation based on normalized biochemical state
  const getCytosolColor = (f: VisualFrame | null) => {
    if (!f) return '#dc2626';
    if (f.cell_state === 'healthy') return '#dc2626';
    if (f.cell_state === 'stressed') return '#d97706';
    if (f.cell_state === 'severely_stressed') return '#ea580c';
    return '#7f1d1d'; // lysis_risk
  };

  const getPallorOpacity = (f: VisualFrame | null) => {
    if (!f) return 0.35;
    // As damage rises, central pallor fades or becomes disordered
    return Math.max(0.15, 0.45 - f.damage * 0.3);
  };

  return (
    <div className="bg-slate-900/95 rounded-xl border border-slate-800 p-5 space-y-5 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Erythrocyte State Playback</span>
            {isStreaming && (
              <span className="text-xs font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800 flex items-center gap-1.5 animate-pulse">
                <Radio className="w-3.5 h-3.5" />
                <span>Live SSE Stream</span>
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Model-derived biochemical animation mapping normalized GSH, NADPH, and oxidative stress index D.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleStartSSEStream}
            disabled={isStreaming || loading}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Radio className="w-3.5 h-3.5 text-rose-400" />
            <span>Stream via SSE</span>
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800"
              title="Close playback viewer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Model Boundary Notice */}
      <AlertBox type="disclaimer" title="Scientific Boundary: Illustrative Morphology Notice">
        This visualization reflects <strong>modeled cytosolic biochemistry</strong> (GSH, NADPH, D).
        Physical membrane deformations (echinocytosis, spiculation, crenation, or swelling) are{' '}
        <strong>NOT simulated or predicted</strong> by the ordinary differential equations.
      </AlertBox>

      {error && <AlertBox type="error" title="Playback Error">{error}</AlertBox>}

      {/* Main Canvas + Metrics Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* SVG Erythrocyte Graphic */}
        <div className="md:col-span-6 flex flex-col items-center justify-center p-6 bg-slate-950/80 rounded-xl border border-slate-800 relative min-h-[300px]">
          <svg viewBox="0 0 320 320" className="w-64 h-64 select-none filter drop-shadow-2xl">
            <defs>
              {/* Radial gradient representing biconcave disc lighting */}
              <radialGradient id="rbcRim" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ffffff" stopOpacity={getPallorOpacity(currentFrame)} />
                <stop offset="45%" stopColor={getCytosolColor(currentFrame)} stopOpacity="0.85" />
                <stop offset="90%" stopColor={getCytosolColor(currentFrame)} stopOpacity="1" />
                <stop offset="100%" stopColor="#450a0a" stopOpacity="0.95" />
              </radialGradient>

              {/* Central pallor shadow */}
              <radialGradient id="pallorShadow" cx="50%" cy="50%" r="40%">
                <stop offset="0%" stopColor="#000000" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#000000" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Erythrocyte Body */}
            <circle
              cx="160"
              cy="160"
              r="135"
              fill="url(#rbcRim)"
              stroke={currentFrame?.cell_state === 'lysis_risk' ? '#ef4444' : '#7f1d1d'}
              strokeWidth={currentFrame?.cell_state === 'lysis_risk' ? '3.5' : '2'}
              strokeDasharray={currentFrame?.cell_state === 'lysis_risk' ? '6 4' : 'none'}
              className="transition-all duration-150"
            />

            {/* Central Pallor (Biconcave Impression) */}
            <ellipse
              cx="160"
              cy="160"
              rx="65"
              ry="58"
              fill="url(#pallorShadow)"
              className="transition-all duration-200"
            />

            {/* Pulse Indicator on Lysis Risk */}
            {currentFrame?.cell_state === 'lysis_risk' && (
              <circle
                cx="160"
                cy="160"
                r="142"
                fill="none"
                stroke="#ef4444"
                strokeWidth="1.5"
                opacity="0.6"
                className="animate-ping origin-center"
              />
            )}
          </svg>

          {/* Current Cell State Label */}
          <div className="mt-4 flex items-center gap-2">
            <span className="text-xs text-slate-400">State:</span>
            {currentFrame && <StressBadge state={currentFrame.cell_state} />}
          </div>
        </div>

        {/* Real-time State Indicators */}
        <div className="md:col-span-6 space-y-4 bg-slate-950/60 p-5 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Current Simulation Timestamp
            </span>
            <span className="text-base font-mono font-bold text-slate-100">
              {currentFrame ? (
                <>
                  {currentFrame.t_s.toFixed(0)} s{' '}
                  <span className="text-xs text-slate-400 font-sans">
                    ({(currentFrame.t_s / 60).toFixed(1)} min)
                  </span>
                </>
              ) : (
                '0 s'
              )}
            </span>
          </div>

          {/* Normalized GSH Meter */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400 font-medium">Normalized GSH (ref: 2.50 mM)</span>
              <span className="font-mono text-emerald-400 font-bold">
                {currentFrame ? (currentFrame.normalized_gsh * 100).toFixed(0) : 100}%
              </span>
            </div>
            <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.normalized_gsh || 1) * 100)}%` }}
              />
            </div>
          </div>

          {/* Normalized NADPH Meter */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400 font-medium">Normalized NADPH Pool (ref: 30 µM)</span>
              <span className="font-mono text-purple-400 font-bold">
                {currentFrame ? (currentFrame.normalized_nadph * 100).toFixed(0) : 100}%
              </span>
            </div>
            <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-purple-500 h-full rounded-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.normalized_nadph || 1) * 100)}%` }}
              />
            </div>
          </div>

          {/* Oxidative Damage Index D */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400 font-medium">Oxidative Damage Index [D]</span>
              <span className="font-mono text-rose-400 font-bold">
                {currentFrame ? currentFrame.damage.toFixed(3) : '0.000'}
              </span>
            </div>
            <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
              <div
                className="bg-rose-500 h-full rounded-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.damage || 0) * 100)}%` }}
              />
            </div>
          </div>

          {/* Hemolysis Proxy Risk */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
            <span className="text-slate-400">Estimated Lysis Proxy:</span>
            <span className="font-mono text-slate-200 font-semibold">
              {currentFrame ? currentFrame.hemolysis_pct.toFixed(1) : 0.0}%
            </span>
          </div>
        </div>
      </div>

      {/* Playback Controls & Timeline Slider */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
        {/* Timeline Slider */}
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={Math.max(0, frames.length - 1)}
            value={currentFrameIndex}
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentFrameIndex(parseInt(e.target.value, 10));
            }}
            className="w-full accent-rose-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
          />
          <div className="flex justify-between text-[11px] font-mono text-slate-500">
            <span>0 s</span>
            <span>
              Frame {currentFrameIndex + 1} / {frames.length}
            </span>
            <span>{frames[frames.length - 1]?.t_s.toFixed(0) || 0} s</span>
          </div>
        </div>

        {/* Buttons Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-2">
            {/* Play / Pause */}
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              disabled={frames.length === 0}
              className="p-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow font-medium transition-colors disabled:opacity-50"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
            </button>

            {/* Restart */}
            <button
              onClick={() => {
                setCurrentFrameIndex(0);
                setIsPlaying(true);
              }}
              disabled={frames.length === 0}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-50"
              title="Restart from t=0"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Speed:</span>
            {[1, 2, 5, 10].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-2 py-1 rounded text-xs font-mono transition-colors ${
                  playbackSpeed === spd
                    ? 'bg-slate-800 text-slate-100 border border-slate-700 font-bold'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
