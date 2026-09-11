import { Buffer } from "node:buffer";

export type RobotMessage = Record<string, unknown>;

/**
 * The website talks to the FastAPI runtime bridge only through HTTP. Keep the
 * URL server-side so browser requests stay on the Next.js API surface and do
 * not need CORS access to the Jetson.
 */
export const ROBOT_BRIDGE_URL = (process.env.ROBOT_BRIDGE_URL ?? "http://100.69.39.18:8000").replace(/\/+$/, "");

const HISTORY_LIMIT = 2400;
const SYSTEM_CACHE_MS = 1000;
const MAP_CACHE_MS = 1000;
const MAP_RETRY_MS = 2500;
const MAP_SNAPSHOT_TIMEOUT_MS = 20000;
const REQUEST_TIMEOUT_MS = 3000;
const MAP_OPERATION_TIMEOUT_MS = 15000;

type BridgeComponent = {
  id?: string;
  label?: string;
  host_device?: string;
  action?: string;
  running?: boolean;
  pid?: number | null;
  launch_file?: string;
  description?: string;
  capabilities?: Record<string, unknown>;
};

type ComponentsResponse = {
  device_role?: string;
  device_label?: string;
  allowed_actions?: string[];
  bridge_host?: string;
  bridge_port?: number;
  operation_mode?: string;
  components?: BridgeComponent[];
  mapping?: Record<string, unknown>;
};

type TelemetryResponse = {
  timestamp?: number;
  telemetry?: Record<string, unknown>;
};

type BridgeMap = {
  width?: number;
  height?: number;
  resolution?: number;
  origin_x?: number;
  origin_y?: number;
  origin_yaw?: number;
  grid_data?: string;
  timestamp?: number;
  map_source?: string;
  map_name?: string;
  map_yaml?: string;
  map_pgm?: string;
};

type MapResponse = {
  available?: boolean;
  map?: BridgeMap | null;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function asNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function asBoolean(value: unknown): boolean {
  return value === true || value === "true" || value === 1 || value === "1";
}

function toNanoseconds(value: unknown): string {
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds > 0) return String(Math.round(seconds * 1e9));
  return String(Date.now() * 1e6);
}

function isZeroVelocity(vx: number, vy: number, wz: number): boolean {
  return Math.abs(vx) < 0.000001 && Math.abs(vy) < 0.000001 && Math.abs(wz) < 0.000001;
}

export async function requestBridge<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("content-type")) headers.set("content-type", "application/json");
  const signal = init.signal ?? AbortSignal.timeout(REQUEST_TIMEOUT_MS);
  const response = await fetch(`${ROBOT_BRIDGE_URL}${path}`, {
    ...init,
    headers,
    signal,
    cache: "no-store",
  });
  const contentType = response.headers.get("content-type") ?? "";
  const body: unknown = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const record = asRecord(body);
    const detail = typeof record.detail === "string" ? record.detail : typeof body === "string" ? body : "request failed";
    throw new Error(`HTTP bridge ${response.status}: ${detail}`);
  }
  return body as T;
}

function postJson<T>(path: string, payload: Record<string, unknown> = {}, timeoutMs = REQUEST_TIMEOUT_MS): Promise<T> {
  return requestBridge<T>(path, {
    method: "POST",
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(timeoutMs),
  });
}

function componentRunning(components: BridgeComponent[], id: string): boolean {
  return components.some((component) => String(component.id ?? "") === id && component.running === true);
}

function decodeGrid(value: unknown): number[] {
  if (typeof value !== "string" || !value) return [];
  return Array.from(Buffer.from(value, "base64"), (cell) => cell === 255 ? -1 : cell);
}

function encodeRle(values: number[]): number[][] {
  const runs: number[][] = [];
  for (const value of values) {
    const last = runs[runs.length - 1];
    if (last && last[0] === value) last[1] += 1;
    else runs.push([value, 1]);
  }
  return runs;
}

