---
type: method-architecture
status: implementation-ready
evidence_status: interface-only
tags: [robot-console, astra-s, n10p, mecanum, direct-transport]
---

# Robot console architecture

## Purpose

[[06_Methods/methods-overview]] now has one operator surface for commissioning
the physical platform. The laptop app is a monitor and command surface; the
Jetson service is the only process that opens the STM32, N10P and Astra-S
interfaces. This keeps device timing and the motion watchdog next to the
hardware while leaving rendering on the laptop.

## Data path

```text
STM32 body velocity + telemetry ─┐
N10P scan ──────────────────────┼─> Jetson service ── JSON lines ──> laptop app
Astra-S RGB/depth ──────────────┘          │
                                          └─> CSV + map package on scan save
```

The protocol carries a six-state display pose, applied body velocity, a
decimated laser scan, an optional JPEG camera frame, and an occupancy-map
snapshot. It does not carry a future human path. The map is the existing
dead-reckoned occupancy contract from [[06_Methods/final-run-data-package]];
scan matching and loop closure are not claimed by this app.

## Operator safety

Motion is disabled at connection time. A deliberate enable action is required,
the service clamps body-velocity commands, and a 0.7 s command watchdog sends a
zero command. Disconnecting the last laptop client also disarms the robot. The
emergency-stop button is always available and clears held keyboard commands.

## Sensor assets

The service searches [[03_Literature/hardware-sensor-sources]]-related runtime
assets under `openni2_redist/arm64` on Jetson and `openni2_redist/x64` on a
Windows laptop. Astra-S capture is optional at startup so a missing Python
binding cannot hide STM/N10P faults; the status panel reports the exact camera
failure. A camera frame is displayed as RGB; the 3-D panel shows the lidar plane
and camera frustum, not a fabricated depth point cloud.

## Saved package

Selecting **Start scan** creates one ignored run directory. **Save map and data**
writes `map.json`, `map.pgm`, `map.yaml`, `control.csv`, `robot_state.csv`,
`lidar.csv`, `context.csv`, `events.csv`, and a digest manifest. These files are
raw capture material only. Interpretation belongs in
[[07_Analysis/experimental-analysis]] after a physical run and cannot be
transferred to the locked paper without a separate evidence review.

## Open gates

- Install and verify the OpenNI2 Python binding on Jetson.
- Confirm that the Astra distribution's ARM64 core library is loadable by that
  binding; the app reports the failure but does not silently substitute a
  camera.
- Run the operator's emergency-stop and watchdog checks before enabling motion.
- Seal a physical package with [[06_Methods/final-run-data-package]] before any
  training or performance claim.

Related: [[06_Methods/tracking-contract]] · [[06_Methods/evaluation-protocol]] ·
[[08_Decisions/decision-register]] · [[00_MOC/knowledge-galaxy]]
