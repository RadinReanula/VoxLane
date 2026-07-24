"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import type {
  DriveThruSession,
  OrderItem,
  SessionCommand,
  SessionState,
} from "@/lib/contracts";
import { SessionClient } from "@/lib/session-client";
import { OptionalVoiceAdapter } from "@/lib/voice-adapter";
import {
  CarIcon,
  CheckIcon,
  HeadsetIcon,
  MicIcon,
  SparkIcon,
} from "./icons";

const MENU: Omit<OrderItem, "quantity">[] = [
  { id: "classic", name: "Classic Burger", unitPrice: 8.5 },
  { id: "fries", name: "Sea Salt Fries", unitPrice: 3.25 },
  { id: "lime", name: "Sparkling Lime", unitPrice: 2.75 },
];

const STATE_META: Record<
  SessionState,
  { label: string; detail: string; tone: string }
> = {
  approaching: {
    label: "Ready for your arrival",
    detail: "Pull up when you’re ready",
    tone: "cyan",
  },
  greeting: {
    label: "Welcome",
    detail: "Kubernetica is greeting you",
    tone: "cyan",
  },
  listening: {
    label: "Listening",
    detail: "Say your order naturally",
    tone: "green",
  },
  processing: {
    label: "Understanding",
    detail: "Checking what we heard",
    tone: "amber",
  },
  speaking: {
    label: "Speaking",
    detail: "You can interrupt at any time",
    tone: "cyan",
  },
  confirming: {
    label: "Confirm your order",
    detail: "Review your items and total",
    tone: "amber",
  },
  complete: {
    label: "You’re all set",
    detail: "Please pull forward",
    tone: "green",
  },
  recovering: {
    label: "Reconnecting",
    detail: "Your order is safely saved",
    tone: "rose",
  },
  human_help: {
    label: "Team member joining",
    detail: "Please stay at the speaker",
    tone: "rose",
  },
};

const client = new SessionClient();

