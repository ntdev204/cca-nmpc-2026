"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, CircleStop, Crosshair, Move, OctagonAlert, RotateCcw, RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type Velocity = { vx: number; vy: number; wz: number };
type Command = (payload: Record<string, unknown>) => Promise<void>;

type ControlPanelProps = {
  online: boolean;
  armed: boolean;
  command: Command;
};

const ZERO: Velocity = { vx: 0, vy: 0, wz: 0 };

function numberValue(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function HoldButton({ label, velocity, disabled, command }: { label: string; velocity: Velocity; disabled: boolean; command: Command }) {
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const pending = useRef<Velocity | null>(null);
  const sending = useRef(false);
  const flush = useCallback(async () => {
    if (sending.current) return;
    sending.current = true;
    try {
      while (pending.current !== null) {
        const next = pending.current;
        pending.current = null;
        await command({ command: "velocity", ...next });
      }
    } finally {
      sending.current = false;
      if (pending.current !== null) void flush();
    }
  }, [command]);
  const send = useCallback((next: Velocity) => {
    pending.current = next;
    if (!sending.current) void flush();
  }, [flush]);
  const stop = () => {
    if (timer.current !== null) clearInterval(timer.current);
    timer.current = null;
    send(ZERO);
  };
  const start = () => {
    if (disabled) return;
    if (timer.current !== null) clearInterval(timer.current);
    send(velocity);
    timer.current = setInterval(() => send(velocity), 100);
  };
  useEffect(() => () => {
    if (timer.current !== null) clearInterval(timer.current);
    send(ZERO);
  }, [send]);
  return (
    <Button
      type="button"
      variant="outline"
      className="h-11 select-none touch-none text-xs"
      disabled={disabled}
      onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); start(); }}
      onPointerUp={stop}
      onPointerCancel={stop}
      onPointerLeave={stop}
      aria-label={`${label} (hold)`}
    >
      {label}
    </Button>
  );
}

