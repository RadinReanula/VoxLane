import {
  CONTRACT_VERSION,
  type DriveThruSession,
  type SessionCommand,
  type SessionEvent,
  type SessionState,
} from "./contracts";

const FLOW: SessionState[] = [
  "approaching",
  "greeting",
  "listening",
  "processing",
  "speaking",
  "confirming",
  "complete",
];

const STATE_COPY: Record<SessionState, string> = {
  approaching: "Vehicle detected in the approach zone",
  greeting: "Welcome to Kubernetica. What can I get started for you?",
  listening: "I’m listening",
  processing: "Understanding your order",
  speaking: "I’ve added that to your order",
  confirming: "Does everything on the order look right?",
  complete: "Order confirmed. Please pull forward",
  recovering: "Reconnecting the voice channel",
  human_help: "A team member is joining",
};

function event(type: string, message: string): SessionEvent {
  return {
    id: crypto.randomUUID(),
    type,
    message,
    createdAt: new Date().toISOString(),
  };
}

export function createLocalSession(): DriveThruSession {
  const id = `lane-a-${Date.now().toString(36)}`;
  return {
    version: CONTRACT_VERSION,
    id,
    lane: "Lane A",
    state: "approaching",
    order: {
      version: CONTRACT_VERSION,
      id: `order-${Date.now().toString(36)}`,
      currency: "USD",
      items: [],
      status: "draft",
    },
    captions: [],
    events: [event("session.created", "Local session ready")],
    diagnostics: {
      provider: "local-simulator",
      sessionId: id,
      latencyMs: 38,
      connected: true,
      generation: 0,
    },
    startedAt: new Date().toISOString(),
  };
}

export function reduceSession(
  session: DriveThruSession,
  command: SessionCommand,
): DriveThruSession {
  const now = new Date().toISOString();
  let state = session.state;
  let message = "Session updated";
  let items = session.order.items;
  let generation = session.diagnostics.generation;

  if (command.type === "vehicle_arrived") {
    state = "greeting";
    message = "Vehicle arrival simulated";
  } else if (command.type === "advance") {
    const index = FLOW.indexOf(session.state);
    state = FLOW[Math.min(Math.max(index + 1, 1), FLOW.length - 1)];
    message = `State changed to ${state}`;
  } else if (command.type === "interrupt") {
    state = "listening";
    generation += 1;
    message = "Guest interrupted playback";
  } else if (command.type === "request_human") {
    state = "human_help";
    message = "Human handoff requested";
  } else if (command.type === "recover") {
    state = "recovering";
    message = "Voice recovery started";
  } else if (command.type === "add_item") {
    const existing = items.find((item) => item.id === command.item.id);
    items = existing
      ? items.map((item) =>
          item.id === command.item.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        )
      : [...items, { ...command.item, quantity: 1 }];
    state = "speaking";
    message = `${command.item.name} added`;
  } else if (command.type === "remove_item") {
    items = items
      .map((item) =>
        item.id === command.itemId
          ? { ...item, quantity: item.quantity - 1 }
          : item,
      )
      .filter((item) => item.quantity > 0);
    message = "Order item removed";
  }

  const assistantCaption =
    state === "greeting" ||
    state === "speaking" ||
    state === "confirming" ||
    state === "complete" ||
    state === "human_help" ||
    state === "recovering"
      ? {
          id: crypto.randomUUID(),
          speaker: "kubernetica" as const,
          text: STATE_COPY[state],
          final: true,
          createdAt: now,
        }
      : undefined;

  return {
    ...session,
    state,
    order: {
      ...session.order,
      items,
      status: state === "complete" ? "complete" : "draft",
    },
    captions: assistantCaption
      ? [...session.captions, assistantCaption]
      : session.captions,
    events: [...session.events, event(`session.${command.type}`, message)],
    diagnostics: {
      ...session.diagnostics,
      generation,
      latencyMs: 32 + ((session.events.length * 17) % 74),
    },
  };
}

export class SessionClient {
  constructor(private readonly baseUrl = process.env.NEXT_PUBLIC_API_URL) {}

  async create(): Promise<DriveThruSession> {
    if (!this.baseUrl) return createLocalSession();
    try {
      const response = await fetch(`${this.baseUrl}/v1/sessions`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ version: CONTRACT_VERSION, lane: "Lane A" }),
      });
      if (!response.ok) throw new Error("Session API unavailable");
      return (await response.json()) as DriveThruSession;
    } catch {
      return createLocalSession();
    }
  }

  async command(
    session: DriveThruSession,
    command: SessionCommand,
  ): Promise<DriveThruSession> {
    if (!this.baseUrl) return reduceSession(session, command);
    try {
      const response = await fetch(
        `${this.baseUrl}/v1/sessions/${session.id}/commands`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ version: CONTRACT_VERSION, command }),
        },
      );
      if (!response.ok) throw new Error("Command API unavailable");
      return (await response.json()) as DriveThruSession;
    } catch {
      return reduceSession(session, command);
    }
  }
}
