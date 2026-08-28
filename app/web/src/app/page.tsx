"use client";
/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  BatteryMedium,
  Camera,
  Crosshair,
  Database,
  LayoutDashboard,
  MapPinned,
  Radar,
  ScanLine,
  ShieldCheck,
  ShieldOff,
  Wifi,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MapCapturePanel, type SavedMap } from "@/components/map-capture-panel";
import { ControlPanel } from "@/components/control-panel";
import { HistoryPanel } from "@/components/history-panel";

type Snapshot = {
  backend?: string;
  state?: Record<string, unknown>;
  lidar?: Record<string, unknown>;
  map?: Record<string, unknown>;
  events?: Record<string, unknown>[];
  error?: string;
};

type Pose = { x: number; y: number; yaw: number };
type Point = [number, number];
type TfFrame = {
  parent?: string;
  child?: string;
  translation_m?: number[];
  yaw_rad?: number;
  pitch_rad?: number;
};
type TfPayload = { fixed_frame?: string; frames?: TfFrame[]; footprint?: Record<string, unknown> };
type MapPlan = { path_xy?: number[][] };
type MapViewport = { x: number; y: number; width: number; height: number };
type DashboardView = "overview" | "monitor" | "control" | "mapping" | "telemetry";

const DASHBOARD_VIEWS: Array<{ id: DashboardView; label: string; icon: typeof LayoutDashboard }> = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "monitor", label: "Monitor", icon: MapPinned },
  { id: "control", label: "Control", icon: Crosshair },
  { id: "mapping", label: "Mapping & data", icon: Database },
  { id: "telemetry", label: "Telemetry", icon: Activity },
];

const CAMERA_WEBRTC_URL = process.env.NEXT_PUBLIC_ROBOT_WEBRTC_URL ?? "http://100.69.39.18:8766/webrtc/offer";

async function waitForIceGathering(peer: RTCPeerConnection): Promise<void> {
  if (peer.iceGatheringState === "complete") return;
  await new Promise<void>((resolve) => {
    const finish = () => {
      window.clearTimeout(timeout);
      peer.removeEventListener("icegatheringstatechange", onChange);
      resolve();
    };
    const onChange = () => {
      if (peer.iceGatheringState === "complete") finish();
    };
    const timeout = window.setTimeout(finish, 4000);
    peer.addEventListener("icegatheringstatechange", onChange);
  });
}

function asNumber(value: unknown, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function poseFrom(snapshot: Snapshot): Pose {
  const pose = (snapshot.state?.map_pose as number[] | undefined) ?? (snapshot.state?.pose as number[] | undefined) ?? [0, 0, 0];
  return { x: asNumber(pose[0]), y: asNumber(pose[1]), yaw: asNumber(pose[2]) };
}

function frameFrom(tf: TfPayload | undefined, child: string): TfFrame {
  const frame = (tf?.frames ?? []).find((item) => item?.child === child);
  return frame ?? {};
}

function translationFrom(frame: TfFrame): Point {
  return [asNumber(frame.translation_m?.[0]), asNumber(frame.translation_m?.[1])];
}

function worldToSvg(x: number, y: number): Point {
  return [x, -y];
}

function MapToggle({ checked, label, onChange }: { checked: boolean; label: string; onChange: (value: boolean) => void }) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground shadow-sm hover:bg-muted">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="accent-primary" />
      {label}
    </label>
  );
}

function formatAge(timestampNs: unknown): string {
  const timestamp = asNumber(timestampNs, 0);
  if (!timestamp) return "—";
  const ageMs = Math.max(0, Date.now() - timestamp / 1e6);
  if (ageMs < 1000) return `${Math.round(ageMs)} ms ago`;
  return `${(ageMs / 1000).toFixed(1)} s ago`;
}

