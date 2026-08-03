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

from learning.checkpoint_contract import (  # noqa: E402
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    build_strike_contract_payload,
    checkpoint_evaluation_hyperparameters,
    file_sha256,
    seal_checkpoint_contract,
)
from tools.plot_strike_training import (  # noqa: E402
    STAGES,
    default_output_path,
    read_metric_rows,
    render_plot,
    stage_spans,
    step_values,
)
from tools import record_strike_rollout as recorder  # noqa: E402


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
            "false_positive_rate": 0.10,
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
            "strike_wrong_rate": 0.03,
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
        assert [stage for stage, _start, _end in spans] == list(STAGES)
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

        checkpoint = {
            "environment_state": {
                "curriculum_stage": "A3_TIMED_CROSSING",
                "timing_tolerance_ms": 67,
            },
            "training_context": {
                "curriculum_stage": "A2_FREE_CROSSING",
                "curriculum_timing_tolerance_ms": 100,
            },
        }
        assert recorder.restore_stage_and_tolerance(checkpoint) == (
            "A3_TIMED_CROSSING", 67.0)
        fallback = {
            "training_context": {
                "curriculum_stage": "A4_ZONE_CONTROL",
                "curriculum_timing_tolerance_ms": 50,
            },
        }
        assert recorder.restore_stage_and_tolerance(fallback) == (
            "A4_ZONE_CONTROL", 50.0)
        expect_error(
            "timing tolerance",
            lambda: recorder.restore_stage_and_tolerance({
                "training_context": {
                    "curriculum_stage": "A0_PICK_GRIP",
                },
            }))
        expect_error(
            "valid strike curriculum stage",
            lambda: recorder.restore_stage_and_tolerance({
                "environment_state": {
                    "curriculum_stage": "UNKNOWN",
                    "timing_tolerance_ms": 50,
                },
            }))

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

        class FakeIndices:
            def detach(self):
                return self

            def cpu(self):
                return self

            def tolist(self):
                return [0, 1]

        class FakeEnv:
            num_obs = 12
            num_actions = 2
            value_dim = 1
            ctrl_idx = FakeIndices()
            dof_names = ("R_Shoulder_x", "RH:index2")
            observation_manifest = ("base", "strike_goal")

        recorder._fallback_verify_live_contract(
            full_checkpoint, full_document, full_payload, FakeEnv(),
            goal, grip)
        changed_goal = root / "changed_goal.json"
        changed_goal.write_text('{"goal": false}\n', encoding="utf-8")
        expect_error(
            "goal SHA-256",
            lambda: recorder._fallback_verify_live_contract(
                full_checkpoint, full_document, full_payload, FakeEnv(),
                changed_goal, grip))

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

    print("PASS: strike plot and dual-camera artifact contracts")


if __name__ == "__main__":
    main()
