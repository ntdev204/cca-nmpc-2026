---
type: protocol-preflight
status: candidate
evidence_status: interface-pass-admission-blocked
paper_edit: prohibited
---

# PR30 entry preflight — 2026-08-13

The static no-ROS entry check passed for the STM CAN identifiers and CRC
boundary, STM32 serial frame bridge, Python decoder parity, mini-Mecanum URDF
binding, position-state/body-velocity interface scope, commissioning
lock, strict direct CSV/JSON timestamp validation, calibration sidecar contract
and planned H0 template. The report is
`research/metadata/hardware/pr30_entry_preflight_20260813.json` with SHA-256
`7BE114E7C242A4F35368E6DF418E49A8A180FF2988C9323EBC6F9CCAF7B0F28C`.

## Regenerated after per-frame overlay contract — 2026-08-13

The static preflight was rerun after the recorder began recording
`lstm_active` and explicit `LSTM=active/warmup/invalid` overlay states and the
physical packager gained a position-state torque rejection guard. It remains
`PASS`/`BLOCKED`; the current report hash is
`4C7F228556F3CCE28B8A0FF185437F3A3DF84A9F69F7CE8E4042EA8C5876346A`. This is
an interface result only. No Astra-S, N10P, STM32 or CAN device was opened and no
physical package was captured.

Physical admission remains blocked. No sealed hardware package is present; the
robot physical specifications, Astra-S/N10P calibration, independent ground
truth, stage-gate approval and target-hardware manifest are not yet available.
The commissioning lock remains zero, so the firmware must not be treated as
motion-ready. A non-unknown direct package will now be rejected without a
hash-bound `calibration.json`; this preflight is still software/interface QA,
not hardware evidence.

## Direct-recorder robustness checkpoint — 2026-08-13 01:05 UTC

The no-ROS recorder was corrected before any device run. The output directory is
now initialized before `map.json` and `calibration.json` are copied; wheel,
command and applied CAN frames retain separate source timestamps; repeated
camera-loop snapshots are not written as duplicate state/control rows. The
updated source hashes are:

- `src/python/cca_hardware.py` —
  `E649674B291FC98559544ABF20B6860414836A85CA1E766931709B4646A7A5E7`
- `scripts/python/tools/record_hardware.py` —
  `514E89909A3C532DD867977F055B7AC99A14685F7D36C8D00193D8AD4AC79615`

The full Python suite and Ruff pass after this change. It remains a capture-only
integration scaffold: it sends no actuator command, and physical admission is
still blocked until hardware specifications, calibration, safety approval and a
sealed direct package exist.

## Direct-sensor timing/profile checkpoint — 2026-08-13 01:35 UTC

The recorder now requires an explicit `n10p-108b-v1` profile in the hardware
configuration instead of silently selecting a N10P packet layout. Astra-S keeps
host receive time as canonical `t_ns`, records an OpenNI2 device timestamp in
`context.csv` when available, and can reject a color/depth pair above a declared
skew limit. The sidecar records observed timestamp availability and pair skew.
This is an interface safeguard only; no device timestamp or physical skew has
been measured. Current source hashes are:

- `src/python/cca_hardware.py` —
  `6DE04D1E4D87C53C2B6552B4E6734A726A177679ECD31BF35341173DBA87FE35`
- `scripts/python/tools/record_hardware.py` —
  `CF7D8E7C713B36836AC136B602E10356AABD9D954110EC6DF753F0A47F794081`

Focused hardware tests (`12`), full Python QA (`178 passed`), Ruff and the
static preflight pass; no hardware package was created and admission remains
`BLOCKED`.

## Position-state scope checkpoint — 2026-08-13 03:57 UTC

