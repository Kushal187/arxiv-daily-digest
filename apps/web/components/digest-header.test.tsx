import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DigestHeader } from "./digest-header";

describe("DigestHeader", () => {
  it("renders the resolved digest date without shifting the day", () => {
    render(
      <DigestHeader requestedDate="2026-03-10" resolvedDate="2026-03-10" isFallback={false} />
    );

    expect(screen.getByRole("heading", { name: "March 10, 2026" })).toBeInTheDocument();
  });

  it("shows a fallback banner when rendering an older resolved digest", () => {
    render(
      <DigestHeader requestedDate="2026-03-10" resolvedDate="2026-03-09" isFallback />
    );

    expect(
      screen.getByText(/showing the latest available digest from March 9, 2026/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/March 10, 2026 is still empty/i)).toBeInTheDocument();
  });
});
