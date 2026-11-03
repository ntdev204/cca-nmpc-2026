export const LINEAR_COMMAND_COMPENSATION = 1.89;

export function compensateLinearCommand(payload: Record<string, unknown>): Record<string, unknown> {
  const compensated = { ...payload };
  const command = String(payload.command ?? "");
  const fields = command === "velocity" ? ["vx", "vy"] : ["speed_mps", "speed"];

  for (const field of fields) {
    const value = payload[field];
    if (typeof value === "number" && Number.isFinite(value)) {
      compensated[field] = value / LINEAR_COMMAND_COMPENSATION;
    }
  }

  return compensated;
}