The preflight was regenerated after the position-state amendment. It now checks
the declared state `[x_m,y_m,theta_rad,vx_mps,vy_mps,omega_radps]`, the body-
velocity physical boundary and the unchanged zero-actuation commissioning lock.
The report remains `PASS` with admission `BLOCKED`; its SHA-256 is
`7BE114E7C242A4F35368E6DF418E49A8A180FF2988C9323EBC6F9CCAF7B0F28C`.
The recorder and packager record the mathematical aliases `theta/omega` as
`yaw_rad/wz_radps`; no torque/current channel is required. No device was opened,
no command schedule was executed and no physical result was created. The latest
software QA is Python `187 passed`, Ruff `PASS`, and repository validation
`PASS`; MATLAB remains `70 passed, 0 failed, 0 incomplete`.

## Checkpoint-free context intake correction — 2026-08-13

The recorder no longer requires an LSTM checkpoint for the initial context-only
capture. This is necessary because the first real `context.csv` is the training
source for that checkpoint. A missing checkpoint now produces explicit
`lstm_configured=false` and `LSTM=disabled` records; a supplied checkpoint keeps
the `warmup/active/invalid` labels. Focused hardware tests pass and the static
report was regenerated with `status=PASS`, `admission_status=BLOCKED`. No device
was opened and no physical package was created.

Knowledge links: [[07_Analysis/current-evidence-index]] ·
[[07_Analysis/completion-audit]] · [[01_Governance/limitations]] ·
[[00_MOC/project-map]]

## Current no-device preflight — 2026-08-14

The full recorder and `hardware_entry.py` require a validated
`--safety-record` whenever motion is requested; the record must set approval,
emergency stop, remote disable and watchdog checks to true. The latest static
preflight is `status=PASS`, `admission_status=BLOCKED`, has no hardware package,
and opened no device. Its report SHA-256 is
`A8337AD6F08CE46C9CD5D42622DB7FB3280A53EC056A8BF3CF11B876EDEBBADA`.
The full Python regression suite passes `239` tests; this remains software
interface evidence only.

## Checkpoint after repeated-run hardening — 2026-08-14

The subsequent source reset and checkpoint-hash correction changed only the
direct runtime provenance path. The static preflight was regenerated with
report SHA-256
`B150C152199EC8085C540227EB43D9600D8AB77EC2DACB6E4E67B1D67843DC59` and
remains `PASS`/`BLOCKED`; no device was opened and no run package was created.

## Online CCA-NMPC branch checkpoint — 2026-08-13

The recorder now exposes an explicit `--controller cca_nmpc` path for the
position-state/body-velocity experiment. It requires STM32 serial transport,
`--allow-actuation`, a sealed LSTM checkpoint and a map containing a fixed
`global_path_xy` plus positive CCA settings. The internal context prediction is
passed only to the CCA controller; no human future path is written to CSV or
drawn on the overlay. LSTM warmup, invalid context, solve deadline miss and an
STM stop latch all produce a zero command. Source hashes are:

- `scripts/python/tools/record_hardware.py` —
  `3F9901083E6137B597C9BEE43FDD2FCAC64EBB3CFE92242E4672FBFD301FDCA5`
- `scripts/python/tools/README.md` —
  `EDE0E0272E948523424DBC2B3600C4AEBBE63DADD7DB9153781750C0782F7414`

The static report was regenerated with SHA-256
`349A26F6738554B23ECC3C453D905971B5EC0ECA11ECBE3CF753E1B0D24826CC` and
remains `PASS`/`BLOCKED`. No device was opened and no physical command or
timing result was created.

## Full mini-Mecanum package trace — 2026-08-13

`hardware_entry.py` now reads the complete `rai_robot_urdf` source package
before a runtime configuration is created. The intake record binds
`mini_mec_robot.urdf` and `mini_mec_gazebo.urdf.xacro` by SHA-256, enumerates
the `base_link`, four wheel links, controller link, `camera_link` and
`laser_link` visual/collision meshes, and records the camera and laser fixed
joint origins. The wheel-joint spans give
`half_length=0.08595 m` and `half_width=0.099012 m`; the xacro wheel macro
declares `radius=0.0363 m`. The URDF mass fields sum to `1.049432913 kg`.
The package sensor library also contains `meshes/sensors/astra.dae`,
`lds.stl` and `r200.dae`; those are asset references, not evidence that the
installed device is Astra-S or N10P. The active sensor identity remains bound
by the physical config and measured firmware/baud records.