function normalizeMap(source: BridgeMap): RobotMessage {
  const width = Math.max(1, Math.floor(asNumber(source.width, 1)));
  const height = Math.max(1, Math.floor(asNumber(source.height, 1)));
  const resolution = Math.max(0.001, asNumber(source.resolution, 0.05));
  const mapSource = String(source.map_source ?? "live_slam");
  const mapName = String(source.map_name ?? "");
  const occupancy = decodeGrid(source.grid_data);
  const expected = width * height;
  const cells = occupancy.length >= expected ? occupancy.slice(0, expected) : [...occupancy, ...new Array(expected - occupancy.length).fill(-1)];
  let occupiedCells = 0;
  let knownCells = 0;
  for (const cell of cells) {
    if (cell === 100) occupiedCells += 1;
    if (cell === 0 || cell === 100) knownCells += 1;
  }
  return {
    width,
    height,
    resolution_m: resolution,
    origin: [asNumber(source.origin_x), asNumber(source.origin_y), asNumber(source.origin_yaw)],
    occupancy_rle: encodeRle(cells),
    metadata: {
      map_id: mapSource === "saved" && mapName ? `saved:${mapName}` : "ros-map",
      map_source: mapSource,
      ...(mapName ? { map_name: mapName } : {}),
      ...(source.map_yaml ? { map_yaml: source.map_yaml } : {}),
      ...(source.map_pgm ? { map_pgm: source.map_pgm } : {}),
      scans: 0,
      points: 0,
      occupied_cells: occupiedCells,
      known_cells: knownCells,
      robot_radius_m: 0.29,
      history: { trajectory: [] },
    },
  };
}

function directionVelocity(payload: RobotMessage): { vx: number; vy: number; wz: number } {
  const direction = String(payload.direction ?? "stop");
  const speed = Math.max(0, Math.min(1.5, asNumber(payload.speed_mps, 0.2)));
  const yaw = Math.max(0, Math.min(3, asNumber(payload.yaw_radps, 0.6)));
  const diagonal = speed / Math.sqrt(2);
  const velocities: Record<string, { vx: number; vy: number; wz: number }> = {
    forward: { vx: speed, vy: 0, wz: 0 },
    backward: { vx: -speed, vy: 0, wz: 0 },
    left: { vx: 0, vy: speed, wz: 0 },
    right: { vx: 0, vy: -speed, wz: 0 },
    forward_left: { vx: diagonal, vy: diagonal, wz: 0 },
    forward_right: { vx: diagonal, vy: -diagonal, wz: 0 },
    backward_left: { vx: -diagonal, vy: diagonal, wz: 0 },
    backward_right: { vx: -diagonal, vy: -diagonal, wz: 0 },
    rotate_left: { vx: 0, vy: 0, wz: yaw },
    rotate_right: { vx: 0, vy: 0, wz: -yaw },
    stop: { vx: 0, vy: 0, wz: 0 },
  };
  return velocities[direction] ?? velocities.stop;
}

function velocityFromPayload(payload: RobotMessage): { vx: number; vy: number; wz: number } {
  return {
    vx: asNumber(payload.vx ?? payload.linear_x),
    vy: asNumber(payload.vy ?? payload.linear_y),
    wz: asNumber(payload.wz ?? payload.angular_z),
  };
}

class RobotBridge {
  private readonly latest = new Map<string, RobotMessage>();
  private readonly recentEvents: RobotMessage[] = [];
  private readonly historyByType = new Map<string, RobotMessage[]>();
  private commandQueue: Promise<void> = Promise.resolve();
  private motionArmed = false;
  private systemCache: ComponentsResponse | null = null;
  private systemCacheAt = 0;
  private systemRequest: Promise<ComponentsResponse> | null = null;
  private systemRequestGeneration = -1;
  private systemGeneration = 0;
  private mapCache: RobotMessage | null = null;
  private mapCacheAt = 0;
  private mapRequest: Promise<void> | null = null;
  private readRequest: Promise<RobotMessage[]> | null = null;

  private invalidateSystemCache(): void {
    this.systemCacheAt = 0;
    this.systemGeneration += 1;
  }

  private clearMapCache(): void {
    this.mapCache = null;
    this.mapCacheAt = 0;
    this.latest.delete("map");
  }

  private async readSystem(): Promise<ComponentsResponse> {
    const now = Date.now();
    if (this.systemCache && now - this.systemCacheAt < SYSTEM_CACHE_MS) return this.systemCache;
    if (this.systemRequest && this.systemRequestGeneration === this.systemGeneration) return this.systemRequest;
    const generation = this.systemGeneration;
    const request = requestBridge<ComponentsResponse>("/api/system/components")
      .then((response) => {
        if (generation === this.systemGeneration) {
          this.systemCache = response;
          this.systemCacheAt = Date.now();
        }
        return response;
      });
    this.systemRequest = request;
    this.systemRequestGeneration = generation;
    request.then(
      () => {
        if (this.systemRequest === request) {
          this.systemRequest = null;
          this.systemRequestGeneration = -1;
        }
      },
      () => {
        if (this.systemRequest === request) {
          this.systemRequest = null;
          this.systemRequestGeneration = -1;
        }
      },
    );
    return request;
  }

