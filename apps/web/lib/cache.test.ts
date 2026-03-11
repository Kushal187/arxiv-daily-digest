import { beforeEach, describe, expect, it, vi } from "vitest";
import { invalidateUserCache, loadCachedUserPayload, resetCacheClientForTests } from "./cache";

const { mockPipelineExec, mockPipelineGet, mockPipelineSet, mockSet, redisCtor } = vi.hoisted(
  () => ({
    mockPipelineExec: vi.fn(),
    mockPipelineGet: vi.fn(),
    mockPipelineSet: vi.fn(),
    mockSet: vi.fn(),
    redisCtor: vi.fn()
  })
);

vi.mock("@upstash/redis", () => ({
  Redis: redisCtor
}));

function createPipeline() {
  return {
    get: mockPipelineGet,
    set: mockPipelineSet,
    exec: mockPipelineExec
  };
}

describe("cache", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.UPSTASH_REDIS_REST_URL = "https://upstash.example.com";
    process.env.UPSTASH_REDIS_REST_TOKEN = "token";
    const pipeline = createPipeline();
    mockPipelineGet.mockReturnValue(pipeline);
    mockPipelineSet.mockReturnValue(pipeline);
    redisCtor.mockImplementation(() => ({
      pipeline: () => pipeline,
      set: mockSet
    }));
    resetCacheClientForTests();
  });

  it("returns a hit when the cached payload is newer than invalidation", async () => {
    mockPipelineExec.mockResolvedValue([
      10,
      {
        createdAt: 20,
        value: { ok: true }
      }
    ]);

    const load = vi.fn().mockResolvedValue({ ok: false });
    const result = await loadCachedUserPayload({
      userId: "user-1",
      namespace: "digest",
      identity: "2026-03-10",
      ttlSeconds: 60,
      load
    });

    expect(result).toEqual({ value: { ok: true }, status: "hit" });
    expect(load).not.toHaveBeenCalled();
  });

  it("stores and returns a miss when the cached payload is stale", async () => {
    mockPipelineExec.mockResolvedValue([
      20,
      {
        createdAt: 10,
        value: { ok: false }
      }
    ]);
    mockSet.mockResolvedValue("OK");

    const load = vi.fn().mockResolvedValue({ ok: true });
    const result = await loadCachedUserPayload({
      userId: "user-1",
      namespace: "digest",
      identity: "2026-03-10",
      ttlSeconds: 60,
      load
    });

    expect(result).toEqual({ value: { ok: true }, status: "miss" });
    expect(load).toHaveBeenCalledTimes(1);
    expect(mockSet).toHaveBeenCalledTimes(1);
  });

  it("does not call the loader twice when cache write fails", async () => {
    mockPipelineExec.mockResolvedValue([0, null]);
    mockSet.mockRejectedValue(new Error("upstash write failed"));

    const load = vi.fn().mockResolvedValue({ ok: true });
    const result = await loadCachedUserPayload({
      userId: "user-1",
      namespace: "digest",
      identity: "2026-03-10",
      ttlSeconds: 60,
      load
    });

    expect(result).toEqual({ value: { ok: true }, status: "miss" });
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("invalidates ranking namespaces immediately for explicit writes", async () => {
    mockPipelineExec.mockResolvedValue([]);

    await invalidateUserCache("user-1");

    expect(mockPipelineSet).toHaveBeenCalledTimes(3);
  });
});