function LidarView({ points }: { points: number[][] }) {
  const size = 330;
  const center = size / 2;
  const scale = 34;
  const rings = [1, 2, 3, 4, 5, 6];
  return (
    <div className="relative mx-auto aspect-square max-h-[210px] max-w-[210px] w-full overflow-hidden rounded-lg border bg-slate-950 p-2">
      <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full" role="img" aria-label="Live N10P LiDAR polar view">
        <g stroke="#1e3a5f" fill="none" strokeWidth="0.8">
          {rings.map((ring) => <circle key={ring} cx={center} cy={center} r={ring * scale} />)}
          <path d={`M ${center} 8 V ${size - 8} M 8 ${center} H ${size - 8}`} />
        </g>
        <g fill="#22c55e">
          {points.map((point, index) => {
            const angle = asNumber(point?.[0], Number.NaN);
            const distance = asNumber(point?.[1], Number.NaN);
            if (!Number.isFinite(angle) || !Number.isFinite(distance) || distance <= 0) return null;
            const radius = Math.min(6 * scale, distance * scale);
            return <circle key={index} cx={center + radius * Math.cos(angle)} cy={center - radius * Math.sin(angle)} r="1.7" opacity="0.85" />;
          })}
        </g>
        <circle cx={center} cy={center} r="5" fill="#38bdf8" stroke="#e0f2fe" strokeWidth="1" />
        <line x1={center} y1={center} x2={center + 24} y2={center} stroke="#f8fafc" strokeWidth="2" />
      </svg>
      <div className="pointer-events-none absolute left-3 top-3 rounded bg-slate-900/75 px-2 py-1 text-[11px] text-slate-100">N10P · 0–6 m</div>
      <div className="pointer-events-none absolute bottom-3 left-3 rounded bg-slate-900/75 px-2 py-1 text-[11px] text-slate-300">green: returns · blue: robot</div>
    </div>
  );
}

function OccupancyCanvas({ data, viewport }: { data?: Record<string, unknown>; viewport: MapViewport }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const width = Math.max(1, Math.floor(asNumber(data?.width, 1)));
  const height = Math.max(1, Math.floor(asNumber(data?.height, 1)));
  const resolution = Math.max(0.001, asNumber(data?.resolution_m, 0.025));
  const origin = (data?.origin as number[] | undefined) ?? [0, 0, 0];
  const originX = asNumber(origin[0]);
  const originY = asNumber(origin[1]);
  const rawOccupancy = data?.occupancy;
  const occupancy = Array.isArray(rawOccupancy) ? rawOccupancy as number[] : undefined;
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const pixelsWide = Math.max(1, Math.ceil(viewport.width / resolution));
    const pixelsHigh = Math.max(1, Math.ceil(viewport.height / resolution));
    canvas.width = pixelsWide;
    canvas.height = pixelsHigh;
    const context = canvas.getContext("2d");
    if (!context) return;
    const image = context.createImageData(pixelsWide, pixelsHigh);
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const value = occupancy?.[y * width + x];
        if (value !== 100 && value !== 0) continue;
        const px = Math.floor((originX + x * resolution - viewport.x) / resolution);
        const py = Math.floor((-(originY + (y + 1) * resolution) - viewport.y) / resolution);
        if (px < 0 || py < 0 || px >= pixelsWide || py >= pixelsHigh) continue;
        const index = (py * pixelsWide + px) * 4;
        if (value === 100) {
          image.data[index] = 21;
          image.data[index + 1] = 94;
          image.data[index + 2] = 117;
          image.data[index + 3] = 255;
        } else {
          image.data[index] = 226;
          image.data[index + 1] = 232;
          image.data[index + 2] = 240;
          image.data[index + 3] = 120;
        }
      }
    }
    context.putImageData(image, 0, 0);
  }, [height, occupancy, originX, originY, resolution, viewport.height, viewport.width, viewport.x, viewport.y, width]);
  return <canvas ref={canvasRef} className="pointer-events-none absolute inset-0 h-full w-full object-contain" aria-hidden="true" />;
}

