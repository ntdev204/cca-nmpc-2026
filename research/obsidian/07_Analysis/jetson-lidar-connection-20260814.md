---
type: evidence-analysis
status: candidate-not-evidence
evidence_status: hardware-commissioning; lidar-transport-confirmed; recorder-dependency-open
updated_at: 2026-08-14
paper_edit: prohibited
---

# Jetson LiDAR connection — N10P

## Scope

This note records a read-only sensor-transport check after reconnecting the
N10P LiDAR on the Jetson. No movement command, ROS/ROS 2 node, map run,
CCA-NMPC rollout, or paper edit was used. The check is commissioning evidence,
not a manuscript result.

## Connection

- Host: `rai-k63` Jetson, aarch64.
- Device: `/dev/rai_lidar -> /dev/ttyACM1`.
- USB identity: QinHeng USB Single Serial, serial `5AA6052218`;
  `1a86:55d4`.
- Protocol profile: `n10p-108b-v1`.
- Working baud rate: `460800` baud. The previously noted `468000` setting did
  not yield valid packets on this unit.
- Packet framing: `A5 5A` header, 108-byte packets, 16-point packet payload,
  eight-bit additive checksum.

## Raw-stream evidence

At `460800` baud, a one-second diagnostic read returned `10240` bytes and
`92` valid packets. The decoded packet angles included `0.67` and `10.0`
degrees, and the sampled ranges had a minimum of `2337` mm. The repository
`N10PSerialSource` class was then exercised with a temporary import stub for
the missing AI dependency: it produced `scans_ready=True`, `1032` points, and
`minimum_range_m=0.777` after two seconds. The start and stop command sequence
completed normally.

## Gate and next action

The LiDAR transport and decoder are connected and producing complete scans.
The full `record_hardware.py` pipeline is not yet admitted: the Jetson image
does not currently provide PyTorch, while `src/hardware.py` imports the LSTM
module at import time. Install the target AI runtime or make that dependency
lazy before collecting synchronized camera/LiDAR/STM CSV and JSON artifacts.
This dependency note is kept in Obsidian only and must not be copied into the
locked paper as a result or blocker.

Related knowledge: [[07_Analysis/current-evidence-index]],
[[06_Methods/final-run-data-package]], [[01_Governance/status-and-provenance]].
