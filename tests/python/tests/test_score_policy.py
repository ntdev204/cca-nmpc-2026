import json
from collections import deque
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from tools.map_run import (
    CONTROLLER_DEFINITIONS,
    CONTROLLERS,
    DEADLINE_MS,
    HUMAN_RADIUS_M,
    MAP_CONTRACT,
    ROBOT_GEOMETRY,
    ROBOT_RADIUS_M,
    SCENARIOS,
    ContextPolicyParameters,
    ContextLstmAdapter,
    context_observation,
    context_prediction,
    controller_for_path,
    load_protocol_freeze,
    load_rl_policy,
    main,
    outcome_score,
    path_cross_track_error,
    paired_bootstrap_intervals,
    paired_effect_intervals,
    run_episode,
    score_policy_search,
    sha256_file,
    validate_robot_geometry_contract,
    validate_confirmatory_lstm_provenance,
    validate_benchmark_pairs,
)
from runtime.controller import CompiledController
from simulation.model import NmpcPrediction
from ai.context import ContextScorer


def test_outcome_score_rejects_collision() -> None:
    assert outcome_score({"collision": True, "safe_completion": True}) == 0.0


def test_path_cross_track_error_uses_segment_projection() -> None:
    assert path_cross_track_error([0.5, 0.2], [[0.0, 0.0], [1.0, 0.0]]) == pytest.approx(0.2)


def test_score_loop_uses_environment_outcomes_without_targets() -> None:
    candidates = (
        ContextPolicyParameters(lateral_offset_m=1.0),
        ContextPolicyParameters(lateral_offset_m=1.5),
    )

    def evaluate(parameters: ContextPolicyParameters):
        return [
            {
                "collision": False,
                "safe_completion": parameters.lateral_offset_m > 1.2,
                "minimum_context_margin_m": parameters.lateral_offset_m - 1.0,
                "final_goal_error_m": 0.1,
                "controller_failure_count": 0,
                "deadline_miss_count": 0,
            }
        ]

    result = score_policy_search(candidates, evaluate, target_score=0.8, patience=2)
    assert result.best_parameters.lateral_offset_m == pytest.approx(1.5)
    assert result.target_reached
    assert all(row["training_targets_used"] is False for row in result.iterations)


def test_rl_policy_contract_loads_score_penalty_parameters(tmp_path) -> None:
    path = tmp_path / "rl_policy.json"
    path.write_text(
        json.dumps(
            {
                "schema": "cca-tabular-rl-policy-v1",
                "training_mode": "tabular_q_learning_score_penalty",
                "best_action": 7,
                "best_parameters": {
                    "safe_distance_m": 0.2,
                    "lateral_offset_m": 1.7,
                    "longitudinal_offset_m": 0.85,
                    "context_radius_m": 0.6,
                },
                "score_target": 0.85,
                "episodes_completed": 81,
            }
        ),
        encoding="utf-8",
    )
    metadata = load_rl_policy(path)
    assert metadata["training_mode"] == "tabular_q_learning_score_penalty"
    assert metadata["best_parameters"]["lateral_offset_m"] == pytest.approx(1.7)


def test_benchmark_declares_distinct_controller_contracts() -> None:
    assert set(CONTROLLERS) == {"mpc", "nmpc", "dwa", "mppi", "cca_nmpc"}
    assert set(CONTROLLERS) <= set(CONTROLLER_DEFINITIONS)
    assert CONTROLLER_DEFINITIONS["mpc"]["context_used"] is False
    assert CONTROLLER_DEFINITIONS["nmpc"]["risk_strategy"] == "deterministic"
    assert CONTROLLER_DEFINITIONS["cca_nmpc"]["risk_strategy"] == "cca_fixed_budget"
    assert CONTROLLER_DEFINITIONS["dwa"]["implementation"] != CONTROLLER_DEFINITIONS["mppi"]["implementation"]


def test_benchmark_deadline_matches_map_sample_period() -> None:
    assert DEADLINE_MS == pytest.approx(1000.0 * float(MAP_CONTRACT["dt_s"]))