The no-ROS intake output is
`research/metadata/hardware/mini_mec_intake_20260813.json`. Its current status
is `no_serial_device_detected`, so it is an interface/source audit rather than
a hardware run. The generated config example is deliberately marked with a
measurement-required firmware value and must not be promoted until the actual
STM32/N10P ports, N10P baud, calibration and safety gate are recorded.

Knowledge links: [[06_Methods/final-run-data-package]] ·
[[06_Methods/execution-roadmap]] · [[03_Literature/hardware-sensor-sources]] ·
[[00_MOC/project-map]]

## Operator preflight command — 2026-08-14

The single entrypoint now exposes `hardware_entry.py preflight`. It validates
the prepared runtime config, URDF/Xacro hashes, calibration, map, ARM64
YOLO26s-pose TensorRT manifest, optional LSTM path, schedule and output
directories without importing a device or sending a command. `record` invokes
the same validation before opening any camera, LiDAR or STM transport. A
successful preflight is therefore a no-device interface check, not a hardware
run. The updated static report is
`814813A51965B7F74CC428F04AC3E76E8B72789EBC45CB6131E02D1B2DE0E0F2` and the
Python suite contains 223 collected tests; admission remains `BLOCKED` until
H0 approval and a sealed physical package exist.

The report was regenerated once more after the static validator began checking
the no-device preflight contract. The current report SHA-256 is
`53132D9ADB67E2CCC49C45D24FB84843910BBA82DCDB330FDAE35D1462AF340B`;
status remains `PASS` with hardware admission `BLOCKED`.

## Current direct-recorder recheck — 2026-08-14

The report was regenerated after the direct STM recorder gained stop-flag
latching. Current report SHA-256 is
`ECBE604C216A0E6D960D72FFC816FC64E146020546B5503B93EEC2E6E287D284`;
`PASS`/`BLOCKED` is unchanged. The Python stop-flag regression passes, and no
device or capture package was created.

## Pre-command stop-latch recheck — 2026-08-14

The full recorder now inspects the latest STM telemetry before selecting each
command, not only after writing the state row. An asserted stop flag therefore
forces zero before the next send and remains latched. The static report was
regenerated as `PASS`/`BLOCKED` with SHA-256
`EDE97BD6E55F1014D440C08FF1246CFC768A283E530D1AD6909BA123EFB800CF`;
the Python suite passes `239` tests. No device or capture package was created.

## Motion safety-record gate — 2026-08-14

The direct full recorder and the single hardware entrypoint now require a
validated `--safety-record` whenever motion is requested. The record must set
`approved`, `emergency_stop_verified`, `remote_disable_verified` and
`watchdog_verified` to true. The no-device preflight checks the record before
opening any sensor or sending a command; the sealed runtime metadata stores
only its path and SHA-256. The regenerated preflight report is
`3EFB346D7BE4524BFBDE6459D6A0D31585C422AA0B15659C12E149BABF878FB8` with
`status=PASS`, `admission_status=BLOCKED`, no hardware package and no device
access.

## Runtime geometry provenance checkpoint — 2026-08-14

The direct recorder now verifies and writes the selected URDF source and
URDF/xacro hashes into the adjacent `capture.json` sidecar. Wheel radius,
wheel-span geometry and footprint are accepted only from a separate measured
physical-spec file; the current mesh-derived footprint is CAD/reference
metadata and cannot bind a physical capture. This keeps the CSV/map payload
unchanged while preventing the incorrect intake file from being promoted.
It also writes each complete decoded N10P scan to `lidar.csv`, so the final
package retains more than the minimum-range context diagnostic.
The regenerated static preflight remains `PASS`/`BLOCKED`; its report SHA-256 is
`909D652DEC602CEA1490EF24FCA4ADD192F45462140B3DA66E93292CB2ECF85D`.
No device was opened and no hardware evidence was created.

