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

vi.mock("../../../lib/worker", () => ({
  refreshUserProfile: vi.fn()
}));

const TEST_PAPER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

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
        body: JSON.stringify({ paperId: TEST_PAPER_ID, action: "open" })
      })
    );

    expect(response.status).toBe(200);
    expect(recordInteraction).toHaveBeenCalledWith("user-1", TEST_PAPER_ID, "open");
    expect(invalidateUserCache).not.toHaveBeenCalled();
  });

  it("immediately invalidates ranking caches for save-like actions", async () => {
    const { POST } = await import("./route");
    const response = await POST(
      new Request("http://localhost/api/interactions", {
        method: "POST",
        body: JSON.stringify({ paperId: TEST_PAPER_ID, action: "save" })
      })
    );

    expect(response.status).toBe(200);
    expect(recordInteraction).toHaveBeenCalledWith("user-1", TEST_PAPER_ID, "save");
    expect(invalidateUserCache).toHaveBeenCalledWith("user-1");
  });

  it("rejects invalid paperId format", async () => {
    const { POST } = await import("./route");
    const response = await POST(
      new Request("http://localhost/api/interactions", {
        method: "POST",
        body: JSON.stringify({ paperId: "not-a-uuid", action: "open" })
      })
    );

    expect(response.status).toBe(400);
    const body = await response.json();
    expect(body.error).toBe("Invalid paperId format");
  });
});