export function ControlPanel({ online, armed, command }: ControlPanelProps) {
  const [speed, setSpeed] = useState("0.20");
  const [yawSpeed, setYawSpeed] = useState("0.60");
  const [goalX, setGoalX] = useState("1.00");
  const [goalY, setGoalY] = useState("0.00");
  const [goalYaw, setGoalYaw] = useState("0.00");
  const [direction, setDirection] = useState("forward");
  const speedValue = Math.min(0.3, Math.max(0, numberValue(speed, 0.2)));
  const yawValue = Math.min(0.9, Math.max(0, numberValue(yawSpeed, 0.6)));
  const disabled = !online || !armed;
  const sendVelocity = (vx: number, vy: number, wz: number) => command({ command: "velocity", vx, vy, wz });
  const sendGoal = () => command({
    command: "nav_goal",
    x: numberValue(goalX, 1),
    y: numberValue(goalY, 0),
    yaw: numberValue(goalYaw, 0),
  });
  const sendPreset = () => command({ command: "direction", direction, speed_mps: speedValue, yaw_radps: yawValue });

  return (
    <Card className="shadow-sm">
      <CardHeader className="border-b bg-slate-50/70 py-3">
        <CardTitle className="flex items-center gap-2 text-base"><Move className="size-4 text-primary" />Control &amp; navigation</CardTitle>
        <CardDescription>Commands are sent as HTTP requests to the FastAPI bridge. Hold a direction button or use W/S/A/D, arrows and Q/E.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 p-3 lg:grid-cols-[minmax(230px,0.75fr)_minmax(260px,1fr)]">
        <div className="space-y-3 rounded-lg border bg-background p-3">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <label className="space-y-1"><span className="text-muted-foreground">Linear speed (m/s)</span><input value={speed} onChange={(event) => setSpeed(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
            <label className="space-y-1"><span className="text-muted-foreground">Yaw speed (rad/s)</span><input value={yawSpeed} onChange={(event) => setYawSpeed(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
          </div>
          <div className="mx-auto grid max-w-[245px] grid-cols-3 gap-2">
            <HoldButton label="↖" velocity={{ vx: speedValue, vy: speedValue, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="↑ W" velocity={{ vx: speedValue, vy: 0, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="↗" velocity={{ vx: speedValue, vy: -speedValue, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="← A" velocity={{ vx: 0, vy: speedValue, wz: 0 }} disabled={disabled} command={command} />
            <Button type="button" variant="secondary" className="h-11" disabled={!online} onClick={() => command({ command: "stop" })} title="Stop motion"><CircleStop className="size-4" /></Button>
            <HoldButton label="→ D" velocity={{ vx: 0, vy: -speedValue, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="↙" velocity={{ vx: -speedValue, vy: speedValue, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="↓ S" velocity={{ vx: -speedValue, vy: 0, wz: 0 }} disabled={disabled} command={command} />
            <HoldButton label="↘" velocity={{ vx: -speedValue, vy: -speedValue, wz: 0 }} disabled={disabled} command={command} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <HoldButton label="Q · rotate left" velocity={{ vx: 0, vy: 0, wz: yawValue }} disabled={disabled} command={command} />
            <HoldButton label="E · rotate right" velocity={{ vx: 0, vy: 0, wz: -yawValue }} disabled={disabled} command={command} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button type="button" variant="destructive" disabled={!online} onClick={() => command({ command: "emergency_stop" })}><OctagonAlert className="size-4" />Emergency stop</Button>
            <Button type="button" variant="outline" disabled={!online} onClick={() => sendVelocity(0, 0, 0)}><CircleStop className="size-4" />Zero velocity</Button>
          </div>
          <p className="text-[11px] leading-4 text-muted-foreground">Motion is {armed ? "armed" : "disarmed"} in this browser session. The HTTP bridge watchdog stops stale commands.</p>
          <div className="space-y-2 border-t pt-3">
            <div className="text-xs font-medium">One-shot direction command</div>
            <div className="flex gap-2">
              <Select value={direction} onValueChange={(value) => { if (value !== null) setDirection(value); }}>
                <SelectTrigger size="sm" className="min-w-0 flex-1 bg-background text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="forward">Forward</SelectItem>
                  <SelectItem value="backward">Backward</SelectItem>
                  <SelectItem value="left">Left strafe</SelectItem>
                  <SelectItem value="right">Right strafe</SelectItem>
                  <SelectItem value="forward_left">Forward-left</SelectItem>
                  <SelectItem value="forward_right">Forward-right</SelectItem>
                  <SelectItem value="backward_left">Backward-left</SelectItem>
                  <SelectItem value="backward_right">Backward-right</SelectItem>
                  <SelectItem value="rotate_left">Rotate left</SelectItem>
                  <SelectItem value="rotate_right">Rotate right</SelectItem>
                  <SelectItem value="stop">Stop</SelectItem>
                </SelectContent>
              </Select>
              <Button type="button" variant="outline" onClick={sendPreset} disabled={disabled}>Send</Button>
            </div>
          </div>
        </div>

        <div className="space-y-3 rounded-lg border bg-background p-3">
          <div className="flex items-center justify-between"><div><h3 className="flex items-center gap-2 text-sm font-medium"><Crosshair className="size-4 text-primary" />HTTP navigation goal</h3><p className="text-xs text-muted-foreground">Send a map-frame goal to the bridge&apos;s RAI navigation endpoint.</p></div><span className="rounded-md bg-muted px-2 py-1 text-[11px]">REST</span></div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <label className="space-y-1"><span className="text-muted-foreground">Goal x (m)</span><input value={goalX} onChange={(event) => setGoalX(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
            <label className="space-y-1"><span className="text-muted-foreground">Goal y (m)</span><input value={goalY} onChange={(event) => setGoalY(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
            <label className="space-y-1"><span className="text-muted-foreground">Yaw (rad)</span><input value={goalYaw} onChange={(event) => setGoalYaw(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button type="button" onClick={sendGoal} disabled={!online}><Crosshair className="size-4" />Send goal</Button>
            <Button type="button" variant="outline" onClick={() => command({ command: "nav_cancel" })} disabled={!online}><RotateCcw className="size-4" />Cancel navigation</Button>
          </div>
          <p className="text-[11px] leading-4 text-muted-foreground">The bridge enforces its device-role permissions for navigation. Commands stay on the REST API path.</p>
          <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><ArrowUp className="size-3" />W / ↑ forward</span>
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><ArrowDown className="size-3" />S / ↓ backward</span>
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><ArrowLeft className="size-3" />A / ← strafe</span>
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><ArrowRight className="size-3" />D / → strafe</span>
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><RotateCcw className="size-3" />Q rotate left</span>
            <span className="flex items-center gap-1 rounded-md border px-2 py-1"><RotateCw className="size-3" />E rotate right</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
