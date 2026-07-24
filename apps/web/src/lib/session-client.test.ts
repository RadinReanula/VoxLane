import { describe, expect, it } from "vitest";
import { CONTRACT_VERSION } from "./contracts";
import { createLocalSession, reduceSession } from "./session-client";

describe("local session reducer", () => {
  it("creates a versioned deterministic fallback session", () => {
    const session = createLocalSession();

    expect(session.version).toBe(CONTRACT_VERSION);
    expect(session.diagnostics.provider).toBe("local-simulator");
    expect(session.state).toBe("approaching");
  });

  it("persists order items while advancing conversation state", () => {
    const session = createLocalSession();
    const withItem = reduceSession(session, {
      type: "add_item",
      item: { id: "classic", name: "Classic Burger", unitPrice: 8.5 },
    });
    const interrupted = reduceSession(withItem, { type: "interrupt" });

    expect(interrupted.order.items).toEqual([
      {
        id: "classic",
        name: "Classic Burger",
        unitPrice: 8.5,
        quantity: 1,
      },
    ]);
    expect(interrupted.state).toBe("listening");
    expect(interrupted.diagnostics.generation).toBe(1);
  });
});
