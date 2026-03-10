import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PaperSummary } from "./paper-summary";

describe("PaperSummary", () => {
  it("renders extractive fallback summaries", () => {
    render(
      <PaperSummary
        summary="This is the fallback summary."
        summarySource="extractive"
      />
    );

    expect(screen.getByText("This is the fallback summary.")).toBeInTheDocument();
    expect(screen.getByText(/extractive fallback/i)).toBeInTheDocument();
  });
});
