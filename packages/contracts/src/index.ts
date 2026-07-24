export const CONTRACT_VERSION = "2026-07-01" as const;

export type SessionState =
  | "approaching"
  | "greeting"
  | "listening"
  | "processing"
  | "speaking"
  | "confirming"
  | "complete"
  | "recovering"
  | "human_help";

export type OrderItem = {
  id: string;
  name: string;
  quantity: number;
  unitPrice: number;
};

export type Caption = {
  id: string;
  speaker: "guest" | "kubernetica" | "operator";
  text: string;
  final: boolean;
  createdAt: string;
};

export type SessionEvent = {
  id: string;
  type: string;
  message: string;
  createdAt: string;
  sequence?: number;
};

export type SessionDiagnostics = {
  provider: "local-simulator" | "pipecat-smallwebrtc";
  sessionId: string;
  latencyMs: number | null;
  connected: boolean;
  generation: number;
};

export type Order = {
  version: typeof CONTRACT_VERSION;
  id: string;
  currency: "USD";
  items: OrderItem[];
  status: "draft" | "confirmed" | "complete";
};

export type DriveThruSession = {
  version: typeof CONTRACT_VERSION;
  id: string;
  lane: string;
  state: SessionState;
  order: Order;
  captions: Caption[];
  events: SessionEvent[];
  diagnostics: SessionDiagnostics;
  startedAt: string;
};

export type SessionCommand =
  | { type: "vehicle_arrived" }
  | { type: "advance" }
  | { type: "interrupt" }
  | { type: "request_human" }
  | { type: "recover" }
  | { type: "add_item"; item: Omit<OrderItem, "quantity"> }
  | { type: "remove_item"; itemId: string };

export type BackendSessionSnapshot = {
  schema_version: "1.0";
  session: {
    id: string;
    status: "active" | "confirmed" | "human_help" | "closed";
    generation_id: number;
    order_id: string;
  };
  order: {
    id: string;
    total: string;
    lines: Array<{
      id: string;
      item_name: string;
      quantity: number;
    }>;
  };
  events: Array<Record<string, unknown>>;
  latest_sequence: number;
};
