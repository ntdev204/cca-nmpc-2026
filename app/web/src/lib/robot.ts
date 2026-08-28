import net from "node:net";
import { inflateSync } from "node:zlib";
import JSONbig from "json-bigint";

export type RobotMessage = Record<string, unknown>;

const ROBOT_HOST = process.env.ROBOT_HOST ?? "100.69.39.18";
const ROBOT_PORT = Number(process.env.ROBOT_PORT ?? "8765");
const WIRE_ENCODING = "zlib+base64";
const parseJson = JSONbig({ storeAsString: true }).parse;
const STREAM_TYPES = new Set(["state", "lidar", "map"]);
const HISTORY_LIMIT = 2400;

function decodeWireMessage(value: RobotMessage): RobotMessage {
  if (value.encoding !== WIRE_ENCODING) return value;
  if (typeof value.payload !== "string") throw new Error("compressed robot message has no payload");
  const decoded = parseJson(inflateSync(Buffer.from(value.payload, "base64")).toString("utf8")) as RobotMessage;
  if (String(decoded.type ?? "") !== String(value.type ?? "")) throw new Error("compressed robot message type mismatch");
  return decoded;
}

function encodeCommand(payload: RobotMessage): string {
  return `${JSON.stringify({ ...payload, compression: [WIRE_ENCODING] })}\n`;
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

class RobotBridge {
  private socket: net.Socket | null = null;
  private connecting: Promise<void> | null = null;
  private buffer = "";
  private connected = false;
  private readonly latest = new Map<string, RobotMessage>();
  private readonly recentEvents: RobotMessage[] = [];
  private readonly historyByType = new Map<string, RobotMessage[]>();
  private commandQueue: Promise<RobotMessage[]> = Promise.resolve([]);

  async ensureConnected(): Promise<void> {
    if (this.socket && !this.socket.destroyed && this.connected) return;
    if (this.connecting) return this.connecting;

    this.connecting = new Promise<void>((resolve, reject) => {
      const socket = net.createConnection({ host: ROBOT_HOST, port: ROBOT_PORT });
      let settled = false;
      const finish = (error?: Error) => {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        if (error) reject(error);
        else resolve();
      };
      const timeout = setTimeout(() => {
        socket.destroy();
        finish(new Error(`robot backend connection timed out (${ROBOT_HOST}:${ROBOT_PORT})`));
      }, 3000);

      this.socket = socket;
      this.buffer = "";
      this.connected = false;
      socket.setNoDelay(true);
      socket.setKeepAlive(true, 5000);
      socket.on("data", (chunk: Buffer) => this.ingest(chunk));
      socket.once("connect", () => {
        this.connected = true;
        try {
          socket.write(encodeCommand({ command: "ping" }));
          finish();
        } catch (error) {
          finish(error instanceof Error ? error : new Error(String(error)));
        }
      });
      socket.once("error", (error) => {
        this.markDisconnected(socket);
        finish(error);
      });
      socket.once("close", () => {
        this.markDisconnected(socket);
        finish(new Error("robot backend connection closed"));
      });
    }).finally(() => {
      this.connecting = null;
    });
    return this.connecting;
  }

  private markDisconnected(socket: net.Socket): void {
    if (this.socket === socket) {
      this.socket = null;
      this.connected = false;
    }
  }

  private ingest(chunk: Buffer): void {
    this.buffer += chunk.toString("utf8");
    const lines = this.buffer.split("\n");
    this.buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const message = decodeWireMessage(parseJson(line) as RobotMessage);
        const type = String(message.type ?? "event");
        if (type === "pong") continue;
        if (STREAM_TYPES.has(type)) {
          this.latest.set(type, message);
          this.appendHistory(type, message);
        }
        else {
          this.recentEvents.push(message);
          this.appendHistory("event", message);
          while (this.recentEvents.length > 8) this.recentEvents.shift();
        }
      } catch {
        this.recentEvents.push({ type: "event", event: "decode_error", message: "invalid robot stream item" });
        this.appendHistory("event", { type: "event", event: "decode_error", message: "invalid robot stream item" });
        while (this.recentEvents.length > 8) this.recentEvents.shift();
      }
    }
  }

  private appendHistory(type: string, message: RobotMessage): void {
    const history = this.historyByType.get(type) ?? [];
    history.push(type === "map" ? mapHistoryRecord(message) : message);
    if (history.length > HISTORY_LIMIT) history.splice(0, history.length - HISTORY_LIMIT);
    this.historyByType.set(type, history);
  }

  private messages(): RobotMessage[] {
    return [...this.latest.values(), ...this.recentEvents];
  }

  private async waitForState(): Promise<void> {
    const deadline = Date.now() + 420;
    while (!this.latest.has("state") && Date.now() < deadline) await sleep(40);
  }

  async read(): Promise<RobotMessage[]> {
    await this.ensureConnected();
    await this.waitForState();
    return this.messages();
  }

  async readHistory(type: string, page: number, pageSize: number): Promise<{
    items: RobotMessage[];
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  }> {
    await this.ensureConnected();
    await this.waitForState();
    const source = this.historyByType.get(type) ?? [];
    const total = source.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    const end = total - (safePage - 1) * pageSize;
    const start = Math.max(0, end - pageSize);
    const records = source.slice(start, end).reverse();
    return {
      items: records.map((item) => historyItem(type, item)),
      page: safePage,
      pageSize,
      total,
      totalPages,
    };
  }

  send(payload: RobotMessage): Promise<RobotMessage[]> {
    if (String(payload.command ?? "") === "velocity") return this.sendVelocity(payload);
    const request = this.commandQueue.then(async () => {
      await this.ensureConnected();
      if (!this.socket || this.socket.destroyed || !this.connected) throw new Error("robot backend is not connected");
      this.socket.write(encodeCommand(payload));
      await this.waitForState();
      return this.messages();
    });
    this.commandQueue = request.catch(() => []);
    return request;
  }

  private async sendVelocity(payload: RobotMessage): Promise<RobotMessage[]> {
    await this.ensureConnected();
    if (!this.socket || this.socket.destroyed || !this.connected) throw new Error("robot backend is not connected");
    this.socket.write(encodeCommand(payload));
    return this.messages();
  }
}

