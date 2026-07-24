import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LaneExperience } from "./lane-experience";

describe("LaneExperience", () => {
  it("supports arrival and persistent cart interaction", async () => {
    const user = userEvent.setup();
    render(<LaneExperience />);

    const arrival = await screen.findByRole("button", {
      name: /simulate vehicle arrival/i,
    });
    await user.click(arrival);

    expect(
      await screen.findByRole("heading", { name: "Welcome" }),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: /add classic burger/i }),
    );

    expect(screen.getAllByText("$8.50")).not.toHaveLength(0);
    await waitFor(() =>
      expect(window.localStorage.getItem("kubernetica-order")).toContain(
        "Classic Burger",
      ),
    );
  });

  it("exposes human help with icon and text", async () => {
    const user = userEvent.setup();
    render(<LaneExperience />);

    await user.click(
      await screen.findByRole("button", { name: /get team member/i }),
    );

    expect(
      await screen.findByRole("heading", { name: /team member joining/i }),
    ).toBeInTheDocument();
  });
});
