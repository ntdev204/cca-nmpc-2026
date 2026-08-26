# CCA AI C++ boundary

This host-buildable library is the deployment-side snapshot gate. It mirrors
the Python five-feature context formula and rejects malformed, stale,
uncalibrated or non-YOLO26s-pose snapshots before CCA-NMPC can consume them.

The library owns the deterministic STM32 serial boundary and the position-state
controller. Python owns YOLO26s-pose TensorRT `.engine` loading, LSTM
inference/training, scenario orchestration and CSV/JSON packaging. On the
`ros2` branch, `src/ros2/cca_stm_bridge` uses this library as its only hardware
path and publishes the resulting odometry and IMU messages.
The CCA CAN CRC, body-velocity payload and status/wheel frame codec are also
implemented in `can.hpp/.cpp`. The C ABI exposes that fixed-width codec to
`shared.py`, so the direct Linux recorder uses the same C++ implementation
for wire frames; Python remains the explicit fallback for offline hosts.
The five-feature context score is exposed through the same C ABI and selected
by `ai.context` on Linux; `CCA_CONTEXT_BACKEND=python` is the explicit
fallback for hosts without the shared library.

Build:

```powershell
cmake -S src/control -B src/control/build
cmake --build src/control/build --config Release
ctest --test-dir src/control/build -C Release --output-on-failure
```

Direct STM32 commissioning on Jetson/Raspberry Pi/Linux:

```bash
src/control/build/stm_probe \
  --port /dev/rai_controller --baud 115200 \
  --duration-s 30 --period-s 0.05 \
  --operator <operator-id> --firmware-id <firmware-id> \
  --output experiments/runs/stm-cpp-<UTC>
```

The default command is zero velocity. Nonzero motion requires
`--allow-actuation --safety-record <h0-safety.json>`. The probe writes only
`robot_state.csv`, `control.csv`, `events.csv`, `capture.json` and
`manifest.json`; it does not infer physical dimensions or create a map.
`stm_probe` is the low-level STM bring-up path. The full Astra-S/N10P and
CCA-NMPC recorder remains the higher-level Python process; its current Python
serial class is retained as a compatibility fallback until the target builds
the C++ transport library.

The `control_transport` shared library remains available to replay tools. The
ROS 2 bridge links `control_core` directly, so the byte-level parser is not
duplicated in a ROS node.

| Boundary | Preferred implementation | Reason |
|---|---|---|
| STM32 serial frames and stop latch | C++ | deterministic I/O and fail-safe zero command |
| CCA CAN CRC and frame codec | C++ through `shared.py` | fixed-width wire contract |
| context score and snapshot gate | C++ core; context score through the C ABI | deterministic controller boundary |
| Astra-S/OpenNI2 and N10P acquisition | Python | vendor SDK and packet integration |
| LSTM, YOLO26s-pose and context publication | Python | model/runtime orchestration |
| CA-NMPC command generation | C++ through `cca_nmpc_node` | bounded controller path |
| calibration, manifests and analysis | Python | provenance and research artifacts |

`build/` is generated and must remain ignored.