function MapView({
  data,
  pose,
  lidar,
  tf,
  trace,
  history,
  plan,
  showLaser,
  showTrace,
  showPath,
}: {
  data?: Record<string, unknown>;
  pose: Pose;
  lidar: number[][];
  tf?: TfPayload;
  trace: Point[];
  history: Point[];
  plan?: MapPlan;
  showLaser: boolean;
  showTrace: boolean;
  showPath: boolean;
}) {
  const width = Math.max(1, Math.floor(asNumber(data?.width, 1)));
  const height = Math.max(1, Math.floor(asNumber(data?.height, 1)));
  const resolution = Math.max(0.001, asNumber(data?.resolution_m, 0.025));
  const origin = (data?.origin as number[] | undefined) ?? [0, 0, 0];
  const originX = asNumber(origin[0]);
  const originY = asNumber(origin[1]);

  const mapWidth = width * resolution;
  const mapHeight = height * resolution;
  const mapBounds = useMemo<MapViewport>(() => ({
    x: originX - 0.25,
    y: -(originY + mapHeight) - 0.25,
    width: Math.max(mapWidth + 0.5, 2),
    height: Math.max(mapHeight + 0.5, 2),
  }), [mapHeight, mapWidth, originX, originY]);
  const [fixedViewport, setFixedViewport] = useState<MapViewport | null>(null);
  const previousScans = useRef(0);
  const previousMapKey = useRef("");
  const metadata = data?.metadata as Record<string, unknown> | undefined;
  const scanCount = asNumber(metadata?.scans, 0);
  const mapId = String(metadata?.map_id ?? "");
  const mapKey = mapId || `${width}:${height}:${resolution}:${originX}:${originY}`;
  useEffect(() => {
    if (previousMapKey.current !== mapKey) {
      previousMapKey.current = mapKey;
      previousScans.current = scanCount;
      setFixedViewport(mapBounds);
      return;
    }
    if (scanCount <= 0) return;
    setFixedViewport((current) => {
      if (current === null || scanCount < previousScans.current) return mapBounds;
      return current;
    });
    previousScans.current = scanCount;
  }, [mapBounds, mapKey, scanCount]);
  const viewport = fixedViewport ?? mapBounds;
  const viewBox = `${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`;
  const radius = Math.max(0.05, asNumber(tf?.footprint?.circumscribed_radius_m, 0.2828427));
  const laserFrame = frameFrom(tf, "laser");
  const [laserX, laserY] = translationFrom(laserFrame);
  const laserWorldX = pose.x + Math.cos(pose.yaw) * laserX - Math.sin(pose.yaw) * laserY;
  const laserWorldY = pose.y + Math.sin(pose.yaw) * laserX + Math.cos(pose.yaw) * laserY;
  const robotSvg = worldToSvg(pose.x, pose.y);
  const laserRays: ReactNode[] = [];
  if (showLaser) {
    lidar.forEach((raw, index) => {
      const angle = asNumber(raw?.[0], Number.NaN);
      const distance = asNumber(raw?.[1], Number.NaN);
      if (!Number.isFinite(angle) || !Number.isFinite(distance) || distance <= 0) return;
      const globalAngle = pose.yaw + asNumber(laserFrame.yaw_rad) + angle;
      const [startX, startY] = worldToSvg(
        pose.x + radius * Math.cos(globalAngle),
        pose.y + radius * Math.sin(globalAngle),
      );
      const [endX, endY] = worldToSvg(
        laserWorldX + distance * Math.cos(globalAngle),
        laserWorldY + distance * Math.sin(globalAngle),
      );
      laserRays.push(<line key={`ray-${index}`} x1={startX} y1={startY} x2={endX} y2={endY} stroke="#16a34a" strokeWidth="0.012" opacity="0.7" />);
      laserRays.push(<circle key={`hit-${index}`} cx={endX} cy={endY} r="0.018" fill="#15803d" opacity="0.85" />);
    });
  }

  const tracePoints = (history.length > 1 ? history : trace).map(([x, y]) => worldToSvg(x, y).join(",")).join(" ");
  const planPoints = (plan?.path_xy ?? []).map((point) => worldToSvg(asNumber(point?.[0]), asNumber(point?.[1])).join(",")).join(" ");
  return (
    <div className="relative h-[520px] w-full overflow-hidden bg-slate-50">
      <OccupancyCanvas data={data} viewport={viewport} />
      <svg className="absolute inset-0 h-full w-full" viewBox={viewBox} role="img" aria-label="Fixed 2D map with robot footprint and LiDAR" shapeRendering="geometricPrecision">
        <defs>
          <pattern id="map-grid" width="0.5" height="0.5" patternUnits="userSpaceOnUse">
            <path d="M 0.5 0 L 0 0 0 0.5" fill="none" stroke="#cbd5e1" strokeWidth="0.012" />
          </pattern>
        </defs>
        <rect x={viewport.x} y={viewport.y} width={viewport.width} height={viewport.height} fill="url(#map-grid)" />
        {showTrace && tracePoints && <polyline points={tracePoints} fill="none" stroke="#7c3aed" strokeWidth="0.028" opacity="0.75" />}
        {showPath && planPoints && <polyline points={planPoints} fill="none" stroke="#ea580c" strokeWidth="0.04" strokeDasharray="0.12 0.06" />}
        <g className="laser-layer">
          {laserRays}
          {showLaser && <circle cx={worldToSvg(laserWorldX, laserWorldY)[0]} cy={worldToSvg(laserWorldX, laserWorldY)[1]} r="0.06" fill="none" stroke="#16a34a" strokeWidth="0.018" />}
        </g>
        <circle cx={robotSvg[0]} cy={robotSvg[1]} r={radius} fill="none" stroke="#0f172a" strokeWidth="0.025" strokeDasharray="0.08 0.05" />
        <rect x={pose.x - 0.2} y={-pose.y - 0.2} width="0.4" height="0.4" rx="0.035" fill="#2563eb" stroke="#0f172a" strokeWidth="0.025" transform={`rotate(${-pose.yaw * 180 / Math.PI} ${pose.x} ${-pose.y})`} />
        <line x1={robotSvg[0]} y1={robotSvg[1]} x2={robotSvg[0] + 0.32 * Math.cos(pose.yaw)} y2={robotSvg[1] - 0.32 * Math.sin(pose.yaw)} stroke="#ffffff" strokeWidth="0.035" />
      </svg>
      <div className="pointer-events-none absolute left-3 top-3 flex flex-wrap gap-1.5 text-[11px]">
        <span className="rounded bg-white/90 px-2 py-1 text-slate-700 shadow">laser rays start at circumscribed footprint</span>
      </div>
      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-2 rounded-md bg-white/90 px-2 py-1.5 text-[11px] shadow">
        <span className="flex items-center gap-1"><i className="size-2 rounded-full bg-cyan-700" />occupied</span>
        <span className="flex items-center gap-1"><i className="size-2 rounded-full bg-sky-200" />free</span>
        <span className="flex items-center gap-1"><i className="size-2 rounded-full bg-green-600" />laser</span>
        <span className="flex items-center gap-1"><i className="size-2 rounded-full bg-orange-500" />planned path</span>
      </div>
    </div>
  );
}