function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function LaneExperience() {
  const [session, setSession] = useState<DriveThruSession | null>(null);
  const [micStatus, setMicStatus] = useState<
    "idle" | "requesting" | "ready" | "blocked"
  >("idle");
  const voice = useRef<OptionalVoiceAdapter | null>(null);

  useEffect(() => {
    voice.current = new OptionalVoiceAdapter();
    let active = true;
    void client.create().then((created) => {
      if (!active) return;
      const saved =
        typeof window !== "undefined"
          ? window.localStorage.getItem("kubernetica-order")
          : null;
      if (saved) {
        try {
          created.order.items = JSON.parse(saved) as OrderItem[];
        } catch {
          window.localStorage.removeItem("kubernetica-order");
        }
      }
      setSession(created);
    });
    return () => {
      active = false;
      voice.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    if (session) {
      window.localStorage.setItem(
        "kubernetica-order",
        JSON.stringify(session.order.items),
      );
      window.localStorage.setItem(
        "kubernetica-session",
        JSON.stringify(session),
      );
    }
  }, [session]);

  const dispatch = useCallback(
    async (command: SessionCommand) => {
      if (!session) return;
      if (command.type === "interrupt") voice.current?.interrupt();
      setSession(await client.command(session, command));
    },
    [session],
  );

  const total = useMemo(
    () =>
      session?.order.items.reduce(
        (sum, item) => sum + item.quantity * item.unitPrice,
        0,
      ) ?? 0,
    [session],
  );

  async function enableMicrophone() {
    setMicStatus("requesting");
    try {
      await voice.current?.requestMicrophone();
      setMicStatus("ready");
    } catch {
      setMicStatus("blocked");
    }
  }

  if (!session) {
    return (
      <main className="loading-shell" aria-busy="true">
        <SparkIcon className="brand-mark" />
        <p>Preparing your lane…</p>
      </main>
    );
  }

  const meta = STATE_META[session.state];
  const canInterrupt = session.state === "speaking";
  const nextLabel =
    session.state === "confirming"
      ? "Confirm order"
      : session.state === "complete"
        ? "Start new visit"
        : "Continue simulation";

  return (
    <main className="lane-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Kubernetica home">
          <span className="brand-icon">
            <SparkIcon />
          </span>
          <span>Kubernetica</span>
        </Link>
        <div className="lane-badge">
          <span className="status-dot" />
          Lane A · Online
        </div>
      </header>

      <div className="lane-grid">
        <section className="conversation-panel" aria-labelledby="lane-title">
          <div className={`state-orb tone-${meta.tone}`} aria-hidden="true">
            {session.state === "approaching" ? (
              <CarIcon />
            ) : session.state === "complete" ? (
              <CheckIcon />
            ) : session.state === "human_help" ? (
              <HeadsetIcon />
            ) : (
              <MicIcon />
            )}
            {(session.state === "listening" ||
              session.state === "speaking") && (
              <span className="sound-rings">
                <i />
                <i />
                <i />
              </span>
            )}
          </div>

          <div className="state-copy" aria-live="polite" aria-atomic="true">
            <span className={`eyebrow tone-text-${meta.tone}`}>
              <span className="state-symbol" aria-hidden="true">
                ●
              </span>
              {session.state.replace("_", " ")}
            </span>
            <h1 id="lane-title">{meta.label}</h1>
            <p>{meta.detail}</p>
          </div>

          <div
            className="caption-card"
            aria-label="Live conversation captions"
            aria-live="polite"
          >
            {session.captions.length ? (
              session.captions.slice(-3).map((caption) => (
                <div
                  className={`caption ${caption.final ? "final" : "interim"}`}
                  key={caption.id}
                >
                  <span>{caption.speaker}</span>
                  <p>{caption.text}</p>
                  <small>{caption.final ? "Final" : "Listening…"}</small>
                </div>
              ))
            ) : (
              <div className="caption empty-caption">
                <span>Conversation</span>
                <p>Your conversation will appear here.</p>
              </div>
            )}
            {session.state === "listening" && (
              <div className="caption interim">
                <span>You</span>
                <p>“I’d like a…”</p>
                <small>Interim</small>
              </div>
            )}
          </div>

          <div className="primary-actions">
            {session.state === "approaching" ? (
              <button
                className="button button-primary"
                onClick={() => void dispatch({ type: "vehicle_arrived" })}
              >
                <CarIcon /> Simulate vehicle arrival
              </button>
            ) : (
              <button
                className="button button-primary"
                onClick={() => {
                  if (session.state === "complete") {
                    window.localStorage.removeItem("kubernetica-order");
                    window.location.reload();
                  } else {
                    void dispatch({ type: "advance" });
                  }
                }}
              >
                {session.state === "confirming" && <CheckIcon />}
                {nextLabel}
              </button>
            )}
            {canInterrupt && (
              <button
                className="button button-interrupt"
                onClick={() => void dispatch({ type: "interrupt" })}
              >
                <MicIcon /> Interrupt & speak
              </button>
            )}
          </div>

          <div className="support-actions">
            <button
              className="text-button"
              onClick={() => void enableMicrophone()}
              disabled={micStatus === "requesting" || micStatus === "ready"}
            >
              <MicIcon />
              {micStatus === "ready"
                ? "Microphone ready"
                : micStatus === "blocked"
                  ? "Microphone blocked — try again"
                  : micStatus === "requesting"
                    ? "Requesting microphone…"
                    : "Enable microphone"}
            </button>
            <button
              className="text-button"
              onClick={() => void dispatch({ type: "request_human" })}
            >
              <HeadsetIcon /> Get team member
            </button>
          </div>
        </section>

        <aside className="order-panel" aria-labelledby="order-title">
          <div className="order-heading">
            <div>
              <span className="eyebrow">Live order</span>
              <h2 id="order-title">Your order</h2>
            </div>
            <span className="item-count">
              {session.order.items.reduce(
                (count, item) => count + item.quantity,
                0,
              )}{" "}
              items
            </span>
          </div>

          <div className="order-items">
            {session.order.items.length ? (
              session.order.items.map((item) => (
                <div className="order-row" key={item.id}>
                  <span className="quantity">{item.quantity}</span>
                  <div>
                    <strong>{item.name}</strong>
                    <small>{money(item.unitPrice)} each</small>
                  </div>
                  <span>{money(item.quantity * item.unitPrice)}</span>
                  <button
                    className="remove-button"
                    aria-label={`Remove one ${item.name}`}
                    onClick={() =>
                      void dispatch({
                        type: "remove_item",
                        itemId: item.id,
                      })
                    }
                  >
                    −
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-order">
                <span aria-hidden="true">◎</span>
                <p>Your items will stay visible here.</p>
              </div>
            )}
          </div>

          <div className="quick-add" aria-labelledby="quick-add-title">
            <h3 id="quick-add-title">Prototype quick add</h3>
            <div>
              {MENU.map((item) => (
                <button
                  key={item.id}
                  onClick={() => void dispatch({ type: "add_item", item })}
                  aria-label={`Add ${item.name} for ${money(item.unitPrice)}`}
                >
                  <span>+</span>
                  {item.name}
                  <small>{money(item.unitPrice)}</small>
                </button>
              ))}
            </div>
          </div>

          <div className="total-row">
            <span>Total</span>
            <strong>{money(total)}</strong>
          </div>
          <p className="tax-note">Taxes calculated at checkout</p>
        </aside>
      </div>

      <footer className="lane-footer">
        <span>Voice powered by Kubernetica</span>
        <Link href="/console">Operator console</Link>
        <span>Session {session.id.slice(-6).toUpperCase()}</span>
      </footer>
    </main>
  );
}
