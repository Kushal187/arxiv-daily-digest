import { beforeEach, describe, expect, it, vi } from "vitest";
import { authCallbacks } from "./auth-callbacks";

const { ensureUserRecord } = vi.hoisted(() => ({
  ensureUserRecord: vi.fn()
}));

vi.mock("./queries", () => ({
  ensureUserRecord
}));

describe("authCallbacks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("provisions the app user only on initial sign-in", async () => {
    ensureUserRecord.mockResolvedValue({
      id: "user-1",
      onboardingCompleted: false
    });

    const result = await authCallbacks.jwt({
      token: {
        email: "user@example.com",
        name: "User Example",
        picture: "https://example.com/avatar.png"
      },
      account: {
        providerAccountId: "google-123"
      },
      profile: {
        sub: "google-subject"
      }
    });

    expect(ensureUserRecord).toHaveBeenCalledTimes(1);
    expect(result.appUserId).toBe("user-1");
  });

  it("does not hit the database for ordinary jwt refreshes", async () => {
    const result = await authCallbacks.jwt({
      token: {
        email: "user@example.com",
        appUserId: "user-1",
        onboardingCompleted: true
      }
    });

    expect(ensureUserRecord).not.toHaveBeenCalled();
    expect(result.appUserId).toBe("user-1");
    expect(result.onboardingCompleted).toBe(true);
  });

  it("maps the stored app user id onto the session", async () => {
    const session = await authCallbacks.session({
      session: { user: {} },
      token: {
        appUserId: "user-1",
        onboardingCompleted: true
      }
    });

    expect(session.user?.id).toBe("user-1");
    expect(session.user?.onboardingCompleted).toBe(true);
  });
});
