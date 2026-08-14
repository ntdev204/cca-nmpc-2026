# CCA AI C++ boundary

This host-buildable library is the deployment-side snapshot gate. It mirrors
the Python five-feature context formula and rejects malformed, stale,
uncalibrated or non-YOLO26s-pose snapshots before CCA-NMPC can consume them.

The library owns the deterministic STM32 serial boundary and the position-state
controller. Python owns YOLO26s-pose TensorRT `.engine` loading, LSTM
inference/training, scenario orchestration and CSV/JSON packaging. The serial
bridge reproduces the legacy 11-byte velocity command and 24-byte telemetry
frame from `reference/robot/turn_on_rai_robot` without launching ROS or ROS 2.
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

The `control_transport` shared library is selected automatically by
`hardware.Stm32SerialSource` on the target platform. Set
`CCA_STM_BACKEND=python` only for an explicit compatibility fallback.
Its small C ABI is in `stm_c_api.h`, so the Python recorder does not duplicate
the byte-level parser when the target library is present.

| Boundary | Preferred implementation | Reason |
|---|---|---|
| STM32 serial frames and stop latch | C++ | deterministic I/O and fail-safe zero command |
| CCA CAN CRC and frame codec | C++ through `shared.py` | fixed-width wire contract |
| context score and snapshot gate | C++ core; context score through the C ABI | deterministic controller boundary |
| Astra-S/OpenNI2 and N10P acquisition | Python | vendor SDK and packet integration |
| LSTM, YOLO26s-pose and CCA-NMPC | Python | model/runtime orchestration |
| calibration, manifests and analysis | Python | provenance and research artifacts |

`build/` is generated and must remain ignored.
