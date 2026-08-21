"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import type { ReactNode } from "react";

type Snapshot = {
  backend?: string;
  state?: Record<string, unknown>;
  lidar?: Record<string, unknown>;
  map?: Record<string, unknown>;
  camera?: Record<string, unknown>;
  error?: string;
};

const zero = { vx: 0, vy: 0, wz: 0 };

function asNumber(value: unknown, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function poseFrom(snapshot: Snapshot) {
  const pose = (snapshot.state?.map_pose as number[] | undefined) ?? (snapshot.state?.pose as number[] | undefined) ?? [0, 0, 0];
  return { x: asNumber(pose[0]), y: asNumber(pose[1]), yaw: asNumber(pose[2]) };
}

function MapView({ data, pose }: { data?: Record<string, unknown>; pose: { x: number; y: number; yaw: number } }) {
  const width = asNumber(data?.width, 1);
  const height = asNumber(data?.height, 1);
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
        <rect key={`${x}-${y}`} x={x * resolution + origin[0]} y={-(y * resolution + origin[1])} width={resolution * stride} height={resolution * stride} fill={value === 100 ? "#ef6b73" : "#294254"} />,
      );
    }
  }
  const viewSize = 6;
  return (
    <svg className="map" viewBox={`${pose.x - viewSize / 2} ${-pose.y - viewSize / 2} ${viewSize} ${viewSize}`} role="img" aria-label="2D robot map">
      <g>{cells}</g>
      <line x1={pose.x} y1={-pose.y} x2={pose.x + 0.35 * Math.cos(pose.yaw)} y2={-(pose.y + 0.35 * Math.sin(pose.yaw))} stroke="#fff" strokeWidth="0.025" />
      <rect x={pose.x - 0.2} y={-pose.y - 0.2} width="0.4" height="0.4" fill="#2f80ed" stroke="#b9dcff" strokeWidth="0.025" transform={`rotate(${-pose.yaw * 180 / Math.PI} ${pose.x} ${-pose.y})`} />
    </svg>
  );
}

export default function Home() {
  const [snapshot, setSnapshot] = useState<Snapshot>({ backend: "connecting" });
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
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
    const id = setInterval(refresh, 600);
    return () => {
      window.clearTimeout(initial);
      clearInterval(id);
    };
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
    if (timer.current) clearInterval(timer.current);
    void command({ command: "velocity", ...velocity });
    timer.current = setInterval(() => void command({ command: "velocity", ...velocity }), 140);
  };
  const release = () => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    void command({ command: "velocity", ...zero });
  };
  const state = snapshot.state ?? {};
  const status = (state.status as Record<string, unknown> | undefined) ?? {};
  const telemetry = (state.telemetry as Record<string, unknown> | undefined) ?? {};
  const pose = poseFrom(snapshot);
  const camera = typeof snapshot.camera?.jpeg === "string" ? `data:image/jpeg;base64,${snapshot.camera.jpeg}` : null;
  return (
    <main className="shell">
      <header className="topbar"><div><span className="eyebrow">NO-ROS ROBOT CONSOLE</span><h1>Mecanum Robot</h1></div><span className={`connection ${snapshot.backend === "online" ? "online" : "offline"}`}>{snapshot.backend ?? "offline"}</span></header>
      <section className="status-grid">
        <span>STM <b>{String(status.stm ?? "offline")}</b></span><span>N10P <b>{String(status.lidar ?? "offline")}</b></span><span>Astra-S <b>{String(status.camera ?? "offline")}</b></span><span>Motion <b>{status.armed ? "armed" : "disarmed"}</b></span>
      </section>
      <section className="workspace">
        <section className="panel map-panel"><div className="panel-title"><span>Live 2D map</span><small>map pose follows the latest scan</small></div><MapView data={snapshot.map?.map as Record<string, unknown> | undefined} pose={pose} /></section>
        <aside className="side">
          <section className="panel telemetry"><div className="panel-title"><span>Telemetry</span><small>map pose {pose.x.toFixed(2)}, {pose.y.toFixed(2)}</small></div><div className="metrics"><label>Velocity<strong>{asNumber(telemetry.vx_mps).toFixed(2)} / {asNumber(telemetry.vy_mps).toFixed(2)} m/s</strong></label><label>Yaw rate<strong>{asNumber(telemetry.wz_radps).toFixed(2)} rad/s</strong></label><label>Battery<strong>{asNumber(telemetry.voltage_v).toFixed(2)} V</strong></label><label>Laser points<strong>{Array.isArray(snapshot.lidar?.points) ? snapshot.lidar?.points.length : 0}</strong></label></div></section>
          <section className="panel controls"><div className="panel-title"><span>Teleoperation</span><small>hold a direction</small></div><div className="control-row"><button onClick={() => void command({ command: "arm", enabled: true })} disabled={busy}>Enable</button><button className="danger" onClick={() => void command({ command: "emergency_stop" })}>Emergency stop</button></div><div className="pad"><button onPointerDown={() => hold({ vx: 0.2, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↖</button><button onPointerDown={() => hold({ vx: 0.2, vy: 0, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↑</button><button onPointerDown={() => hold({ vx: 0.2, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↗</button><button onPointerDown={() => hold({ vx: 0, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>←</button><button className="stop" onClick={release}>■</button><button onPointerDown={() => hold({ vx: 0, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>→</button><button onPointerDown={() => hold({ vx: -0.2, vy: 0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↙</button><button onPointerDown={() => hold({ vx: -0.2, vy: 0, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↓</button><button onPointerDown={() => hold({ vx: -0.2, vy: -0.2, wz: 0 })} onPointerUp={release} onPointerCancel={release}>↘</button></div><div className="control-row"><button onPointerDown={() => hold({ ...zero, wz: 0.6 })} onPointerUp={release} onPointerCancel={release}>↺ Rotate</button><button onPointerDown={() => hold({ ...zero, wz: -0.6 })} onPointerUp={release} onPointerCancel={release}>↻ Rotate</button></div></section>
          <section className="panel camera-panel"><div className="panel-title"><span>Astra-S</span><small>monitoring frame</small></div>{camera ? <Image src={camera} alt="Astra-S camera stream" width={640} height={480} unoptimized /> : <div className="empty">Camera stream unavailable</div>}</section>
          <section className="panel scan-controls"><div className="panel-title"><span>Map capture</span><small>{String(status.scan ?? "idle")}</small></div><div className="control-row"><button onClick={() => void command({ command: "scan_start" })}>Start scan</button><button onClick={() => void command({ command: "scan_save" })}>Save</button><button onClick={() => void command({ command: "scan_stop" })}>Stop</button></div></section>
        </aside>
      </section>
      {snapshot.error && <p className="error">{snapshot.error}</p>}
    </main>
  );
}