def test_map_geometry_is_bound_to_the_full_robot_urdf() -> None:
    geometry = validate_robot_geometry_contract()
    assert geometry["model"] == "mini_mec_robot"
    assert ROBOT_RADIUS_M == pytest.approx(float(geometry["footprint_radius_m"]))
    assert ROBOT_GEOMETRY["source_urdf_sha256"] == geometry["source_urdf_sha256"]
    assert len(str(geometry["source_intake_sha256"])) == 64


def test_sampled_controllers_receive_the_urdf_footprint() -> None:
    path = np.asarray(((0.0, 0.0), (1.0, 0.0)), dtype=np.float64)
    dwa = controller_for_path("dwa", path, seed=1, horizon=6)
    mppi = controller_for_path("mppi", path, seed=1, horizon=6)
    assert dwa.robot_radius_m == pytest.approx(ROBOT_RADIUS_M)
    assert dwa.human_radius_m == pytest.approx(HUMAN_RADIUS_M)
    assert mppi.robot_radius_m == pytest.approx(ROBOT_RADIUS_M)
    assert mppi.human_radius_m == pytest.approx(HUMAN_RADIUS_M)


def test_position_mpc_and_nmpc_use_different_reference_policies() -> None:
    state = np.zeros(6, dtype=np.float64)
    reference = np.zeros((6, 7), dtype=np.float64)
    reference[0, 1:] = np.asarray((0.01, 0.2, 0.4, 0.6, 0.8, 1.0))
    previous = np.zeros(3, dtype=np.float64)
    mpc = CompiledController("mpc", 0.1, horizon=6, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    nmpc = CompiledController("nmpc", 0.1, horizon=6, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    mpc_result = mpc.command(state, reference, previous)
    nmpc_result = nmpc.command(state, reference, previous)
    assert mpc_result.status == "MPC_SUCCESS"
    assert nmpc_result.status == "NMPC_SUCCESS"
    assert nmpc_result.iterations > 0
    assert nmpc_result.predicted_states.shape == (6, 6)
    assert not np.allclose(mpc_result.first_command_mps, nmpc_result.first_command_mps)


def test_compiled_controller_reads_state_major_reference_correctly() -> None:
    horizon = 3
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    reference[0, 1:] = np.asarray((0.3, 0.6, 0.9))
    controller = CompiledController("nmpc", 0.1, horizon, 100.0, 0.18, 0.34)
    result = controller.command(np.zeros(6), reference, np.zeros(3))
    assert result.first_command_mps[0] > 0.0


def test_compiled_controller_rejects_invalid_state_dimensions() -> None:
    controller = CompiledController("nmpc", 0.1, horizon=3, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    with pytest.raises(ValueError, match="invalid size"):
        controller.command(np.zeros(5), np.zeros((6, 4)), np.zeros(3))


def test_cca_position_nmpc_uses_projected_covariance_margin() -> None:
    mean_xy = np.asarray([[[[0.40, 0.0], [0.55, 0.0], [0.70, 0.0]]]], dtype=np.float64)
    velocity_xy = np.zeros((1, 1, 3, 2), dtype=np.float64)
    context = np.full((1, 3), 0.5, dtype=np.float64)
    base = dict(
        mean_xy=mean_xy,
        velocity_xy=velocity_xy,
        probability=np.ones((1, 1), dtype=np.float64),
        context=context,
        nominal_robot_xy=mean_xy[0, 0].copy(),
        human_yaw_rad=np.zeros((1, 3), dtype=np.float64),
    )
    low = NmpcPrediction(
        relative_covariance_xy=np.zeros((1, 1, 3, 2, 2), dtype=np.float64),
        **base,
    )
    high_covariance = np.zeros((1, 1, 3, 2, 2), dtype=np.float64)
    high_covariance[..., 0, 0] = 0.10**2
    high_covariance[..., 1, 1] = 0.10**2
    high = NmpcPrediction(relative_covariance_xy=high_covariance, **base)
    state = np.zeros(6, dtype=np.float64)
    reference = np.zeros((6, 4), dtype=np.float64)
    reference[0, 1:] = np.asarray((0.30, 0.60, 0.90))
    controller = CompiledController("cca_nmpc", 0.1, horizon=3, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    low_result = controller.command(state, reference, np.zeros(3), low)
    high_result = controller.command(state, reference, np.zeros(3), high)
    assert high_result.maximum_constraint_violation >= low_result.maximum_constraint_violation


def test_cca_controller_reports_finite_risk_output() -> None:
    horizon = 1
    prediction = NmpcPrediction(
        mean_xy=np.asarray([[[[0.5, 0.0]]]], dtype=np.float64),
        velocity_xy=np.zeros((1, 1, horizon, 2), dtype=np.float64),
        relative_covariance_xy=np.zeros((1, 1, horizon, 2, 2), dtype=np.float64),
        probability=np.ones((1, 1), dtype=np.float64),
        context=np.ones((1, horizon), dtype=np.float64),
        nominal_robot_xy=np.asarray(((0.1, 0.0),), dtype=np.float64),
        human_yaw_rad=np.zeros((1, horizon), dtype=np.float64),
    )
    controller = CompiledController("cca_nmpc", 0.1, horizon=horizon, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    result = controller.command(np.zeros(6), np.zeros((6, horizon + 1)), np.zeros(3), prediction)
    assert np.isfinite(result.risk_bound)
    assert np.isfinite(result.maximum_constraint_violation)


def test_compiled_controller_rejects_malformed_prediction() -> None:
    horizon = 1
    prediction = SimpleNamespace(mean_xy=np.zeros((1, 1, 2, 2)), context=np.zeros((1, horizon)), relative_covariance_xy=np.zeros((1, 1, horizon, 2, 2)), nominal_robot_xy=np.zeros((horizon, 2)))
    controller = CompiledController("cca_nmpc", 0.1, horizon=horizon, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    with pytest.raises((ValueError, RuntimeError)):
        controller.command(np.zeros(6), np.zeros((6, horizon + 1)), np.zeros(3), prediction)


def test_position_nmpc_uses_prediction_nominal_robot_geometry() -> None:
    horizon = 3
    mean_xy = np.asarray([[[[0.5, 0.0], [0.6, 0.0], [0.7, 0.0]]]], dtype=np.float64)
    covariance = np.zeros((1, 1, horizon, 2, 2), dtype=np.float64)
    common = dict(
        mean_xy=mean_xy,
        velocity_xy=np.zeros((1, 1, horizon, 2), dtype=np.float64),
        relative_covariance_xy=covariance,
        probability=np.ones((1, 1), dtype=np.float64),
        context=np.full((1, horizon), 0.5, dtype=np.float64),
        human_yaw_rad=np.zeros((1, horizon), dtype=np.float64),
    )
    near_axis = NmpcPrediction(
        nominal_robot_xy=np.asarray(((0.1, 0.0), (0.2, 0.0), (0.3, 0.0))),
        **common,
    )
    off_axis = NmpcPrediction(
        nominal_robot_xy=np.asarray(((0.1, 0.5), (0.2, 0.5), (0.3, 0.5))),
        **common,
    )
    controller = CompiledController("cca_nmpc", 0.1, horizon=horizon, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    state = np.zeros(6, dtype=np.float64)
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    previous = np.zeros(3, dtype=np.float64)
    near_result = controller.command(state, reference, previous, near_axis)
    off_result = controller.command(state, reference, previous, off_axis)
    assert np.isfinite(near_result.first_command_mps).all()
    assert np.isfinite(off_result.first_command_mps).all()
    assert near_result.maximum_constraint_violation != off_result.maximum_constraint_violation


def test_prediction_contract_preserves_observed_context_only() -> None:
    prediction = context_prediction(context_observation(SCENARIOS[0], 0.0), np.zeros((6, 4)), np.zeros(6), 3)
    assert prediction.mean_xy.shape[-1] == 2
    assert prediction.nominal_robot_xy.shape == (3, 2)


def test_dynamic_context_position_and_cca_prediction_are_dynamic() -> None:
    scenario = SCENARIOS[0]
    at_zero = context_observation(scenario, 0.0)
    at_one = context_observation(scenario, 1.0)
    assert at_one.position_xy[0] < at_zero.position_xy[0]
    horizon = 3
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    prediction = context_prediction(
        at_zero,
        reference,
        np.zeros(6, dtype=np.float64),
        horizon,
    )
    assert prediction.mean_xy.shape == (1, 1, horizon, 2)
    assert prediction.mean_xy[0, 0, 0, 0] < at_zero.position_xy[0]
    expected_x = at_zero.position_xy[0] - float(MAP_CONTRACT["dt_s"]) * at_zero.speed_per_s * np.arange(1, horizon + 1)
    np.testing.assert_allclose(prediction.mean_xy[0, 0, :, 0], expected_x)


def test_context_prediction_uses_shared_five_feature_score() -> None:
    observation = context_observation(SCENARIOS[0], 0.0)
    horizon = 3
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    reference[0, 1:] = [0.05, 0.10, 0.15]
    reference[1, 1:] = [0.02, 0.04, 0.06]
    reference[2, 1:] = [0.1, 0.2, 0.3]
    reference[3, 1:] = [0.12, 0.10, 0.08]
    reference[4, 1:] = [0.03, 0.04, 0.05]
    prediction = context_prediction(observation, reference, np.zeros(6), horizon)
    human_velocity = np.asarray(observation.heading_unit, dtype=np.float64) * float(observation.speed_per_s)
    robot_xy = prediction.nominal_robot_xy
    robot_velocity = np.column_stack(
        (
            np.cos(reference[2, 1:]) * reference[3, 1:] - np.sin(reference[2, 1:]) * reference[4, 1:],
            np.sin(reference[2, 1:]) * reference[3, 1:] + np.cos(reference[2, 1:]) * reference[4, 1:],
        )
    )
    scorer = ContextScorer()
    expected = []
    for index in range(horizon):
        expected.append(
            scorer.score(
                0,
                0,
                np.asarray(observation.position_xy, dtype=np.float64) - robot_xy[index],
                human_velocity - robot_velocity[index],
                0.0,
                1.0,
                robot_velocity_xy=robot_velocity[index],
                human_velocity_xy=human_velocity,
            ).phi
        )
    np.testing.assert_allclose(prediction.context[0], expected)


def test_lstm_adapter_rejects_out_of_range_context_speed() -> None:
    adapter = object.__new__(ContextLstmAdapter)
    adapter.observed_steps = 1
    adapter.history = deque(maxlen=1)
    adapter.model = lambda history: SimpleNamespace(
        context_velocity_xy=torch.tensor([[3.0, 0.0]], dtype=torch.float32)
    )
    observation = context_observation(SCENARIOS[0], 0.0)
    assert adapter.observe(observation) is None


def test_only_cca_receives_internal_future_prediction_without_path_artifact(monkeypatch) -> None:
    import tools.map_run as map_run

    calls: list[int] = []
    original = map_run.context_prediction

    def wrapped(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(map_run, "context_prediction", wrapped)
    baseline_rows: dict[str, list[dict[str, object]]] = {}
    for method in ("mpc", "nmpc", "dwa", "mppi"):
        _, baseline_rows[method] = run_episode(SCENARIOS[0], method, 31, 3)
    assert not calls
    _, cca_rows = run_episode(SCENARIOS[0], "cca_nmpc", 31, 3)
    assert calls
    forbidden = ("human_future", "human_trajectory", "predicted_path", "predicted_trajectory")
    assert not any(any(token in key for token in forbidden) for key in cca_rows[0])
    for rows in baseline_rows.values():
        assert not any(any(token in key for token in forbidden) for key in rows[0])


def test_lstm_observation_is_consumed_only_by_cca_nmpc() -> None:
    class Recorder:
        def __init__(self) -> None:
            self.reset_calls = 0
            self.observe_calls = 0

        def reset(self) -> None:
            self.reset_calls += 1

        def observe(self, observation: object) -> None:
            del observation
            self.observe_calls += 1
            return None

    for method in ("mpc", "nmpc", "dwa", "mppi"):
        baseline_recorder = Recorder()
        run_episode(SCENARIOS[0], method, 37, 3, context_lstm=baseline_recorder)
        assert baseline_recorder.reset_calls == 0
        assert baseline_recorder.observe_calls == 0
    cca_recorder = Recorder()
    run_episode(SCENARIOS[0], "cca_nmpc", 37, 3, context_lstm=cca_recorder)
    assert cca_recorder.reset_calls == 1
    assert cca_recorder.observe_calls > 0


def test_confirmatory_lstm_provenance_requires_sealed_capture(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("tools.map_run.PROJECT_ROOT", tmp_path)
    capture = tmp_path / "capture"
    capture.mkdir()
    calibration_path = capture / "calibration.json"
    calibration_path.write_text(
        json.dumps(
            {
                "schema": "cca-capture-calibration-v1",
                "calibration_id": "cal-test-01",
                "camera": "Astra S",
                "lidar": "N10P",
                "robot_frame": "base_link",
                "calibrated_at_utc": "2026-08-13T00:00:00Z",
                "camera_intrinsics": {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0, "width": 640, "height": 480},
                "camera_to_robot": {"translation_m": [0.1, 0.0, 0.2], "rpy_rad": [0.0, 0.0, 0.0]},
                "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.3], "rpy_rad": [0.0, 0.0, 0.0]},
                "quality": {"camera_reprojection_rmse_px": 0.5, "lidar_alignment_rmse_m": 0.01},
            }
        ),
        encoding="utf-8",
    )
    manifest_path = capture / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "status": "verified",
                "integrity_status": "verified",
                "capture_source": "hardware",
                "context_only": True,
                "human_trajectory_generated": False,
                "sensors": {"camera": "Astra S", "lidar": "N10P"},
                "calibration": {"path": "calibration.json", "sha256": sha256_file(calibration_path), "calibration_id": "cal-test-01"},
                "files": {"calibration.json": {"sha256": sha256_file(calibration_path)}},
            }
        ),
        encoding="utf-8",
    )
    metadata = {
        "source_capture": "hardware",
        "source_capture_manifest_sha256": sha256_file(manifest_path),
        "source_capture_manifest_path": "capture/manifest.json",
        "source_calibration_sha256": sha256_file(calibration_path),
    }
    assert validate_confirmatory_lstm_provenance(metadata) == {
        "capture_source": "hardware",
        "capture_manifest_sha256": sha256_file(manifest_path),
        "capture_manifest_path": "capture/manifest.json",
        "calibration_sha256": sha256_file(calibration_path),
    }
    with pytest.raises(ValueError, match="real capture source"):
        validate_confirmatory_lstm_provenance(
            {"source_capture": "simulation", "source_capture_manifest_sha256": "a" * 64}
        )
    with pytest.raises(ValueError, match="capture manifest hash"):
        validate_confirmatory_lstm_provenance({"source_capture": "hardware"})
    with pytest.raises(ValueError, match="capture manifest path"):
        validate_confirmatory_lstm_provenance(
            {"source_capture": "hardware", "source_capture_manifest_sha256": "a" * 64}
        )
    with pytest.raises(ValueError, match="does not match"):
        validate_confirmatory_lstm_provenance(
            {
                **metadata,
                "source_capture_manifest_sha256": "a" * 64,
            }
        )


def test_confirmatory_campaign_contract_requires_replicates_and_no_tuning(monkeypatch, tmp_path) -> None:
    output = tmp_path / "confirmatory"
    monkeypatch.setattr(
        "sys.argv",
        [
            "map_run.py",
            "--campaign",
            "confirmatory",
            "--replicates",
            str(int(MAP_CONTRACT["confirmatory_replicates"]) - 1),
            "--no-score-tune",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit, match="replicates"):
        main()


def test_confirmatory_campaign_rejects_score_tuning(monkeypatch, tmp_path) -> None:
    output = tmp_path / "confirmatory"
    monkeypatch.setattr(
        "sys.argv",
        [
            "map_run.py",
            "--campaign",
            "confirmatory",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit, match="no-score-tune"):
        main()


def test_confirmatory_campaign_requires_protocol_freeze(monkeypatch, tmp_path) -> None:
    output = tmp_path / "confirmatory"
    monkeypatch.setattr(
        "sys.argv",
        [
            "map_run.py",
            "--campaign",
            "confirmatory",
            "--replicates",
            str(int(MAP_CONTRACT["confirmatory_replicates"])),
            "--no-score-tune",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit, match="protocol-freeze"):
        main()


def test_protocol_freeze_loader_rejects_incomplete_record(tmp_path) -> None:
    record = tmp_path / "freeze.json"
    record.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid protocol-freeze manifest"):
        load_protocol_freeze(record)


def test_benchmark_pair_contract_rejects_incomplete_campaign() -> None:
    with pytest.raises(ValueError, match="fully paired"):
        validate_benchmark_pairs([], [], replicates=1)


def test_paired_bootstrap_intervals_are_deterministic() -> None:
    summaries = []
    for replicate in range(2):
        for scenario_index in range(3):
            for controller_index, controller in enumerate(CONTROLLERS):
                summaries.append(
                    {
                        "replicate": replicate,
                        "scenario_id": f"scenario-{scenario_index}",
                        "controller": controller,
                        "collision": bool((replicate + scenario_index + controller_index) % 5 == 0),
                        "safe_completion": True,
                        "final_goal_error_m": 0.1 + 0.01 * controller_index,
                        "compute_p95_ms": 10.0 + controller_index,
                    }
                )
    first = paired_bootstrap_intervals(summaries, replicates=40, seed=7)
    second = paired_bootstrap_intervals(summaries, replicates=40, seed=7)
    assert first == second
    assert first["cca_nmpc"]["safe_completion_rate"]["unit_count"] == 6
    assert first["mpc"]["collision_rate"]["replicates"] == 40


def test_paired_effect_intervals_define_positive_reference_gain() -> None:
    summaries = []
    for replicate in range(2):
        for scenario_index in range(3):
            for controller_index, controller in enumerate(CONTROLLERS):
                summaries.append(
                    {
                        "replicate": replicate,
                        "scenario_id": f"scenario-{scenario_index}",
                        "controller": controller,
                        "collision": controller != "cca_nmpc",
                        "safe_completion": controller == "cca_nmpc",
                        "final_goal_error_m": 0.2 if controller != "cca_nmpc" else 0.1,
                        "compute_p95_ms": 20.0 if controller != "cca_nmpc" else 10.0,
                        "path_length_m": 1.2 if controller != "cca_nmpc" else 1.0,
                        "tracking_rmse_m": 0.4 if controller != "cca_nmpc" else 0.2,
                        "yaw_rmse_rad": 0.3 if controller != "cca_nmpc" else 0.1,
                        "mean_command_variation_norm": 0.8 if controller != "cca_nmpc" else 0.5,
                        "fallback_duration_s": 0.2 if controller != "cca_nmpc" else 0.0,
                    }
                )
    effects = paired_effect_intervals(summaries, replicates=30, seed=9)
    assert effects["mpc"]["safe_completion_rate_gain"]["positive_favors_reference"] is True
    assert effects["mpc"]["collision_rate_reduction"]["lower"] == pytest.approx(1.0)
    assert effects["mpc"]["final_goal_error_reduction_m"]["lower"] == pytest.approx(0.1)
    assert effects["mpc"]["path_length_reduction_m"]["lower"] == pytest.approx(0.2)
    assert effects["mpc"]["tracking_rmse_reduction_m"]["lower"] == pytest.approx(0.2)
