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
snapshot. A new client is sent the current map snapshot even when the scan has
not changed. It does not carry a future human path. The map is the existing
dead-reckoned occupancy contract from [[06_Methods/final-run-data-package]];
scan matching and loop closure are not claimed by this app.

The map view also accepts an operator goal by clicking the streamed map. The
Jetson service converts the map payload to the obstacle-rectangle contract of
the existing `simulation.planning.astar_plan` implementation, using the map
origin as a coordinate offset and the frozen robot footprint radius for
inflation. Unknown cells are occupied by default (fail-closed). The existing
eight-neighbour A* search, shortcut and densification are unchanged. The
result is returned as `plan_ready`, drawn on the laptop, and saved as
`navigation_plan.json`; planning itself never sends a velocity command.

## Operator safety

After the handshake the laptop arms the session automatically only when a live
STM32 source is present; there is no separate enable button or enable-key
state. The service still clamps body-velocity commands, and a 0.7 s command
watchdog sends a zero command. Disconnecting the last laptop client also
disarms the robot. The emergency-stop button is always available and clears
held keyboard commands. A* planning remains separate from this actuation
interlock.

For display stability, the laptop keeps a fixed world viewport instead of
rescaling from each LiDAR packet and applies a display-only pose filter. The
raw STM32-integrated pose remains the display/control value; each map update
receives a copy so bounded scan matching cannot overwrite live odometry. The
renderer and mapper steps do not alter commands or controller equations. The status panel
also shows live map scan/point counters and grid size, so a trial can
distinguish a stalled mapper from a marker-only rendering problem.

After capture, **View last saved map** requests the newest `map.json` from the
Jetson service and streams it through the existing map message; **Open local
map.json** handles a package copied to the laptop. The saved-map viewer does
not alter the active motion or planning controller.

## Sensor assets

The service searches [[03_Literature/hardware-sensor-sources]]-related runtime
assets under `openni2_redist/arm64` on Jetson and `openni2_redist/x64` on a
Windows laptop. Astra-S capture is optional at startup so a missing Python
binding cannot hide STM/N10P faults; the status panel reports the exact camera
failure. A camera frame is displayed as RGB. The 2-D marker uses the same
map-frame pose that placed the latest lidar scan, and a follow toggle keeps the
moving robot visible during a scan.

## Saved package

Selecting **Start scan** creates one ignored run directory. **Save map and data**
writes `map.json`, `map.pgm`, `map.yaml`, `control.csv`, `robot_state.csv`,
`lidar.csv`, `context.csv`, `events.csv`, and a digest manifest. If a route was
planned, the package additionally contains `navigation_plan.json` and its
digest. These files are raw capture/planning material only. Interpretation belongs in
[[07_Analysis/experimental-analysis]] after a physical run and cannot be
transferred to the locked paper without a separate evidence review.

The service also finalizes an active run on `SIGTERM`. For an older interrupted
run that has raw CSV streams but no map artifacts,
`recover_interrupted_robot_console_map.py` replays the same occupancy-map
implementation offline and marks the manifest as `recovered`.

## Controller hand-off

`src/runtime/navigation.py` wraps the A* result in the existing
`FixedGlobalLocalPath.from_global` structure. The global path is therefore
fixed once; the existing context conflict/direction-change logic may replace
only its local path. `scripts/python/tools/plan_map.py` can merge this path into
a controller map while preserving `cca_nmpc` settings. The existing
`record_hardware.py --controller cca_nmpc` then constructs `OnlineCcaNmpc`,
`_polyline_reference`, and `CompiledController` exactly as before. No CCA/NMPC
equation or candidate-rollout implementation is changed by the navigation
adapter.

## Open gates

- Install and verify the OpenNI2 Python binding on Jetson.
- Confirm that the Astra distribution's ARM64 core library is loadable by that
  binding; the app reports the failure but does not silently substitute a
  camera.
- Run the operator's emergency-stop and watchdog checks before enabling motion.
- Seal a physical package with [[06_Methods/final-run-data-package]] before any
  training or performance claim.

Related: [[06_Methods/tracking-contract]] · [[06_Methods/evaluation-protocol]] ·
[[08_Decisions/decision-register]] · [[07_Analysis/astar-map-navigation-development-20260820]] ·
[[00_MOC/knowledge-galaxy]]