  private refreshMapIfNeeded(): void {
    const now = Date.now();
    const interval = this.mapCache ? MAP_CACHE_MS : MAP_RETRY_MS;
    if (this.mapRequest || now - this.mapCacheAt < interval) return;
    this.mapRequest = requestBridge<MapResponse>("/api/map/snapshot", {
      signal: AbortSignal.timeout(MAP_SNAPSHOT_TIMEOUT_MS),
    })
      .then((response) => {
        if (response.available && response.map) {
          const nextMap = {
            type: "map",
            t_ns: toNanoseconds(response.map.timestamp),
            map: normalizeMap(response.map),
          };
          const previousTimestamp = String(this.mapCache?.t_ns ?? "");
          this.mapCache = nextMap;
          if (previousTimestamp !== String(nextMap.t_ns)) this.appendHistory("map", nextMap);
        } else {
          this.clearMapCache();
        }
        this.mapCacheAt = Date.now();
      })
      .catch(() => {
        // A missing ROS map must not mark the healthy HTTP bridge offline.
        this.mapCacheAt = Date.now();
      })
      .finally(() => { this.mapRequest = null; });
  }

  private appendHistory(type: string, message: RobotMessage): void {
    const history = this.historyByType.get(type) ?? [];
    history.push(type === "map" ? mapHistoryRecord(message) : message);
    if (history.length > HISTORY_LIMIT) history.splice(0, history.length - HISTORY_LIMIT);
    this.historyByType.set(type, history);
  }

  private addEvent(event: string, message: string): void {
    const record = { type: "event", t_ns: toNanoseconds(Date.now() / 1000), event, message };
    this.recentEvents.push(record);
    this.appendHistory("event", record);
    while (this.recentEvents.length > 8) this.recentEvents.shift();
  }

  private messages(): RobotMessage[] {
    return [...this.latest.values(), ...this.recentEvents];
  }

