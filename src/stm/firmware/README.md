# CCA firmware boundary

This directory is the only new control boundary added to the legacy STM32F407
project. It does not implement CCA-NMPC on the MCU. The Jetson-side controller
may request body velocity; STM owns wheel-speed tracking, watchdog and motor
shutdown.

## Selected interface

`BODY_VELOCITY` is the only accepted mode. `WHEEL_TORQUE` is defined for
protocol compatibility but rejected because the current board exposes encoder
speed and PWM only—no calibrated motor-current or wheel-torque feedback.

The commissioning lock in `firmware_config.h` is deliberately zero.
Therefore a valid arm command seizes authority but produces zero PWM and
reports `CCA_FAULT_NOT_COMMISSIONED`. Do not set it to one until wheel signs,
PI gains, bandwidth, delay, saturation and safe-stop behavior pass bench/HIL.

## CAN contract

All multi-byte integers are big-endian. Application CRC is
CRC-8/SAE-J1850 (`poly=0x1D`, `init=0xFF`, `xorout=0xFF`).

| ID | Direction | Payload |
|---|---|---|
| `0x190` | host → STM | magic, version, mode, sequence, deadline ticks, geometry profile, flags, CRC |
| `0x191` | host → STM | `vx_mm/s`, `vy_mm/s`, `wz_mrad/s`, matching sequence, CRC |
| `0x198` | STM → host | version/status, applied sequence, profile, remaining ticks, CRC |
| `0x199` | STM → host | applied body setpoint, sequence, CRC |
| `0x19A` | STM → host | canonical FL/FR/RL wheel speed in `0.01 rad/s`, sequence, CRC |
| `0x19B` | STM → host | RR speed, battery mV, PWM mask, external faults, sequence, CRC |

One deadline tick is the 10 ms firmware control period. Valid deadlines are
10–500 ms. Header and payload must both pass CRC and carry the same fresh
sequence. Duplicate, stale, incomplete, wrong-profile, torque-mode or expired
commands stop the CCA path. Timeout remains authority-latched at zero command;
legacy input cannot silently take over.

## Wheel ordering

Legacy physical channels are `A=RL`, `B=FL`, `C=FR`, `D=RR`. Telemetry is
reordered to the mathematical ABI `FL,FR,RL,RR`. The kinematic mapping is
host-tested against the MATLAB matrix for `L=0.156+0.176 m`.

## Direct recorder mapping

The host recorder timestamps each decoded CAN frame with one monotonic `t_ns`
clock and writes the required final-run tables directly. It does not write a
middleware log or a replay file.

The direct sensor table `lidar.csv` is part of the final package: each row is a
complete N10P scan with its timestamp and JSON-encoded points, rather than only
the minimum-range diagnostic used by the context table.

| CAN source | Final table | Decoded fields |
|---|---|---|
| `0x191` | `control.csv` | `vx_cmd_mps`, `vy_cmd_mps`, `wz_cmd_radps` after conversion from mm/s and mrad/s |
| `0x199` | `control.csv` | applied body setpoint and command sequence |
| `0x19A`, `0x19B` | `robot_state.csv` | `wheel_fl_radps`, `wheel_fr_radps`, `wheel_rl_radps`, `wheel_rr_radps`, battery, PWM mask and fault fields when available |
| `0x198` | `events.csv` | status, applied sequence, deadline remainder and fault/stop events |

The pose and body-velocity columns required by `robot_state.csv` are produced
by the host odometry/IMU estimator using the same timestamp; they are not
claimed to be measured by the STM telemetry alone. The camera/LiDAR pipeline
writes the context fields to `context.csv` and one complete decoded N10P scan
per row to `lidar.csv` (`t_ns`, point count and JSON points), and the Python
map builder writes the frozen occupancy grid to `map.json`. After a safe stop, run
`scripts/python/tools/final_pack.py` once to validate and seal the package.

## Verification

Run:

```powershell
src/stm/tests/run_host_tests.ps1
```

The test builds portable protocol/runtime/kinematics/PI code with MSVC
`/W4 /WX`. It does not replace a Keil target build, HIL or motor commissioning.
