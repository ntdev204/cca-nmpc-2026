import { NextResponse } from "next/server";

import { readRobotHistory } from "@/lib/robot";

const TYPES = new Set(["state", "lidar", "map", "event"]);
const DEFAULT_PAGE_SIZE = 12;
const MAX_PAGE_SIZE = 50;

function integer(value: string | null, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const type = params.get("kind") ?? "state";
  if (!TYPES.has(type)) {
    return NextResponse.json({ error: "kind must be state, lidar, map or event" }, { status: 400 });
  }
  const page = integer(params.get("page"), 1);
  const pageSize = Math.min(MAX_PAGE_SIZE, integer(params.get("pageSize"), DEFAULT_PAGE_SIZE));
  try {
    const result = await readRobotHistory(type, page, pageSize);
    return NextResponse.json({ backend: "online", kind: type, ...result }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { backend: "offline", error: error instanceof Error ? error.message : "robot backend unavailable" },
      { status: 503 },
    );
  }
}
