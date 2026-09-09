import { NextResponse } from "next/server";

import { sendRobotCommand, snapshot } from "@/lib/robot";

const ALLOWED = new Set([
  "arm",
  "velocity",
  "move",
  "direction",
  "stop",
  "emergency_stop",
  "nav_goal",
  "nav_cancel",
  "map_scan_start",
  "map_scan_stop",
  "map_clear",
  "map_save",
  "dataset_start",
  "dataset_stop",
]);

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as Record<string, unknown>;
    const command = String(payload.command ?? "");
    if (!ALLOWED.has(command)) {
      return NextResponse.json({ error: "command is not allowed" }, { status: 400 });
    }
    const messages = await sendRobotCommand(payload);
    if (command === "velocity") return NextResponse.json({ backend: "online" }, { headers: { "Cache-Control": "no-store" } });
    return NextResponse.json({ backend: "online", ...snapshot(messages) });
  } catch (error) {
    return NextResponse.json(
      { backend: "offline", error: error instanceof Error ? error.message : "robot backend unavailable" },
      { status: 503 },
    );
  }
}
