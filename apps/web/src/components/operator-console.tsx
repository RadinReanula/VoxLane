"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { DriveThruSession, SessionEvent } from "@/lib/contracts";
import { createLocalSession, reduceSession } from "@/lib/session-client";
import { HeadsetIcon, MicIcon, SparkIcon } from "./icons";

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function OperatorConsole() {
  const [session, setSession] = useState<DriveThruSession | null>(null);
  const [filter, setFilter] = useState<"all" | "voice" | "session">("all");

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
      const saved = window.localStorage.getItem("kubernetica-session");
      if (saved) {
        try {
          setSession(JSON.parse(saved) as DriveThruSession);
          return;
        } catch {
          window.localStorage.removeItem("kubernetica-session");
        }
      }
      setSession(createLocalSession());
    });
    return () => {
      active = false;
    };
  }, []);

  const events = useMemo(() => {
    if (!session) return [];
    if (filter === "all") return session.events;
    return session.events.filter((item) => item.type.includes(filter));
  }, [filter, session]);

  function addOperatorEvent(type: string, message: string) {
    setSession((current) => {
      if (!current) return current;
      const entry: SessionEvent = {
        id: crypto.randomUUID(),
        type,
        message,
        createdAt: new Date().toISOString(),
      };
      return { ...current, events: [...current.events, entry] };
    });
  }

  if (!session) {
    return <main className="loading-shell">Loading console…</main>;
  }

  const itemCount = session.order.items.reduce(
    (sum, item) => sum + item.quantity,
    0,
  );

  return (
    <main className="console-shell">
      <header className="console-topbar">
        <Link className="brand" href="/">
          <span className="brand-icon">
            <SparkIcon />
          </span>
          <span>Kubernetica</span>
        </Link>
        <span className="console-label">Operations console</span>
        <div className="operator-profile">
          <span className="status-dot" />
          Operator online
        </div>
      </header>

      <section className="console-content" aria-labelledby="console-title">
        <div className="console-title-row">
          <div>
            <span className="eyebrow">Live operations</span>
            <h1 id="console-title">Lane overview</h1>
            <p>Monitor sessions, intervene, and trace voice events.</p>
          </div>
          <Link className="button button-secondary" href="/lane">
            Open customer lane
          </Link>
        </div>

        <div className="metric-grid">
          <article className="metric-card">
            <span>Active sessions</span>
            <strong>1</strong>
            <small className="metric-good">● Healthy</small>
          </article>
          <article className="metric-card">
            <span>Voice latency</span>
            <strong>
              {session.diagnostics.latencyMs ?? "—"}
              <small> ms</small>
            </strong>
            <small>Target under 250 ms</small>
          </article>
          <article className="metric-card">
            <span>Human handoffs</span>
            <strong>{session.state === "human_help" ? 1 : 0}</strong>
            <small>Current shift</small>
          </article>
          <article className="metric-card">
            <span>Provider</span>
            <strong className="metric-provider">
              {session.diagnostics.provider === "local-simulator"
                ? "Simulator"
                : "SmallWebRTC"}
            </strong>
            <small>
              <span className="status-dot" /> Connected
            </small>
          </article>
        </div>

        <div className="console-grid">
          <section className="session-card" aria-labelledby="active-session">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Active session</span>
                <h2 id="active-session">{session.lane}</h2>
              </div>
              <span className={`state-pill state-${session.state}`}>
                ● {session.state.replace("_", " ")}
              </span>
            </div>

            <dl className="session-details">
              <div>
                <dt>Session ID</dt>
                <dd>{session.diagnostics.sessionId}</dd>
              </div>
              <div>
                <dt>Order</dt>
                <dd>
                  {itemCount} items · {session.order.status}
                </dd>
              </div>
              <div>
                <dt>Generation</dt>
                <dd>{session.diagnostics.generation}</dd>
              </div>
              <div>
                <dt>Started</dt>
                <dd>{formatTime(session.startedAt)}</dd>
              </div>
            </dl>

            <div className="operator-actions">
              <button
                className="button button-interrupt"
                onClick={() => {
                  setSession((current) =>
                    current
                      ? reduceSession(current, { type: "interrupt" })
                      : current,
                  );
                  addOperatorEvent(
                    "voice.interrupted",
                    "Operator stopped AI playout",
                  );
                }}
              >
                <MicIcon /> Stop AI & listen
              </button>
              <button
                className="button button-primary"
                onClick={() => {
                  setSession((current) =>
                    current
                      ? reduceSession(current, { type: "request_human" })
                      : current,
                  );
                  addOperatorEvent(
                    "session.handoff",
                    "Operator accepted handoff",
                  );
                }}
              >
                <HeadsetIcon /> Take over
              </button>
              <button
                className="button button-secondary"
                onClick={() =>
                  setSession((current) =>
                    current
                      ? reduceSession(current, { type: "recover" })
                      : current,
                  )
                }
              >
                Recover voice
              </button>
            </div>
          </section>

          <section className="events-card" aria-labelledby="events-title">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Trace</span>
                <h2 id="events-title">Event stream</h2>
              </div>
              <select
                aria-label="Filter event stream"
                value={filter}
                onChange={(event) =>
                  setFilter(event.target.value as typeof filter)
                }
              >
                <option value="all">All events</option>
                <option value="voice">Voice</option>
                <option value="session">Session</option>
              </select>
            </div>

            <ol className="event-list" aria-live="polite">
              {[...events].reverse().map((item) => (
                <li key={item.id}>
                  <span className="event-node" aria-hidden="true" />
                  <div>
                    <strong>{item.type}</strong>
                    <p>{item.message}</p>
                  </div>
                  <time dateTime={item.createdAt}>
                    {formatTime(item.createdAt)}
                  </time>
                </li>
              ))}
            </ol>
          </section>
        </div>
      </section>
    </main>
  );
}
