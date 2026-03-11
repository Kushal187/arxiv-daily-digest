import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DigestPaper } from "@arxiv-digest/shared";
import { DiscoverCard } from "./discover-card";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => <a href={href}>{children}</a>
}));

const PAPER: DigestPaper = {
  id: "paper-1",
  sourceId: "source-1",
  canonicalArxivId: "1234.5678",
  arxivVersion: 1,
  title: "Interpreting transformer circuits",
  abstract: "This is a long abstract about mechanistic interpretability in transformers.",
  authors: ["Author One", "Author Two", "Author Three"],
  categories: ["cs.CL"],
  primaryCategory: "cs.CL",
  publishedAt: "2026-03-10T12:00:00Z",
  updatedAt: "2026-03-10T12:00:00Z",
  url: "https://arxiv.org/abs/1234.5678",
  clusterLabel: "interp",
  topics: [
    { slug: "mechanistic-interpretability", areaSlug: "interpretability", confidence: 0.9, isHidden: false },
    { slug: "llm-evaluation", areaSlug: "nlp", confidence: 0.6, isHidden: false }
  ],
  reasons: [{ type: "topic", label: "matches Mechanistic Interpretability", score: 0.8 }],
  score: 1,
  isSaved: false,
  isDismissed: false
};

describe("DiscoverCard", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows a compact author line and visible topic tags", () => {
    render(<DiscoverCard paper={PAPER} />);

    expect(screen.getByText(/Author One, Author Two \+1/)).toBeInTheDocument();
    expect(screen.getByText("Mechanistic Interpretability")).toBeInTheDocument();
    expect(screen.getByText("LLM Evaluation")).toBeInTheDocument();
  });

  it("expands the abstract on demand", async () => {
    const user = userEvent.setup();
    render(<DiscoverCard paper={PAPER} />);

    await user.click(screen.getByRole("button", { name: /expand abstract/i }));

    expect(screen.getByRole("button", { name: /collapse abstract/i })).toBeInTheDocument();
  });
});
