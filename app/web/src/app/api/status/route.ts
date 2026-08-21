import { NextResponse } from "next/server";

import { readRobot, snapshot } from "@/lib/robot";

export async function GET() {
  try {
    const messages = await readRobot();
    return NextResponse.json({ backend: "online", ...snapshot(messages) });
  } catch (error) {
    return NextResponse.json(
      { backend: "offline", error: error instanceof Error ? error.message : "robot backend unavailable" },
      { status: 503 },
    );
  }
}
