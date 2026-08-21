---
type: development-record
status: implementation-complete-for-host-interface
evidence_status: software-interface-only
date: 2026-08-20
tags: [astar, occupancy-map, robot-console, navigation, cca-nmpc, mecanum]
---

# A* map navigation development — 2026-08-20

## Scope completed

This increment adds the map-to-navigation boundary requested for the laptop
console. The occupancy map produced by `manual_map.OccupancyMap` is streamed
to the app and remains visible after scan save. A reconnect resets only the
map-stream cache, so a new laptop client receives the current map without
requiring another scan.

The laptop map canvas accepts a left-click goal. The current Jetson pose is the
default start; the server also accepts an explicit `start_xy`. The service
returns an A* path, and the app renders the path and goal marker over occupied
cells, LiDAR and the robot trace. `plan_clear` removes the overlay. A planned
route is written to `navigation_plan.json` inside the active capture package.

## Algorithm and coordinate contract

No second A* implementation was introduced. `src/simulation/occupancy_astar.py`
only translates occupancy cells into the existing rectangle obstacle format
and calls `simulation.planning.astar_plan`. The existing eight-connected
neighbour expansion, Euclidean queue heuristic, obstacle inflation,
line-of-sight shortcut and densification remain the active algorithm.

The map origin is subtracted before the existing planner call because that
planner's bounds begin at `(0, 0)`; the origin is added back to every returned
point. Occupied cells and, by default, unknown cells are represented by their
cell centre and half-cell extents. Unknown-as-obstacle is deliberately
fail-closed. Inflation uses `map.robot_radius_m` from the frozen study
contract, not a new controller formula.

## Existing-controller hand-off

`src/runtime/navigation.py` wraps the returned path in
`FixedGlobalLocalPath.from_global`. Thus the A* path is the fixed global path;
the existing context replanner can still replace only the local path on its
declared conflict/direction-change triggers. `plan_map.py` writes
`global_path_xy` into a controller map while retaining any existing
`cca_nmpc` settings. The established `record_hardware.py` path then consumes
that map through `OnlineCcaNmpc`, `_polyline_reference`, and
`CompiledController`. No controller equation, horizon, candidate rollout, or
CCA allocation logic was edited.

The console `plan` command is intentionally plan-only. It does not turn a map
click into an unreviewed actuator command. Physical execution remains behind
the existing `record_hardware.py --controller cca_nmpc --allow-actuation`
requirements, STM32 serial check, LSTM/checkpoint check and H0 safety record.

## Verification performed

- `test_occupancy_astar.py`: world-origin translation, wall avoidance,
  fail-closed unknown cells and explicit unknown-space override.
- `test_navigation_adapter.py`: fixed global path hand-off and preservation of
  existing CCA settings.
- Existing context-path tests: local detours still leave the global path
  unchanged.
- Local Python compile, robot-console self-test, Tk construction/click smoke
  test and an in-process `plan`/`plan_clear` protocol test passed.
- No nonzero hardware command was sent during this increment.

## Remaining research gates

This is host/interface evidence only. Before a physical navigation claim, the
map frame and STM odometry must be independently calibrated, start/goal cell
validity and clearance must be reviewed, the A* plan must be replayed in the
simulation/controller path, and H0 emergency-stop/watchdog approval must be
sealed. The paper claim ledger remains unchanged.

## Display-pose stability correction — 2026-08-20

The first console trial exposed visual pose jumps while the robot was being
observed. The cause was in the laptop renderer: without an occupancy map it
recomputed world bounds from every LiDAR packet, so changing scan extents
changed the pixel scale and apparent robot position. The renderer now keeps a
fixed view window and expands/recentres only when the robot actually leaves a
margin. While a map is growing, its bounds are unioned rather than replaced,
so the view does not oscillate with individual scans.

The app also applies a display-only pose filter to the 10 Hz state samples
before drawing the marker and trace. The raw server pose, STM32 telemetry,
mapper pose, control commands, A* path and CCA-NMPC interface are unchanged.
This is a visual/transport correction, not a change to odometry or controller
equations. The correction passed display unit tests, a Tk canvas smoke test,
the Jetson self-test and a zero-speed protocol check; no nonzero hardware
command was sent.

The status panel now exposes the live map scan/point counters and grid size.
This makes the two failure modes observable during a trial: a changing
counter with a static marker indicates a renderer/pose-display problem,
whereas a static counter indicates that scan capture or `mapper.update` is
not receiving new data. If the counter grows while `Velocity` remains zero,
the current architecture is correctly reporting that no STM32 odometry was
available to move the map frame; LiDAR-only pose estimation is outside this
change and must not be inferred from the screenshot.

The interrupted trial also exposed a capture-integrity edge case: a process
terminated during an active scan could leave the raw CSV streams without the
derived map files. `recover_interrupted_robot_console_map.py` replays those
CSV rows through the same `OccupancyMap` (no hardware access and no velocity
command) and writes the missing map package plus a `recovered` manifest. The
service now handles `SIGTERM` by waking its serving loop so its normal close
path disarms the robot and finalizes the map before exit.

The next console trial added two observability paths for the reported static
robot symptom. The laptop status panel now shows the service's armed state and
last body-velocity command alongside STM32 telemetry; a zero command means the
keyboard/button path did not request motion, while a nonzero command with zero
telemetry isolates the hardware/STM32 actuation path. The same UI can request
the latest saved `map.json` from Jetson or open a locally copied map, so map
inspection no longer depends on the scan session remaining open.

## Live pose correction — 2026-08-20

The next hardware capture sent a forward command for approximately 54 seconds
and recorded STM32 velocities up to 0.30 m/s, while the displayed pose stayed
within roughly 0.15 m. The cause was object aliasing: the existing bounded
scan matcher correctly corrected its input pose in place, but that same object
was also the live odometry pose broadcast to the laptop. The service now gives
the matcher a per-scan `Pose` copy. The matcher, its search window and all
control equations are unchanged; only the ownership boundary is corrected so
the robot marker follows live odometry while the map uses the matcher result.
