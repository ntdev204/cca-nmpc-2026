import net from "node:net";

export type RobotMessage = Record<string, unknown>;

const ROBOT_HOST = process.env.ROBOT_HOST ?? "100.69.39.18";
const ROBOT_PORT = Number(process.env.ROBOT_PORT ?? "8765");

function collect(payload: RobotMessage, timeoutMs = 450): Promise<RobotMessage[]> {
  return new Promise((resolve, reject) => {
    const messages: RobotMessage[] = [];
    let buffer = "";
    let settled = false;
    const socket = net.createConnection({ host: ROBOT_HOST, port: ROBOT_PORT });
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      if (error) reject(error);
      else resolve(messages);
    };
    const timer = setTimeout(() => finish(), timeoutMs);
    socket.once("connect", () => socket.write(`${JSON.stringify(payload)}\n`));
    socket.on("data", (chunk: Buffer) => {
      buffer += chunk.toString("utf8");
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const value = JSON.parse(line) as RobotMessage;
          messages.push(value);
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