  private buildState(response: TelemetryResponse, system: ComponentsResponse): RobotMessage {
    const telemetry = asRecord(response.telemetry);
    const odom = asRecord(telemetry.odom);
    const battery = asRecord(telemetry.battery);
    const hasMapPose = telemetry.map_pose !== null
      && telemetry.map_pose !== undefined
      && typeof telemetry.map_pose === "object"
      && !Array.isArray(telemetry.map_pose);
    const mapPose = asRecord(telemetry.map_pose);
    const cameraCaptureNs = asNumber(telemetry.camera_capture_t_ns, 0);
    const components = Array.isArray(system.components) ? system.components : [];
    const x = asNumber(odom.x);
    const y = asNumber(odom.y);
    const yaw = asNumber(odom.theta);
    const mapX = asNumber(mapPose.x, x);
    const mapY = asNumber(mapPose.y, y);
    const mapYaw = asNumber(mapPose.yaw, yaw);
    const vx = asNumber(odom.linear_x);
    const vy = asNumber(odom.linear_y);
    const wz = asNumber(odom.angular_z);
    const gyroZ = asNumber(odom.gyro_z, wz);
    const poseSource = String(
      telemetry.pose_source ?? (hasMapPose ? "slam_tf" : "odometry_feedback"),
    );
    const reportedPoseTimestampNs = telemetry.pose_timestamp_ns;
    const poseTimestampNs = reportedPoseTimestampNs !== undefined
      && reportedPoseTimestampNs !== null
      && String(reportedPoseTimestampNs) !== "0"
      ? reportedPoseTimestampNs
      : odom.timestamp_ns ?? response.timestamp;
    const displayPose = hasMapPose ? [mapX, mapY, mapYaw] : [x, y, yaw];
    const lidarOnline = componentRunning(components, "lidar");
    const cameraOnline = componentRunning(components, "camera");
    const datasetOnline = componentRunning(components, "dataset");
    const mapping = asRecord(system.mapping);
    const mappingScanning = "scanning" in mapping ? asBoolean(mapping.scanning) : true;
    const mappingPaused = "paused" in mapping ? asBoolean(mapping.paused) : false;
    const navigationReady = "navigation_ready" in mapping ? asBoolean(mapping.navigation_ready) : false;
    const mapData = asRecord(this.mapCache?.map);
    const mapResolution = this.mapCache ? asNumber(mapData.resolution_m, 0.05) : 0.05;
    const mapLibrary = Array.isArray(mapping.maps) ? mapping.maps : [];
    const selectedMap = String(mapping.selected_map ?? "");
    const status = {
      armed: this.motionArmed,
      lidar: lidarOnline ? "online" : "offline",
      camera: cameraOnline ? "online" : "offline",
      camera_transport: "webrtc-h264",
      camera_rate_hz: asNumber(telemetry.camera_rate_hz),
      lidar_rate_hz: asNumber(telemetry.lidar_rate_hz),
      scan: datasetOnline ? "recording" : "idle",
      dataset: { active: datasetOnline, running: datasetOnline },
      maps: mapLibrary,
      selected_map: selectedMap,
      map_source: String(mapping.map_source ?? "live_slam"),
      navigation_ready: navigationReady,
      map_resolution_m: mapResolution,
      map_available: Boolean(this.mapCache) || asBoolean(mapping.map_available),
      map_width: asNumber(mapData.width),
      map_height: asNumber(mapData.height),
      mapping: { ...mapping, scanning: mappingScanning, paused: mappingPaused },
      map_scanning: mappingScanning,
      map_paused: mappingPaused,
      map_save_root: mapping.map_save_root,
      allowed_actions: system.allowed_actions ?? [],
      components,
      operation_mode: system.operation_mode ?? "real",
    };
    return {
      type: "state",
      t_ns: toNanoseconds(response.timestamp),
      // `pose` is the measured pose used by the dashboard. It is never
      // integrated from the command sent to the robot.
      pose: displayPose,
      sensor_pose: displayPose,
      odom_pose: [x, y, yaw],
      ...(hasMapPose ? { map_pose: [mapX, mapY, mapYaw] } : {}),
      pose_source: poseSource,
      pose_timestamp_ns: poseTimestampNs,
      camera_capture_t_ns: cameraCaptureNs > 0 ? String(Math.round(cameraCaptureNs)) : undefined,
      telemetry: {
        vx_mps: vx,
        vy_mps: vy,
        wz_radps: wz,
        gyro_z_radps: gyroZ,
        voltage_v: asNumber(battery.voltage),
        battery_percentage: asNumber(battery.percentage),
        charging: asBoolean(telemetry.charging),
        lidar_rate_hz: asNumber(telemetry.lidar_rate_hz),
        camera_rate_hz: asNumber(telemetry.camera_rate_hz),
        camera_capture_t_ns: cameraCaptureNs > 0 ? cameraCaptureNs : undefined,
        context: telemetry.context,
        humans: telemetry.humans,
        solver: telemetry.solver,
      },
      pose_diagnostics: {
        speed_mps: Math.hypot(vx, vy),
        yaw_rate_source: "imu_feedback",
        pose_source: poseSource,
        pose_timestamp_ns: poseTimestampNs,
        map_pose_available: Boolean(telemetry.map_pose),
      },
      status,
      bridge: {
        device_role: system.device_role,
        device_label: system.device_label,
        allowed_actions: system.allowed_actions,
        operation_mode: system.operation_mode,
      },
    };
  }

  private async readOnce(): Promise<RobotMessage[]> {
    while (true) {
      const generation = this.systemGeneration;
      const [telemetry, system] = await Promise.all([
        requestBridge<TelemetryResponse>("/api/telemetry/current"),
        this.readSystem(),
      ]);
      // A map command may invalidate the component cache while the two reads
      // above are in flight. Retry inside this request instead of returning a
      // stale snapshot to one of the many polling callers.
      if (generation !== this.systemGeneration) continue;
      const state = this.buildState(telemetry, system);
      this.latest.set("state", state);
      this.appendHistory("state", state);
      this.refreshMapIfNeeded();
      if (this.mapCache) this.latest.set("map", this.mapCache);
      return this.messages();
    }
  }

  async read(): Promise<RobotMessage[]> {
    // The dashboard polls faster than the bridge can sometimes answer. Share
    // one in-flight read so those polls cannot pile up and self-trigger the
    // three-second HTTP timeout that would falsely show the backend offline.
    if (this.readRequest) return this.readRequest;
    const request = this.readOnce();
    this.readRequest = request;
    request.then(
      () => {
        if (this.readRequest === request) this.readRequest = null;
      },
      () => {
        if (this.readRequest === request) this.readRequest = null;
      },
    );
    return request;
  }

