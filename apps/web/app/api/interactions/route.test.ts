import { beforeEach, describe, expect, it, vi } from "vitest";

const { auth, recordInteraction, invalidateUserCache } = vi.hoisted(() => ({
  auth: vi.fn(),
  recordInteraction: vi.fn(),
  invalidateUserCache: vi.fn()
}));

vi.mock("../../../lib/auth", () => ({
  auth
}));

vi.mock("../../../lib/queries", () => ({
  recordInteraction
}));

vi.mock("../../../lib/cache", () => ({
  invalidateUserCache
}));

describe("POST /api/interactions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.mockResolvedValue({
      user: {
        id: "user-1"
      }
    });
    recordInteraction.mockResolvedValue(undefined);
    invalidateUserCache.mockResolvedValue(undefined);
  });

  it("does not invalidate cache for open interactions", async () => {
    const { POST } = await import("./route");
    const response = await POST(
      new Request("http://localhost/api/interactions", {
        method: "POST",
        body: JSON.stringify({ paperId: "paper-1", action: "open" })
      })
    );

    expect(response.status).toBe(200);
    expect(recordInteraction).toHaveBeenCalledWith("user-1", "paper-1", "open");
    expect(invalidateUserCache).not.toHaveBeenCalled();
  });

  it("immediately invalidates ranking caches for save-like actions", async () => {
    const { POST } = await import("./route");
    const response = await POST(
      new Request("http://localhost/api/interactions", {
        method: "POST",
        body: JSON.stringify({ paperId: "paper-1", action: "save" })
      })
    );

    expect(response.status).toBe(200);
    expect(recordInteraction).toHaveBeenCalledWith("user-1", "paper-1", "save");
    expect(invalidateUserCache).toHaveBeenCalledWith("user-1");
  });
});
