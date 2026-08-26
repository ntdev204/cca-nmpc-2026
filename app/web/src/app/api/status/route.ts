import { NextResponse } from "next/server";

import { readRobot, snapshot } from "@/lib/robot";

export async function GET(request: Request) {
  try {
    const messages = await readRobot();
    const full = new URL(request.url).searchParams.get("full") === "1";
    return NextResponse.json({ backend: "online", ...snapshot(messages, { full }) }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { backend: "offline", error: error instanceof Error ? error.message : "robot backend unavailable" },
      { status: 503 },
    );
  }
}
