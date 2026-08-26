from __future__ import annotations

import numpy as np
import pytest

from runtime.kalman import KalmanConfig, SixStateKalman


def test_six_state_kalman_integrates_body_velocity() -> None:
    estimator = SixStateKalman(config=KalmanConfig(max_dt_s=2.0))
    estimator.step(0, (0.0, 0.0, 0.0))
    state = estimator.step(1_000_000_000, (1.0, 0.0, 0.0))
    assert state[0] == pytest.approx(0.0, abs=5.0e-2)
    state = estimator.step(2_000_000_000, (1.0, 0.0, 0.0))
    assert state[0] == pytest.approx(1.0, abs=2.0e-2)
    assert state[1] == pytest.approx(0.0, abs=1.0e-6)
    assert state[3] == pytest.approx(1.0, abs=5.0e-2)


def test_six_state_kalman_rotates_body_velocity_into_world_position() -> None:
    estimator = SixStateKalman(
        state=(0.0, 0.0, np.pi / 2.0, 0.0, 0.0, 0.0),
        config=KalmanConfig(max_dt_s=2.0),
    )
    estimator.step(0, (0.0, 0.0, 0.0))
    state = estimator.step(1_000_000_000, (1.0, 0.0, 0.0))
    assert state[0] == pytest.approx(0.0, abs=5.0e-2)
    assert state[1] == pytest.approx(0.0, abs=5.0e-2)
    state = estimator.step(2_000_000_000, (1.0, 0.0, 0.0))
    assert state[1] == pytest.approx(1.0, abs=2.0e-2)


def test_six_state_kalman_covariance_stays_symmetric_and_finite() -> None:
    estimator = SixStateKalman(config=KalmanConfig(max_dt_s=0.1))
    for index in range(20):
        estimator.step(
            index * 100_000_000,
            (0.2, -0.05, 0.1),
            acceleration_body_mps2=(0.1, -0.1),
            gyro_z_radps=0.1,
        )
    covariance = estimator.covariance
    assert np.isfinite(covariance).all()
    assert np.allclose(covariance, covariance.T)
    assert np.linalg.eigvalsh(covariance).min() >= -1.0e-10
    assert estimator.samples == 20


def test_six_state_kalman_rejects_nonmonotonic_timestamps() -> None:
    estimator = SixStateKalman()
    estimator.step(100, (0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="monotonic"):
        estimator.step(99, (0.0, 0.0, 0.0))
