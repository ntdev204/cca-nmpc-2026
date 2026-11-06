import { NextResponse } from "next/server";

import { readRobot, snapshot } from "@/lib/robot";

export async function GET(request: Request) {
  try {
    const messages = await readRobot();
    const search = new URL(request.url).searchParams;
    if (search.get("pose_only") === "1") {
      const state = messages.filter((message) => message.type === "state" || message.type === "pose")
        .reduce<(typeof messages)[number] | undefined>((latest, item) =>
          !latest || Number(item.t_ns) > Number(latest.t_ns) ? item : latest, undefined);
      return NextResponse.json({
        state: state && {
          t_ns: state.t_ns,
          pose_sample_t_ns: state.pose_sample_t_ns,
          map_pose: state.map_pose,
          pose: state.pose,
        },
      }, { headers: { "Cache-Control": "no-store" } });
    }
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
