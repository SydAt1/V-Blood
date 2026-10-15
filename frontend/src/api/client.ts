/**
 * Typed API Client for V-Blood Mechanistic Backend.
 * Uses VITE_API_BASE_URL (defaults to empty string for relative proxying in dev).
 */

import type {
  CohortInterpretationRequest,
  CohortInterpretationResponse,
  CompoundResponse,
  HealthResponse,
  InterpretationStatusResponse,
  ModelDetailResponse,
  PlaygroundInterpretationRequest,
  PlaygroundInterpretationResponse,
  PopulationRequest,
  PopulationResult,
  ScenarioRequest,
  ScenarioRunResponse,
  VisualFrame,
  VisualTrajectoryResponse,
} from '../types/api';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ''
).replace(/\/$/, '');

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...options.headers,
      },
    });

    if (!res.ok) {
      let errorMessage = `HTTP ${res.status} ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (typeof errorJson.detail === 'string') {
          errorMessage = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorMessage = errorJson.detail
            .map((d: any) => `${d.loc?.join('.') || 'param'}: ${d.msg}`)
            .join('; ');
        }
      } catch {
        // Body was not JSON
      }
      throw new ApiError(res.status, errorMessage);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    if (err.name === 'AbortError') {
      throw new ApiError(0, 'Simulation request was aborted by user.');
    }
    throw new ApiError(
      0,
      `Cannot connect to simulation backend at ${API_BASE_URL || 'local server'}. Please ensure the V-Blood API server is running.`
    );
  }
}

/* ------------------------------------------------------------------ */
/* Endpoint Methods                                                   */
/* ------------------------------------------------------------------ */

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

export async function getModels(): Promise<ModelDetailResponse[]> {
  return apiFetch<ModelDetailResponse[]>('/models');
}

export async function getCompounds(): Promise<CompoundResponse[]> {
  return apiFetch<CompoundResponse[]>('/compounds');
}

export async function getCompound(id: string): Promise<CompoundResponse> {
  return apiFetch<CompoundResponse>(`/compounds/${encodeURIComponent(id)}`);
}

export async function runScenario(
  request: ScenarioRequest,
  signal?: AbortSignal
): Promise<ScenarioRunResponse> {
  return apiFetch<ScenarioRunResponse>('/scenarios', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}

export async function getScenario(runId: string): Promise<ScenarioRunResponse> {
  return apiFetch<ScenarioRunResponse>(`/scenarios/${encodeURIComponent(runId)}`);
}

export async function runPopulationScenario(
  request: PopulationRequest,
  signal?: AbortSignal
): Promise<PopulationResult> {
  return apiFetch<PopulationResult>('/scenarios/population', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}

export async function getVisualTrajectory(
  runId: string,
  maxFrames: number = 300
): Promise<VisualTrajectoryResponse> {
  return apiFetch<VisualTrajectoryResponse>(
    `/scenarios/${encodeURIComponent(runId)}/visual?max_frames=${maxFrames}`
  );
}

/**
 * Connects to Server-Sent Events (SSE) stream for real-time visual frame playback.
 * Disconnects automatically on stream completion or error.
 */
export function subscribeVisualFrames(
  runId: string,
  onFrame: (frame: VisualFrame) => void,
  onComplete: () => void,
  onError: (err: Error) => void,
  maxFrames: number = 200
): () => void {
  const url = `${API_BASE_URL}/scenarios/${encodeURIComponent(runId)}/stream?max_frames=${maxFrames}`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener('frame', (event) => {
    try {
      const frame: VisualFrame = JSON.parse(event.data);
      onFrame(frame);
    } catch (e: any) {
      onError(e);
    }
  });

  eventSource.addEventListener('complete', () => {
    eventSource.close();
    onComplete();
  });

  eventSource.onerror = () => {
    eventSource.close();
    onError(new Error('Visual frame stream connection closed or failed.'));
  };

  return () => {
    eventSource.close();
  };
}

/* ------------------------------------------------------------------ */
/* Milestone 6: Scientific Interpretation Methods                     */
/* ------------------------------------------------------------------ */

export async function getInterpretationStatus(): Promise<InterpretationStatusResponse> {
  return apiFetch<InterpretationStatusResponse>('/interpret/status');
}

export async function interpretPlayground(
  request: PlaygroundInterpretationRequest,
  signal?: AbortSignal
): Promise<PlaygroundInterpretationResponse> {
  return apiFetch<PlaygroundInterpretationResponse>('/interpret/playground', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}

export async function interpretCohort(
  request: CohortInterpretationRequest,
  signal?: AbortSignal
): Promise<CohortInterpretationResponse> {
  return apiFetch<CohortInterpretationResponse>('/interpret/cohort', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}
