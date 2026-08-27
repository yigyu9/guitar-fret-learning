"""The strike CLI parser must not import torch before Isaac Gym."""
from __future__ import annotations

import ast
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    assert "torch" not in sys.modules
    assert "isaacgym" not in sys.modules

    from tab2body import strike_checkpoint, train_strike

    assert "torch" not in sys.modules
    assert "isaacgym" not in sys.modules
    parser = train_strike.build_parser()
    args = parser.parse_args([
        "--iterations", "7",
        "--curriculum-stage", "A2_FREE_CROSSING",
    ])
    assert args.iterations == 7
    assert args.curriculum_stage == "A2_FREE_CROSSING"
    assert not train_strike._curriculum_stalled({})
    assert train_strike._curriculum_stalled({
        "next_curriculum_stalled": True})
    incomplete_a4 = type("Env", (), {
        "curriculum_stage": "A4_ZONE_CONTROL",
        "tempo_lambda": 0.75,
    })()
    complete_a4 = type("Env", (), {
        "curriculum_stage": "A4_ZONE_CONTROL",
        "tempo_lambda": 1.0,
    })()
    a3 = type("Env", (), {
        "curriculum_stage": "A3_TIMED_CROSSING",
        "tempo_lambda": 1.0,
    })()
    assert not train_strike._full_song_evaluation_ready(incomplete_a4)
    assert train_strike._full_song_evaluation_ready(complete_a4)
    assert not train_strike._full_song_evaluation_ready(a3)
    assert "song_id" not in train_strike.STRIKE
    assert "video_interval" not in train_strike.STRIKE
    assert "control_prefixes" not in train_strike.STRIKE
    semantic = strike_checkpoint.semantic_strike_config(train_strike.STRIKE)
    assert semantic["safety"] == train_strike.STRIKE["safety"]
    assert "control_prefixes" not in semantic
    runtime_files = strike_checkpoint.STRIKE_RUNTIME_IMPLEMENTATION_FILES
    assert "train.py" not in runtime_files
    assert "learning/run_layout.py" not in (
        runtime_files)
    assert "env/config.py" in runtime_files
    assert "env/safety.py" in runtime_files
    assert "env/metrics.py" in runtime_files
    assert "strike_checkpoint.py" in runtime_files
    assert "strike_training_runtime.py" in runtime_files
    assert "learning/checkpoint_contract.py" in runtime_files
    assert "train_strike.py" in train_strike.STRIKE_TOOLING_PROVENANCE_FILES
    assert "tools/audit_strike_motion.py" in (
        train_strike.STRIKE_TOOLING_PROVENANCE_FILES)
    assert not (
        set(runtime_files)
        & set(train_strike.STRIKE_TOOLING_PROVENANCE_FILES))



    task_source = (
        PROJECT_ROOT / "tab2body/env/tasks/task_strike.py").read_text(
            encoding="utf-8")
    task_tree = ast.parse(task_source)
    strike_class = next(
        node for node in task_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "StrikeTask")
    rollout_assignment = next(
        node for node in strike_class.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "rollout_diagnostic_keys"
                for target in node.targets))
    rollout_diagnostics = ast.literal_eval(rollout_assignment.value)
    for diagnostic in (
            "release_phase_violation",
            "tip_speed_m_s",
            "guitar_penetration_depth",
            "guitar_swept_penetration_depth",
            "guitar_penetration",
            "action_saturation_fraction"):
        assert diagnostic in rollout_diagnostics
    assert "target_lane_shift_m" in rollout_diagnostics
    assert '"release_phase_violation": release_phase_violation' in task_source
    assert '"release_depth_m": detection["depth"].clone()' in task_source
    assert '"release_across_speed_m_s": detection[' in task_source
    assert "self.target_lane_y[continuing]" not in task_source
    assert "RightGuitarPenetrationMonitor" in task_source

    assert "torch" not in sys.modules
    assert "isaacgym" not in sys.modules
    print("PASS: strike parser keeps Isaac Gym and torch runtime-lazy")


if __name__ == "__main__":
    main()
