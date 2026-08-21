import net from "node:net";
import { inflateSync } from "node:zlib";
import JSONbig from "json-bigint";

export type RobotMessage = Record<string, unknown>;

const ROBOT_HOST = process.env.ROBOT_HOST ?? "100.69.39.18";
const ROBOT_PORT = Number(process.env.ROBOT_PORT ?? "8765");
const WIRE_ENCODING = "zlib+base64";
const parseJson = JSONbig({ storeAsString: true }).parse;

function decodeWireMessage(value: RobotMessage): RobotMessage {
  if (value.encoding !== "zlib+base64") return value;
  if (typeof value.payload !== "string") throw new Error("compressed robot message has no payload");
  const decoded = parseJson(inflateSync(Buffer.from(value.payload, "base64")).toString("utf8")) as RobotMessage;
  if (String(decoded.type ?? "") !== String(value.type ?? "")) throw new Error("compressed robot message type mismatch");
  return decoded;
}

function collect(payload: RobotMessage, timeoutMs = 450): Promise<RobotMessage[]> {
  return new Promise((resolve, reject) => {
    const messages: RobotMessage[] = [];
    let buffer = "";
    let settled = false;
    const wirePayload = { ...payload, compression: [WIRE_ENCODING] };
    const socket = net.createConnection({ host: ROBOT_HOST, port: ROBOT_PORT });
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      if (error) reject(error);
      else resolve(messages);
    };
    const timer = setTimeout(() => finish(), timeoutMs);
    socket.once("connect", () => {
      socket.setNoDelay(true);
      socket.setKeepAlive(true, 5000);
      socket.write(`${JSON.stringify(wirePayload)}\n`);
    });
    socket.on("data", (chunk: Buffer) => {
      buffer += chunk.toString("utf8");
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const value = parseJson(line) as RobotMessage;
          messages.push(decodeWireMessage(value));
        } catch {
          // Ignore a partial or malformed stream item; the next poll retries.
        }
      }
    });
    socket.once("error", (error) => {
      clearTimeout(timer);
      finish(error);
    });
    socket.once("close", () => {
      clearTimeout(timer);
      finish();
    });
  });
}

export function readRobot(): Promise<RobotMessage[]> {
  return collect({ command: "ping" });
}

export function sendRobotCommand(payload: RobotMessage): Promise<RobotMessage[]> {
  return collect(payload, 650);
}

export function snapshot(messages: RobotMessage[]) {
  const result: { state?: RobotMessage; lidar?: RobotMessage; map?: RobotMessage; camera?: RobotMessage; events: RobotMessage[] } = { events: [] };
  for (const message of messages) {
    const type = String(message.type ?? "");
    if (type === "state") result.state = message;
    else if (type === "lidar") result.lidar = message;
    else if (type === "map") result.map = message;
    else if (type === "camera") result.camera = message;
    else result.events.push(message);
  }
  return result;
}
