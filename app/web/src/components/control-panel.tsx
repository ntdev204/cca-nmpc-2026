"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, CircleStop, Crosshair, Move, OctagonAlert, RotateCcw, RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Velocity = { vx: number; vy: number; wz: number };
type Command = (payload: Record<string, unknown>) => void;

type ControlPanelProps = {
  online: boolean;
  armed: boolean;
  command: Command;
  plan?: Record<string, unknown>;
};

const ZERO: Velocity = { vx: 0, vy: 0, wz: 0 };

function numberValue(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function HoldButton({ label, velocity, disabled, command }: { label: string; velocity: Velocity; disabled: boolean; command: Command }) {
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const stop = () => {
    if (timer.current !== null) clearInterval(timer.current);
    timer.current = null;
    command({ command: "velocity", ...ZERO });
  };
  const start = () => {
    if (disabled) return;
    if (timer.current !== null) clearInterval(timer.current);
    command({ command: "velocity", ...velocity });
    timer.current = setInterval(() => command({ command: "velocity", ...velocity }), 100);
  };
  useEffect(() => () => {
    if (timer.current !== null) clearInterval(timer.current);
  }, []);
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

export function ControlPanel({ online, armed, command, plan }: ControlPanelProps) {
  const [speed, setSpeed] = useState("0.20");
  const [yawSpeed, setYawSpeed] = useState("0.60");
  const [goalX, setGoalX] = useState("1.00");
  const [goalY, setGoalY] = useState("0.00");
  const [inflation, setInflation] = useState("0.30");
  const [direction, setDirection] = useState("forward");
  const speedValue = Math.min(0.3, Math.max(0, numberValue(speed, 0.2)));
  const yawValue = Math.min(0.9, Math.max(0, numberValue(yawSpeed, 0.6)));
  const disabled = !online || !armed;
  const sendVelocity = (vx: number, vy: number, wz: number) => command({ command: "velocity", vx, vy, wz });
  const sendPlan = () => command({
    command: "plan",
    goal_xy: [numberValue(goalX, 1), numberValue(goalY, 0)],
    inflation_m: Math.min(1, Math.max(0, numberValue(inflation, 0.3))),
    unknown_is_occupied: true,
  });
  const sendPreset = () => command({ command: "direction", direction, speed_mps: speedValue, yaw_radps: yawValue });
  const planStatus = String(plan?.status ?? "No plan");
  const planPath = Array.isArray(plan?.path_xy) ? plan.path_xy.length : 0;

  return (
    <Card className="shadow-sm">
      <CardHeader className="border-b bg-slate-50/70 py-3">
        <CardTitle className="flex items-center gap-2 text-base"><Move className="size-4 text-primary" />Control &amp; navigation</CardTitle>
        <CardDescription>Hold a direction button or use W/S/A/D, arrows and Q/E. Combined keys are supported.</CardDescription>
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
          <p className="text-[11px] leading-4 text-muted-foreground">Motion is {armed ? "armed" : "disarmed"}. Releasing a button sends zero velocity; the backend watchdog also stops on a stale command.</p>
          <div className="space-y-2 border-t pt-3">
            <div className="text-xs font-medium">One-shot direction command</div>
            <div className="flex gap-2"><select value={direction} onChange={(event) => setDirection(event.target.value)} className="h-8 min-w-0 flex-1 rounded-md border border-input bg-background px-2 text-xs"><option value="forward">Forward</option><option value="backward">Backward</option><option value="left">Left strafe</option><option value="right">Right strafe</option><option value="forward_left">Forward-left</option><option value="forward_right">Forward-right</option><option value="backward_left">Backward-left</option><option value="backward_right">Backward-right</option><option value="rotate_left">Rotate left</option><option value="rotate_right">Rotate right</option><option value="stop">Stop</option></select><Button type="button" variant="outline" onClick={sendPreset} disabled={disabled}>Send</Button></div>
          </div>
        </div>

        <div className="space-y-3 rounded-lg border bg-background p-3">
          <div className="flex items-center justify-between"><div><h3 className="flex items-center gap-2 text-sm font-medium"><Crosshair className="size-4 text-primary" />A* map-frame planner</h3><p className="text-xs text-muted-foreground">Global path remains fixed; the backend returns the current local path.</p></div><span className="rounded-md bg-muted px-2 py-1 text-[11px]">{planStatus}</span></div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <label className="space-y-1"><span className="text-muted-foreground">Goal x (m)</span><input value={goalX} onChange={(event) => setGoalX(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
            <label className="space-y-1"><span className="text-muted-foreground">Goal y (m)</span><input value={goalY} onChange={(event) => setGoalY(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
            <label className="space-y-1"><span className="text-muted-foreground">Inflation (m)</span><input value={inflation} onChange={(event) => setInflation(event.target.value)} inputMode="decimal" className="h-8 w-full rounded-md border border-input bg-background px-2" /></label>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button type="button" onClick={sendPlan} disabled={!online}><Crosshair className="size-4" />Plan route</Button>
            <Button type="button" variant="outline" onClick={() => command({ command: "plan_clear" })} disabled={!online}><RotateCcw className="size-4" />Clear plan</Button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
            <span className="rounded-md bg-muted px-2 py-1">Path points: {planPath}</span>
            <span className="rounded-md bg-muted px-2 py-1">Unknown cells: occupied</span>
          </div>
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
