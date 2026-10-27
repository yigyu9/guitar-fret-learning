"""Independent scalar accounting on CPU tensor fixtures; no simulator."""
from pathlib import Path
import json
import math
import sys

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
from guitar_learning.tests.test_gpu_environment import TensorSongTests


def main():
    torch.set_num_threads(1)
    rng = np.random.default_rng(16023)
    env, snapshot, _ = TensorSongTests().environment()
    previous = np.zeros((2, 39), dtype=np.float32)
    maximum_error = 0.
    for tick in range(37):
        action = torch.tensor(rng.uniform(-1, 1, (2, 39)), dtype=torch.float32)
        action[:, 33:] = 0.  # Preserve the existing inactive right-hand contract.
        current = action.numpy().copy()
        expected = []
        for row in range(2):
            total = 0.
            for column, name in enumerate(ACTIVE_NAMES):
                coefficient = 0. if name in LEFT_HAND_NAMES else (
                    .0025 if name in ('L_Wrist_x', 'L_Wrist_y', 'L_Wrist_z') else .01)
                delta = float(np.float32(current[row, column]-previous[row, column]))
                total += coefficient*max(abs(delta)-.05, 0.)**2
            expected.append(-total/39/60)
        TensorSongTests.advance(env, snapshot, action)
        for actual, reference in zip(env.terms['action_change'].tolist(), expected):
            error = abs(actual-reference)
            maximum_error = max(maximum_error, error)
            assert math.isclose(actual, reference, rel_tol=1e-6, abs_tol=3e-11)
        previous = current
        np.testing.assert_array_equal(env.previous_action.numpy(), previous)
        if tick == 19:
            env.set_curriculum(2.)
        if tick == 31:
            env.reset_reward_window()
            env.reset([0], snapshot)
            previous[0] = 0.
            np.testing.assert_array_equal(env.previous_action.numpy(), previous)
    print(json.dumps(dict(status='PASS', seed=16023, control_ticks=37,
        scalar_rate_comparisons=74, maximum_absolute_error=maximum_error,
        absolute_tolerance=3e-11, relative_tolerance=1e-6,
        collection_boundary_and_selected_reset_checked=True,
        stage_change_checked=True, native_or_GPU_execution=False)))


if __name__ == '__main__':
    main()
