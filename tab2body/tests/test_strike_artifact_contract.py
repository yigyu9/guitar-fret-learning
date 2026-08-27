"""CPU-only contract checks for strike plots and dual-camera recordings."""
from pathlib import Path
import json
import tempfile
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
for path in (str(PACKAGE_ROOT), str(PROJECT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from learning.checkpoint_contract import (
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    build_strike_contract_payload,
    checkpoint_evaluation_hyperparameters,
    file_sha256,
    seal_checkpoint_contract,
)
from tools.plot_strike_training import (
    PANEL_SERIES,
    STAGES,
    available_series,
    default_output_path,
    read_metric_rows,
    render_plot,
    stage_spans,
    step_values,
)
from tools import record_strike_rollout as recorder
from tools.audit_strike_motion import (
    resolve_motion_audit_path,
    summarize_samples,
)


def expect_error(fragment, callback, error_type=ValueError):
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(
            "expected {} containing {!r}".format(
                error_type.__name__, fragment))


def metric_fixture():
    return [
        {
            "steps": 100,
            "curriculum_stage": "A0_PICK_GRIP",
            "reward": 0.1,
            "curriculum_grip_quality": 0.72,
            "grip_success_rate": 0.60,
        },
        {
            "steps": 200,
            "curriculum_stage": "A1_TIP_READY",
            "reward": 0.2,
            "tip_ready_success_rate": 0.75,
        },
        {
            "steps": 300,
            "curriculum_stage": "A2_FREE_CROSSING",
            "reward": 0.3,
            "release_recall": 0.80,
            "strike_false_positive_rate": 0.10,
        },
        {
            "steps": 400,
            "curriculum_stage": "A3_TIMED_CROSSING",
            "reward": 0.4,
            "strike_precision": 0.85,
            "strike_recall": 0.83,
            "strike_f1": 0.84,
            "strike_timing_mae_ms": 41.0,
            "timing_p95_ms": 78.0,
            "timing_tolerance_ms": 100.0,
        },
        {
            "steps": 500,
            "curriculum_stage": "A4_ZONE_CONTROL",
            "reward": 0.5,
            "curriculum_strike_f1": 0.91,
            "curriculum_timing_p95_ms": 49.0,
            "curriculum_timing_tolerance_ms": 50.0,
            "zone_success_rate": 0.88,
            "failure_termination": 0.02,
            "strike_false_positive_rate": 0.03,
            "curriculum_tip_speed_m_s": 0.42,
            "curriculum_guitar_penetration_depth": 0.001,
            "curriculum_guitar_swept_penetration_depth": 0.002,
            "curriculum_release_phase_violation": 0.01,
            "curriculum_guitar_penetration": 0.02,
            "curriculum_action_saturation_fraction": 0.04,
        },
    ]


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        metrics = root / "run" / "logs" / "metrics.jsonl"
        metrics.parent.mkdir(parents=True)
        rows = metric_fixture()
        metrics.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8")

        loaded = read_metric_rows(metrics)
        x = step_values(loaded)
        spans = stage_spans(loaded, x)
        # assert [stage for stage, _start, _end in spans] == list(STAGES)
        
        # metric_fixture() only exercises A0-A4 (one row each); STAGES now
        # also includes the X0_MINI_STRUM extension, which this fixture
        # does not visit, so compare against the fixture's own stage
        # sequence rather than the full STAGES tuple.
        assert [stage for stage, _start, _end in spans] == [
            row["curriculum_stage"] for row in rows]
        assert set(STAGES) >= set(row["curriculum_stage"] for row in rows)

        failure_series = dict(PANEL_SERIES[-1][1])
        wrong_x, wrong_y = available_series(
            loaded, x, failure_series["wrong crossing"])
        assert wrong_x == [300.0, 500.0]
        assert wrong_y == [0.10, 0.03]
        precedence_rows = [{
            "steps": 1,
            "strike_false_positive_rate": 0.02,
            "false_positive_rate": 0.80,
        }]
        release_aliases = dict(PANEL_SERIES[3][1])[
            "false positive rate"]
        _x, values = available_series(
            precedence_rows, [1.0], release_aliases)
        assert values == [0.02]
        motion_rates = dict(PANEL_SERIES[-2][1])
        _x, saturation = available_series(
            loaded, x, motion_rates["action saturation"])
        assert saturation == [0.04]
        expected_plot = root / "run" / "plots" / "strike_training_curves.png"
        assert default_output_path(metrics) == expected_plot
        plotted = render_plot(metrics)
        assert plotted == expected_plot
        assert plotted.is_file() and plotted.stat().st_size > 1000

        sparse = root / "sparse.jsonl"
        sparse.write_text(
            json.dumps({
                "iteration": 1,
                "stage": "A0_PICK_GRIP",
                "mean_reward": 0.0,
            }) + "\n",
            encoding="utf-8")
        sparse_plot = render_plot(sparse)
        assert sparse_plot.is_file()

        backwards = root / "backwards.jsonl"
        backwards.write_text(
            '{"steps": 2}\n{"steps": 1}\n', encoding="utf-8")
        expect_error(
            "not monotonic",
            lambda: step_values(read_metric_rows(backwards)))

        malformed = root / "malformed.jsonl"
        malformed.write_text('{"steps": 1}\n{broken}\n', encoding="utf-8")
        expect_error("line 2", lambda: read_metric_rows(malformed))

        checkpoint_path = (
            root / "run" / "checkpoints" / "strike_000500.pt")
        expected_paths = recorder.resolve_video_paths(checkpoint_path)
        assert expected_paths == {
            "remembered": (
                root / "run" / "videos"
                / "strike_000500_rollout_remembered.mp4"),
            "current": (
                root / "run" / "videos"
                / "strike_000500_rollout_current.mp4"),
        }
        override = root / "custom.mp4"
        assert recorder.resolve_video_paths(
            checkpoint_path, remembered=override)["remembered"] == override
        assert resolve_motion_audit_path(checkpoint_path) == (
            root / "run" / "evaluations"
            / "strike_000500.motion_diagnostics.json")
        summary = summarize_samples([3.0, 1.0, 2.0, float("nan")])
        assert summary["count"] == 3
        assert summary["mean"] == 2.0
        assert summary["p50"] == 2.0
        assert summary["p95"] == 2.9
        assert summary["maximum"] == 3.0
        assert summarize_samples([])["p95"] is None

        checkpoint = {
            "environment_state": {
                "schema": "tab2body.strike_environment_state.v2",
                "curriculum_stage": "A3_TIMED_CROSSING",
                "timing_tolerance_ms": 67,
                "tempo_lambda": 1.0,
            },
            "training_context": {
                "curriculum_stage": "A3_TIMED_CROSSING",
                "curriculum_timing_tolerance_ms": 67,
            },
        }
        assert recorder.restore_stage_and_tolerance(checkpoint) == (
            "A3_TIMED_CROSSING", 67.0, 1.0)
        mismatch = {
            "environment_state": {
                "schema": "tab2body.strike_environment_state.v2",
                "curriculum_stage": "A3_TIMED_CROSSING",
                "timing_tolerance_ms": 67,
                "tempo_lambda": 1.0,
            },
            "training_context": {
                "curriculum_stage": "A4_ZONE_CONTROL",
                "curriculum_timing_tolerance_ms": 50,
            },
        }
        expect_error(
            "curriculum state mismatch",
            lambda: recorder.restore_stage_and_tolerance(mismatch))
        expect_error(
            "environment_state.v2",
            lambda: recorder.restore_stage_and_tolerance({
                "training_context": {
                    "curriculum_stage": "A4_ZONE_CONTROL",
                    "curriculum_timing_tolerance_ms": 50,
                },
            }))
        expect_error(
            "timing tolerance",
            lambda: recorder.restore_stage_and_tolerance({
                "environment_state": {
                    "schema": "tab2body.strike_environment_state.v2",
                    "curriculum_stage": "A0_PICK_GRIP",
                },
                "training_context": {
                    "curriculum_stage": "A0_PICK_GRIP",
                    "curriculum_timing_tolerance_ms": 100,
                },
            }))
        expect_error(
            "valid strike curriculum stage",
            lambda: recorder.restore_stage_and_tolerance({
                "environment_state": {
                    "schema": "tab2body.strike_environment_state.v2",
                    "curriculum_stage": "UNKNOWN",
                    "timing_tolerance_ms": 50,
                    "tempo_lambda": 1.0,
                },
                "training_context": {
                    "curriculum_stage": "UNKNOWN",
                    "curriculum_timing_tolerance_ms": 50,
                },
            }))
        invalid_tempo = json.loads(json.dumps(checkpoint))
        invalid_tempo["environment_state"]["tempo_lambda"] = 1.5
        expect_error(
            "tempo lambda",
            lambda: recorder.restore_stage_and_tolerance(invalid_tempo))

        document = seal_checkpoint_contract({
            "schema": STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
            "task": "strike",
        })
        validated, payload = recorder._checkpoint_payload({
            "checkpoint_contract": document,
        })
        assert validated == document and payload["task"] == "strike"
        tampered = json.loads(json.dumps(document))
        tampered["payload"]["task"] = "fret"
        expect_error(
            "integrity failure",
            lambda: recorder._checkpoint_payload({
                "checkpoint_contract": tampered,
            }))

        goal = root / "goal.json"
        grip = root / "grip.json"
        goal.write_text('{"goal": true}\n', encoding="utf-8")
        grip.write_text('{"grip": true}\n', encoding="utf-8")
        full_payload = build_strike_contract_payload(
            controlled_dof_names=("R_Shoulder_x", "RH:index2"),
            num_obs=12,
            num_actions=2,
            value_dim=1,
            action_scale=1.0,
            action_alpha=0.5,
            reset_soft_limit_fraction=0.02,
            policy_init_std=0.04,
            strike_config={"stage_order": list(STAGES)},
            ppo_config={"horizon": 32},
            observation_manifest=("base", "strike_goal"),
            goal_sha256=file_sha256(goal),
            grip_reference_sha256=file_sha256(grip),
            asset_fingerprint={"sha256": "1" * 64, "manifest": []},
            implementation_fingerprint={
                "sha256": "2" * 64, "manifest": []},
            policy_distribution_version=(
                "tanh_squashed_diagonal_gaussian.v1"),
            sim_hz=60,
            sim_substeps=4,
        )
        full_document = seal_checkpoint_contract(full_payload)
        full_checkpoint = {"checkpoint_contract": full_document}
        init_std, saved_ppo = checkpoint_evaluation_hyperparameters(
            full_checkpoint)
        assert init_std == 0.04
        assert saved_ppo == {"horizon": 32}
        saved_ppo["horizon"] = 99
        assert full_document["payload"]["config"]["ppo"]["horizon"] == 32
        expect_error(
            "not a strike policy",
            lambda: checkpoint_evaluation_hyperparameters({
                "checkpoint_contract": seal_checkpoint_contract({
                    **full_payload,
                    "task": "fret",
                }),
            }))

        assert set(recorder.CAMERA_DIRECTIONS) == {
            "remembered", "current"}
        assert recorder.CAMERA_DIRECTIONS["remembered"] == (
            0.15, 0.85, 0.62)
        assert recorder.CAMERA_DIRECTIONS["current"] == (
            -0.7474, 0.4317, 0.62)
        assert recorder.CAMERA_DISTANCE_M == 0.7
        assert recorder.CAMERA_HORIZONTAL_FOV_DEG == 42.0
        for direction in recorder.CAMERA_DIRECTIONS.values():
            unit = recorder._unit(direction)
            assert abs(sum(value * value for value in unit) - 1.0) < 1e-12

        original_which = recorder.shutil.which
        try:
            recorder.shutil.which = lambda _name: None
            expect_error(
                "ffmpeg is required", recorder.require_ffmpeg,
                error_type=RuntimeError)
        finally:
            recorder.shutil.which = original_which

        frames = root / "frames"
        frames.mkdir()
        protected_video = root / "protected.mp4"
        protected_video.write_bytes(b"existing-good-video")
        expect_error(
            "ffmpeg failed",
            lambda: recorder._encode_video(
                "/bin/false", frames, 30, protected_video),
            error_type=RuntimeError)
        assert protected_video.read_bytes() == b"existing-good-video"
        assert not list(root.glob(".protected.*.mp4"))

    print("PASS: strike plot and dual-camera artifact contracts")


if __name__ == "__main__":
    main()
