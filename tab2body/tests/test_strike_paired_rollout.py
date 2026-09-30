from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.tools.record_strike_rollout import (
    LiveStrikeRolloutRecorder,
    _goal_event_trace,
    actual_practice_direction,
    force_practice_direction,
)


class FakeEnvironment:
    curriculum_stage = "S2_TIMED_STRUM"

    def __init__(self):
        self.practice_direction = torch.tensor([1, -1], dtype=torch.long)
        self.rng = torch.Generator(device="cpu")
        self.rng.manual_seed(1234)
        self.reset_generation = torch.tensor([9, 12], dtype=torch.long)
        self.sample = None

    def compute_observations(self):
        return torch.tensor([
            float(self.sample),
            float(self.practice_direction[0]),
        ])


def snapshot_runtime(env):
    return {
        "rng_state": env.rng.get_state().clone(),
        "reset_generation": env.reset_generation.clone(),
    }


def restore_runtime(env, state):
    env.rng.set_state(state["rng_state"].clone())
    env.reset_generation.copy_(state["reset_generation"])
    env.sample = int(torch.randint(
        0, 1_000_000, (1,), generator=env.rng).item())
    env.reset_generation += 1
    env.practice_direction.fill_(1)
    return env.compute_observations()


def test_forced_direction_rebuilds_observation_from_actual_direction():
    env = FakeEnvironment()
    env.sample = 7
    assert actual_practice_direction(env, required=True) == "down"
    observation = force_practice_direction(env, "up")
    assert actual_practice_direction(env, required=True) == "up"
    assert observation.tolist() == [7.0, -1.0]


def test_paired_recorder_matches_conditions_and_restores_rng_runtime():
    env = FakeEnvironment()
    recorder = LiveStrikeRolloutRecorder.__new__(LiveStrikeRolloutRecorder)
    recorder.env = env
    observed = []

    def fake_record(_torch, _model, observation, _outputs, _max_steps):
        direction = actual_practice_direction(env, required=True)
        observed.append((direction, int(observation[0].item())))
        torch.randint(0, 1_000_000, (3,), generator=env.rng)
        env.reset_generation += 5
        return {"practice_direction": direction, "steps_simulated": 1}

    recorder.record = fake_record
    before = snapshot_runtime(env)
    outputs = {
        "down": {"remembered": "down-r.mp4", "current": "down-c.mp4"},
        "up": {"remembered": "up-r.mp4", "current": "up-c.mp4"},
    }
    captures, restored_observation = recorder.record_practice_direction_pair(
        torch, object(), outputs, 10,
        snapshot_runtime=snapshot_runtime,
        restore_runtime=restore_runtime)

    assert [item[0] for item in observed] == ["down", "up"]
    assert observed[0][1] == observed[1][1]
    assert captures["down"]["practice_direction"] == "down"
    assert captures["up"]["practice_direction"] == "up"
    assert captures["down"]["training_runtime_restored_after_pair"]
    assert captures["up"]["training_rng_restored_before_reset"]
    assert int(restored_observation[0].item()) == observed[0][1]

    expected = FakeEnvironment()
    expected.rng.set_state(before["rng_state"])
    expected.reset_generation.copy_(before["reset_generation"])
    expected_observation = restore_runtime(expected, before)
    assert torch.equal(env.rng.get_state(), expected.rng.get_state())
    assert torch.equal(env.reset_generation, expected.reset_generation)
    assert torch.equal(restored_observation, expected_observation)


def test_event_trace_uses_practice_direction_and_retains_plan_direction():
    class Goals:
        traversal_mask = torch.tensor([[True, True, False, False, False, False]])
        audible_mask = traversal_mask.clone()
        gesture = torch.tensor([1])
        direction = torch.tensor([-1])
        event_ids = [["event-0"]]
        frame = torch.tensor([10])
        time = torch.tensor([0.5])

    class Env:
        goals = Goals()
        _event_times = torch.tensor([0.5])

    trace = _goal_event_trace(Env(), 0, practice_direction="down")
    assert trace["direction"] == "down"
    assert trace["practice_direction"] == "down"
    assert trace["planned_direction"] == "up"


if __name__ == "__main__":
    test_forced_direction_rebuilds_observation_from_actual_direction()
    test_paired_recorder_matches_conditions_and_restores_rng_runtime()
    test_event_trace_uses_practice_direction_and_retains_plan_direction()
    print("strike paired rollout tests passed")
