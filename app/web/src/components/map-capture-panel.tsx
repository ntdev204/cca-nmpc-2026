"use client";

import { useState } from "react";
import { Check, Database, FolderOpen, Map as MapIcon, Play, Save, ScanLine, Square, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Component = {
  id?: string;
  label?: string;
  host_device?: string;
  running?: boolean;
  pid?: number | null;
  description?: string;
};

type MapCommand = (payload: Record<string, unknown>) => void;

type SavedMap = {
  name: string;
  yaml?: string;
  pgm?: string | null;
  ready?: boolean;
  updated_at?: number | string;
  size_bytes?: number;
};

type MapCapturePanelProps = {
  online: boolean;
  status: Record<string, unknown>;
  onCommand: MapCommand;
};

function number(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function savedMap(value: unknown): value is SavedMap {
  return Boolean(value && typeof value === "object" && typeof (value as { name?: unknown }).name === "string");
}

function formatUpdated(value: unknown): string {
  const numeric = Number(value);
  const date = Number.isFinite(numeric) && numeric > 0 ? new Date(numeric * 1000) : new Date(String(value ?? ""));
  return Number.isNaN(date.getTime()) ? "unknown time" : date.toLocaleString();
}

function formatBytes(value: unknown): string {
  const bytes = number(value);
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MapCapturePanel({ online, status, onCommand }: MapCapturePanelProps) {
  const [mapName, setMapName] = useState("");
  const components = Array.isArray(status.components) ? status.components.filter((item): item is Component => Boolean(item && typeof item === "object")) : [];
  const dataset = status.dataset && typeof status.dataset === "object" ? status.dataset as Record<string, unknown> : {};
  const datasetRunning = Boolean(dataset.active || dataset.running);
  const allowedActions = Array.isArray(status.allowed_actions) ? status.allowed_actions.map(String) : [];
  const datasetAllowed = allowedActions.includes("dataset");
  const mapping = status.mapping && typeof status.mapping === "object" && !Array.isArray(status.mapping) ? status.mapping as Record<string, unknown> : {};
  const maps = (Array.isArray(status.maps) ? status.maps : Array.isArray(mapping.maps) ? mapping.maps : []).filter(savedMap);
  const selectedMap = String(status.selected_map ?? mapping.selected_map ?? "");
  const mapSource = String(status.map_source ?? mapping.map_source ?? "live_slam");
  const savedMapSelected = mapSource === "saved" && Boolean(selectedMap);
  const slamRunning = components.some((component) => component.id === "slam" && component.running === true);
  const slamEnabled = mapping.slam_enabled !== false;
  const scanning = typeof mapping.scanning === "boolean" ? mapping.scanning : status.map_scanning !== false;
  const mapAvailable = status.map_available === true || mapping.map_available === true;
  const mapWidth = number(status.map_width);
  const mapHeight = number(status.map_height);
  const mapResolution = number(status.map_resolution_m, 0.05);
  const mapSaveRoot = typeof mapping.map_save_root === "string" ? mapping.map_save_root : "/home/rai/cca-nmpc-ros2/maps";
  const lastSaved = mapping.last_saved && typeof mapping.last_saved === "object" ? mapping.last_saved as Record<string, unknown> : null;

  const startNewScan = () => {
    if (typeof window === "undefined" || window.confirm("Bắt đầu quét map mới? Map chưa lưu sẽ bị xóa; các map đã lưu sẽ không bị ảnh hưởng.")) {
      onCommand({ command: "map_new_scan" });
    }
  };

  const clearCurrentMap = () => {
    if (typeof window === "undefined" || window.confirm("Xóa map đang quét dở và khởi tạo phiên SLAM mới? Các map đã lưu sẽ không bị xóa.")) {
      onCommand({ command: "map_clear" });
    }
  };

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3 border-b bg-slate-50/70 py-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><Database className="size-4 text-primary" />HTTP runtime &amp; map</CardTitle>
          <CardDescription>Runtime state comes from the FastAPI bridge. The ROS map is fetched over HTTP and decoded locally for display.</CardDescription>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <Badge variant={mapAvailable ? "default" : "outline"}>{mapAvailable ? "map online" : "no map"}</Badge>
          <Badge variant="outline">{savedMapSelected ? "saved map" : "live map"}</Badge>
          <Badge variant={datasetRunning ? "default" : "outline"}>{datasetRunning ? "dataset running" : "dataset idle"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-3">
        <div className="grid gap-3 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <section className="space-y-2 rounded-lg border border-primary/25 bg-primary/5 p-3" aria-labelledby="map-source-title">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div id="map-source-title" className="flex items-center gap-2 text-sm font-semibold"><MapIcon className="size-4 text-primary" />Map source</div>
                <p className="mt-1 text-[11px] leading-4 text-muted-foreground">Chọn map đã lưu để xem lại, hoặc tạo một phiên quét mới.</p>
              </div>
              <Badge variant={savedMapSelected ? "default" : "outline"}>{savedMapSelected ? `saved · ${selectedMap}` : "live SLAM"}</Badge>
            </div>
            <Button className="w-full" onClick={startNewScan} disabled={!online || !slamEnabled}><ScanLine className="size-4" />Quét map mới</Button>
            <p className="text-[11px] leading-4 text-muted-foreground">
              {savedMapSelected
                ? "Đang hiển thị map đã lưu; SLAM tạm dừng. Vị trí robot trên màn hình vẫn lấy từ cảm biến."
                : "Live map lấy trực tiếp từ SLAM Toolbox. Nút quét mới sẽ xóa map chưa lưu và reset phiên đo."}
            </p>
          </section>

          <section className="space-y-2 rounded-lg border bg-background p-3" aria-labelledby="saved-maps-title">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm font-semibold"><FolderOpen className="size-4 text-primary" /><span id="saved-maps-title">Saved maps</span></div>
              <Badge variant="outline">{maps.length}</Badge>
            </div>
            <div className="max-h-44 space-y-2 overflow-y-auto pr-1">
              {maps.map((map) => {
                const ready = map.ready !== false;
                const selected = savedMapSelected && selectedMap === map.name;
                return (
                  <div key={map.name} className={`flex flex-wrap items-center justify-between gap-2 rounded-md border px-2.5 py-2 ${selected ? "border-primary/50 bg-primary/5" : "bg-slate-50/60"}`}>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 text-xs font-medium"><MapIcon className="size-3.5 shrink-0 text-primary" /><span className="truncate">{map.name}</span>{selected && <Badge variant="default" className="shrink-0 text-[10px]">selected</Badge>}</div>
                      <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{map.yaml ?? `${map.name}.yaml`} · {map.pgm ?? `${map.name}.pgm`} · {formatBytes(map.size_bytes)} · {formatUpdated(map.updated_at)}</p>
                    </div>
                    <Button size="sm" variant={selected ? "default" : "outline"} onClick={() => onCommand({ command: "map_select", name: map.name })} disabled={!online || !ready || selected} title={ready ? `Use ${map.name}` : "PGM file is missing"}>
                      {selected ? <Check className="size-3.5" /> : <MapIcon className="size-3.5" />}{selected ? "Đang dùng" : ready ? "Dùng map" : "Thiếu PGM"}
                    </Button>
                  </div>
                );
              })}
              {!maps.length && <p className="rounded-md border border-dashed px-3 py-4 text-center text-xs text-muted-foreground">Chưa có map đã lưu trong <code>{mapSaveRoot}</code>.</p>}
            </div>
          </section>
        </div>

        <div className="space-y-3 rounded-lg border border-primary/25 bg-primary/5 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold"><ScanLine className="size-4 text-primary" />Live SLAM scan</div>
              <p className="mt-1 text-[11px] leading-4 text-muted-foreground">Start/Stop pause hoặc resume phép đo mới mà không mất map hiện tại. Supervisor giữ đúng một phiên SLAM trong bringup.</p>
            </div>
            <Badge variant={slamRunning && scanning && !savedMapSelected ? "default" : "outline"}>{savedMapSelected ? "saved map" : !slamRunning ? "slam offline" : scanning ? "scanning" : "paused"}</Badge>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Button onClick={() => onCommand({ command: "map_scan_start" })} disabled={!online || !slamEnabled || savedMapSelected || (slamRunning && scanning)}><Play className="size-4" />{scanning ? "Scanning" : "Resume scan"}</Button>
            <Button variant="secondary" onClick={() => onCommand({ command: "map_scan_stop" })} disabled={!online || !slamEnabled || savedMapSelected || !slamRunning || !scanning}><Square className="size-4" />Stop scan</Button>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium" htmlFor="map-save-name">Tên map</label>
            <input
              id="map-save-name"
              value={mapName}
              onChange={(event) => setMapName(event.target.value)}
              maxLength={64}
              placeholder="Ví dụ: sanh-tang-1 (không nhập đuôi file)"
              className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <p className="text-[11px] leading-4 text-muted-foreground">Chỉ nhập tên map. Hệ thống tự tạo <code>{mapSaveRoot}/&lt;tên&gt;.yaml</code>, <code>{mapSaveRoot}/&lt;tên&gt;.pgm</code> và các file phụ nếu SLAM Toolbox tạo ra. Không cần nhập đường dẫn hoặc đuôi file.</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Button onClick={() => onCommand({ command: "map_save", name: mapName.trim() })} disabled={!online || savedMapSelected || !slamRunning || !mapAvailable}><Save className="size-4" />Save map</Button>
            <Button variant="destructive" onClick={clearCurrentMap} disabled={!online || !slamEnabled || !mapAvailable}><Trash2 className="size-4" />Clear current map</Button>
          </div>
          <p className="text-[11px] leading-4 text-muted-foreground">{lastSaved ? `Đã lưu gần nhất: ${String(lastSaved.name ?? "map")}` : "Clear khởi tạo lại pose-graph đang quét; không xóa thư mục đã lưu."}</p>
        </div>

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.8fr)]">
          <div className="space-y-2 rounded-lg border bg-background p-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <span><span className="font-medium text-foreground">Displayed map:</span> {mapAvailable ? `${mapWidth} × ${mapHeight} cells` : "not available"}</span>
              <span>{(mapResolution * 1000).toFixed(0)} mm resolution</span>
            </div>
            <p className="text-[11px] leading-4 text-muted-foreground">Map snapshots use <code>/api/map/snapshot</code>. Map selection is read-only for the dashboard; use New scan to return to live SLAM.</p>
          </div>

          <div className="space-y-2 rounded-lg border bg-background p-3">
            <div className="flex items-center justify-between text-xs font-medium"><span>Dataset launch</span><span className="text-muted-foreground">{datasetAllowed ? "available" : "not allowed on this role"}</span></div>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="default" onClick={() => onCommand({ command: "dataset_start" })} disabled={!online || !datasetAllowed || datasetRunning}><Play className="size-4" />Start</Button>
              <Button variant="secondary" onClick={() => onCommand({ command: "dataset_stop" })} disabled={!online || !datasetAllowed || !datasetRunning}><Square className="size-4" />Stop</Button>
            </div>
            <p className="text-[11px] leading-4 text-muted-foreground">Dataset control follows the bridge role permissions and runs on the configured ROS host.</p>
          </div>
        </div>

        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {components.map((component) => (
            <div key={String(component.id ?? component.label)} className="rounded-lg border bg-background p-3">
              <div className="flex items-center justify-between gap-2 text-xs font-medium">
                <span>{String(component.label ?? component.id ?? "component")}</span>
                <Badge variant={component.running ? "default" : "outline"}>{component.running ? "running" : "stopped"}</Badge>
              </div>
              <p className="mt-1 text-[11px] leading-4 text-muted-foreground">{String(component.host_device ?? "")}{component.pid ? ` · pid ${component.pid}` : ""}</p>
            </div>
          ))}
          {!components.length && <p className="text-xs text-muted-foreground">No runtime components reported.</p>}
        </div>
      </CardContent>
    </Card>
  );
}
