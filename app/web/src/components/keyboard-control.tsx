"use client";

import { useCallback, useEffect, useRef } from "react";

type Velocity = { vx: number; vy: number; wz: number };

const ZERO: Velocity = { vx: 0, vy: 0, wz: 0 };
const PERIOD_MS = 100;
const CONTROL_KEYS = new Set(["w", "s", "a", "d", "q", "e", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]);

function normalizeKey(key: string): string {
  return key.length === 1 ? key.toLowerCase() : key;
}

function hasAny(keys: Set<string>, choices: string[]): boolean {
  return choices.some((choice) => keys.has(choice));
}

function velocityFrom(keys: Set<string>): Velocity {
  const forward = hasAny(keys, ["w", "ArrowUp"]);
  const backward = hasAny(keys, ["s", "ArrowDown"]);
  const left = hasAny(keys, ["a", "ArrowLeft"]);
  const right = hasAny(keys, ["d", "ArrowRight"]);
  return {
    vx: (forward ? 0.20 : 0) + (backward ? -0.20 : 0),
    vy: (left ? 0.20 : 0) + (right ? -0.20 : 0),
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
  const pending = useRef<Velocity | null>(null);
  const sending = useRef(false);

  const send = useCallback((velocity: Velocity) => {
    pending.current = velocity;
    if (sending.current) return;
    const flush = async () => {
      if (sending.current) return;
      sending.current = true;
      try {
        while (pending.current !== null) {
          const next = pending.current;
          pending.current = null;
          await fetch("/api/command", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ command: "velocity", ...next }),
            cache: "no-store",
            keepalive: next.vx === 0 && next.vy === 0 && next.wz === 0,
          });
        }
      } catch {
        pending.current = null;
      } finally {
        sending.current = false;
        if (pending.current !== null) void flush();
      }
    };
    void flush();
  }, []);

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
      hold(velocityFrom(pressed.current));
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
      else hold(velocityFrom(pressed.current));
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