  async readHistory(type: string, page: number, pageSize: number): Promise<{
    items: RobotMessage[];
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  }> {
    await this.read();
    const source = this.historyByType.get(type) ?? [];
    const total = source.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    const end = total - (safePage - 1) * pageSize;
    const start = Math.max(0, end - pageSize);
    return {
      items: source.slice(start, end).reverse().map((item) => historyItem(type, item)),
      page: safePage,
      pageSize,
      total,
      totalPages,
    };
  }

  private async postVelocity(vx: number, vy: number, wz: number): Promise<void> {
    await postJson("/api/robot/cmd_vel", { linear_x: vx, linear_y: vy, angular_z: wz });
  }

  private async dispatch(payload: RobotMessage): Promise<void> {
    const command = String(payload.command ?? "");
    if (command === "arm") {
      this.motionArmed = asBoolean(payload.enabled);
      if (!this.motionArmed) await this.postVelocity(0, 0, 0);
      this.addEvent("motion", this.motionArmed ? "Motion enabled in this browser session." : "Motion disabled; zero velocity sent.");
      return;
    }
    if (command === "velocity") {
      const { vx, vy, wz } = velocityFromPayload(payload);
      if (!this.motionArmed && !isZeroVelocity(vx, vy, wz)) {
        this.addEvent("motion_blocked", "Velocity ignored while motion is disabled.");
        return;
      }
      await this.postVelocity(vx, vy, wz);
      return;
    }
    if (command === "move" || command === "direction") {
      const velocity = directionVelocity(payload);
      if (!this.motionArmed && !isZeroVelocity(velocity.vx, velocity.vy, velocity.wz)) {
        this.addEvent("motion_blocked", "Direction ignored while motion is disabled.");
        return;
      }
      await this.postVelocity(velocity.vx, velocity.vy, velocity.wz);
      return;
    }
    if (command === "stop" || command === "emergency_stop") {
      await this.postVelocity(0, 0, 0);
      if (command === "emergency_stop") this.motionArmed = false;
      this.addEvent(command, "Zero velocity sent through the HTTP bridge.");
      return;
    }
    if (command === "nav_goal") {
      const goal = Array.isArray(payload.goal_xy) ? payload.goal_xy : [];
      await postJson("/api/robot/nav/goal", {
        x: asNumber(payload.x ?? goal[0]),
        y: asNumber(payload.y ?? goal[1]),
        yaw: asNumber(payload.yaw),
      });
      this.addEvent("navigation", "Navigation goal sent.");
      return;
    }
    if (command === "nav_cancel") {
      await postJson("/api/robot/nav/cancel");
      this.addEvent("navigation", "Navigation cancelled.");
      return;
    }
    if (command === "map_scan_start") {
      await postJson("/api/map/scan/start", {}, MAP_OPERATION_TIMEOUT_MS);
      this.invalidateSystemCache();
      this.addEvent("map", "SLAM map scanning started.");
      return;
    }
    if (command === "map_scan_stop") {
      await postJson("/api/map/scan/stop", {}, MAP_OPERATION_TIMEOUT_MS);
      this.invalidateSystemCache();
      this.addEvent("map", "SLAM map scanning paused.");
      return;
    }
    if (command === "map_select") {
      const name = typeof payload.name === "string" ? payload.name.trim() : "";
      const response = await postJson<Record<string, unknown>>(
        "/api/map/select",
        { name },
        MAP_OPERATION_TIMEOUT_MS,
      );
      this.invalidateSystemCache();
      this.clearMapCache();
      this.addEvent("map", `Saved map selected: ${String(response.name ?? name)}.`);
      return;
    }
    if (command === "map_set_initial_pose") {
      await postJson(
        "/api/map/localization/pose",
        {
          x: asNumber(payload.x),
          y: asNumber(payload.y),
          yaw: asNumber(payload.yaw),
        },
        MAP_OPERATION_TIMEOUT_MS,
      );
      this.invalidateSystemCache();
      this.addEvent("map", "Saved-map localization pose updated.");
      return;
    }
    if (command === "map_clear" || command === "map_new_scan") {
      await postJson("/api/map/clear", {}, MAP_OPERATION_TIMEOUT_MS);
      this.invalidateSystemCache();
      this.clearMapCache();
      this.addEvent(
        "map",
        command === "map_new_scan"
          ? "New SLAM map scan started; saved map files were kept."
          : "Current SLAM map cleared and a fresh scan session started; saved map files were kept.",
      );
      return;
    }
    if (command === "map_save") {
      const response = await postJson<Record<string, unknown>>(
        "/api/map/save",
        { name: typeof payload.name === "string" ? payload.name : "" },
        MAP_OPERATION_TIMEOUT_MS,
      );
      this.invalidateSystemCache();
      const name = String(response.name ?? payload.name ?? "map");
      const basePath = String(response.base_path ?? response.directory ?? "");
      this.addEvent("map", `Map saved: ${name}${basePath ? ` (${basePath})` : ""}`);
      return;
    }
    if (command === "dataset_start") {
      await postJson("/api/dataset/launch/start", payload);
      this.addEvent("dataset", "Dataset launch started.");
      return;
    }
    if (command === "dataset_stop") {
      await postJson("/api/dataset/launch/stop");
      this.addEvent("dataset", "Dataset launch stopped.");
      return;
    }
    throw new Error(`HTTP bridge command is not supported: ${command || "empty"}`);
  }

