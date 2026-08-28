"use client";

import { useEffect, useState } from "react";
import { Activity, Database, ListChecks, Radar } from "lucide-react";

import { Pagination } from "@/components/pagination";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type RecordValue = Record<string, unknown>;
type Kind = "state" | "lidar" | "map" | "event";

type HistoryResponse = {
  backend?: string;
  items?: RecordValue[];
  page?: number;
  pageSize?: number;
  total?: number;
  totalPages?: number;
  error?: string;
};

function value(item: RecordValue, key: string, fallback = "—"): string {
  const raw = item[key];
  return raw === undefined || raw === null ? fallback : String(raw);
}

function decimal(raw: unknown, digits = 2): string {
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : "—";
}

function time(raw: unknown): string {
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) return "—";
  return new Date(parsed / 1e6).toLocaleTimeString();
}

function tabLabel(kind: Kind): string {
  return { state: "Telemetry", lidar: "LiDAR", map: "Map updates", event: "Events" }[kind];
}

export function HistoryPanel() {
  const [kind, setKind] = useState<Kind>("state");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);
  const [data, setData] = useState<HistoryResponse>({});
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/history?kind=${kind}&page=${page}&pageSize=${pageSize}`, { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const body = (await response.json()) as HistoryResponse;
        if (!response.ok) throw new Error(body.error ?? "history unavailable");
        setData(body);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setData({ error: error instanceof Error ? error.message : "history unavailable" });
      });
    return () => controller.abort();
  }, [kind, page, pageSize, refreshTick]);

  useEffect(() => {
    const id = window.setInterval(() => setRefreshTick((current) => current + 1), 2500);
    return () => window.clearInterval(id);
  }, []);

  const items = data.items ?? [];
  const totalPages = Math.max(1, Number(data.totalPages ?? 1));
  const loading = data.backend === undefined && !data.error;
  const icon = kind === "state" ? <Activity className="size-4 text-primary" /> : kind === "lidar" ? <Radar className="size-4 text-primary" /> : kind === "map" ? <Database className="size-4 text-primary" /> : <ListChecks className="size-4 text-primary" />;

  return (
    <Card className="shadow-sm">
      <CardHeader className="border-b bg-slate-50/70 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><CardTitle className="flex items-center gap-2 text-base">{icon}Telemetry, maps &amp; events</CardTitle><CardDescription>Lossless timestamps are retained in the browser-facing history API; large sensor payloads are represented by counts.</CardDescription></div>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">Rows
            <Select value={String(pageSize)} onValueChange={(value) => { setPageSize(Number(value)); setPage(1); }}>
              <SelectTrigger size="sm" className="w-[78px] bg-background text-foreground"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="8">8</SelectItem>
                <SelectItem value="12">12</SelectItem>
                <SelectItem value="24">24</SelectItem>
                <SelectItem value="50">50</SelectItem>
              </SelectContent>
            </Select>
          </label>
        </div>
        <div className="flex flex-wrap gap-1.5 pt-2">
          {(["state", "lidar", "map", "event"] as Kind[]).map((item) => <ButtonTab key={item} active={kind === item} onClick={() => { setKind(item); setPage(1); }}>{tabLabel(item)}</ButtonTab>)}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-3">
        {loading && <p className="text-xs text-muted-foreground">Loading {tabLabel(kind).toLowerCase()}…</p>}
        {data.error && <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">{data.error}</p>}
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full min-w-[620px] text-left text-xs">
            <thead className="bg-muted/50 text-muted-foreground"><tr>{headers(kind).map((header) => <th key={header} className="whitespace-nowrap px-3 py-2 font-medium">{header}</th>)}</tr></thead>
            <tbody className="divide-y">
              {items.map((item, index) => <HistoryRow key={`${value(item, "t_ns")}-${index}`} kind={kind} item={item} />)}
              {!items.length && !loading && <tr><td colSpan={headers(kind).length} className="px-3 py-8 text-center text-muted-foreground">No history has arrived yet.</td></tr>}
            </tbody>
          </table>
        </div>
        <Pagination page={Number(data.page ?? page)} totalPages={totalPages} total={Number(data.total ?? 0)} label={kind === "event" ? "events" : `${kind} samples`} onPageChange={setPage} />
      </CardContent>
    </Card>
  );
}

function ButtonTab({ active, children, onClick }: { active: boolean; children: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={`rounded-md border px-2.5 py-1.5 text-xs transition-colors ${active ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background text-muted-foreground hover:bg-muted"}`} aria-pressed={active}>{children}</button>;
}

function headers(kind: Kind): string[] {
  if (kind === "state") return ["Time", "Pose (x, y, yaw)", "Velocity (vx, vy, ω)", "Command", "Status"];
  if (kind === "lidar") return ["Time", "Returns"];
  if (kind === "map") return ["Time", "Scans", "Points", "Grid"];
  return ["Time", "Event", "Message", "State"];
}

function HistoryRow({ kind, item }: { kind: Kind; item: RecordValue }) {
  if (kind === "state") {
    const pose = Array.isArray(item.pose) ? item.pose : [];
    const telemetry = item.telemetry as RecordValue | undefined;
    const command = Array.isArray(item.command) ? item.command : [];
    return <tr><td className="whitespace-nowrap px-3 py-2">{time(item.t_ns)}</td><td className="px-3 py-2">{decimal(pose[0])}, {decimal(pose[1])}, {decimal(pose[2], 3)}</td><td className="px-3 py-2">{decimal(telemetry?.vx_mps)}, {decimal(telemetry?.vy_mps)}, {decimal(telemetry?.wz_radps, 3)}</td><td className="px-3 py-2">{command.map((value) => decimal(value)).join(", ") || "—"}</td><td className="px-3 py-2"><Badge variant="outline">{String((item.status as RecordValue | undefined)?.scan ?? "idle")}</Badge></td></tr>;
  }
  if (kind === "lidar") return <tr><td className="whitespace-nowrap px-3 py-2">{time(item.t_ns)}</td><td className="px-3 py-2">{value(item, "points", "0")}</td></tr>;
  if (kind === "map") return <tr><td className="whitespace-nowrap px-3 py-2">{time(item.t_ns)}</td><td className="px-3 py-2">{value(item, "scans", "0")}</td><td className="px-3 py-2">{value(item, "points", "0")}</td><td className="px-3 py-2">{value(item, "width", "0")} × {value(item, "height", "0")}</td></tr>;
  const status = item.status as RecordValue | undefined;
  return <tr><td className="whitespace-nowrap px-3 py-2">{time(item.t_ns)}</td><td className="px-3 py-2 font-medium">{value(item, "event", value(item, "type"))}</td><td className="max-w-[360px] truncate px-3 py-2">{value(item, "message")}</td><td className="px-3 py-2">{status ? String(status.message ?? status.scan ?? "updated") : "—"}</td></tr>;
}