export default function Home() {
  const [snapshot, setSnapshot] = useState<Snapshot>({ backend: "connecting" });
  const [view, setView] = useState<DashboardView>("overview");
  const [showLaser, setShowLaser] = useState(false);
  const [showTrace, setShowTrace] = useState(true);
  const [showPath, setShowPath] = useState(true);
  const [trace, setTrace] = useState<Point[]>([]);
  const [selectedMapId, setSelectedMapId] = useState("");
  const cameraVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraPeerRef = useRef<RTCPeerConnection | null>(null);
  const [cameraConnection, setCameraConnection] = useState("idle");
  const [cameraFallback, setCameraFallback] = useState(false);
  const firstRefresh = useRef(true);

  const selectView = useCallback((next: DashboardView) => {
    setView(next);
    const query = next === "overview" ? "" : `?view=${next}`;
    window.history.pushState({}, "", `/${query}`);
  }, []);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("view") as DashboardView | null;
    if (requested && DASHBOARD_VIEWS.some((item) => item.id === requested)) setView(requested);
    const onPopState = () => {
      const next = new URLSearchParams(window.location.search).get("view") as DashboardView | null;
      if (next && DASHBOARD_VIEWS.some((item) => item.id === next)) setView(next);
      else setView("overview");
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const mergeSnapshot = useCallback((previous: Snapshot, next: Snapshot): Snapshot => ({
    ...previous,
    ...next,
    state: next.state ?? previous.state,
    lidar: next.lidar ?? previous.lidar,
    map: next.map ?? previous.map,
    events: next.events ?? previous.events,
    error: next.error,
  }), []);

  const refresh = useCallback(async () => {
    try {
      const endpoint = firstRefresh.current ? "/api/status?full=1" : "/api/status";
      firstRefresh.current = false;
      const response = await fetch(endpoint, { cache: "no-store" });
      const body = (await response.json()) as Snapshot;
      setSnapshot((previous) => mergeSnapshot(previous, body));
      const nextPose = body.state ? poseFrom(body) : null;
      if (!nextPose) return;
      setTrace((previous) => {
        const last = previous[previous.length - 1];
        if (last && Math.hypot(nextPose.x - last[0], nextPose.y - last[1]) < 0.01) return previous;
        return [...previous, [nextPose.x, nextPose.y] as Point].slice(-1500);
      });
    } catch (error) {
      firstRefresh.current = true;
      setSnapshot((previous) => ({ ...previous, backend: "offline", error: String(error) }));
    }
  }, [mergeSnapshot]);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const id = window.setInterval(() => void refresh(), 250);
    return () => { window.clearTimeout(initial); window.clearInterval(id); };
  }, [refresh]);

  const pose = poseFrom(snapshot);

  const command = useCallback(async (payload: Record<string, unknown>) => {
    try {
      const response = await fetch("/api/command", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
      const body = (await response.json()) as Snapshot;
      setSnapshot((previous) => mergeSnapshot(previous, body));
    } catch (error) {
      setSnapshot((previous) => ({ ...previous, backend: "offline", error: String(error) }));
    }
  }, [mergeSnapshot]);

  const state = snapshot.state ?? {};
  const status = (state.status as Record<string, unknown> | undefined) ?? {};
  const armed = status.armed === true || status.armed === "true";
  const telemetry = (state.telemetry as Record<string, unknown> | undefined) ?? {};
  const poseDiagnostics = (state.pose_diagnostics as Record<string, unknown> | undefined) ?? {};
  const tf = (state.tf as TfPayload | undefined);
  const mapData = snapshot.map?.map as Record<string, unknown> | undefined;
  const plan = snapshot.map?.plan as MapPlan | undefined;
  const lidar = useMemo(() => (Array.isArray(snapshot.lidar?.points) ? snapshot.lidar.points as number[][] : []), [snapshot.lidar]);
  const mapHistory = useMemo(() => {
    const historyPayload = (mapData?.metadata as Record<string, unknown> | undefined)?.history as Record<string, unknown> | undefined;
    const trajectory = Array.isArray(historyPayload?.trajectory) ? historyPayload.trajectory : [];
    return trajectory.filter((point): point is number[] => Array.isArray(point) && point.length >= 2).map((point) => [asNumber(point[0]), asNumber(point[1])] as Point);
  }, [mapData]);
  const online = snapshot.backend === "online";
  const cameraOnline = online && status.camera === "online";
  const cameraActive = cameraOnline && view !== "telemetry";
  const dataset = (status.dataset as Record<string, unknown> | undefined) ?? {};
  const savedMaps = useMemo<SavedMap[]>(() => {
    if (!Array.isArray(status.maps)) return [];
    return status.maps.filter((item): item is SavedMap => Boolean(item && typeof item === "object"));
  }, [status.maps]);
  useEffect(() => {
    const statusMapId = String(status.selected_map ?? "");
    const preferred = statusMapId || String(savedMaps.find((map) => map.selected)?.run_id ?? "");
    setSelectedMapId((current) => current && savedMaps.some((map) => String(map.run_id ?? "") === current) ? current : preferred);
  }, [savedMaps, status.selected_map]);
  const cameraTimestamp = state.camera_capture_t_ns;
  const lidarAge = formatAge(snapshot.lidar?.t_ns);
  const cameraAge = formatAge(cameraTimestamp);
  const lastEvent = snapshot.events?.[snapshot.events.length - 1];
  const activeView = DASHBOARD_VIEWS.find((item) => item.id === view) ?? DASHBOARD_VIEWS[0];

  useEffect(() => {
    if (!cameraActive) {
      cameraPeerRef.current?.close();
      cameraPeerRef.current = null;
      if (cameraVideoRef.current) cameraVideoRef.current.srcObject = null;
      setCameraConnection("idle");
      setCameraFallback(false);
      return;
    }
    let cancelled = false;
    const videoElement = cameraVideoRef.current;
    if (typeof RTCPeerConnection === "undefined") {
      setCameraFallback(true);
      setCameraConnection("mjpeg-fallback: WebRTC unavailable");
      return () => { cancelled = true; };
    }
    const peer = new RTCPeerConnection({ iceServers: [] });
    cameraPeerRef.current = peer;
    setCameraFallback(false);
    setCameraConnection("connecting");
    peer.addTransceiver("video", { direction: "recvonly" });
    peer.ontrack = (event) => {
      if (cancelled) return;
      const stream = event.streams[0] ?? new MediaStream([event.track]);
      if (videoElement) {
        videoElement.srcObject = stream;
        void videoElement.play().catch(() => undefined);
      }
      setCameraConnection("connected");
    };
    peer.onconnectionstatechange = () => {
      if (peer.connectionState === "connected") setCameraConnection("connected");
      if (["failed", "closed"].includes(peer.connectionState)) {
        setCameraFallback(true);
        setCameraConnection("mjpeg-fallback: WebRTC connection failed");
      }
    };
    void (async () => {
      try {
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        await waitForIceGathering(peer);
        if (cancelled || !peer.localDescription) return;
        const response = await fetch(CAMERA_WEBRTC_URL, {
          method: "POST",
          mode: "cors",
          cache: "no-store",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ type: peer.localDescription.type, sdp: peer.localDescription.sdp }),
        });
        if (!response.ok) throw new Error(`WebRTC offer failed (${response.status})`);
        const answer = (await response.json()) as RTCSessionDescriptionInit;
        await peer.setRemoteDescription(answer);
      } catch (error) {
        if (!cancelled) {
          peer.close();
          if (cameraPeerRef.current === peer) cameraPeerRef.current = null;
          setCameraFallback(true);
          setCameraConnection(`mjpeg-fallback: ${String(error)}`);
        }
      }
    })();
    return () => {
      cancelled = true;
      peer.ontrack = null;
      peer.onconnectionstatechange = null;
      peer.close();
      if (cameraPeerRef.current === peer) cameraPeerRef.current = null;
      if (videoElement) videoElement.srcObject = null;
    };
  }, [cameraActive]);

  return (
    <main className="min-h-screen bg-slate-50 text-foreground">
      <div className="flex min-h-screen">
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r bg-card lg:flex">
          <div className="border-b px-5 py-5">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-[0.16em] text-primary"><Crosshair className="size-4" />MECANUM ROBOT</div>
            <p className="mt-2 text-xs text-muted-foreground">Operator dashboard</p>
          </div>
          <nav className="flex-1 space-y-1 p-3" aria-label="Robot console navigation">
            {DASHBOARD_VIEWS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => selectView(id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors ${view === id ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}
                aria-current={view === id ? "page" : undefined}
              >
                <Icon className="size-4" />
                <span>{id === "mapping" ? "Mapping & data" : label}</span>
                {view === id && <span className="ml-auto size-1.5 rounded-full bg-current" />}
              </button>
            ))}
          </nav>
          <div className="m-3 rounded-lg border bg-slate-50 p-3">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Live status</p>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between"><span>Backend</span><span className="flex items-center gap-1.5"><i className={`size-1.5 rounded-full ${online ? "bg-emerald-500" : "bg-red-500"}`} />{online ? "online" : "offline"}</span></div>
              <div className="flex items-center justify-between"><span>LiDAR</span><span className="flex items-center gap-1.5"><i className={`size-1.5 rounded-full ${status.lidar === "online" ? "bg-emerald-500" : "bg-red-500"}`} />{String(status.lidar ?? "offline")}</span></div>
              <div className="flex items-center justify-between"><span>Astra-S</span><span className="flex items-center gap-1.5"><i className={`size-1.5 rounded-full ${status.camera === "online" ? "bg-emerald-500" : "bg-red-500"}`} />{String(status.camera ?? "offline")}</span></div>
              <div className="flex items-center justify-between"><span>Motion</span><span className={armed ? "font-medium text-emerald-700" : "font-medium text-amber-700"}>{armed ? "armed" : "disarmed"}</span></div>
            </div>
          </div>
        </aside>
        <div className="min-w-0 flex-1">
      <div className="mx-auto max-w-[1680px] space-y-4 p-4 md:p-6">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div><div className="flex items-center gap-2 text-xs font-semibold tracking-[0.18em] text-primary"><Crosshair className="size-4" />NO-ROS WEB CONSOLE</div><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{activeView.label}</h1><p className="mt-1 text-sm text-muted-foreground">Mecanum Robot · fixed map, Astra-S view and keyboard control</p></div>
          <div className="flex flex-wrap items-center justify-end gap-1.5 text-xs">
            <Badge variant={online ? "default" : "destructive"} className="h-7 gap-1.5 px-3 uppercase tracking-[0.12em]"><Wifi className="size-3.5" />{snapshot.backend ?? "offline"}</Badge>
            <Badge variant="outline" className="bg-white">Pose {pose.x.toFixed(2)}, {pose.y.toFixed(2)} m · {(pose.yaw * 180 / Math.PI).toFixed(1)}°</Badge>
            <Badge variant="outline" className="bg-white">v {asNumber(telemetry.vx_mps).toFixed(2)} / {asNumber(telemetry.vy_mps).toFixed(2)} m/s</Badge>
            <Badge variant="outline" className="bg-white">speed {asNumber(poseDiagnostics.speed_mps).toFixed(2)} m/s</Badge>
            <Badge variant="outline" className="bg-white">ω {asNumber(telemetry.wz_radps).toFixed(2)} / gyro {asNumber(telemetry.gyro_z_radps).toFixed(2)}</Badge>
            <Badge variant="outline" className="bg-white">yaw source {String(poseDiagnostics.yaw_rate_source ?? "none")}</Badge>
            <Badge variant="outline" className="gap-1 bg-white"><BatteryMedium className="size-3.5 text-primary" />{asNumber(telemetry.voltage_v).toFixed(2)} V</Badge>
            <Badge variant="outline" className="gap-1 bg-white"><Radar className="size-3.5 text-primary" />{asNumber(status.lidar_rate_hz).toFixed(1)} Hz</Badge>
            <Badge variant="outline" className="gap-1 bg-white"><Camera className="size-3.5 text-primary" />{String(status.camera_transport ?? "webrtc-h264")} · {asNumber(status.camera_rate_hz).toFixed(1)} fps</Badge>
            <Button
              type="button"
              size="sm"
              variant={armed ? "default" : "outline"}
              disabled={!online}
              aria-pressed={armed}
              onClick={() => void command({ command: "arm", enabled: !armed })}
              title={armed ? "Disable motion" : "Enable motion"}
            >
              {armed ? <ShieldCheck className="size-3.5" /> : <ShieldOff className="size-3.5" />}
              {armed ? "Motion ON" : "Motion OFF"}
            </Button>
          </div>
        </header>
        <nav className="flex gap-1 overflow-x-auto rounded-lg border bg-card p-1 shadow-sm lg:hidden" aria-label="Robot console navigation">
          {DASHBOARD_VIEWS.map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => selectView(id)} className={`inline-flex shrink-0 items-center gap-1.5 rounded-md px-3 py-2 text-xs font-medium transition-colors ${view === id ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`} aria-current={view === id ? "page" : undefined}><Icon className="size-3.5" />{id === "mapping" ? "Mapping" : label}</button>)}
        </nav>
        {lastEvent && <div className="rounded-lg border bg-card px-3 py-2 text-xs text-muted-foreground"><span className="font-medium text-foreground">Last backend event:</span> {String(lastEvent.event ?? lastEvent.type ?? "event")} {lastEvent.message ? `· ${String(lastEvent.message)}` : ""}</div>}

        {(view === "overview" || view === "monitor" || view === "control" || view === "mapping") && <Card className="overflow-hidden shadow-sm">
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 border-b bg-slate-50/70 py-3">
            <div><CardTitle className="flex items-center gap-2"><MapPinned className="size-4 text-primary" />Map &amp; camera monitor</CardTitle><CardDescription>Fixed viewport · {asNumber(mapData?.resolution_m, asNumber(status.map_resolution_m, 0.025)) * 1000} mm cells · odometry marker</CardDescription></div>
            <div className="flex flex-wrap items-center gap-1.5">
              <MapToggle checked={showLaser} label="Laser" onChange={setShowLaser} />
              <MapToggle checked={showTrace} label="Trace" onChange={setShowTrace} />
              <MapToggle checked={showPath} label="Path" onChange={setShowPath} />
              <Badge variant="outline" className="gap-1.5 bg-white"><ScanLine className="size-3.5" />{lidar.length} points</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 p-3 xl:grid-cols-[minmax(0,1fr)_minmax(280px,0.38fr)]">
            <MapView data={mapData} pose={pose} lidar={lidar} tf={tf} trace={trace} history={mapHistory} plan={plan} showLaser={showLaser} showTrace={showTrace} showPath={showPath} />
            <section className="flex min-h-[520px] flex-col rounded-lg border bg-slate-950/5 p-2" aria-label="Astra-S camera monitor">
              <div className="flex items-center justify-between px-1 pb-2"><div className="flex items-center gap-2 text-sm font-medium"><Camera className="size-4 text-primary" />Astra-S camera</div><span className="text-xs text-muted-foreground">{cameraAge}</span></div>
              <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-md bg-slate-100">{cameraOnline && cameraFallback ? <><span className="sr-only">Astra-S MJPEG fallback stream</span>{/* MJPEG multipart must stay an img stream. */}<img src="/api/camera" className="max-h-full w-full object-contain" alt="Astra-S MJPEG camera stream" /></> : cameraOnline && !cameraConnection.startsWith("failed") ? <><span className="sr-only">Astra-S WebRTC H.264 stream</span><video ref={cameraVideoRef} muted autoPlay playsInline className="max-h-full w-full object-contain" aria-label="Astra-S WebRTC H.264 camera stream" /></> : <p className="px-3 text-center text-sm text-muted-foreground">{cameraConnection.startsWith("failed") ? cameraConnection : "Camera stream unavailable"}</p>}</div>
              <div className="flex items-center justify-between px-1 pt-2 text-xs text-muted-foreground"><span>{dataset.active ? "recording frame" : "monitoring only"}</span><span>{cameraFallback ? "MJPEG fallback" : "WebRTC · H.264"} · {cameraConnection} · 0° level</span></div>
            </section>
          </CardContent>
        </Card>}

        {(view === "overview" || view === "monitor") && <section className="grid items-start gap-4 xl:grid-cols-[minmax(260px,0.45fr)_minmax(0,1fr)]">
          <Card className="overflow-hidden shadow-sm">
            <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-base"><Radar className="size-4 text-primary" />Live LiDAR</CardTitle><CardDescription>{lidar.length} returns · {lidarAge}</CardDescription></CardHeader>
            <Separator />
            <CardContent className="p-3"><LidarView points={lidar} /></CardContent>
          </Card>
        </section>}
        {(view === "overview" || view === "control") && <ControlPanel online={online} armed={armed} command={(payload) => void command(payload)} plan={plan as Record<string, unknown> | undefined} />}
        {(view === "overview" || view === "mapping") && <MapCapturePanel
          online={online}
          dataset={dataset}
          status={status}
          maps={savedMaps}
          selectedMapId={selectedMapId}
          onSelectMap={setSelectedMapId}
          onCommand={(payload) => void command(payload)}
        />}
        {(view === "overview" || view === "telemetry") && <HistoryPanel />}
        {snapshot.error && <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">{snapshot.error}</p>}
      </div>
        </div>
      </div>
    </main>
  );
}