  send(payload: RobotMessage): Promise<RobotMessage[]> {
    const command = String(payload.command ?? "");
    if (command === "velocity") return this.dispatch(payload).then(() => this.messages());
    const request = this.commandQueue.then(async () => {
      await this.dispatch(payload);
      await this.read();
      return this.messages();
    });
    this.commandQueue = request.then(() => undefined, () => undefined);
    return request;
  }
}

function mapHistoryRecord(message: RobotMessage): RobotMessage {
  const map = asRecord(message.map);
  const metadata = asRecord(map.metadata);
  return {
    type: "map",
    t_ns: message.t_ns,
    map: {
      width: map.width ?? 0,
      height: map.height ?? 0,
      metadata: {
        scans: metadata.scans ?? 0,
        points: metadata.points ?? 0,
      },
    },
  };
}

type RobotGlobal = typeof globalThis & { __mecanumRobotBridge?: RobotBridge };
const globalState = globalThis as RobotGlobal;
const bridge = globalState.__mecanumRobotBridge ?? new RobotBridge();
globalState.__mecanumRobotBridge = bridge;

export function readRobot(): Promise<RobotMessage[]> {
  return bridge.read();
}

export function readRobotHistory(type: string, page: number, pageSize: number) {
  return bridge.readHistory(type, page, pageSize);
}

export function sendRobotCommand(payload: RobotMessage): Promise<RobotMessage[]> {
  return bridge.send(payload);
}

function historyItem(type: string, item: RobotMessage): RobotMessage {
  if (type === "state") {
    return {
      type,
      t_ns: item.t_ns,
      pose: item.pose,
      sensor_pose: item.sensor_pose,
      odom_pose: item.odom_pose,
      map_pose: item.map_pose,
      pose_source: item.pose_source,
      pose_timestamp_ns: item.pose_timestamp_ns,
      telemetry: item.telemetry,
      command: item.command,
      status: item.status,
    };
  }
  if (type === "lidar") {
    return {
      type,
      t_ns: item.t_ns,
      points: Array.isArray(item.points) ? item.points.length : Number(item.points ?? 0),
    };
  }
  if (type === "map") {
    const map = asRecord(item.map);
    const metadata = asRecord(map.metadata);
    return {
      type,
      t_ns: item.t_ns,
      scans: metadata.scans ?? 0,
      points: metadata.points ?? 0,
      width: map.width ?? 0,
      height: map.height ?? 0,
    };
  }
  return {
    ...item,
    type: item.type ?? "event",
  };
}

type SnapshotOptions = { full?: boolean };

const deliveredStreams = { map: "" };

export function snapshot(messages: RobotMessage[], options: SnapshotOptions = {}) {
  const result: { state?: RobotMessage; map?: RobotMessage; events: RobotMessage[] } = { events: [] };
  for (const message of messages) {
    const type = String(message.type ?? "");
    if (type === "state") result.state = message;
    else if (type === "map") result.map = message;
    else result.events.push(message);
  }
  if (!options.full) {
    const message = result.map;
    const timestamp = String(message?.t_ns ?? "");
    if (message && timestamp) {
      if (deliveredStreams.map === timestamp) delete result.map;
      else deliveredStreams.map = timestamp;
    }
  } else {
    const timestamp = String(result.map?.t_ns ?? "");
    if (timestamp) deliveredStreams.map = timestamp;
  }
  return result;
}
