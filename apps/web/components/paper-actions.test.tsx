import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PaperActions } from "./paper-actions";

describe("PaperActions", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
    global.fetch = originalFetch;
  });

  it("does not surface an error when open tracking fails", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("network")) as typeof fetch;
    const user = userEvent.setup();

    render(
      <PaperActions
        paperId="paper-1"
        paperUrl="https://arxiv.org/abs/1234.5678"
        initialSaved={false}
        initialDismissed={false}
      />
    );

    await user.click(screen.getByRole("link", { name: /open arxiv/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    expect(screen.queryByText(/could not/i)).not.toBeInTheDocument();
  });

  it("toggles dismiss into undo dismiss", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true }) as unknown as typeof fetch;
    const user = userEvent.setup();

    render(
      <PaperActions
        paperId="paper-1"
        initialSaved={false}
        initialDismissed={false}
      />
    );

    await user.click(screen.getByRole("button", { name: "dismiss" }));

    expect(screen.getByRole("button", { name: "undo dismiss" })).toBeInTheDocument();
  });

  it("shows a clear reading queue indication after save", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true }) as unknown as typeof fetch;
    const user = userEvent.setup();

    render(
      <PaperActions
        paperId="paper-1"
        initialSaved={false}
        initialDismissed={false}
      />
    );

    await user.click(screen.getByRole("button", { name: "save" }));

    expect(screen.getByText("Saved to reading queue.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "remove" })).toBeInTheDocument();
  });
});
