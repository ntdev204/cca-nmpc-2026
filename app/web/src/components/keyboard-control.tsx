"use client";

import { useCallback, useEffect, useRef } from "react";

type Velocity = { vx: number; vy: number; wz: number };

const ZERO: Velocity = { vx: 0, vy: 0, wz: 0 };
const PERIOD_MS = 100;
const CONTROL_KEYS = new Set(["w", "s", "a", "d", "q", "e", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]);
const DEFAULT_LINEAR_SPEED = 0.2;
const MAX_CONTROL_REQUESTS = 2;
const CONTROL_REQUEST_TIMEOUT_MS = 350;

function configuredLinearSpeed(): number {
  const value = Number(window.localStorage.getItem("robot-linear-speed-mps"));
  return Number.isFinite(value) && value >= 0 ? value : DEFAULT_LINEAR_SPEED;
}

function normalizeKey(key: string): string {
  return key.length === 1 ? key.toLowerCase() : key;
}

function hasAny(keys: Set<string>, choices: string[]): boolean {
  return choices.some((choice) => keys.has(choice));
}

function velocityFrom(keys: Set<string>, linearSpeed: number): Velocity {
  const forward = hasAny(keys, ["w", "ArrowUp"]);
  const backward = hasAny(keys, ["s", "ArrowDown"]);
  const left = hasAny(keys, ["a", "ArrowLeft"]);
  const right = hasAny(keys, ["d", "ArrowRight"]);
  return {
    vx: (forward ? linearSpeed : 0) + (backward ? -linearSpeed : 0),
    vy: (left ? linearSpeed : 0) + (right ? -linearSpeed : 0),
    wz: (keys.has("q") ? 0.60 : 0) + (keys.has("e") ? -0.60 : 0),
  };
}

function editableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

export function KeyboardControl() {
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const active = useRef<Velocity | null>(null);
  const pressed = useRef(new Set<string>());
  const pending = useRef<{ velocity: Velocity; sequence: number } | null>(null);
  const inFlight = useRef(0);
  const clientId = useRef("");
  const sequence = useRef(0);

  const launch = useCallback((item: { velocity: Velocity; sequence: number }) => {
    inFlight.current += 1;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), CONTROL_REQUEST_TIMEOUT_MS);
    void fetch("/api/command", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        command: "velocity",
        ...item.velocity,
        control_client_id: clientId.current,
        control_sequence: item.sequence,
      }),
      cache: "no-store",
      keepalive: item.velocity.vx === 0 && item.velocity.vy === 0 && item.velocity.wz === 0,
      signal: controller.signal,
    }).catch(() => undefined).finally(() => {
      window.clearTimeout(timeout);
      inFlight.current = Math.max(0, inFlight.current - 1);
      if (pending.current !== null && inFlight.current < MAX_CONTROL_REQUESTS) {
        const latest = pending.current;
        pending.current = null;
        launch(latest);
      }
    });
  }, []);

  const send = useCallback((velocity: Velocity) => {
    if (!clientId.current) {
      clientId.current = typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    }
    const item = { velocity, sequence: ++sequence.current };
    if (inFlight.current < MAX_CONTROL_REQUESTS) launch(item);
    else pending.current = item;
  }, [launch]);

  const release = useCallback(() => {
    if (timer.current !== null) clearInterval(timer.current);
    timer.current = null;
    active.current = null;
    pressed.current.clear();
    send(ZERO);
  }, [send]);

  const hold = useCallback((velocity: Velocity) => {
    if (timer.current !== null) clearInterval(timer.current);
    active.current = velocity;
    send(velocity);
    timer.current = setInterval(() => {
      if (active.current) send(active.current);
    }, PERIOD_MS);
  }, [send]);

  useEffect(() => {
    const down = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.altKey || event.metaKey || editableTarget(event.target)) return;
      if (event.key === " ") {
        event.preventDefault();
        release();
        return;
      }
      const key = normalizeKey(event.key);
      if (!CONTROL_KEYS.has(key)) return;
      event.preventDefault();
      if (event.repeat && pressed.current.has(key)) return;
      pressed.current.add(key);
      hold(velocityFrom(pressed.current, configuredLinearSpeed()));
    };
    const up = (event: KeyboardEvent) => {
      if (editableTarget(event.target)) return;
      if (event.key === " ") {
        event.preventDefault();
        release();
        return;
      }
      const key = normalizeKey(event.key);
      if (!CONTROL_KEYS.has(key)) return;
      event.preventDefault();
      pressed.current.delete(key);
      if (pressed.current.size === 0) release();
      else hold(velocityFrom(pressed.current, configuredLinearSpeed()));
    };
    const stopOnHidden = () => { if (document.hidden) release(); };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    window.addEventListener("blur", release);
    window.addEventListener("beforeunload", release);
    document.addEventListener("visibilitychange", stopOnHidden);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
      window.removeEventListener("blur", release);
      window.removeEventListener("beforeunload", release);
      document.removeEventListener("visibilitychange", stopOnHidden);
      release();
    };
  }, [hold, release]);

  return null;
}
