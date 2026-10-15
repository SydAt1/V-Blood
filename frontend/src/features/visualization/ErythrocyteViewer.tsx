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
      <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-8 text-center text-[#767D75]">
        <p className="text-sm font-editorial">
          Select or execute a simulation run to view animated erythrocyte dynamics.
        </p>
      </div>
    );
  }

  // Cytosolic color calculation based on biological red cell state
  const getCytosolColor = (f: VisualFrame | null) => {
    if (!f) return '#9B332B';
    if (f.cell_state === 'healthy') return '#A53830';
    if (f.cell_state === 'stressed') return '#B85526';
    if (f.cell_state === 'severely_stressed') return '#8A321B';
    return '#691F18'; // lysis_risk
  };

  const getPallorOpacity = (f: VisualFrame | null) => {
    if (!f) return 0.45;
    return Math.max(0.2, 0.5 - f.damage * 0.3);
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#D8D1C2] p-5 space-y-5 shadow-[3px_3px_0px_0px_rgba(24,27,24,0.08)]">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D8D1C2] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
              PLATE 02 //
            </span>
            <h2 className="font-editorial text-lg font-bold text-[#181B18] flex items-center gap-2">
              <span>Erythrocyte State Playback</span>
              {isStreaming && (
                <span className="text-[10px] font-mono text-[#284431] bg-[#EDF3EE] px-2 py-0.5 border border-[#BCD0C1] flex items-center gap-1.5 animate-pulse">
                  <Radio className="w-3 h-3 text-[#3E5C46]" />
                  <span>Live SSE Stream</span>
                </span>
              )}
            </h2>
          </div>
          <p className="text-xs text-[#666E65] mt-0.5 font-sans">
            Model-derived biochemical animation mapping normalized GSH, NADPH, and oxidative stress index D.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleStartSSEStream}
            disabled={isStreaming || loading}
            className="px-3 py-1.5 text-xs font-mono font-medium bg-[#FFFFFF] hover:bg-[#FAF7F2] text-[#181B18] border border-[#B5AC99] flex items-center gap-1.5 transition-colors disabled:opacity-50 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]"
          >
            <Radio className="w-3.5 h-3.5 text-[#9B332B]" />
            <span>Stream via SSE</span>
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-[#767D75] hover:text-[#181B18] hover:bg-[#F2ECE1] border border-[#D8D1C2] transition-colors"
              title="Close playback viewer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Model Boundary Notice - Preserving exact required text for tests */}
      <AlertBox type="disclaimer" title="Scientific Boundary: Illustrative Morphology Notice">
        This visualization reflects <strong>modeled cytosolic biochemistry</strong> (GSH, NADPH, D).
        Physical membrane deformations (echinocytosis, spiculation, crenation, or swelling) are{' '}
        <strong>NOT simulated or predicted</strong> by the ordinary differential equations.
      </AlertBox>

      {error && <AlertBox type="error" title="Playback Error">{error}</AlertBox>}

      {/* Main Canvas + Metrics Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* SVG Erythrocyte Scientific Illustration Plate */}
        <div className="md:col-span-6 flex flex-col items-center justify-center p-6 bg-[#FAF8F3] border border-[#D8D1C2] relative min-h-[300px]">
          <div className="absolute top-2 left-3 font-mono text-[9px] text-[#868E85] uppercase tracking-wider">
            FIG. II — BICONCAVE ERYTHROCYTE SECTION
          </div>

          <svg viewBox="0 0 320 320" className="w-60 h-60 select-none filter drop-shadow-sm">
            <defs>
              {/* Radial gradient representing anatomical biconcave disc lighting */}
              <radialGradient id="rbcRimParchment" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#FFFFFF" stopOpacity={getPallorOpacity(currentFrame)} />
                <stop offset="42%" stopColor={getCytosolColor(currentFrame)} stopOpacity="0.85" />
                <stop offset="85%" stopColor={getCytosolColor(currentFrame)} stopOpacity="1" />
                <stop offset="100%" stopColor="#4A1612" stopOpacity="0.95" />
              </radialGradient>

              {/* Central pallor shadow */}
              <radialGradient id="pallorShadowParchment" cx="50%" cy="50%" r="42%">
                <stop offset="0%" stopColor="#2A1B18" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#2A1B18" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Erythrocyte Body */}
            <circle
              cx="160"
              cy="160"
              r="135"
              fill="url(#rbcRimParchment)"
              stroke={currentFrame?.cell_state === 'lysis_risk' ? '#8F251E' : '#5A1E1A'}
              strokeWidth={currentFrame?.cell_state === 'lysis_risk' ? '3.5' : '1.5'}
              strokeDasharray={currentFrame?.cell_state === 'lysis_risk' ? '5 4' : 'none'}
              className="transition-all duration-150"
            />

            {/* Central Pallor (Biconcave Impression) */}
            <ellipse
              cx="160"
              cy="160"
              rx="66"
              ry="58"
              fill="url(#pallorShadowParchment)"
              className="transition-all duration-200"
            />

            {/* Micro Calibration Calipers */}
            <line x1="20" y1="160" x2="25" y2="160" stroke="#868E85" strokeWidth="1" />
            <line x1="295" y1="160" x2="300" y2="160" stroke="#868E85" strokeWidth="1" />
            <line x1="160" y1="20" x2="160" y2="25" stroke="#868E85" strokeWidth="1" />
            <line x1="160" y1="295" x2="160" y2="300" stroke="#868E85" strokeWidth="1" />
          </svg>

          {/* Current Cell State Label */}
          <div className="mt-4 flex items-center gap-2">
            <span className="text-xs font-mono text-[#767D75]">State Classification:</span>
            {currentFrame && <StressBadge state={currentFrame.cell_state} />}
          </div>
        </div>

        {/* Real-time State Indicators Deck */}
        <div className="md:col-span-6 space-y-4 bg-[#FAF7F2] p-5 border border-[#D8D1C2]">
          <div className="flex items-center justify-between border-b border-[#D8D1C2] pb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#767D75]">
              Current Simulation Timestamp
            </span>
            <span className="text-base font-mono font-bold text-[#181B18]">
              {currentFrame ? (
                <>
                  {currentFrame.t_s.toFixed(0)} s{' '}
                  <span className="text-xs text-[#767D75] font-sans">
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
              <span className="text-[#383E38] font-medium font-sans">Normalized GSH (ref: 2.50 mM)</span>
              <span className="font-mono text-[#286345] font-bold">
                {currentFrame ? (currentFrame.normalized_gsh * 100).toFixed(0) : 100}%
              </span>
            </div>
            <div className="w-full bg-[#EDE8DE] h-2 border border-[#D8D1C2]">
              <div
                className="bg-[#286345] h-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.normalized_gsh || 1) * 100)}%` }}
              />
            </div>
          </div>

          {/* Normalized NADPH Meter */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-[#383E38] font-medium font-sans">Normalized NADPH Pool (ref: 30 µM)</span>
              <span className="font-mono text-[#4B466D] font-bold">
                {currentFrame ? (currentFrame.normalized_nadph * 100).toFixed(0) : 100}%
              </span>
            </div>
            <div className="w-full bg-[#EDE8DE] h-2 border border-[#D8D1C2]">
              <div
                className="bg-[#4B466D] h-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.normalized_nadph || 1) * 100)}%` }}
              />
            </div>
          </div>

          {/* Oxidative Damage Index D */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-[#383E38] font-medium font-sans">Oxidative Damage Index [D]</span>
              <span className="font-mono text-[#9B332B] font-bold">
                {currentFrame ? currentFrame.damage.toFixed(3) : '0.000'}
              </span>
            </div>
            <div className="w-full bg-[#EDE8DE] h-2 border border-[#D8D1C2]">
              <div
                className="bg-[#9B332B] h-full transition-all duration-75"
                style={{ width: `${Math.min(100, (currentFrame?.damage || 0) * 100)}%` }}
              />
            </div>
          </div>

          {/* Hemolysis Proxy Risk */}
          <div className="flex items-center justify-between pt-2 border-t border-[#D8D1C2] text-xs">
            <span className="text-[#666E65] font-mono">Estimated Lysis Proxy:</span>
            <span className="font-mono text-[#181B18] font-bold">
              {currentFrame ? currentFrame.hemolysis_pct.toFixed(1) : 0.0}%
            </span>
          </div>
        </div>
      </div>

      {/* Playback Controls & Timeline Slider */}
      <div className="bg-[#FAF7F2] p-4 border border-[#D8D1C2] space-y-3">
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
            className="w-full accent-[#9B332B] cursor-pointer h-1.5 bg-[#EDE8DE]"
          />
          <div className="flex justify-between text-[10.5px] font-mono text-[#767D75]">
            <span>0 s</span>
            <span className="font-semibold text-[#181B18]">
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
              className="px-3 py-1.5 bg-[#9B332B] hover:bg-[#802821] text-white text-xs font-mono font-semibold transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.15)] disabled:opacity-50 flex items-center gap-1.5"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isPlaying ? 'Pause' : 'Play'}</span>
            </button>

            {/* Restart */}
            <button
              onClick={() => {
                setCurrentFrameIndex(0);
                setIsPlaying(true);
              }}
              disabled={frames.length === 0}
              className="p-1.5 bg-[#FFFFFF] hover:bg-[#FAF7F2] text-[#484E48] border border-[#B5AC99] transition-colors disabled:opacity-50"
              title="Restart from t=0"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 text-xs font-mono text-[#767D75]">
            <span className="mr-1">RATE:</span>
            {[1, 2, 5, 10].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-2 py-0.5 border text-xs font-mono transition-colors ${
                  playbackSpeed === spd
                    ? 'bg-[#181B18] text-white border-[#181B18] font-bold shadow-[1px_1px_0px_0px_rgba(24,27,24,0.1)]'
                    : 'bg-[#FFFFFF] border-[#D8D1C2] text-[#767D75] hover:text-[#181B18]'
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
