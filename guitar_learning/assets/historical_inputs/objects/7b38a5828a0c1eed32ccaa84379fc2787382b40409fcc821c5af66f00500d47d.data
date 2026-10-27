import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import torch

from tab2body.learning.strike_repeat_evaluation import (
    fixed_evaluation_cases, repeated_case_summary, repeated_evaluation_quality_key,
    reconcile_event_diagnostics,
)
from tab2body.learning.checkpoint_contract import file_sha256
from tab2body.learning.run_layout import layout_for
from tab2body.train_strike import _update_best_evaluation


class Env:
    num_envs = 3
    max_episode_length = 5
    episode_metric_keys = ("score",)

    def __init__(self):
        self.rng = torch.Generator()
        self._reset_generation = torch.ones(3, dtype=torch.long) * 12
        self.event_index = torch.zeros(3, dtype=torch.long)
        self.goals = SimpleNamespace(num_events=2, direction=torch.tensor([1, -1]),
                                     traversal_mask=torch.tensor([[1, 0], [0, 1]]))

    def reset(self):
        self.frame = 0
        self._reset_generation += 1
        self.target_lane_y = torch.rand(3, generator=self.rng)
        return None

    def step(self, action):
        self.frame += 1
        done = torch.tensor([self.frame == 4, True, True])
        return None, None, done, {"score": torch.arange(3)[done],
                                 "target_hit": torch.tensor([True, False, False]),
                                 "miss": torch.tensor([False, True, True])}


class Model:
    def act(self, obs, deterministic):
        assert deterministic
        return None, None, None


env = Env()
first = [(case, int(info["score"][local]))
         for case, local, info in fixed_evaluation_cases(torch, env, Model(), 2)]
second = [(case, int(info["score"][local]))
          for case, local, info in fixed_evaluation_cases(torch, env, Model(), 2)]
assert first == second
assert [case["env_id"] for case, _ in first] == [1, 0]
assert [score for _, score in first] == [1, 0]
assert first[0][0]["event_diagnostics"][1]["observed_frames"] == 0
assert first[0][0]["event_diagnostics"][1]["miss"] is False
assert first[0][0]["event_diagnostics"][0]["miss"] is True
assert len(list(fixed_evaluation_cases(torch, env, Model(), 5))) == 5

# A physically completed but mistimed event emits miss, yet is TP rather than FN.
case = {"event_diagnostics": [
    {"observed_frames": 1, "miss": True, "physical_hit_count": 1,
     "physical_miss_count": 0, "wrong_crossing_count": 0.},
    {"observed_frames": 1, "miss": True, "physical_hit_count": 0,
     "physical_miss_count": 1, "wrong_crossing_count": 2.},
    {"observed_frames": 0, "miss": False, "physical_hit_count": 0,
     "physical_miss_count": 0, "wrong_crossing_count": 0.}]}
reconcile_event_diagnostics(case, {
    "strike_true_positive_count": torch.tensor([1.]),
    "strike_false_negative_count": torch.tensor([1.]),
    "strike_false_positive_count": torch.tensor([2.]),
    "episode_failure_termination": torch.tensor([True]),
}, 0)
assert case["event_reconciliation"]["raw_miss_event_count"] == 2
assert case["event_reconciliation"]["false_negative"]["event_count"] == 1
assert all(case["event_reconciliation"][key]["matches"]
           for key in ("true_positive", "false_negative", "false_positive"))
assert case["event_diagnostics"][2]["observation_status"] == "not_reached_early_termination"
assert first[0][0]["event_reconciliation"]["false_negative"]["matches"] is None


class OutcomeEnv(Env):
    def step(self, action):
        self.event_index.fill_(1)
        return None, None, torch.ones(3, dtype=torch.bool), {
            "score": torch.arange(3), "miss": torch.ones(3, dtype=torch.bool),
            "target_hit": torch.zeros(3, dtype=torch.bool),
            "physical_target_hit": torch.ones(3, dtype=torch.bool),
            "physical_target_miss": torch.zeros(3, dtype=torch.bool),
            "wrong_crossing_count": torch.zeros(3),
            "target_event_index_before_step": torch.zeros(3, dtype=torch.long),
            "strike_true_positive_count": torch.ones(3),
            "strike_false_negative_count": torch.zeros(3),
            "strike_false_positive_count": torch.zeros(3)}


outcome_env = OutcomeEnv()
outcome_env.event_index.fill_(1)
outcome_case = next(fixed_evaluation_cases(torch, outcome_env, Model(), 1))[0]
assert outcome_case["event_diagnostics"][0]["physical_hit_count"] == 1
assert outcome_case["event_diagnostics"][1]["observed_frames"] == 0
assert outcome_case["event_reconciliation"]["false_negative"]["matches"] is True

summary = repeated_case_summary([
    {"strike_episode_f1": 1.0, "strike_release_recall": 1.0},
    {"strike_episode_f1": 0.8, "strike_release_recall": 0.8}])
assert summary["clean_full_song_rate"] == 0.5
assert abs(summary["f1_p10"] - 0.82) < 1e-6

with tempfile.TemporaryDirectory() as directory:
    layout = layout_for(directory, create=True)
    checkpoint = layout.checkpoints / "strike_000100.pt"
    checkpoint.write_bytes(b"test policy")
    report = {"iteration": 100, "checkpoint": "checkpoints/strike_000100.pt",
              "checkpoint_sha256": file_sha256(checkpoint),
              "evaluated_model_sha256": "model-content-hash",
              "case_protocol": {"seed": 1729, "num_envs": 3},
              "case_summary": summary,
              "quality_eligibility": {"safety_passed": True, "grip_passed": True},
              "metrics": {"strike_f1": 0.9, "release_recall": 0.9,
                          "false_positive_rate": 0.0, "timing_p95_ms": 10.0}}
    target = layout.evaluations / "test.json"
    target.write_text(json.dumps(report))
    best = _update_best_evaluation(layout, report, target)
    snapshot = layout.root / best["checkpoint"]
    assert snapshot.is_file() and not Path(best["checkpoint"]).is_absolute()
    checkpoint.write_bytes(b"resaved training state")
    assert snapshot.read_bytes() == b"test policy"
    worse = dict(report, case_summary=dict(summary, clean_full_song_rate=0.4))
    assert repeated_evaluation_quality_key(worse) < repeated_evaluation_quality_key(report)
    unsafe = dict(report, quality_eligibility={"safety_passed": False, "grip_passed": True},
                  case_summary=dict(summary, clean_full_song_rate=1.0))
    bad_grip = dict(report, quality_eligibility={"safety_passed": True, "grip_passed": False},
                    case_summary=dict(summary, clean_full_song_rate=1.0))
    assert repeated_evaluation_quality_key(unsafe) < repeated_evaluation_quality_key(report)
    assert repeated_evaluation_quality_key(bad_grip) < repeated_evaluation_quality_key(report)
    assert _update_best_evaluation(layout, worse, target)["iteration"] == 100
print("strike repeat evaluation tests passed")
