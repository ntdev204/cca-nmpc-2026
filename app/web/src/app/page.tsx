"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Activity, BatteryMedium, Camera, Crosshair, MapPinned, Radar, ScanLine, ShieldCheck, Wifi } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

type Snapshot = {
  backend?: string;
  state?: Record<string, unknown>;
  lidar?: Record<string, unknown>;
  map?: Record<string, unknown>;
  camera?: Record<string, unknown>;
  error?: string;
};

type Pose = { x: number; y: number; yaw: number };
const zero = { vx: 0, vy: 0, wz: 0 };

function asNumber(value: unknown, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function poseFrom(snapshot: Snapshot): Pose {
  const pose = (snapshot.state?.map_pose as number[] | undefined) ?? (snapshot.state?.pose as number[] | undefined) ?? [0, 0, 0];
  return { x: asNumber(pose[0]), y: asNumber(pose[1]), yaw: asNumber(pose[2]) };
}

function MapView({ data, pose }: { data?: Record<string, unknown>; pose: Pose }) {
  const width = Math.max(1, Math.floor(asNumber(data?.width, 1)));
  const height = Math.max(1, Math.floor(asNumber(data?.height, 1)));
  const resolution = asNumber(data?.resolution_m, 0.05);
  const origin = (data?.origin as number[] | undefined) ?? [0, 0];
  const occupancy = (data?.occupancy as number[] | undefined) ?? [];
  const cells: ReactNode[] = [];
  const stride = Math.max(1, Math.ceil(Math.max(width, height) / 140));
  for (let y = 0; y < height; y += stride) {
    for (let x = 0; x < width; x += stride) {
      const value = occupancy[y * width + x];
      if (value === undefined || value < 0) continue;
      cells.push(
        <rect key={`${x}-${y}`} x={x * resolution + origin[0]} y={-(y * resolution + origin[1])} width={resolution * stride} height={resolution * stride} fill={value === 100 ? "#1d5f8f" : "#dcebf5"} />,
      );
    }
  }
  const viewSize = 6;
  return (
    <svg className="h-full min-h-[470px] w-full bg-slate-50" viewBox={`${pose.x - viewSize / 2} ${-pose.y - viewSize / 2} ${viewSize} ${viewSize}`} role="img" aria-label="2D robot map">
      <defs>
        <pattern id="map-grid" width="0.5" height="0.5" patternUnits="userSpaceOnUse">
          <path d="M 0.5 0 L 0 0 0 0.5" fill="none" stroke="#c8dbe8" strokeWidth="0.012" />
        </pattern>
      </defs>
      <rect x={pose.x - viewSize / 2} y={-pose.y - viewSize / 2} width={viewSize} height={viewSize} fill="url(#map-grid)" />
      <g>{cells}</g>
      <line x1={pose.x} y1={-pose.y} x2={pose.x + 0.35 * Math.cos(pose.yaw)} y2={-(pose.y + 0.35 * Math.sin(pose.yaw))} stroke="#0f3552" strokeWidth="0.028" />
      <rect x={pose.x - 0.2} y={-pose.y - 0.2} width="0.4" height="0.4" rx="0.04" fill="#2f80ed" stroke="#0f3552" strokeWidth="0.025" transform={`rotate(${-pose.yaw * 180 / Math.PI} ${pose.x} ${-pose.y})`} />
    </svg>
  );
}

function StatusCard({ icon: Icon, label, value, online }: { icon: LucideIcon; label: string; value: string; online: boolean }) {
  return (
    <Card size="sm" className="bg-card/90 shadow-sm">
      <CardContent className="flex items-center gap-3 p-3">
        <span className="grid size-9 place-items-center rounded-lg bg-accent text-primary"><Icon className="size-4" /></span>
        <span className="min-w-0"><span className="block text-xs text-muted-foreground">{label}</span><span className="flex items-center gap-1.5 font-medium"><span className={`size-1.5 rounded-full ${online ? "bg-emerald-500" : "bg-slate-300"}`} />{value}</span></span>
      </CardContent>
    </Card>
  );
}

export default function Home() {
  const [snapshot, setSnapshot] = useState<Snapshot>({ backend: "connecting" });
  const [busy, setBusy] = useState(false);
  const timer = useRef<number | null>(null);
  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/status", { cache: "no-store" });
      setSnapshot(await response.json());
    } catch (error) {
      setSnapshot({ backend: "offline", error: String(error) });
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const id = window.setInterval(refresh, 600);
    return () => { window.clearTimeout(initial); window.clearInterval(id); };
  }, [refresh]);

  const command = async (payload: Record<string, unknown>) => {
    setBusy(true);
    try {
      const response = await fetch("/api/command", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
      setSnapshot(await response.json());
    } finally {
      setBusy(false);
    }
  };

  const hold = (velocity: typeof zero) => {
    if (timer.current) window.clearInterval(timer.current);
    void command({ command: "velocity", ...velocity });
    timer.current = window.setInterval(() => void command({ command: "velocity", ...velocity }), 160);
  };

  const release = () => {
    if (timer.current) window.clearInterval(timer.current);
    timer.current = null;
    void command({ command: "velocity", ...zero });
  };

  const state = snapshot.state ?? {};
  const status = (state.status as Record<string, unknown> | undefined) ?? {};
  const telemetry = (state.telemetry as Record<string, unknown> | undefined) ?? {};
  const pose = poseFrom(snapshot);
  const online = snapshot.backend === "online";
  const camera = typeof snapshot.camera?.jpeg === "string" ? `data:image/jpeg;base64,${snapshot.camera.jpeg}` : null;
  const lidarPoints = Array.isArray(snapshot.lidar?.points) ? snapshot.lidar.points.length : 0;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-[1600px] space-y-5 p-4 md:p-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div><div className="flex items-center gap-2 text-xs font-semibold tracking-[0.18em] text-primary"><Crosshair className="size-4" />NO-ROS OPERATOR CONSOLE</div><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Mecanum Robot</h1><p className="mt-1 text-sm text-muted-foreground">Live map, sensors and safe teleoperation</p></div>
          <Badge variant={online ? "default" : "destructive"} className="h-7 gap-1.5 px-3 uppercase tracking-[0.12em]"><Wifi className="size-3.5" />{snapshot.backend ?? "offline"}</Badge>
        </header>

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatusCard icon={Activity} label="STM32 controller" value={String(status.stm ?? "offline")} online={status.stm === "online"} />
          <StatusCard icon={Radar} label="N10P LiDAR" value={String(status.lidar ?? "offline")} online={status.lidar === "online"} />
          <StatusCard icon={Camera} label="Astra-S camera" value={String(status.camera ?? "offline")} online={status.camera === "online"} />
          <StatusCard icon={ShieldCheck} label="Motion safety" value={status.armed ? "armed" : "disarmed"} online={Boolean(status.armed)} />
        </section>

        <section className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
          <Card className="overflow-hidden shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between border-b bg-slate-50/70 py-4">
              <div><CardTitle className="flex items-center gap-2"><MapPinned className="size-4 text-primary" />Live 2D map</CardTitle><CardDescription>Map-frame pose follows the latest scan</CardDescription></div>
              <Badge variant="outline" className="gap-1.5 bg-white"><ScanLine className="size-3.5" />{lidarPoints} points</Badge>
            </CardHeader>
            <CardContent className="p-0"><MapView data={snapshot.map?.map as Record<string, unknown> | undefined} pose={pose} /></CardContent>
          </Card>

          <aside className="grid gap-5">
            <Card className="shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="text-base">Telemetry</CardTitle><CardDescription>Map pose {pose.x.toFixed(2)}, {pose.y.toFixed(2)} m</CardDescription></CardHeader>
              <Separator />
              <CardContent className="grid grid-cols-2 gap-3 pt-4">
                <div><p className="text-xs text-muted-foreground">Body velocity</p><p className="font-medium">{asNumber(telemetry.vx_mps).toFixed(2)} / {asNumber(telemetry.vy_mps).toFixed(2)} m/s</p></div>
                <div><p className="text-xs text-muted-foreground">Yaw rate</p><p className="font-medium">{asNumber(telemetry.wz_radps).toFixed(2)} rad/s</p></div>
                <div><p className="text-xs text-muted-foreground">Battery</p><p className="flex items-center gap-1 font-medium"><BatteryMedium className="size-4 text-primary" />{asNumber(telemetry.voltage_v).toFixed(2)} V</p></div>
                <div><p className="text-xs text-muted-foreground">Laser points</p><p className="font-medium">{lidarPoints}</p></div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="text-base">Teleoperation</CardTitle><CardDescription>Hold a direction; release sends zero velocity</CardDescription></CardHeader>
              <Separator />
              <CardContent className="space-y-3 pt-4">
                <div className="flex gap-2"><Button className="flex-1" onClick={() => void command({ command: "arm", enabled: true })} disabled={busy}>Enable motion</Button><Button className="flex-1" variant="destructive" onClick={() => void command({ command: "emergency_stop" })}>Emergency stop</Button></div>
                <div className="mx-auto grid max-w-[220px] grid-cols-3 gap-2">
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="forward left" onPointerDown={() => hold({ vx: 0.2, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↖</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="forward" onPointerDown={() => hold({ vx: 0.2, vy: 0, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↑</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="forward right" onPointerDown={() => hold({ vx: 0.2, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↗</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="left" onPointerDown={() => hold({ vx: 0, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>←</Button>
                  <Button variant="secondary" size="icon" className="h-11 w-11" aria-label="stop" onClick={release}>■</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="right" onPointerDown={() => hold({ vx: 0, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>→</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="backward left" onPointerDown={() => hold({ vx: -0.2, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↙</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="backward" onPointerDown={() => hold({ vx: -0.2, vy: 0, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↓</Button>
                  <Button variant="outline" size="icon" className="h-11 w-11 text-lg" aria-label="backward right" onPointerDown={() => hold({ vx: -0.2, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↘</Button>
                </div>
                <div className="flex gap-2"><Button variant="outline" className="flex-1" onPointerDown={() => hold({ ...zero, wz: 0.6 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↺ Rotate</Button><Button variant="outline" className="flex-1" onPointerDown={() => hold({ ...zero, wz: -0.6 })} onPointerUp={release} onPointerLeave={release} onPointerCancel={release}>↻ Rotate</Button></div>
              </CardContent>
            </Card>

            <Card className="overflow-hidden shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><Camera className="size-4 text-primary" />Astra-S camera</CardTitle><CardDescription>Compressed monitoring frame</CardDescription></CardHeader>
              <Separator />
              <CardContent className="p-3">{camera ? <Image src={camera} alt="Astra-S camera stream" width={384} height={288} unoptimized className="h-auto w-full rounded-lg bg-slate-100 object-cover" /> : <div className="grid min-h-40 place-items-center rounded-lg bg-slate-50 text-sm text-muted-foreground">Camera stream unavailable</div>}</CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="text-base">Map capture</CardTitle><CardDescription>Current scan state: {String(status.scan ?? "idle")}</CardDescription></CardHeader>
              <Separator />
              <CardContent className="flex gap-2 pt-4"><Button variant="outline" className="flex-1" onClick={() => void command({ command: "scan_start" })}>Start</Button><Button variant="outline" className="flex-1" onClick={() => void command({ command: "scan_save" })}>Save</Button><Button variant="secondary" className="flex-1" onClick={() => void command({ command: "scan_stop" })}>Stop</Button></CardContent>
            </Card>
          </aside>
        </section>
        {snapshot.error && <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">{snapshot.error}</p>}
      </div>
    </main>
  );
}
