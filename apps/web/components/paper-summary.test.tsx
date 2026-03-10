import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PaperSummary } from "./paper-summary";

describe("PaperSummary", () => {
  it("renders extractive summaries with correct label", () => {
    render(
      <PaperSummary
        summary="This is the fallback summary."
        summarySource="extractive"
      />
    );

    expect(screen.getByText("This is the fallback summary.")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
  });

  it("renders LLM summaries with AI label", () => {
    render(
      <PaperSummary
        summary="This is an AI generated summary."
        summarySource="llm"
      />
    );

    expect(screen.getByText("This is an AI generated summary.")).toBeInTheDocument();
    expect(screen.getByText("AI summary")).toBeInTheDocument();
  });

  it("renders nothing when summary is null", () => {
    const { container } = render(
      <PaperSummary summary={null} summarySource={null} />
    );

    expect(container.innerHTML).toBe("");
  });
});
