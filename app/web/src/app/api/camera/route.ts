export const dynamic = "force-dynamic";

const ROBOT_HOST = process.env.ROBOT_HOST ?? "100.69.39.18";
const ROBOT_CAMERA_PORT = Number(process.env.ROBOT_CAMERA_PORT ?? "8766");
const CAMERA_URL = process.env.ROBOT_CAMERA_URL ?? `http://${ROBOT_HOST}:${ROBOT_CAMERA_PORT}/mjpeg`;

export async function GET(request: Request) {
  try {
    const upstream = await fetch(CAMERA_URL, {
      cache: "no-store",
      signal: request.signal,
      headers: { Accept: "multipart/x-mixed-replace" },
    });
    if (!upstream.ok || !upstream.body) {
      return new Response("camera stream unavailable", { status: 502 });
    }
    return new Response(upstream.body, {
      status: 200,
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        Connection: "keep-alive",
        Pragma: "no-cache",
        "X-Accel-Buffering": "no",
        "Content-Type": upstream.headers.get("content-type") ?? "multipart/x-mixed-replace; boundary=mecanum-frame",
      },
    });
  } catch {
    return new Response("camera stream unavailable", { status: 502 });
  }
}