function mapHistoryRecord(message: RobotMessage): RobotMessage {
  const map = message.map as RobotMessage | undefined;
  const metadata = map?.metadata as RobotMessage | undefined;
  return {
    type: "map",
    t_ns: message.t_ns,
    map: {
      width: map?.width ?? 0,
      height: map?.height ?? 0,
      metadata: {
        scans: metadata?.scans ?? 0,
        points: metadata?.points ?? 0,
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
      map_pose: item.map_pose,
      telemetry: item.telemetry,
      command: item.command,
      status: item.status,
    };
  }
  if (type === "lidar") {
    return {
      type,
      t_ns: item.t_ns,
      points: Array.isArray(item.points) ? item.points.length : 0,
    };
  }
  if (type === "map") {
    const map = item.map as RobotMessage | undefined;
    const metadata = map?.metadata as RobotMessage | undefined;
    return {
      type,
      t_ns: item.t_ns,
      scans: metadata?.scans ?? 0,
      points: metadata?.points ?? 0,
      width: map?.width ?? 0,
      height: map?.height ?? 0,
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
  const result: { state?: RobotMessage; lidar?: RobotMessage; map?: RobotMessage; events: RobotMessage[] } = { events: [] };
  for (const message of messages) {
    const type = String(message.type ?? "");
    if (type === "state") result.state = message;
    else if (type === "lidar") result.lidar = message;
    else if (type === "map") result.map = message;
    else result.events.push(message);
  }
  // Map frames are delivered once per new timestamp; the browser keeps the last frame.
  // State and LiDAR remain frequent because they are small and drive the UI.
  if (!options.full) {
    for (const type of ["map"] as const) {
      const message = result[type];
      const timestamp = String(message?.t_ns ?? message?.capture_t_ns ?? "");
      if (!message || !timestamp) continue;
      if (deliveredStreams[type] === timestamp) delete result[type];
      else deliveredStreams[type] = timestamp;
    }
  } else {
    for (const type of ["map"] as const) {
      const message = result[type];
      const timestamp = String(message?.t_ns ?? message?.capture_t_ns ?? "");
      if (timestamp) deliveredStreams[type] = timestamp;
    }
  }
  return result;
}
