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
        "--curriculum-stage", "A2_SINGLE_CROSSING",
    ])
    assert args.iterations == 7
    assert args.curriculum_stage == "A2_SINGLE_CROSSING"
    assert args.observation_contract == "strike.observation.v2"
    assert args.initialize_tempo == 0.0
    smoke_video = parser.parse_args([
        "--smoke", "--smoke-video",
        "--periodic-video-min-gap", "1",
    ])
    assert smoke_video.smoke_video
    assert smoke_video.periodic_video_min_gap == 1
    endpoint_transfer = parser.parse_args([
        "--initialize-from", "/tmp/strike_003147.pt",
        "--initialize-stage", "S2_TIMED_STRUM",
        "--allow-policy-objective-transfer",
    ])
    assert endpoint_transfer.initialize_stage == "S2_TIMED_STRUM"
    assert endpoint_transfer.allow_policy_objective_transfer
    automatic_transfer = parser.parse_args([
        "--initialize-from", "/tmp/strike_004000.pt",
    ])
    assert automatic_transfer.initialize_tempo == 0.0
    metric_line = train_strike.full_song_evaluation_line(500, {
        "metrics": {
            "strike_f1": 0.8754,
            "precision": 0.91,
            "release_recall": 0.844,
        },
    })
    assert "full-song-F1=0.875" in metric_line
    assert "tempo=original" in metric_line
    runner_source = (
        PROJECT_ROOT / "tab2body/train_strike.py").read_text(
            encoding="utf-8")
    assert "_StrikeCurriculumStalled" not in runner_source
    assert "raise _StrikeCurriculumStalled" not in runner_source
    incomplete_a4 = type("Env", (), {
        "curriculum_stage": "S3_SONG_INTEGRATION",
        "tempo_lambda": 0.75,
    })()
    complete_a4 = type("Env", (), {
        "curriculum_stage": "S3_SONG_INTEGRATION",
        "tempo_lambda": 1.0,
    })()
    a3 = type("Env", (), {
        "curriculum_stage": "A3_TIMED_SINGLE",
        "tempo_lambda": 1.0,
    })()
    assert not train_strike._full_song_evaluation_ready(incomplete_a4)
    assert train_strike._full_song_evaluation_ready(complete_a4)
    assert not train_strike._full_song_evaluation_ready(a3)
    assert "song_id" not in train_strike.STRIKE
    assert "video_interval" not in train_strike.STRIKE
    assert "control_prefixes" not in train_strike.STRIKE
    semantic = strike_checkpoint.semantic_strike_config(train_strike.STRIKE)
    assert semantic["observation_contract"] == "strike.observation.v2"
    assert semantic["safety"] == train_strike.STRIKE["safety"]
    assert semantic["direction_profile"] == "phrase_dp_microtiming_v3"
    assert semantic["transition_profile"] == "entry_side_edge_gap_v2"
    assert semantic["recovery_contract"] == (
        "path_aware_clearance_handoff.v1")
    assert semantic["timing_reward_contract"] == (
        "physical_endpoint_then_centered_timing.v2")
    assert semantic["strum_motion_contract"] == (
        "direction_symmetric_terminal_exit_progress.v1")
    assert semantic["metric_contract"] == (
        "pooled_recovery_physical_event_diagnostics.v3")
    assert semantic["curriculum_contract"] == (
        "continuous_quality_maintenance_diagnostics.v16")
    assert semantic["success_event"] == (
        "ordered_multi_string_release_with_terminal_exit_then_clearance_handoff")
    legacy_profiles = strike_checkpoint.semantic_strike_config(
        train_strike.STRIKE,
        direction_profile="phrase_dp_microtiming_v2",
        transition_profile="entry_side_edge_gap_v1")
    assert legacy_profiles["direction_profile"] == (
        "phrase_dp_microtiming_v2")
    assert legacy_profiles["transition_profile"] == (
        "entry_side_edge_gap_v1")
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
            "action_saturation_fraction",
            "strum_terminal_progress",
            "strum_physical_completion_pulse",
            "strum_final_string_miss_at_timeout",
            "s2_focus_sampled"):
        assert diagnostic in rollout_diagnostics
    assert "target_lane_shift_m" in rollout_diagnostics
    assert "strum_progress" in rollout_diagnostics
    assert "strum_max_strings" in rollout_diagnostics
    assert '"release_phase_violation": release_phase_violation' in task_source
    assert '"release_depth_m": detection["depth"].clone()' in task_source
    assert '"release_across_speed_m_s": detection[' in task_source
    assert "self.target_lane_y[continuing]" not in task_source
    assert (
        "self.direction_profile = self.goals.compiled.direction_profile"
        in task_source)
    assert (
        "self.transition_profile = self.goals.compiled.transition_profile"
        in task_source)
    assert "RightGuitarPenetrationMonitor" in task_source
    assert '"tab2body.strike_environment_state.v14"' in task_source
    assert "def policy_action_std_floor(self):" in task_source

    assert "torch" not in sys.modules
    assert "isaacgym" not in sys.modules
    print("PASS: strike parser keeps Isaac Gym and torch runtime-lazy")


if __name__ == "__main__":
    main()
