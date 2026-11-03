"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, ArrowDownToLine, CircleStop, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";

type Command = (payload: Record<string, unknown>) => void;
type Props = { online: boolean; armed: boolean; command: Command; telemetry?: Record<string, unknown> };
type BodyVelocity = { vx: number; vy: number; wz: number };
type EncoderSample = BodyVelocity & { tNs: number };
const WHEEL_RADIUS_M = 0.05;
const LEVER_ARM_M = 0.156 + 0.176;
const ZERO = { command: "velocity", vx: 0, vy: 0, wz: 0 };
const parse = (value: string) => Number.isFinite(Number(value)) ? Number(value) : 0;
const fmt = (value: number, digits = 3) => Number(value.toFixed(digits));

export function KinematicsLab({ online, armed, command, telemetry }: Props) {
  const [wheels, setWheels] = useState(["0", "0", "0", "0"]);
  const [distance, setDistance] = useState("1.0");
  const [heading, setHeading] = useState("0");
  const [forwardDuration, setForwardDuration] = useState("3");
  const [inverseDuration, setInverseDuration] = useState("3");
  const [running, setRunning] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [commanded, setCommanded] = useState<BodyVelocity>({ vx: 0, vy: 0, wz: 0 });
  const [encoderDistance, setEncoderDistance] = useState(0);
  const [feedbackStatus, setFeedbackStatus] = useState("Chờ dữ liệu encoder từ STM.");
  const [notice, setNotice] = useState("Nhập thông số để xem kết quả dự kiến.");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const interval = useRef<ReturnType<typeof setInterval> | null>(null);
  const settleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const trackingRef = useRef(false);
  const settlingRef = useRef(false);
  const stoppedSamples = useRef(0);
  const previousEncoderSample = useRef<EncoderSample | null>(null);
  const commandRef = useRef(command);
  useEffect(() => { commandRef.current = command; }, [command]);
  const encoderSample = useMemo<EncoderSample | null>(() => {
    const tNs = Number(telemetry?.t_ns);
    const vx = Number(telemetry?.vx_mps);
    const vy = Number(telemetry?.vy_mps);
    const wz = Number(telemetry?.wz_radps);
    if (![tNs, vx, vy, wz].every(Number.isFinite) || tNs <= 0) return null;
    return { tNs, vx, vy, wz };
  }, [telemetry?.t_ns, telemetry?.vx_mps, telemetry?.vy_mps, telemetry?.wz_radps]);
  const finishMeasurement = useCallback(() => {
    trackingRef.current = false;
    settlingRef.current = false;
    stoppedSamples.current = 0;
    if (settleTimer.current) clearTimeout(settleTimer.current);
    settleTimer.current = null;
    setTracking(false);
    setFeedbackStatus("Đã dừng ghi nhận quãng đường encoder.");
  }, []);
  const settleAfterStop = useCallback(() => {
    setCommanded({ vx: 0, vy: 0, wz: 0 });
    settlingRef.current = true;
    stoppedSamples.current = 0;
    setFeedbackStatus("Đang đo tiếp trong lúc robot giảm tốc; encoder gần 0 sẽ kết thúc đo.");
    if (settleTimer.current) clearTimeout(settleTimer.current);
    settleTimer.current = setTimeout(finishMeasurement, 5000);
  }, [finishMeasurement]);
  useEffect(() => {
    if (!encoderSample) return;
    const previous = previousEncoderSample.current;
    if (trackingRef.current && previous && encoderSample.tNs > previous.tNs) {
      const dt = Math.min((encoderSample.tNs - previous.tNs) / 1e9, 0.5);
      setEncoderDistance((distanceSoFar) => distanceSoFar + Math.hypot(encoderSample.vx, encoderSample.vy) * dt);
    }
    previousEncoderSample.current = encoderSample;
    if (settlingRef.current) {
      stoppedSamples.current = Math.hypot(encoderSample.vx, encoderSample.vy, encoderSample.wz) < 0.02
        ? stoppedSamples.current + 1
        : 0;
      if (stoppedSamples.current >= 5) finishMeasurement();
    }
  }, [encoderSample, finishMeasurement]);
  // Input order matches the firmware mathematical ABI: FL, FR, RL, RR (rad/s).
  const forward = useMemo(() => {
    const [fl, fr, rl, rr] = wheels.map((value) => parse(value) * WHEEL_RADIUS_M);
    const vx = (fl + fr + rl + rr) / 4;
    const vy = (-fl + fr + rl - rr) / 4;
    const wz = (-fl + fr - rl + rr) / (4 * LEVER_ARM_M);
    const seconds = Math.max(0, parse(forwardDuration));
    return { vx, vy, wz, distance: Math.hypot(vx, vy) * seconds, yaw: wz * seconds };
  }, [wheels, forwardDuration]);
  const inverse = useMemo(() => {
    const seconds = Math.max(0.01, parse(inverseDuration));
    const theta = parse(heading) * Math.PI / 180;
    const vx = parse(distance) * Math.cos(theta) / seconds;
    const vy = parse(distance) * Math.sin(theta) / seconds;
    // Invert the STM mapping for zero yaw: RL/FR=vx+vy, FL/RR=vx−vy.
    const canonical = [vx - vy, vx + vy, vx + vy, vx - vy].map((speed) => speed / WHEEL_RADIUS_M);
    return { vx, vy, wheels: canonical.map((speed) => fmt(speed)), seconds };
  }, [distance, heading, inverseDuration]);
  const canRun = online && armed && !running && !tracking;
  const stop = () => {
    if (timer.current) clearTimeout(timer.current);
    if (interval.current) clearInterval(interval.current);
    timer.current = null;
    interval.current = null;
    command(ZERO);
    setRunning(false);
    if (trackingRef.current) settleAfterStop();
  };
  useEffect(() => () => {
    const wasRunning = interval.current !== null;
    if (timer.current) clearTimeout(timer.current);
    if (interval.current) clearInterval(interval.current);
    if (settleTimer.current) clearTimeout(settleTimer.current);
    if (wasRunning) commandRef.current(ZERO);
  }, []);
  const run = (vx: number, vy: number, wz: number, seconds: number) => {
    if (!canRun || seconds <= 0 || seconds > 30) return;
    setNotice(`Đang gửi lệnh trong ${seconds.toFixed(2)} s; watchdog được làm mới mỗi 100 ms.`);
    setRunning(true);
    setTracking(true);
    trackingRef.current = true;
    settlingRef.current = false;
    stoppedSamples.current = 0;
    previousEncoderSample.current = encoderSample;
    setEncoderDistance(0);
    setCommanded({ vx, vy, wz });
    setFeedbackStatus(encoderSample ? "Đang ghi nhận vận tốc từ encoder STM." : "Chưa có telemetry encoder từ STM.");
    const payload = { command: "velocity", vx: fmt(vx), vy: fmt(vy), wz: fmt(wz) };
    command(payload);
    interval.current = setInterval(() => command(payload), 100);
    timer.current = setTimeout(() => {
      if (interval.current) clearInterval(interval.current);
      interval.current = null;
      timer.current = null;
      command(ZERO);
      setRunning(false);
      settleAfterStop();
      setNotice("Đã hết thời gian chạy; đã gửi vận tốc 0.");
    }, seconds * 1000);
  };
  const encoderOnline = encoderSample !== null && online;
  const measuredVx = encoderSample?.vx ?? 0;
  const measuredVy = encoderSample?.vy ?? 0;
  const measuredWz = encoderSample?.wz ?? 0;
  const field = (label: string, value: string, change: (value: string) => void, unit: string) => (
    <label key={label} className="block space-y-1.5 text-sm"><span className="text-slate-600">{label}</span><span className="flex items-center rounded-md border bg-white focus-within:ring-2 focus-within:ring-primary/30"><input type="number" step="any" value={value} onChange={(event) => change(event.target.value)} className="h-10 min-w-0 flex-1 bg-transparent px-3 font-mono tabular-nums outline-none" /><span className="px-3 text-xs text-slate-500">{unit}</span></span></label>
  );
  return <section className="space-y-4">
    <div className="border-b pb-3"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Motion engineering</p><h2 className="mt-1 text-2xl font-semibold tracking-tight">Kinematics lab</h2><p className="mt-1 max-w-3xl text-sm text-muted-foreground">Tính vận tốc thân từ bốn bánh hoặc suy ra tốc độ bánh từ quãng đường và hướng chuyển động.</p></div>
    <div className="grid gap-4 xl:grid-cols-2">
      <article className="space-y-4 rounded-lg border bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2"><Activity className="size-4 text-primary"/><h3 className="font-semibold">Động học thuận</h3><span className="ml-auto text-xs text-slate-500">4 bánh → thân robot</span></div>
        <div className="grid grid-cols-2 gap-3">{["FL · bánh trước trái", "FR · bánh trước phải", "RL · bánh sau trái", "RR · bánh sau phải"].map((label, index) => field(label, wheels[index], (value) => setWheels((current) => current.map((item, i) => i === index ? value : item)), "rad/s"))}</div>
        <div className="max-w-[calc(50%-0.375rem)]">{field("Thời gian di chuyển", forwardDuration, setForwardDuration, "s")}</div>
        <div className="grid grid-cols-2 gap-2 rounded-md bg-slate-50 p-3 font-mono text-sm tabular-nums sm:grid-cols-4"><Value label="vx thân" value={`${fmt(forward.vx)} m/s`}/><Value label="vy thân" value={`${fmt(forward.vy)} m/s`}/><Value label="Quãng đường" value={`${fmt(forward.distance)} m`}/><Value label="Góc xoay dự kiến" value={`${fmt(forward.yaw * 180 / Math.PI, 2)}°`}/></div>
        <Button disabled={!canRun || parse(forwardDuration) <= 0 || parse(forwardDuration) > 30} onClick={() => run(forward.vx, forward.vy, forward.wz, parse(forwardDuration))}><ArrowDownToLine className="size-4"/>Gửi vận tốc thân xuống STM</Button>
      </article>
      <article className="space-y-4 rounded-lg border bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2"><RotateCw className="size-4 text-primary"/><h3 className="font-semibold">Động học nghịch</h3><span className="ml-auto text-xs text-slate-500">quỹ đạo → 4 bánh</span></div>
        <div className="grid grid-cols-2 gap-3">{field("Quãng đường", distance, setDistance, "m")}{field("Góc hướng trên mặt phẳng", heading, setHeading, "°")}{field("Thời gian di chuyển", inverseDuration, setInverseDuration, "s")}</div>
        <div className="grid grid-cols-2 gap-2 rounded-md bg-slate-50 p-3 font-mono text-sm tabular-nums"><Value label="vx thân" value={`${fmt(inverse.vx)} m/s`}/><Value label="vy thân" value={`${fmt(inverse.vy)} m/s`}/></div>
        <div className="grid grid-cols-2 gap-2">{["FL", "FR", "RL", "RR"].map((label, index) => <div key={label} className="rounded-md border px-3 py-2"><p className="text-xs text-slate-500">{label}</p><p className="font-mono text-lg tabular-nums">{inverse.wheels[index]} <span className="text-xs text-slate-500">rad/s</span></p></div>)}</div>
        <Button disabled={!canRun || parse(inverseDuration) <= 0 || parse(inverseDuration) > 30} onClick={() => run(inverse.vx, inverse.vy, 0, inverse.seconds)}><ArrowDownToLine className="size-4"/>Điều khiển theo động học nghịch</Button>
      </article>
    </div>
    <section className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950 text-slate-100" aria-label="Encoder feedback">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 px-4 py-3">
        <Activity className="size-4 text-emerald-400" />
        <h3 className="text-sm font-semibold">Phản hồi encoder · STM → web</h3>
        <span className="ml-auto flex items-center gap-2 text-xs text-slate-300"><i className={`size-2 rounded-full ${encoderOnline ? "bg-emerald-400" : "bg-amber-400"}`} aria-hidden="true" />{encoderOnline ? "Đang nhận telemetry STM" : "Chưa có telemetry từ STM"}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 p-4 sm:grid-cols-3 xl:grid-cols-4">
        <EncoderMetric label="vx đặt" value={`${fmt(commanded.vx)} m/s`} />
        <EncoderMetric label="vx encoder" value={encoderSample ? `${fmt(measuredVx)} m/s` : "—"} />
        <EncoderMetric label="Sai số vx" value={encoderSample ? `${fmt(measuredVx - commanded.vx)} m/s` : "—"} />
        <EncoderMetric label="vy đặt / encoder" value={encoderSample ? `${fmt(commanded.vy)} / ${fmt(measuredVy)} m/s` : `${fmt(commanded.vy)} / —`} />
        <EncoderMetric label="wz đặt / encoder" value={encoderSample ? `${fmt(commanded.wz)} / ${fmt(measuredWz)} rad/s` : `${fmt(commanded.wz)} / —`} />
        <EncoderMetric label="Tốc độ tịnh tiến đo" value={encoderSample ? `${fmt(Math.hypot(measuredVx, measuredVy))} m/s` : "—"} />
        <EncoderMetric label="Quãng đường encoder trong lượt test" value={`${fmt(encoderDistance)} m`} />
        <EncoderMetric label="Trạng thái ghi nhận" value={tracking ? (running ? "Đang chạy" : "Đang giảm tốc") : "Đã dừng"} />
      </div>
      <p className="border-t border-slate-800 px-4 py-2.5 text-xs leading-5 text-slate-400">STM hiện gửi vx/vy/wz thân đã tính từ encoder; web tích phân tốc độ này thành quãng đường cho mỗi lượt test. Giao thức hiện chưa gửi tốc độ riêng của từng bánh.</p>
      {tracking && <p className="px-4 pb-3 text-xs text-emerald-300">{feedbackStatus}</p>}
    </section>
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-slate-50 px-4 py-3 text-sm"><span className={`size-2 rounded-full ${running ? "animate-pulse bg-amber-500" : "bg-slate-400"}`} aria-hidden="true"/><span className="min-w-0 flex-1">{notice} · {online ? (armed ? "STM sẵn sàng" : "Cần bật Motion ON") : "Backend ngoại tuyến"}</span>{running && <Button variant="destructive" size="sm" onClick={stop}><CircleStop className="size-4"/>Dừng</Button>}</div>
    <p className="text-xs leading-5 text-muted-foreground">Mô hình dùng bánh bán kính 0,05 m và L = 0,332 m theo cấu hình hiện tại. Hướng nhập là góc dịch chuyển trong hệ trục thân; quỹ đạo nghịch giữ nguyên hướng robot (ω = 0). Giao thức web/STM nhận vx, vy, wz nên tốc độ bánh được đổi về vận tốc thân trước khi gửi. Đang bật hiệu chỉnh thử: vx/vy gửi xuống STM được chia 1,89; số encoder hiển thị chưa được hiệu chuẩn.</p>
  </section>;
}

function Value({ label, value }: { label: string; value: string }) {
  return <div><p className="font-sans text-[11px] text-slate-500">{label}</p><p className="mt-0.5">{value}</p></div>;
}

function EncoderMetric({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0 border-l border-slate-800 pl-3"><p className="text-[11px] font-medium uppercase tracking-[0.1em] text-slate-400">{label}</p><p className="mt-1 break-words font-mono text-base tabular-nums text-emerald-200">{value}</p></div>;
}
