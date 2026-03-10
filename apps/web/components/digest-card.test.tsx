import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DigestPaper } from "@arxiv-digest/shared";
import { DigestCard } from "./digest-card";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  )
}));

const PAPER: DigestPaper = {
  id: "paper-1",
  sourceId: "source-1",
  canonicalArxivId: "1234.5678",
  arxivVersion: 1,
  title: "A Test Paper",
  abstract: "Abstract text.",
  authors: ["Author One"],
  categories: ["cs.AI"],
  primaryCategory: "cs.AI",
  publishedAt: "2026-03-10T12:00:00Z",
  updatedAt: "2026-03-10T12:00:00Z",
  url: "https://arxiv.org/abs/1234.5678",
  clusterLabel: "test cluster",
  topics: [],
  reasons: [{ type: "saved_similarity", label: "similar to papers you saved", score: 0.8 }],
  score: 1,
  isSaved: false,
  isDismissed: false
};

describe("DigestCard", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    global.fetch = originalFetch;
  });

  it("keeps the saved action state after dismissing a newly saved card", async () => {
    const user = userEvent.setup();

    render(<DigestCard paper={PAPER} />);

    await user.click(screen.getByRole("button", { name: "save" }));
    await user.click(screen.getByRole("button", { name: "dismiss" }));

    expect(screen.getByRole("button", { name: "remove" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "save" })).not.toBeInTheDocument();
  });
});