## Serial-source lifecycle correction — 2026-08-14

The direct N10P and optional CAN sources now clear their stop event on each
start, join their reader thread before closing the transport, and release the
transport/thread handles after stop. This prevents a repeated hardware run from
inheriting a stale stop state and avoids closing a serial/CAN handle underneath
the reader. The refreshed static preflight is `PASS` with report SHA-256
`341FE3A6D85339D40BCCF11EFA7EA6B8DF46602BE1E4F5CFCB2B4543AF2A77C5`; device
admission remains `BLOCKED` until H0, calibration and an actual package exist.

Knowledge links: [[06_Methods/final-run-data-package]] ·
[[07_Analysis/current-evidence-index]] · [[03_Literature/hardware-sensor-sources]]

## Measured-geometry authority correction — 2026-08-14

The supplied physical-geometry file is not yet authoritative. The intake
record keeps its URDF mesh values for traceability but is marked
`cad_reference_only`; `hardware_entry.py prepare` leaves runtime dimensions
null unless a versioned `cca-physical-robot-v1` file with `status: measured` is
provided. `RobotGeometry.from_json` rejects any runtime config without
`geometry_authority: measured_physical_spec`. This is a fail-closed provenance
correction, not a physical measurement or a hardware result.

## Complete link-mesh intake recheck — 2026-08-14

The source audit was rerun after the operator entrypoint was tightened. The
mini-Mecanum mesh inventory now includes every selected URDF link asset:
`base_link`, `controller_link`, all four wheel meshes, `camera_link` and
`laser`. The generated intake remains bound to the selected URDF, the Gazebo
xacro wheel-radius declaration, package/CMake metadata, and the supplied udev
reference by SHA-256. The sensor directory is still recorded as a generic
asset library (`astra.dae`, `lds.stl`, `r200.dae`); it is not used to infer the
identity, calibration or firmware of the installed Astra-S/N10P units.

Focused hardware tests, full Python QA (`214` passed), Ruff, repository
validation and static hardware preflight remain passing. The intake reports
`no_serial_device_detected`; therefore this correction only closes source
coverage and provenance bookkeeping. PR30 admission remains `BLOCKED` until
the target robot, sensors, calibration, safety approval and sealed direct
CSV/JSON package exist.

Knowledge links: [[07_Analysis/current-evidence-index]] ·
[[07_Analysis/completion-audit]] · [[06_Methods/final-run-data-package]]

## Full `rai_robot_urdf` component and sensor parse — 2026-08-14

The no-ROS intake was extended from a selected-mesh check to a complete package
parse. The package contains 37 URDF models; the runtime model remains
`mini_mec_robot`. Its component inventory now binds `lf`, `rf`, `lb` and `rb`
wheel links and joints, their axes, origins, link masses and visual/collision
meshes. It also binds `camera_link`/`camera_joint` and `laser_link`/`laser_joint`,
while recording the controller link and all selected body assets.

The physical role mapping is explicit but not treated as measured evidence:
`camera_link` is the target Astra-S mount, `laser_link` is the target N10P mount,
and the IMU role is the STM32 telemetry channel. The xacro source is separately
parsed for the simulation-only ray lidar (360 samples, 10 Hz), RGB camera
(640x480, 30 Hz), depth camera (640x480, 10 Hz) and IMU (100 Hz) settings. These
settings are not substituted for physical calibration, device identity, baud
measurement or timing measurements.

The regenerated record is
`research/metadata/hardware/mini_mec_intake_20260814.json`. It reports
`no_serial_device_detected`; the parse is therefore source/provenance evidence,
not a hardware experiment or an admission decision.

Knowledge links: [[06_Methods/final-run-data-package]] ·
[[06_Methods/execution-roadmap]] · [[03_Literature/hardware-sensor-sources]] ·
[[00_MOC/project-map]]
