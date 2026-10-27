from pathlib import Path
from copy import deepcopy
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tab2body.learning.ppo import PPOConfig, PPOTrainer, concise_training_line
from tab2body.learning.strike_curriculum import StrikeCurriculum, StrikeCurriculumConfig, STRIKE_STAGES
from tab2body.strike_cfg import STRIKE


def test_learning_rates():
    trainer = PPOTrainer.__new__(PPOTrainer)
    trainer.cfg = PPOConfig(completed_strike_lr_multiplier=0.25)
    trainer.optimizer = SimpleNamespace(param_groups=[{"lr": 1.0}, {"lr": 2.0}])
    trainer.training_context = {"curriculum_complete": True}
    assert trainer._apply_strike_maintenance_learning_rate() == {}
    assert trainer.optimizer.param_groups[0]["lr"] == 1.0
    trainer.training_context["curriculum_song_has_strum"] = False
    for _ in range(3):
        stats = trainer._apply_strike_maintenance_learning_rate()
        assert stats["actor_learning_rate"] == trainer.cfg.actor_learning_rate * 0.25
        assert stats["critic_learning_rate"] == trainer.cfg.learning_rate * 0.25
    trainer.optimizer.param_groups[0]["lr"] = 9.0
    trainer._apply_strike_maintenance_learning_rate()
    assert trainer.optimizer.param_groups[0]["lr"] == trainer.cfg.actor_learning_rate * 0.25
    trainer.training_context["curriculum_complete"] = False
    assert trainer._apply_strike_maintenance_learning_rate()["strike_maintenance_lr_multiplier"] == 1.0


def test_case_diagnostics():
    config = StrikeCurriculumConfig(
        min_iterations={stage: 1 for stage in STRIKE_STAGES},
        max_iterations={stage: 100 for stage in STRIKE_STAGES},
        s2_profiles=tuple(STRIKE["curriculum"]["s2_profiles"]))
    curriculum = StrikeCurriculum(config)
    protocol = {"seed": 1729, "episodes": 64}
    best = {"clean_full_song_rate": 1.0, "f1_p10": 1.0}
    lower = {"clean_full_song_rate": 0.8, "f1_p10": 0.98}
    curriculum._record_case_quality(best, protocol)
    for _ in range(curriculum.config.promotion_windows):
        curriculum._record_case_quality(lower, protocol)
    quality = curriculum.original_tempo_case_quality
    assert quality["repeated_below_best_warning"]
    assert abs(quality["clean_full_song_rate_drop"] - 0.2) < 1e-8
    restored = StrikeCurriculum(config)
    restored.load_context(curriculum.state())
    assert restored.original_tempo_case_quality == quality
    line = concise_training_line({
        "iteration": 1, "curriculum_current_quality_passed": True,
        "curriculum_original_tempo_case_quality": quality,
    }, first=1, last=10)
    assert "case-quality=below-best" in line
    assert "quality=passed" in line
    for key, bad_value in (
            ("f1_p10", float("nan")),
            ("clean_full_song_rate_below_best_streak", float("nan")),
            ("f1_p10_below_best_streak", -1),
            ("same_protocol", 1),
            ("protocol", {"seed": float("inf")}),
            ("f1_p10_drop", 0.5),
            ("repeated_below_best_warning", False)):
        state = deepcopy(curriculum.state())
        state["curriculum_original_tempo_case_quality"][key] = bad_value
        try:
            restored.load_context(state)
        except ValueError:
            pass
        else:
            raise AssertionError("corrupt case quality accepted: " + key)
    curriculum._record_case_quality(lower, {"seed": 1730, "episodes": 64})
    assert not curriculum.original_tempo_case_quality["repeated_below_best_warning"]
    assert curriculum.original_tempo_case_quality["clean_full_song_rate_drop"] == 0.0
    curriculum._record_case_quality(None, None)
    assert curriculum.original_tempo_case_quality == {}


if __name__ == "__main__":
    test_learning_rates()
    test_case_diagnostics()
    print("PASS: Strike maintenance learning rates and case diagnostics")
