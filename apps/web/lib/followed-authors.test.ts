import { describe, expect, it } from "vitest";
import { dedupeFollowedAuthors } from "./followed-authors";

describe("dedupeFollowedAuthors", () => {
  it("keeps the first cleaned display label for duplicate author variants", () => {
    expect(dedupeFollowedAuthors(["Yann LeCun", "  yann   lecun ", "YANN LECUN"])).toEqual([
      "Yann LeCun"
    ]);
  });
});
