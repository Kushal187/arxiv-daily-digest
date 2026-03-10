import { beforeEach, describe, expect, it, vi } from "vitest";

const { auth, replacePreferences, invalidateUserCache } = vi.hoisted(() => ({
  auth: vi.fn(),
  replacePreferences: vi.fn(),
  invalidateUserCache: vi.fn()
}));

vi.mock("../../../lib/auth", () => ({
  auth
}));

vi.mock("../../../lib/queries", () => ({
  replacePreferences
}));

vi.mock("../../../lib/cache", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/cache")>("../../../lib/cache");
  return {
    ...actual,
    invalidateUserCache
  };
});

describe("PUT /api/preferences", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.mockResolvedValue({
      user: {
        id: "user-1"
      }
    });
    replacePreferences.mockResolvedValue(undefined);
    invalidateUserCache.mockResolvedValue(undefined);
  });

  it("invalidates preferences and ranking caches after saving settings", async () => {
    const { PUT } = await import("./route");
    const response = await PUT(
      new Request("http://localhost/api/preferences", {
        method: "PUT",
        body: JSON.stringify({
          topics: ["agent-systems", "multimodal-vlm", "reasoning-planning"],
          followedAuthors: ["Yann LeCun"],
          categories: ["cs.AI"]
        })
      })
    );

    expect(response.status).toBe(200);
    expect(replacePreferences).toHaveBeenCalledWith("user-1", {
      topics: ["agent-systems", "multimodal-vlm", "reasoning-planning"],
      followedAuthors: ["Yann LeCun"],
      categories: ["cs.AI"]
    });
    expect(invalidateUserCache).toHaveBeenCalledWith("user-1", ["preferences", "digest", "paper"]);
  });
});
