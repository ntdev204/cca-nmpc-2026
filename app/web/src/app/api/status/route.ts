import { NextResponse } from "next/server";

import { readRobot, snapshot } from "@/lib/robot";

export async function GET(request: Request) {
  try {
    const messages = await readRobot();
    const search = new URL(request.url).searchParams;
    const full = search.get("full") === "1";
    const mapSince = search.get("map_since") ?? undefined;
    return NextResponse.json({ backend: "online", ...snapshot(messages, { full, mapSince }) }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { backend: "offline", error: error instanceof Error ? error.message : "robot backend unavailable" },
      { status: 503 },
    );
  }
}
