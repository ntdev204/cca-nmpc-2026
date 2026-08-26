import numpy as np

from runtime.controller import CompiledController
from simulations.python.model import position_step


def test_position_state_step_uses_body_velocity_command() -> None:
    next_state = position_step(np.zeros(6), np.asarray((0.4, 0.1, 0.2)), 0.1)
    assert next_state.shape == (6,)
    assert next_state[0] > 0.0
    assert next_state[1] > 0.0
    np.testing.assert_allclose(next_state[3:], (0.4, 0.1, 0.2))


def test_compiled_position_controller_returns_three_command_components() -> None:
    controller = CompiledController("nmpc", 0.1, horizon=3, deadline_ms=100.0, robot_radius_m=0.18, human_radius_m=0.34)
    state = np.zeros(6)
    reference = np.zeros((6, 4))
    reference[0, 1:] = 1.0
    result = controller.command(state, reference, np.zeros(3))
    assert result.first_command_mps.shape == (3,)
    assert result.predicted_states.shape == (3, 6)
