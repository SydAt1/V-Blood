import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiError, getCompounds, subscribeVisualFrames } from '../api/client';

describe('API Client and Error Handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('ApiError formats error message and status code accurately', () => {
    const err = new ApiError(422, 'Dose exceeds allowable limit of 20.0 mM');
    expect(err.status).toBe(422);
    expect(err.detail).toBe('Dose exceeds allowable limit of 20.0 mM');
    expect(err.message).toContain('API Error 422: Dose exceeds allowable limit of 20.0 mM');
  });

  it('parses structured API validation errors from json body', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Content',
      json: async () => ({ detail: 'Unknown chemical compound id: cmp_foo' }),
    });

    await expect(getCompounds()).rejects.toThrow('API Error 422: Unknown chemical compound id: cmp_foo');
  });

  it('subscribeVisualFrames lifecycle sets up EventSource and cleans up on unmount', () => {
    const mockClose = vi.fn();
    const mockAddEventListener = vi.fn();

    const mockConstructor = vi.fn(function (this: any, url: string) {
      this.url = url;
      this.addEventListener = mockAddEventListener;
      this.close = mockClose;
      this.onerror = null;
    });

    (globalThis as any).EventSource = mockConstructor;

    const onFrame = vi.fn();
    const onComplete = vi.fn();
    const onError = vi.fn();

    const cleanup = subscribeVisualFrames('test_run_1', onFrame, onComplete, onError, 100);

    expect(mockConstructor).toHaveBeenCalledWith(expect.stringContaining('/scenarios/test_run_1/stream?max_frames=100'));
    expect(mockAddEventListener).toHaveBeenCalledWith('frame', expect.any(Function));
    expect(mockAddEventListener).toHaveBeenCalledWith('complete', expect.any(Function));

    // Test cleanup
    cleanup();
    expect(mockClose).toHaveBeenCalledTimes(1);
  });
});
