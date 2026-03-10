import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { OnboardingForm } from "./onboarding-form";

describe("OnboardingForm", () => {
  afterEach(() => {
    cleanup();
  });

  function renderForm() {
    render(
      <OnboardingForm
        initialTopics={["agent-systems", "multimodal-vlm", "reasoning-planning"] as string[]}
        initialAuthors={[]}
        initialCategories={["cs.AI"]}
        title="Preferences"
        description="Tune the digest."
        submitLabel="Save"
      />
    );
  }

  it("does not add an author chip on blur", async () => {
    const user = userEvent.setup();
    renderForm();

    const input = screen.getByPlaceholderText("Yann LeCun");
    await user.type(input, "Yann L");
    fireEvent.blur(input);

    expect(screen.queryByText("Yann L")).not.toBeInTheDocument();
    expect(input).toHaveValue("Yann L");
  });

  it("adds an author chip on Enter", async () => {
    const user = userEvent.setup();
    renderForm();

    const input = screen.getByPlaceholderText("Yann LeCun");
    await user.type(input, "Yann LeCun{enter}");

    expect(screen.getByText("Yann LeCun")).toBeInTheDocument();
  });

  it("adds an author chip on comma", async () => {
    const user = userEvent.setup();
    renderForm();

    const input = screen.getByPlaceholderText("Yann LeCun");
    await user.type(input, "Andrej Karpathy,");

    expect(screen.getByText("Andrej Karpathy")).toBeInTheDocument();
  });

  it("collapses duplicate author variants into one chip", async () => {
    const user = userEvent.setup();
    renderForm();

    const input = screen.getByPlaceholderText("Yann LeCun");
    await user.type(input, "Yann LeCun{enter}");
    await user.type(input, "  yann   lecun {enter}");

    expect(screen.getAllByText("Yann LeCun")).toHaveLength(1);
    expect(screen.queryByText("yann lecun")).not.toBeInTheDocument();
  });
});
