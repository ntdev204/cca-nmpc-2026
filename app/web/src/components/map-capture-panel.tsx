"use client";

import { useMemo, useState } from "react";
import { Database, RefreshCw, Save, Square } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Pagination } from "@/components/pagination";

export type SavedMap = {
  run_id?: string;
  saved_at_ns?: string | number;
  scans?: number;
  points?: number;
  resolution_m?: number;
  map_bytes?: number;
  selected?: boolean;
};

type DatasetState = Record<string, unknown>;

type MapCommand = (payload: Record<string, unknown>) => void;

type MapCapturePanelProps = {
  online: boolean;
  dataset: DatasetState;
  status: Record<string, unknown>;
  maps: SavedMap[];
  selectedMapId: string;
  onSelectMap: (runId: string) => void;
  onCommand: MapCommand;
};

function number(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function formatBytes(value: unknown): string {
  const bytes = number(value);
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MapCapturePanel({
  online,
  dataset,
  status,
  maps,
  selectedMapId,
  onSelectMap,
  onCommand,
}: MapCapturePanelProps) {
  const active = Boolean(dataset.active);
  const selectedMap = maps.find((map) => String(map.run_id ?? "") === selectedMapId);
  const mapCount = maps.length;
  const pageSize = 5;
  const [page, setPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(mapCount / pageSize));
  const safePage = Math.min(page, totalPages);
  const visibleMaps = useMemo(() => {
    const current = maps.slice((safePage - 1) * pageSize, safePage * pageSize);
    if (selectedMap && !current.some((map) => String(map.run_id ?? "") === selectedMapId)) return [selectedMap, ...current.slice(0, -1)];
    return current;
  }, [maps, safePage, selectedMap, selectedMapId]);

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3 border-b bg-slate-50/70 py-3">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><Database className="size-4 text-primary" />Map capture &amp; saved maps</CardTitle>
          <CardDescription>Scan and save on Jetson; select a saved map for monitoring or planning.</CardDescription>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <Badge variant={active ? "default" : "outline"}>{active ? "recording" : String(status.scan ?? "idle")}</Badge>
          <Badge variant="outline">{mapCount} saved map{mapCount === 1 ? "" : "s"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-3">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.8fr)]">
          <div className="space-y-2 rounded-lg border bg-background p-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <span><span className="font-medium text-foreground">Current run:</span> {String(dataset.run ?? "not started")}</span>
              <span>{number(dataset.lidar_scans)} scans · {number(dataset.lidar_points)} points · {number(dataset.camera_frames)} images</span>
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <Button variant="default" onClick={() => onCommand({ command: "scan_start" })} disabled={!online || active}><Database className="size-4" />Start scan</Button>
              <Button variant="outline" onClick={() => onCommand({ command: "scan_save" })} disabled={!online || !active}><Save className="size-4" />Save map</Button>
              <Button variant="secondary" onClick={() => onCommand({ command: "scan_stop" })} disabled={!online || !active}><Square className="size-4" />Stop</Button>
            </div>
            <p className="text-[11px] leading-4 text-muted-foreground">The scan writes map.json, map.pgm, robot_state.csv, lidar.csv, camera.csv and manifest.json.</p>
          </div>

          <div className="space-y-2 rounded-lg border bg-background p-3">
            <label className="text-xs font-medium text-foreground" htmlFor="saved-map-select">Select map</label>
            <div className="flex gap-2">
              <select
                id="saved-map-select"
                value={selectedMapId}
                onChange={(event) => onSelectMap(event.target.value)}
                disabled={!online || mapCount === 0}
                className="h-9 min-w-0 flex-1 rounded-md border border-input bg-background px-2 text-xs text-foreground shadow-sm outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Choose a saved map</option>
                {visibleMaps.map((map) => {
                  const runId = String(map.run_id ?? "");
                  return <option key={runId} value={runId}>{runId} · {number(map.scans)} scans</option>;
                })}
              </select>
              <Button variant="outline" onClick={() => onCommand({ command: "map_load", run_id: selectedMapId })} disabled={!online || !selectedMapId} title="Load selected map"><RefreshCw className="size-4" />Load</Button>
            </div>
            {selectedMap ? (
              <p className="text-[11px] leading-4 text-muted-foreground">
                {number(selectedMap.scans)} scans · {number(selectedMap.points)} points · {(number(selectedMap.resolution_m, 0.025) * 1000).toFixed(0)} mm · {formatBytes(selectedMap.map_bytes)}
              </p>
            ) : (
              <p className="text-[11px] leading-4 text-muted-foreground">Saved maps are discovered from completed Jetson runs.</p>
            )}
            <Pagination page={safePage} totalPages={totalPages} total={mapCount} label="saved maps" onPageChange={setPage} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
