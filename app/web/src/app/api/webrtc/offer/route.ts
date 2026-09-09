import { NextResponse } from "next/server";

import { requestBridge } from "@/lib/robot";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const offer = (await request.json()) as Record<string, unknown>;
    const answer = await requestBridge<Record<string, unknown>>("/api/webrtc/offer", {
      method: "POST",
      body: JSON.stringify(offer),
      signal: request.signal,
    });
    return NextResponse.json(answer, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "camera bridge unavailable" },
      { status: 502 },
    );
  }
}
