from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from tab2body.strike_cfg import STRIKE
from tab2body.strike_checkpoint import (
    build_runtime_checkpoint_contract,
)
from tab2body.strike_contract import (
    S2_TIMED_STRUM,
    S3_SONG_INTEGRATION,
    STRIKE_STAGES,
)
from tab2body.strike_metrics import (
    STRIKE_RAW_COUNT_METRIC_KEYS,
    STRIKE_WEIGHTED_METRIC_GROUPS,
    StrikeRewardAlignmentMonitor,
    pool_strike_raw_count_rates,
)
from tab2body.strike_v2_contract import (
    STRIKE_V1_OBSERVATION_CONTRACT,
    STRIKE_V2_OBSERVATION_CONTRACT,
)
from tab2body.strike_training_runtime import (
    StrikeCurriculumRuntime,
    build_strike_curriculum,
    validate_strike_goal_for_training,
    validate_strike_training_alignment,
)
from tab2body.learning.checkpoint_contract import (
    checkpoint_evaluation_hyperparameters,
    file_sha256,
    fingerprint_file_set,
    strike_s2_policy_transfer_spec,
    verify_strike_policy_initialization_contract,
)
from tab2body.learning.run_io import (
    acquire_run_writer,
    append_jsonl_atomic,
    record_artifact_error,
    record_artifact_result,
    record_run_metadata,
    validate_jsonl,
    write_json_object_atomic,
)
from tab2body.learning.run_layout import (
    has_training_history,
    layout_for,
    resolve_run_dir,
)
from tab2body.learning.strike_repeat_evaluation import (
    EVALUATION_SEED,
    fixed_evaluation_cases,
    model_tensor_sha256,
    repeated_case_summary,
    repeated_evaluation_quality_key,
)
from tab2body.learning.periodic_checkpoint_video import (
    PeriodicCheckpointVideoSchedule,
    STRIKE_PAIRED_PRACTICE_STAGES,
    build_strike_practice_direction_report,
    strike_checkpoint_iteration,
    strike_full_song_capture_contract,
    strike_full_song_capture_summary,
    strike_full_song_is_better,
    strike_full_song_quality_key,
    strike_full_song_rollout_artifact_paths,
    strike_full_song_rollout_is_complete,
    strike_paired_rollout_artifact_paths,
    strike_paired_rollout_is_complete,
    strike_periodic_rollout_is_complete,
    strike_rollout_artifact_paths,
    strike_rollout_is_complete,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

STRIKE_TOOLING_PROVENANCE_FILES = (
    "strike_cfg.py",
    "train.py",
    "train_strike.py",
    "learning/run_io.py",
    "learning/run_layout.py",
    "learning/periodic_checkpoint_video.py",
    "learning/strike_evaluation.py",
    "tools/audit_strike_runtime.py",
    "tools/audit_strike_motion.py",
    "tools/audit_strike_string_alignment.py",
    "tools/build_strike_training_data.py",
    "tools/build_strike_plan.py",
    "tools/plot_strike_training.py",
    "tools/record_strike_rollout.py",
    "tools/record_strike_visualized_rollout.py",
    "tools/strike_visualization.py",
)


def _full_song_evaluation_ready(env):
    return bool(
        env.curriculum_stage == "S3_SONG_INTEGRATION"
        and abs(float(env.tempo_lambda) - 1.0) <= 1e-9)


def _strike_runtime_state(env):
    return {
        "curriculum_stage": str(env.curriculum_stage),
        "timing_tolerance_ms": float(env.timing_tolerance_ms),
        "tempo_lambda": float(env.tempo_lambda),
        "strum_span": int(env.strum_span),
        "s2_profile_name": str(env.s2_profile_name),
        "s2_endpoint_recovery_active": bool(getattr(
            env, "s2_endpoint_recovery_active", False)),
        "s2_focus_direction": str(getattr(
            env, "s2_focus_direction", "balanced")),
        "s2_focus_fraction": float(getattr(
            env, "s2_focus_fraction", 0.5)),
        "zone_gate_active": bool(env.zone_gate_active),
        "timing_reward_core_ms": float(env.timing_reward_core_ms),
        "duration_reward_core_ms": float(env.duration_reward_core_ms),
        "approach_lead_s": float(env.approach_lead_s),
        "timing_early_grace_ms": float(env.timing_early_grace_ms),
        "timing_early_penalty_scale_ms": float(
            env.timing_early_penalty_scale_ms),
        "song_f1_gate": float(env.curriculum_song_f1_gate),
        "curriculum_stalled": bool(env.curriculum_stalled),
        "evaluation_full_song": bool(env.evaluation_full_song),
        "event_failure_mass": env._event_failure_mass.clone(),
        "event_failure_exposure": env._event_failure_exposure.clone(),
        "event_failure_score": env._event_failure_score.clone(),
        "hard_window_probability_max": float(
            env._hard_window_probability_max),
        "rng_state": env.rng.get_state().clone(),
        "reset_generation": env._reset_generation.clone(),
    }


def _restore_strike_runtime(env, state):
    env.set_evaluation_mode(False, reset=False)
    env.set_curriculum_stage(
        state["curriculum_stage"],
        state["timing_tolerance_ms"],
        tempo_lambda=state["tempo_lambda"],
        strum_span=state["strum_span"],
        s2_profile_name=state["s2_profile_name"],
        s2_endpoint_recovery_active=state[
            "s2_endpoint_recovery_active"],
        s2_focus_direction=state["s2_focus_direction"],
        s2_focus_fraction=state["s2_focus_fraction"],
        zone_active=state["zone_gate_active"],
        timing_reward_core_ms=state["timing_reward_core_ms"],
        duration_reward_core_ms=state["duration_reward_core_ms"],
        approach_lead_s=state["approach_lead_s"],
        timing_early_grace_ms=state["timing_early_grace_ms"],
        timing_early_penalty_scale_ms=(
            state["timing_early_penalty_scale_ms"]),
        song_f1_gate=state["song_f1_gate"],
        stalled=state["curriculum_stalled"],
        reset=False)
    env.set_evaluation_mode(
        state["evaluation_full_song"], reset=False)
    env._event_failure_mass.copy_(state["event_failure_mass"])
    env._event_failure_exposure.copy_(state["event_failure_exposure"])
    env._event_failure_score.copy_(state["event_failure_score"])
    env._hard_window_probability_max = state[
        "hard_window_probability_max"]
    env.rng.set_state(state["rng_state"].detach().cpu())
    env._reset_generation.copy_(state["reset_generation"])
    return env.reset()


def _update_best_full_song(layout, report, report_path):
    report_path = Path(report_path).resolve()
    best_path = layout.evaluations / "best_full_song.json"
    incumbent = None
    incumbent_record = None
    if best_path.is_file():
        incumbent_record = json.loads(best_path.read_text(encoding="utf-8"))
        if not isinstance(incumbent_record, dict):
            raise ValueError("best full-song record must be a JSON object")
        incumbent_report_path = Path(incumbent_record["report"])
        if not incumbent_report_path.is_absolute():
            incumbent_report_path = layout.root / incumbent_report_path
        incumbent = json.loads(
            incumbent_report_path.read_text(encoding="utf-8"))
    selected = incumbent is None or strike_full_song_is_better(
        report, incumbent)
    quality_key = strike_full_song_quality_key(report)
    if selected:
        checkpoint = Path(report["checkpoint"]).resolve()
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        record = {
            "schema": "tab2body.strike_best_full_song.v1",
            "selected_at_utc": datetime.now(timezone.utc).isoformat(),
            "iteration": int(report["iteration"]),
            "checkpoint": str(checkpoint.relative_to(layout.root)),
            "checkpoint_sha256": file_sha256(checkpoint),
            "report": str(report_path.relative_to(layout.root)),
            "path_base": "run_root",
            "quality_key": list(quality_key),
            "event_trace_summary": dict(report["event_trace_summary"]),
            "grip_preservation": dict(report["grip_preservation"]),
        }
        write_json_object_atomic(best_path, record)
        incumbent_record = record
    write_json_object_atomic(layout.evaluations / "best_video.json", incumbent_record)
    best_summary = incumbent_record["event_trace_summary"]
    current_f1 = float(report["event_trace_summary"]["traversal_f1"])
    best_f1 = float(best_summary["traversal_f1"])
    return {
        "selected": selected,
        "best_record": str(best_path.resolve()),
        "best_checkpoint": incumbent_record["checkpoint"],
        "best_iteration": int(incumbent_record["iteration"]),
        "current_traversal_f1": current_f1,
        "best_traversal_f1": best_f1,
        "regression_warning": current_f1 < best_f1 - 0.01,
    }


def _update_best_evaluation(layout, report, report_path):
    best_path = layout.evaluations / "best_evaluation.json"
    quality_key = repeated_evaluation_quality_key(report)
    incumbent = (json.loads(best_path.read_text(encoding="utf-8"))
                 if best_path.is_file() else None)
    if incumbent is not None:
        if incumbent["case_protocol"] != report["case_protocol"]:
            raise ValueError("best evaluation requires the same fixed-case protocol")
        incumbent_checkpoint = layout.root / incumbent["checkpoint"]
        if (not incumbent_checkpoint.is_file()
                or file_sha256(incumbent_checkpoint) != incumbent["checkpoint_sha256"]):
            raise ValueError("best evaluation snapshot is missing or changed")
        if quality_key <= tuple(incumbent["quality_key"]):
            return incumbent
    checkpoint = layout.root / report["checkpoint"]
    if not checkpoint.is_file() or file_sha256(checkpoint) != report["checkpoint_sha256"]:
        raise ValueError("evaluation checkpoint is missing or changed")
    snapshot_dir = layout.evaluations / "checkpoints"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_dir / f"strike_{int(report['iteration']):06d}_{report['checkpoint_sha256'][:16]}.pt"
    if snapshot.exists():
        if file_sha256(snapshot) != report["checkpoint_sha256"]:
            raise ValueError("immutable evaluation snapshot hash mismatch")
    else:
        temporary = snapshot.with_suffix(".pt.tmp")
        shutil.copyfile(checkpoint, temporary)
        temporary.replace(snapshot)
    record = {
        "schema": "tab2body.strike_best_evaluation.v1",
        "iteration": report["iteration"],
        "checkpoint": str(snapshot.relative_to(layout.root)),
        "checkpoint_sha256": report["checkpoint_sha256"],
        "report": str(Path(report_path).resolve().relative_to(layout.root)),
        "path_base": "run_root",
        "case_protocol": report["case_protocol"],
        "case_summary": report["case_summary"],
        "quality_eligibility": report["quality_eligibility"],
        "evaluated_model_sha256": report["evaluated_model_sha256"],
        "quality_key": list(quality_key),
        "selected_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json_object_atomic(best_path, record)
    return record


def full_song_evaluation_line(iteration, evaluation):
    """Format an unambiguous original-tempo whole-song metric line."""
    metrics = evaluation.get("metrics", {})
    f1 = float(metrics["strike_f1"])
    precision = float(metrics["precision"])
    recall = float(metrics["release_recall"])
    return (
        f"[strike evaluation] iteration {int(iteration)} | "
        f"full-song-F1={f1:.3f} | precision={precision:.3f} | "
        f"recall={recall:.3f} | tempo=original")


def _add_local_isaacgym_path():
    import os

    isaacgym_root = Path(
        os.environ.get(
            "ISAACGYM_ROOT",
            str(PROJECT_ROOT / "isaacgym"),
        )
    ).expanduser()

    local_python = isaacgym_root / "python"
    package = local_python / "isaacgym" / "__init__.py"

    if package.is_file() and str(local_python) not in sys.path:
        sys.path.insert(0, str(local_python))


def _load_strike_support_runtime():
    _add_local_isaacgym_path()
    import isaacgym
    import torch as torch_module
    return torch_module


def _load_strike_task_runtime():
    from tab2body.env.tasks import StrikeTask as strike_task
    from tab2body.learning.models import ActorCritic as actor_critic
    from tab2body.learning.ppo import (
        PPOConfig as ppo_config,
        PPOTrainer as ppo_trainer,
    )

    return strike_task, actor_critic, ppo_config, ppo_trainer


def build_parser():
    parser = argparse.ArgumentParser(
        description="right-hand virtual-pick strike training")
    parser.add_argument("--goal", default=STRIKE["goal_path"])
    parser.add_argument(
        "--song", default=None,
        help="data/song_bundles 아래의 song_id; 지정하면 해당 strike 입력을 사용")
    parser.add_argument(
        "--grip-reference", default=STRIKE["grip_reference_path"])
    parser.add_argument(
        "--observation-contract",
        choices=(
            STRIKE_V1_OBSERVATION_CONTRACT,
            STRIKE_V2_OBSERVATION_CONTRACT),
        default=STRIKE["observation_contract"],
        help="Strike actor observation ABI; v2 is the 303D block contract")
    parser.add_argument("--num-envs", type=int, default=STRIKE["num_envs"])
    parser.add_argument("--device", default=STRIKE["device"])
    parser.add_argument("--iterations", type=int, default=STRIKE["iterations"])
    parser.add_argument(
        "--minibatch-size", type=int,
        default=STRIKE["ppo"]["minibatch_size"])
    parser.add_argument("--seed", type=int, default=STRIKE["seed"])
    parser.add_argument("--out", default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument(
        "--initialize-from", default=None,
        help=(
            "기존 checkpoint의 actor/log_std/observation normalization만 "
            "가져와 새 adaptive run을 시작"))
    parser.add_argument(
        "--initialize-stage",
        choices=(S2_TIMED_STRUM, S3_SONG_INTEGRATION),
        default=S3_SONG_INTEGRATION,
        help=(
            "--initialize-from 전이의 시작 단계; S2는 명시적인 objective "
            "transfer 승인이 필요"))
    parser.add_argument(
        "--allow-policy-objective-transfer", action="store_true",
        help=(
            "deprecated compatibility flag; --initialize-from already means "
            "actor/observation-normalization-only policy transfer"))
    parser.add_argument(
        "--initialize-tempo", type=float, default=0.0,
        choices=tuple(STRIKE["curriculum"]["tempo_lambdas"]),
        help=(
            "--initialize-from 전이 학습의 시작 tempo lambda; critic과 "
            "optimizer는 새로 시작"))
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--eval-policy-transfer", action="store_true",
                        help="--initialize-from의 actor/관측 정규화만 검증·복사하여 새 환경에서 평가; 학습 없음")
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--eval-seed", type=int, default=EVALUATION_SEED)
    parser.add_argument("--eval-metrics-only", action="store_true",
                        help="--eval 전용: 원곡 전체 반복 평가 사례와 진단을 저장")
    parser.add_argument("--maintenance-lr-scale", type=float, default=1.0,
                        help="커리큘럼 완료 후 학습률 배수 (0 초과 1 이하; 기본은 유지)")
    parser.add_argument("--no-random-start", action="store_true")
    parser.add_argument("--no-curriculum", action="store_true")
    parser.add_argument(
        "--curriculum-stage",
        choices=STRIKE_STAGES,
        default=None)
    parser.add_argument(
        "--timing-tolerance-ms", type=float, default=None,
        help="fixed-stage timing tolerance; A3/S2/S3 only")
    parser.add_argument(
        "--smoke", action="store_true",
        help="8 env × 4 steps × 1 PPO update/checkpoint contract test")
    parser.add_argument(
        "--smoke-video", action="store_true",
        help="--smoke에서도 iteration 1 주기 영상을 실제 생성")
    parser.add_argument("--no-auto-video", action="store_true")
    parser.add_argument(
        "--periodic-video-min-gap", type=int,
        default=STRIKE["periodic_video"][
            "minimum_checkpoint_gap_iterations"],
        help=(
            "마지막 완료 영상 이후 이 iteration 이상 지난 다음 저장 "
            "checkpoint에서 두 카메라 영상을 생성"))
    parser.add_argument("--no-auto-artifacts", action="store_true")
    return parser


def _song_identity(path):
    from tab2body.song_bundles import song_id_from_training_path

    path = Path(path).resolve()
    suffix = ".strike_plan.json"
    song_id = song_id_from_training_path(path, suffix)
    return path, song_id


def training_resource_preflight(torch, device, out_dir, num_envs, smoke=False):
    """Compatibility wrapper around the task-neutral resource guard."""
    from tab2body.learning.run_io import training_resource_preflight as shared

    return shared(
        torch, device, out_dir, num_envs, STRIKE["resource_guard"],
        task_name="strike",
        min_free_vram_gib=1.0 if smoke else None)


def _create_task(StrikeTask, args):
    from tab2body.env.config import configured_kwargs

    return StrikeTask(**configured_kwargs(
        StrikeTask,
        STRIKE,
        goal_path=str(args.goal),
        grip_reference_path=str(args.grip_reference),
        num_envs=args.num_envs,
        device=args.device,
        headless=True,
        seed=args.seed,
        random_start=not args.no_random_start,
        observation_contract=args.observation_contract,
    ))


def _load_checkpoint(torch, path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def evaluate_strike(torch, env, model, episodes, *, metrics_only=False,
                    seed=EVALUATION_SEED):
    """Run deterministic stage-appropriate episodes and return explicit gates."""
    from tab2body.learning.strike_evaluation import (
        strike_evaluation_gate_summary,
    )

    episodes = int(episodes)
    if episodes < 1:
        raise ValueError("evaluation episodes must be positive")
    full_song = _full_song_evaluation_ready(env)
    evaluated_tempo_lambda = float(env.tempo_lambda)
    env.set_evaluation_mode(full_song=full_song, reset=False)
    rows = []
    for case, local, info in fixed_evaluation_cases(
            torch, env, model, episodes, seed=seed):
        row = {key: float(info[key][local].detach().cpu())
               for key in env.episode_metric_keys}
        row.update({key: bool(info[f"episode_{key}"][local].item())
                    for key in env.episode_reason_keys})
        row["case"] = case
        for count_key, samples in (
            ("episode_timing_count", (("episode_timing_abs_ms", "_timing_abs_ms"),
                                      ("episode_timing_signed_ms", "_timing_signed_ms"))),
            ("episode_grip_quality_count", (("episode_grip_quality_samples", "_grip_quality"),)),
            ("episode_strum_microtiming_count", (("episode_strum_timing_rms_ms", "_strum_timing_rms_ms"),
                                                ("episode_strum_duration_error_ms", "_strum_duration_error_ms"))),
        ):
            if count_key in info:
                count = int(info[count_key][local].item())
                for source, target in samples:
                    if source in info:
                        row[target] = info[source][local, :count].detach().cpu().tolist()
        rows.append(row)
    rows.sort(key=lambda row: row["case"]["case_id"])
    event_diagnostics = [
        {"case_id": row["case"]["case_id"],
         "events": row["case"].pop("event_diagnostics", [])}
        for row in rows]
    if len(rows) < episodes:
        raise RuntimeError(
            f"evaluation completed only {len(rows)}/{episodes} episodes")
    episode_aggregate = {
        key: sum(row[key] for row in rows) / len(rows)
        for key in env.episode_metric_keys}
    for count_key, metric_keys in STRIKE_WEIGHTED_METRIC_GROUPS:
        total = sum(float(row[count_key]) for row in rows)
        if total > 0.0:
            for key in metric_keys:
                episode_aggregate[key] = sum(
                    float(row[key]) * float(row[count_key])
                    for row in rows) / total
        episode_aggregate[count_key] = total
    for count_key in STRIKE_RAW_COUNT_METRIC_KEYS:
        if count_key not in rows[0]:
            continue
        episode_aggregate[count_key] = sum(
            float(row[count_key]) for row in rows)
    pool_strike_raw_count_rates(episode_aggregate)
    timing_samples = [
        float(value)
        for row in rows
        for value in row.get("_timing_abs_ms", [])
    ]
    if timing_samples:
        timing_tensor = torch.tensor(timing_samples)
        episode_aggregate["strike_timing_mae_ms"] = float(
            timing_tensor.mean())
        episode_aggregate["strike_timing_p95_ms"] = float(
            torch.quantile(timing_tensor, 0.95))
    signed_timing_samples = [
        float(value)
        for row in rows
        for value in row.get("_timing_signed_ms", [])
    ]
    if signed_timing_samples:
        signed_tensor = torch.tensor(signed_timing_samples)
        episode_aggregate["strike_timing_signed_mean_ms"] = float(
            signed_tensor.mean())
        for label, quantile in (("p10", 0.10), ("p50", 0.50), ("p90", 0.90)):
            episode_aggregate[f"strike_timing_signed_{label}_ms"] = float(
                torch.quantile(signed_tensor, quantile))
    grip_quality_samples = [
        float(value)
        for row in rows
        for value in row.get("_grip_quality", [])
    ]
    if grip_quality_samples:
        grip_tensor = torch.tensor(grip_quality_samples)
        episode_aggregate["strike_grip_quality_mean"] = float(
            grip_tensor.mean())
        episode_aggregate["strike_grip_quality_p05"] = float(
            torch.quantile(grip_tensor, 0.05))
        episode_aggregate["strike_grip_quality_min"] = float(
            grip_tensor.min())
    strum_rms_samples = [
        float(value)
        for row in rows
        for value in row.get("_strum_timing_rms_ms", [])]
    strum_duration_samples = [
        abs(float(value))
        for row in rows
        for value in row.get("_strum_duration_error_ms", [])]
    if strum_rms_samples:
        rms_tensor = torch.tensor(strum_rms_samples)
        duration_tensor = torch.tensor(strum_duration_samples)
        episode_aggregate["strike_strum_timing_rms_ms"] = float(
            rms_tensor.mean())
        episode_aggregate["strike_strum_timing_p95_ms"] = float(
            torch.quantile(rms_tensor, 0.95))
        episode_aggregate["strike_strum_sweep_duration_mae_ms"] = float(
            duration_tensor.mean())
        episode_aggregate["strike_strum_sweep_duration_p95_ms"] = float(
            torch.quantile(duration_tensor, 0.95))
    aggregate = {
        "grip_success_rate":
            episode_aggregate["strike_grip_success_rate"],
        "grip_quality_mean":
            episode_aggregate["strike_grip_quality_mean"],
        "grip_quality_p05":
            episode_aggregate["strike_grip_quality_p05"],
        "grip_quality_min":
            episode_aggregate["strike_grip_quality_min"],
        "pinch_quality_mean": episode_aggregate[
            "strike_grip_pinch_quality_mean"],
        "free_quality_mean": episode_aggregate[
            "strike_grip_free_quality_mean"],
        "grip_bad_frame_rate": episode_aggregate[
            "strike_grip_bad_frame_rate"],
        "grip_bad_streak_max_frames": max(
            row["strike_grip_bad_streak_max_frames"] for row in rows),
        "tip_ready_success_rate":
            episode_aggregate["strike_tip_ready_success_rate"],
        "precision":
            episode_aggregate["strike_precision"],
        "release_recall":
            episode_aggregate["strike_release_recall"],
        "false_positive_rate":
            episode_aggregate["strike_false_positive_rate"],
        "strike_f1": episode_aggregate["strike_episode_f1"],
        "timing_mae_ms":
            episode_aggregate["strike_timing_mae_ms"],
        "timing_p95_ms":
            episode_aggregate["strike_timing_p95_ms"],
        "timing_signed_mean_ms": episode_aggregate[
            "strike_timing_signed_mean_ms"],
        "timing_signed_p10_ms": episode_aggregate[
            "strike_timing_signed_p10_ms"],
        "timing_signed_p50_ms": episode_aggregate[
            "strike_timing_signed_p50_ms"],
        "timing_signed_p90_ms": episode_aggregate[
            "strike_timing_signed_p90_ms"],
        "timing_pass_rate": episode_aggregate[
            "strike_timing_pass_rate"],
        "timing_early_rate": episode_aggregate[
            "strike_timing_early_rate"],
        "timing_late_rate": episode_aggregate[
            "strike_timing_late_rate"],
        "premature_release_rate": episode_aggregate[
            "strike_premature_release_rate"],
        "zone_success_rate":
            episode_aggregate["strike_zone_success_rate"],
        "zone_mean_quality":
            episode_aggregate["strike_zone_mean_quality"],
        "raw_zone_success_rate": episode_aggregate[
            "strike_raw_zone_success_rate"],
        "raw_zone_mean_quality": episode_aggregate[
            "strike_raw_zone_mean_quality"],
        "curriculum_success_rate":
            episode_aggregate["curriculum_success_rate"],
        "single_precision": episode_aggregate["strike_single_precision"],
        "single_recall": episode_aggregate["strike_single_recall"],
        "single_f1": episode_aggregate["strike_single_f1"],
        "single_event_count": episode_aggregate["strike_single_event_count"],
        "strum_completion_rate": episode_aggregate[
            "strike_strum_completion_rate"],
        "strum_traversal_recall": episode_aggregate[
            "strike_strum_traversal_recall"],
        "strum_order_accuracy": episode_aggregate[
            "strike_strum_order_accuracy"],
        "strum_direction_accuracy": episode_aggregate[
            "strike_strum_direction_accuracy"],
        "strum_unplanned_crossing_rate": episode_aggregate[
            "strike_strum_unplanned_crossing_rate"],
        "strum_duplicate_crossing_rate": episode_aggregate[
            "strike_strum_duplicate_crossing_rate"],
        "strum_event_count": episode_aggregate["strike_strum_event_count"],
        "strum_timing_rms_ms": episode_aggregate[
            "strike_strum_timing_rms_ms"],
        "strum_timing_p95_ms": episode_aggregate[
            "strike_strum_timing_p95_ms"],
        "strum_sweep_duration_mae_ms": episode_aggregate[
            "strike_strum_sweep_duration_mae_ms"],
        "strum_sweep_duration_p95_ms": episode_aggregate[
            "strike_strum_sweep_duration_p95_ms"],
        "strum_microtiming_sample_count": episode_aggregate[
            "strike_strum_microtiming_sample_count"],
        # S2/S3 use the event-latched scheduled recovery contract.  The
        # legacy fixed-frame diagnostic can pulse again during long recovery
        # and is intentionally not a bounded completion rate for these stages.
        "recovery_completion_rate": episode_aggregate[
            "strike_conditional_recovery_completion_rate"
            if env.curriculum_stage in (
                "S2_TIMED_STRUM", "S3_SONG_INTEGRATION")
            else "strike_recovery_completion_rate"],
        "scheduled_recovery_completion_rate": episode_aggregate[
            "strike_scheduled_recovery_completion_rate"],
        "conditional_recovery_completion_rate": episode_aggregate[
            "strike_conditional_recovery_completion_rate"],
        "end_to_end_recovery_completion_rate": episode_aggregate[
            "strike_end_to_end_recovery_completion_rate"],
        "full_recovery_completion_rate": episode_aggregate[
            "strike_full_recovery_completion_rate"],
        "full_recovery_event_count": episode_aggregate[
            "strike_full_recovery_event_count"],
        "handoff_recovery_completion_rate": episode_aggregate[
            "strike_handoff_recovery_completion_rate"],
        "handoff_recovery_event_count": episode_aggregate[
            "strike_handoff_recovery_event_count"],
        "handoff_required_frames_mean": episode_aggregate[
            "strike_handoff_required_frames_mean"],
        "recovery_event_count": episode_aggregate[
            "strike_recovery_event_count"],
        "recovery_reset_count": episode_aggregate[
            "strike_recovery_reset_count"],
        "recovery_reset_rate": episode_aggregate[
            "strike_recovery_reset_rate"],
        "blocked_crossing_count": episode_aggregate[
            "strike_blocked_crossing_count"],
        "blocked_crossing_rate": episode_aggregate[
            "strike_blocked_crossing_rate"],
        "down_completion_rate": episode_aggregate[
            "strike_down_completion_rate"],
        "down_event_count": episode_aggregate["strike_down_event_count"],
        "down_completed_count": episode_aggregate[
            "strike_down_completed_count"],
        "up_completion_rate": episode_aggregate[
            "strike_up_completion_rate"],
        "up_event_count": episode_aggregate["strike_up_event_count"],
        "up_completed_count": episode_aggregate[
            "strike_up_completed_count"],
        "worst_direction_completion_rate": episode_aggregate[
            "strike_worst_direction_completion_rate"],
        "final_string_miss_count": episode_aggregate[
            "strike_final_string_miss_count"],
        "final_remaining_count_at_resolution": episode_aggregate[
            "strike_final_remaining_count_at_resolution"],
        "strum_exit_distance_mean_m": episode_aggregate[
            "strike_strum_exit_distance_mean_m"],
        "reward_timing_return": episode_aggregate[
            "strike_reward_timing_return"],
        "reward_timing_wait_return": episode_aggregate[
            "strike_reward_timing_wait_return"],
        "reward_strum_progress_return": episode_aggregate[
            "strike_reward_strum_progress_return"],
        "reward_strum_terminal_progress_return": episode_aggregate[
            "strike_reward_strum_terminal_progress_return"],
        "reward_strum_physical_completion_return": episode_aggregate[
            "strike_reward_strum_physical_completion_return"],
        "penalty_premature_release_return": episode_aggregate[
            "strike_penalty_premature_release_return"],
        "penalty_early_timing_return": episode_aggregate[
            "strike_penalty_early_timing_return"],
        "penalty_miss_return": episode_aggregate[
            "strike_penalty_miss_return"],
    }
    safety_passed = all(
        not row["failure_termination"] for row in rows)
    gates_cfg = STRIKE["evaluation"]
    gate_timing_tolerance_ms = env.timing_tolerance_ms
    s2_profile = None
    if env.curriculum_stage == "S2_TIMED_STRUM":
        s2_profile = next(
            profile for profile in env.curriculum_s2_profiles
            if profile["name"] == env.s2_profile_name)
    if env.curriculum_stage == "S3_SONG_INTEGRATION":
        gate_timing_tolerance_ms = min(
            gate_timing_tolerance_ms,
            float(gates_cfg["timing_p95_ms"]))
    timing_center_profile = s2_profile
    if env.curriculum_stage == "S3_SONG_INTEGRATION":
        timing_center_profile = env.curriculum_s2_profiles[-1]
    endpoint_bridge = bool(
        env.curriculum_stage == S2_TIMED_STRUM
        and s2_profile is not None
        and s2_profile["name"]
        == env.curriculum_s2_profiles[0]["name"])
    if metrics_only:
        # Periodic whole-song reporting must not lose TP/FP/FN-derived F1
        # because an unrelated diagnostic rate fails final gate validation.
        # The regular final evaluation still performs every strict gate.
        invalid_rates = {
            key: float(value)
            for key, value in aggregate.items()
            if key.endswith("_rate")
            and isinstance(value, (int, float))
            and (not math.isfinite(float(value))
                 or float(value) > 1.0 + 1e-6
                 or (float(value) < 0.0 and float(value) != -1.0))
        }
        return {
            "schema": "tab2body.strike_full_song_metrics.v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "stage": env.curriculum_stage,
            "evaluation_scope": (
                "full_song_original_tempo"
                if full_song else "training_phrase_current_tempo"),
            "tempo_lambda": evaluated_tempo_lambda,
            "timing_tolerance_ms": float(env.timing_tolerance_ms),
            "episodes": len(rows),
            "metrics": aggregate,
            "raw_counts": {key: episode_aggregate[key]
                           for key in STRIKE_RAW_COUNT_METRIC_KEYS
                           if key in episode_aggregate},
            "case_summary": repeated_case_summary(rows),
            "quality_eligibility": {
                "safety_passed": safety_passed,
                "grip_passed": (
                    aggregate["grip_success_rate"] >= STRIKE["curriculum"]["grip_success_rate"]
                    and all(aggregate[key] >= gates_cfg[key] for key in (
                        "grip_quality_mean", "grip_quality_p05",
                        "pinch_quality_mean", "free_quality_mean"))
                    and aggregate["grip_bad_frame_rate"] <= gates_cfg["max_grip_bad_frame_rate"]
                    and aggregate["grip_bad_streak_max_frames"] <= gates_cfg["max_grip_bad_streak_frames"]),
            },
            "cases": rows,
            "case_protocol": {"version": 1, "seed": int(seed),
                              "num_envs": env.num_envs,
                              "episodes": episodes,
                              "selection": "fixed_ids_first_episode_per_reset_cohort"},
            "event_diagnostics": event_diagnostics,
            "strict_gate_evaluated": False,
            "invalid_diagnostic_rates": invalid_rates,
        }
    gates = strike_evaluation_gate_summary(
        aggregate,
        rows,
        stage=env.curriculum_stage,
        timing_tolerance_ms=gate_timing_tolerance_ms,
        safety_passed=safety_passed,
        grip_success_gate=STRIKE["curriculum"]["grip_success_rate"],
        grip_quality_mean_gate=gates_cfg["grip_quality_mean"],
        grip_quality_p05_gate=gates_cfg["grip_quality_p05"],
        pinch_quality_mean_gate=gates_cfg["pinch_quality_mean"],
        free_quality_mean_gate=gates_cfg["free_quality_mean"],
        max_grip_bad_frame_rate=gates_cfg["max_grip_bad_frame_rate"],
        max_grip_bad_streak_frames=gates_cfg[
            "max_grip_bad_streak_frames"],
        tip_ready_success_gate=STRIKE["curriculum"]["ready_success_rate"],
        precision_gate=gates_cfg["precision"],
        release_recall_gate=gates_cfg["recall"],
        false_positive_rate_gate=gates_cfg["max_wrong_rate"],
        strike_f1_gate=gates_cfg["f1"],
        zone_success_gate=(
            float(s2_profile["zone_success_rate"])
            if s2_profile is not None and env.zone_gate_active
            else gates_cfg["zone_success_rate"]),
        strum_completion_gate=(
            float(s2_profile["completion_rate"])
            if s2_profile is not None
            else gates_cfg["strum_completion_rate"]),
        strum_traversal_recall_gate=gates_cfg["strum_traversal_recall"],
        strum_order_accuracy_gate=gates_cfg["strum_order_accuracy"],
        strum_direction_accuracy_gate=gates_cfg["strum_direction_accuracy"],
        worst_direction_completion_gate=(
            float(s2_profile["worst_direction_completion_rate"])
            if s2_profile is not None else None),
        strum_max_unplanned_rate=gates_cfg["strum_max_unplanned_rate"],
        recovery_completion_gate=gates_cfg["recovery_completion_rate"],
        end_to_end_recovery_completion_gate=(
            float(timing_center_profile["end_to_end_recovery_rate"])
            if timing_center_profile is not None else None),
        full_recovery_completion_gate=gates_cfg[
            "full_recovery_completion_rate"],
        handoff_recovery_completion_gate=gates_cfg[
            "handoff_recovery_completion_rate"],
        max_recovery_reset_count=gates_cfg["max_recovery_reset_count"],
        max_blocked_crossing_count=gates_cfg[
            "max_blocked_crossing_count"],
        strum_timing_rms_gate_ms=(
            float(s2_profile["timing_rms_ms"])
            if s2_profile is not None
            else gates_cfg["strum_timing_rms_ms"]),
        strum_duration_mae_gate_ms=(
            float(s2_profile["duration_mae_ms"])
            if s2_profile is not None
            else gates_cfg["strum_sweep_duration_mae_ms"]),
        timing_pass_rate_gate=(
            float(s2_profile["timing_pass_rate"])
            if s2_profile is not None else None),
        timing_center_mean_abs_gate_ms=(
            float(timing_center_profile["timing_center_mean_abs_ms"])
            if timing_center_profile is not None else None),
        timing_center_tail_abs_gate_ms=(
            float(timing_center_profile["timing_center_tail_abs_ms"])
            if timing_center_profile is not None else None),
        zone_applicable=(
            bool(env.zone_gate_active)
            if s2_profile is not None else None),
        timing_applicable=(False if endpoint_bridge else None),
        strum_applicable=(
            env.song_has_strum
            if env.curriculum_stage == S3_SONG_INTEGRATION else None),
        strum_microtiming_applicable=(
            False if endpoint_bridge else None),
    )
    return {
        "schema": "tab2body.strike_evaluation.v9",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": env.curriculum_stage,
        "s2_profile": getattr(env, "s2_profile_name", None),
        "s2_zone_gate_active": bool(getattr(
            env, "zone_gate_active", False)),
        "song_has_strum": bool(env.song_has_strum),
        "evaluation_scope": (
            "full_song_original_tempo"
            if full_song else "training_phrase_current_tempo"),
        "tempo_lambda": evaluated_tempo_lambda,
        "timing_tolerance_ms": env.timing_tolerance_ms,
        "evaluation_gate_timing_p95_ms": gate_timing_tolerance_ms,
        "direction_profile": env.direction_profile,
        "episodes": len(rows),
        "timing_sample_count": len(timing_samples),
        "strum_microtiming_sample_count": len(strum_rms_samples),
        "metrics": aggregate,
        "gates": gates,
        "episode_rows": rows,
    }


def _write_run_metadata(
        layout, contract, args, resources, goal_validation,
        policy_transfer_spec=None):
    tooling_fingerprint = fingerprint_file_set(
        PACKAGE_ROOT, STRIKE_TOOLING_PROVENANCE_FILES)
    manifest = {
        "schema": "tab2body.strike_run.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "strike",
        "goal": str(args.goal),
        "goal_sha256": file_sha256(args.goal),
        "grip_reference": str(args.grip_reference),
        "grip_reference_sha256": file_sha256(args.grip_reference),
        "checkpoint_contract_schema": contract["payload"]["schema"],
        "checkpoint_contract_sha256": contract["sha256"],
        "direction_profile": goal_validation.get(
            "direction_profile", "phrase_dp_microtiming_v3"),
        "transition_profile": goal_validation.get(
            "transition_profile", "entry_side_edge_gap_v2"),
        "goal_compilation": dict(goal_validation),
        "resources_at_start": resources,
        "provenance": {
            "tooling_fingerprint": tooling_fingerprint,
        },
        "policy_initialization": (
            {
                "checkpoint": str(Path(args.initialize_from).resolve()),
                "checkpoint_sha256": file_sha256(args.initialize_from),
                "restored": ["actor", "log_std", "observation_normalization"],
                "reset": ["critic", "optimizer", "iteration", "curriculum"],
                "initial_stage": str(args.initialize_stage),
                "objective_transfer_allowed": bool(
                    args.allow_policy_objective_transfer),
                "initial_tempo_lambda": (
                    float(args.initialize_tempo)
                    if args.initialize_stage == S3_SONG_INTEGRATION
                    else None),
                "transfer_audit": (
                    None if policy_transfer_spec is None
                    else dict(policy_transfer_spec)),
            }
            if args.initialize_from else None),
        "artifacts": {},
    }
    record_run_metadata(
        layout,
        manifest,
        {
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "evaluation" if args.eval else "training",
            "iterations": args.iterations,
            "checkpoint": args.checkpoint,
            "initialize_from": args.initialize_from,
            "initialize_stage": (
                str(args.initialize_stage) if args.initialize_from else None),
            "allow_policy_objective_transfer": bool(
                args.allow_policy_objective_transfer),
            "initialize_tempo_lambda": (
                float(args.initialize_tempo)
                if (args.initialize_from
                    and args.initialize_stage == S3_SONG_INTEGRATION)
                else None),
            "periodic_video_min_gap_iterations": (
                args.periodic_video_min_gap),
            "automatic_video_enabled": not args.no_auto_video,
            "tooling_fingerprint": tooling_fingerprint,
        },
    )


def _write_analysis(layout, checkpoint, evaluation, last_stats=None):
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    lines = [
        "# Strike 학습 자동 분석",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- 평가 단계: `{evaluation['stage']}`",
        f"- 평가 범위: `{evaluation['evaluation_scope']}`",
        f"- tempo lambda: `{evaluation['tempo_lambda']:.2f}`",
        f"- 시간 허용 오차: `{evaluation['timing_tolerance_ms']:.0f} ms`",
        f"- 평가 episode: `{evaluation['episodes']}`",
        f"- 단계 목표 통과: `{'PASS' if gates['task_passed'] else 'NOT YET'}`",
        f"- 안전 gate 통과: `{'PASS' if gates['safety_passed'] else 'FAIL'}`",
        "",
        "## 핵심 지표",
        "",
        f"- grip success: `{metrics['grip_success_rate']:.3f}`",
        f"- grip quality mean/p05/min: "
        f"`{metrics['grip_quality_mean']:.3f} / "
        f"{metrics['grip_quality_p05']:.3f} / "
        f"{metrics['grip_quality_min']:.3f}`",
        f"- pinch/free quality mean: "
        f"`{metrics['pinch_quality_mean']:.3f} / "
        f"{metrics['free_quality_mean']:.3f}`",
        f"- grip bad frame rate/max streak: "
        f"`{metrics['grip_bad_frame_rate']:.3f} / "
        f"{metrics['grip_bad_streak_max_frames']:.0f} frames`",
        f"- ready success: `{metrics['tip_ready_success_rate']:.3f}`",
        f"- precision: `{metrics['precision']:.3f}`",
        f"- release recall: `{metrics['release_recall']:.3f}`",
        f"- false positive rate: `{metrics['false_positive_rate']:.3f}`",
        f"- strike F1: `{metrics['strike_f1']:.3f}`",
        f"- timing p95: `{metrics['timing_p95_ms']:.2f} ms`",
        f"- timing signed mean/p10/p50/p90: "
        f"`{metrics['timing_signed_mean_ms']:.2f} / "
        f"{metrics['timing_signed_p10_ms']:.2f} / "
        f"{metrics['timing_signed_p50_ms']:.2f} / "
        f"{metrics['timing_signed_p90_ms']:.2f} ms`",
        f"- timing pass/early/late/premature: "
        f"`{metrics['timing_pass_rate']:.3f} / "
        f"{metrics['timing_early_rate']:.3f} / "
        f"{metrics['timing_late_rate']:.3f} / "
        f"{metrics['premature_release_rate']:.3f}`",
        f"- zone success: `{metrics['zone_success_rate']:.3f}`",
        f"- raw zone success/quality: "
        f"`{metrics['raw_zone_success_rate']:.3f} / "
        f"{metrics['raw_zone_mean_quality']:.3f}`",
        f"- single F1: `{metrics['single_f1']:.3f}`",
        f"- strum events: `{metrics['strum_event_count']:.1f}`",
        f"- strum completion: `{metrics['strum_completion_rate']:.3f}`",
        f"- strum traversal recall: `{metrics['strum_traversal_recall']:.3f}`",
        f"- strum order accuracy: `{metrics['strum_order_accuracy']:.3f}`",
        f"- strum direction accuracy: `{metrics['strum_direction_accuracy']:.3f}`",
        f"- strum timing RMS: `{metrics['strum_timing_rms_ms']:.2f} ms`",
        f"- strum sweep duration MAE: "
        f"`{metrics['strum_sweep_duration_mae_ms']:.2f} ms`",
        f"- fixed full recovery diagnostic: "
        f"`{metrics['recovery_completion_rate']:.3f}`",
        f"- scheduled recovery: "
        f"`{metrics['scheduled_recovery_completion_rate']:.3f}`",
        f"- conditional/end-to-end recovery: "
        f"`{metrics['conditional_recovery_completion_rate']:.3f} / "
        f"{metrics['end_to_end_recovery_completion_rate']:.3f}`",
        f"- full recovery: `{metrics['full_recovery_completion_rate']:.3f}` "
        f"({metrics['full_recovery_event_count']:.0f} events)",
        f"- handoff recovery: "
        f"`{metrics['handoff_recovery_completion_rate']:.3f}` "
        f"({metrics['handoff_recovery_event_count']:.0f} events, "
        f"mean {metrics['handoff_required_frames_mean']:.2f} frames)",
        f"- recovery resets: `{metrics['recovery_reset_count']:.0f}` "
        f"(rate `{metrics['recovery_reset_rate']:.3f}`)",
        f"- blocked-before-rearm crossings: "
        f"`{metrics['blocked_crossing_count']:.0f}` "
        f"(rate `{metrics['blocked_crossing_rate']:.3f}`)",
        f"- down completion: `{metrics['down_completion_rate']:.3f}` "
        f"({metrics['down_event_count']:.0f} events)",
        f"- up completion: `{metrics['up_completion_rate']:.3f}` "
        f"({metrics['up_event_count']:.0f} events)",
        f"- worst-direction completion: "
        f"`{metrics['worst_direction_completion_rate']:.3f}`",
        f"- final-string misses/remaining: "
        f"`{metrics['final_string_miss_count']:.0f} / "
        f"{metrics['final_remaining_count_at_resolution']:.0f}`",
        f"- strum exit distance mean: "
        f"`{1000.0 * metrics['strum_exit_distance_mean_m']:.2f} mm`",
        f"- timing/wait/progress reward return: "
        f"`{metrics['reward_timing_return']:.4f} / "
        f"{metrics['reward_timing_wait_return']:.4f} / "
        f"{metrics['reward_strum_progress_return']:.4f}`",
        f"- terminal-progress/physical-completion reward return: "
        f"`{metrics['reward_strum_terminal_progress_return']:.4f} / "
        f"{metrics['reward_strum_physical_completion_return']:.4f}`",
        f"- premature/early-center/miss penalty return: "
        f"`{metrics['penalty_premature_release_return']:.4f} / "
        f"{metrics['penalty_early_timing_return']:.4f} / "
        f"{metrics['penalty_miss_return']:.4f}`",
        "",
        "## 해석",
        "",
        "- 수치 gate와 별개로 remembered/current 두 영상을 사람이 확인해야 합니다.",
        "- 다음 단계 승급은 최소 학습량과 연속 성능 gate를 모두 만족할 때만 일어납니다.",
    ]
    if last_stats:
        lines += [
            "",
            "## 마지막 학습 iteration",
            "",
            f"- iteration: `{int(last_stats.get('iteration', 0))}`",
            f"- mean reward: `{float(last_stats.get('reward', 0.0)):.5f}`",
            f"- curriculum stage: `{last_stats.get('curriculum_stage', 'unknown')}`",
            f"- S2 profile: "
            f"`{last_stats.get('curriculum_s2_profile_name', 'n/a')}`",
            f"- reward alignment warning: "
            f"`{bool(last_stats.get('reward_alignment_warning', False))}`",
        ]
    target = layout.root / "ANALYSIS.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _run_logged_tool(layout, command, expected):
    with layout.artifact_log.open("a", encoding="utf-8") as stream:
        subprocess.run(
            command, check=True, stdout=stream, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
    missing = [str(path) for path in expected.values() if not path.is_file()]
    if missing:
        raise RuntimeError(
            "strike artifact tool completed without expected outputs: "
            + ", ".join(missing))
    return expected


def _run_plot(layout):
    target = layout.plots / "strike_training_curves.png"
    command = [
        sys.executable, "-m", "tab2body.tools.plot_strike_training",
        str(layout.metrics),
        "--out", str(target),
    ]
    return _run_logged_tool(
        layout, command, {"training_plot": target})["training_plot"]


def _run_motion_audit(layout, checkpoint, goal, grip, device):
    target = (
        layout.evaluations
        / f"{Path(checkpoint).stem}.motion_diagnostics.json")
    command = [
        sys.executable, "-m", "tab2body.tools.audit_strike_motion",
        "--checkpoint", str(checkpoint),
        "--goal", str(goal),
        "--grip-reference", str(grip),
        "--device", str(device),
        "--out", str(target),
    ]
    return _run_logged_tool(
        layout, command,
        {"motion_diagnostics": target})["motion_diagnostics"]


def _run_videos(layout, checkpoint, goal, grip, device):
    existing = strike_rollout_artifact_paths(checkpoint)
    if strike_rollout_is_complete(checkpoint):
        return existing
    outputs = {
        key: existing[key]
        for key in ("remembered", "current")
    }
    report = existing["report"]
    command = [
        sys.executable, "-m", "tab2body.tools.record_strike_rollout",
        "--checkpoint", str(checkpoint),
        "--goal", str(goal),
        "--grip-reference", str(grip),
        "--device", str(device),
        "--out-remembered", str(outputs["remembered"]),
        "--out-current", str(outputs["current"]),
    ]
    artifacts = {**outputs, "report": report}
    return _run_logged_tool(layout, command, artifacts)


def _append_periodic_video_event(layout, row):
    target = layout.logs / "periodic_videos.jsonl"
    append_jsonl_atomic(target, row)
    return target


def _attempt_artifact(
        layout, name, producer, artifact_errors, resolved_errors=()):
    try:
        produced = {
            key: str(Path(path).resolve())
            for key, path in producer().items()
        }
        record_artifact_result(
            layout, produced, resolved_errors=resolved_errors)
        return produced
    except Exception as exc:
        artifact_errors[name] = exc
        record_artifact_error(layout, name, exc)
        return {}


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.song:
        from tab2body.song_bundles import strike_goal_path

        if args.goal != STRIKE["goal_path"]:
            raise SystemExit("--song and --goal cannot be used together")
        args.goal = str(strike_goal_path(args.song))
    if args.eval_policy_transfer:
        if args.eval or args.checkpoint or not args.initialize_from:
            raise SystemExit("--eval-policy-transfer requires --initialize-from only")
        if not args.out or Path(args.out).exists():
            raise SystemExit("--eval-policy-transfer requires a new --out directory")
        source_run = Path(args.initialize_from).resolve().parent
        while source_run.name in ("checkpoints", "evaluations"):
            source_run = source_run.parent
        evaluation_out = Path(args.out).resolve()
        if evaluation_out == source_run or source_run in evaluation_out.parents:
            raise SystemExit("evaluation output must be outside the source run")
        if args.initialize_stage != S3_SONG_INTEGRATION:
            raise SystemExit("--eval-policy-transfer requires S3 initialization")
        args.eval = True
        args.eval_metrics_only = True
        args.no_auto_video = True
        args.no_auto_artifacts = True
    if args.eval and not args.checkpoint and not args.eval_policy_transfer:
        raise SystemExit("--eval requires --checkpoint")
    if args.initialize_from and (args.checkpoint or (args.eval and not args.eval_policy_transfer)):
        raise SystemExit(
            "--initialize-from cannot be combined with --checkpoint or --eval")
    if args.initialize_from and (
            args.no_curriculum or args.curriculum_stage is not None
            or args.timing_tolerance_ms is not None):
        raise SystemExit(
            "--initialize-from starts an adaptive curriculum; fixed-stage "
            "options cannot be combined")
    if args.allow_policy_objective_transfer and not args.initialize_from:
        raise SystemExit(
            "--allow-policy-objective-transfer requires --initialize-from")
    # ``--initialize-from`` is already an explicit request for policy-only
    # transfer.  Requiring a second acknowledgement made the safe path harder
    # to use without adding protection: strict actor ABI verification below is
    # still mandatory and optimizer/critic/environment state are still reset.
    if args.initialize_from:
        args.allow_policy_objective_transfer = True
    if args.smoke_video and not args.smoke:
        raise SystemExit("--smoke-video requires --smoke")
    if args.iterations < 1 and not args.eval:
        raise SystemExit("--iterations must be positive")
    if args.eval_episodes < 1:
        raise SystemExit("--eval-episodes must be positive")
    if args.eval_seed < 0:
        raise SystemExit("--eval-seed must be nonnegative")
    if args.eval_metrics_only and not args.eval:
        raise SystemExit("--eval-metrics-only requires --eval")
    if not 0.0 < args.maintenance_lr_scale <= 1.0:
        raise SystemExit("--maintenance-lr-scale must be in (0, 1]")
    if args.periodic_video_min_gap < 1:
        raise SystemExit("--periodic-video-min-gap must be positive")
    args.goal, song_id = _song_identity(args.goal)
    args.grip_reference = Path(args.grip_reference).resolve()
    if not args.goal.is_file():
        raise FileNotFoundError(f"strike goal not found: {args.goal}")
    if not args.grip_reference.is_file():
        raise FileNotFoundError(
            f"pick-grip reference not found: {args.grip_reference}")
    if args.checkpoint:
        args.checkpoint = str(Path(args.checkpoint).resolve())
    if args.initialize_from:
        args.initialize_from = str(Path(args.initialize_from).resolve())
    torch = _load_strike_support_runtime()
    fixed_stage = args.curriculum_stage
    if args.no_curriculum and fixed_stage is None:
        fixed_stage = "A0_PICK_GRIP"
    goal_validation = validate_strike_goal_for_training(
        args.goal,
        STRIKE,
        require_song=(
            fixed_stage == "S3_SONG_INTEGRATION"
            or (not args.eval and fixed_stage is None)))
    out_dir = resolve_run_dir(
        PROJECT_ROOT, song_id, explicit=args.out,
        run_name=args.run_name, checkpoint=args.checkpoint,
        task_name="strike")
    layout = layout_for(out_dir, create=False)
    if (not args.checkpoint and not args.eval
            and has_training_history(layout, task_name="strike")):
        raise FileExistsError(
            f"strike run already exists at {layout.root}; use --checkpoint "
            "or choose another --run-name")
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    if args.smoke:
        args.num_envs = min(args.num_envs, 8)
        args.iterations = 1
        args.eval_episodes = min(args.eval_episodes, args.num_envs)
        if not args.smoke_video:
            args.no_auto_video = True
    resources = training_resource_preflight(
        torch, args.device, layout.root, args.num_envs, smoke=args.smoke)
    layout = layout_for(out_dir, create=True)
    writer_lease = None
    if not args.eval:
        writer_lease = acquire_run_writer(layout)
        try:
            validate_jsonl(layout.metrics)
        except Exception:
            writer_lease.close()
            raise
    try:
        StrikeTask, ActorCritic, PPOConfig, PPOTrainer = (
            _load_strike_task_runtime())
        env = _create_task(StrikeTask, args)
    except Exception:
        if writer_lease is not None:
            writer_lease.close()
        raise
    last_stats = {"value": None}
    evaluation = None
    checkpoint_path = None
    artifacts = {}
    interruption_artifact = None
    try:
        checkpoint = (
            _load_checkpoint(torch, args.checkpoint, args.device)
            if args.checkpoint else None)
        initialization_checkpoint = (
            _load_checkpoint(torch, args.initialize_from, args.device)
            if args.initialize_from else None)
        policy_transfer_spec = None
        policy_init_std = float(STRIKE["policy_init_std"])
        saved_eval_ppo = None
        if args.eval and not args.eval_policy_transfer:
            policy_init_std, saved_eval_ppo = (
                checkpoint_evaluation_hyperparameters(checkpoint))
        ModelType = ActorCritic
        if env.observation_contract == STRIKE_V2_OBSERVATION_CONTRACT:
            from tab2body.learning.strike_v2_model import (
                strike_actor_critic_class,
            )
            ModelType = strike_actor_critic_class(env.observation_contract)
        model = ModelType(
            env.num_obs,
            env.num_actions,
            value_dim=env.value_dim,
            init_std=policy_init_std,
            init_mean=env.policy_neutral_action[0],
        ).to(args.device)
        ppo_values = dict(STRIKE["ppo"])
        ppo_values["minibatch_size"] = args.minibatch_size
        ppo_values["completed_strike_lr_multiplier"] = args.maintenance_lr_scale
        if saved_eval_ppo is not None:
            ppo_values = saved_eval_ppo
        elif args.smoke:
            ppo_values.update(
                horizon=4, epochs=1, minibatch_size=32,
                save_interval=1, log_interval=1)
        ppo_config = PPOConfig(**ppo_values)
        validate_strike_training_alignment(env, ppo_config)
        trainer = PPOTrainer(env, model, ppo_config, out_dir=layout.root)
        contract_config = deepcopy(STRIKE)
        contract_config["observation_contract"] = args.observation_contract
        contract_config["grip_reference_path"] = str(args.grip_reference)
        checkpoint_contract = build_runtime_checkpoint_contract(
            env, model, args.goal, config=contract_config,
            ppo_config=vars(ppo_config))
        trainer.set_checkpoint_contract(checkpoint_contract)

        curriculum = build_strike_curriculum(
            STRIKE,
            args.num_envs,
            song_has_strum=bool(goal_validation["song_has_strum"]))
        curriculum_runtime = StrikeCurriculumRuntime(
            curriculum,
            fixed_stage=fixed_stage,
            tolerance_ms=args.timing_tolerance_ms)

        if checkpoint is not None:
            curriculum_runtime.restore(
                checkpoint.get("training_context", {}))
            trainer.resume(
                checkpoint, purpose="evaluate" if args.eval else "resume")
        elif initialization_checkpoint is not None:
            if args.initialize_stage == S2_TIMED_STRUM:
                policy_transfer_spec = strike_s2_policy_transfer_spec(
                    initialization_checkpoint, checkpoint_contract)
            else:
                verify_strike_policy_initialization_contract(
                    initialization_checkpoint, checkpoint_contract)
            initialized_tensors = trainer.initialize_policy(
                initialization_checkpoint)
            if (policy_transfer_spec is not None
                    and tuple(initialized_tensors) != tuple(
                        policy_transfer_spec["copied_model_tensors"])):
                raise RuntimeError(
                    "validated S2 policy-transfer tensor set does not match "
                    "the tensors copied by PPOTrainer")
            if args.initialize_stage == S2_TIMED_STRUM:
                curriculum.initialize_timed_strum_transfer()
            else:
                curriculum.initialize_song_integration_transfer(
                    args.initialize_tempo)
            transfer_context = {
                "policy_initialized_from": args.initialize_from,
                "policy_initialized_from_iteration": int(
                    initialization_checkpoint.get("iteration", 0)),
                "policy_initialized_tensor_count": len(initialized_tensors),
                "policy_transfer_reset_critic": True,
                "policy_transfer_reset_optimizer": True,
                "policy_transfer_reset_environment_state": True,
                "policy_transfer_initial_stage": args.initialize_stage,
                "policy_transfer_reset_curriculum_to_s2": (
                    args.initialize_stage == S2_TIMED_STRUM),
                "policy_transfer_reset_curriculum_to_s3": (
                    args.initialize_stage == S3_SONG_INTEGRATION),
                "policy_transfer_initial_tempo_lambda": (
                    float(args.initialize_tempo)
                    if args.initialize_stage == S3_SONG_INTEGRATION
                    else None),
            }
            if policy_transfer_spec is not None:
                transfer_context["policy_transfer_audit"] = dict(
                    policy_transfer_spec)
            trainer.training_context.update(transfer_context)
        initial_state, reset_obs = curriculum_runtime.apply(env)
        if reset_obs is not None:
            trainer.obs = reset_obs
        trainer.training_context.update(initial_state)
        _write_run_metadata(
            layout, checkpoint_contract, args, resources,
            goal_validation, policy_transfer_spec=policy_transfer_spec)

        video_schedule = PeriodicCheckpointVideoSchedule.from_layout(
            layout, args.periodic_video_min_gap)
        live_video_recorder = {"value": None}

        def get_live_video_recorder():
            if live_video_recorder["value"] is None:
                from isaacgym import gymapi
                from tab2body.tools.record_strike_rollout import (
                    LiveStrikeRolloutRecorder,
                )

                video_config = STRIKE["periodic_video"]
                live_video_recorder["value"] = LiveStrikeRolloutRecorder(
                    gymapi,
                    env,
                    fps=int(video_config["fps"]),
                    width=int(video_config["width"]),
                    height=int(video_config["height"]),
                )
            return live_video_recorder["value"]

        def evaluate_s3_full_song_metrics(iteration):
            """Evaluate the complete original-tempo song without video."""
            if env.curriculum_stage != "S3_SONG_INTEGRATION":
                return None
            runtime_state = _strike_runtime_state(env)
            wrong_termination = bool(
                env.wrong_crossing_termination_enabled)
            failure_mining_updates = bool(
                env.failure_mining_updates_enabled)
            try:
                env.wrong_crossing_termination_enabled = False
                env.failure_mining_updates_enabled = False
                env.set_evaluation_mode(True, reset=False)
                evaluation = evaluate_strike(
                    torch,
                    env,
                    model,
                    int(STRIKE["evaluation"]["full_song_episodes"]),
                    metrics_only=True,
                )
            finally:
                env.wrong_crossing_termination_enabled = wrong_termination
                env.failure_mining_updates_enabled = failure_mining_updates
                trainer.obs = _restore_strike_runtime(env, runtime_state)
            report = {
                **evaluation,
                "iteration": int(iteration),
                "evaluation_contract_sha256": checkpoint_contract["sha256"],
                "goal_sha256": file_sha256(args.goal),
                "timing_tolerance_ms": float(evaluation.get(
                    "timing_tolerance_ms", env.timing_tolerance_ms)),
                "evaluation_scope": "full_song_original_tempo",
                "wrong_crossing_termination_suppressed": wrong_termination,
                "training_runtime_restored_after_evaluation": True,
            }
            target = layout.evaluations / (
                f"strike_{int(iteration):06d}.full_song.eval.json")
            curriculum_runtime.record_original_tempo_evaluation(
                iteration, report["metrics"],
                case_summary=report.get("case_summary"),
                case_protocol=report.get("case_protocol"))
            trainer.training_context.update(curriculum.state())
            trainer.training_context["original_tempo_evaluated_iteration"] = int(iteration)
            trainer.save(iteration)
            checkpoint = layout.checkpoints / f"strike_{int(iteration):06d}.pt"
            report.update({
                "checkpoint": str(checkpoint.relative_to(layout.root)),
                "checkpoint_sha256": file_sha256(checkpoint),
                "checkpoint_sha256_scope": "at_evaluation_regular_checkpoint_may_be_resaved",
                "evaluated_model_sha256": model_tensor_sha256(model),
                "path_base": "run_root",
                "original_tempo_evaluated_iteration": int(iteration),
            })
            write_json_object_atomic(target, report)
            _update_best_evaluation(layout, report, target)
            record_artifact_result(layout, {
                f"full_song_evaluation_{int(iteration):06d}":
                    str(target.resolve()),
            })
            print(full_song_evaluation_line(iteration, report), flush=True)
            return report

        def capture_s3_full_song(saved_checkpoint, reason):
            if env.curriculum_stage != "S3_SONG_INTEGRATION":
                return {}
            saved_checkpoint = Path(saved_checkpoint).resolve()
            iteration = strike_checkpoint_iteration(saved_checkpoint)
            artifact_name = f"full_song_rollout_{iteration:06d}"
            outputs = strike_full_song_rollout_artifact_paths(
                saved_checkpoint)
            if strike_full_song_rollout_is_complete(saved_checkpoint):
                completed_report = json.loads(
                    outputs["report"].read_text(encoding="utf-8"))
                if completed_report.get("schema") == (
                        "tab2body.strike_full_song_rollout.v2"):
                    completed_best = _update_best_full_song(
                        layout, completed_report, outputs["report"])
                    record_artifact_result(layout, {
                        "best_full_song_record": completed_best[
                            "best_record"],
                    })
                return outputs
            started_at = datetime.now(timezone.utc).isoformat()
            runtime_state = _strike_runtime_state(env)
            wrong_termination = bool(
                env.wrong_crossing_termination_enabled)
            failure_mining_updates = bool(
                env.failure_mining_updates_enabled)
            try:
                try:
                    env.wrong_crossing_termination_enabled = False
                    env.failure_mining_updates_enabled = False
                    env.set_evaluation_mode(True, reset=False)
                    observation = env.reset()
                    contract = strike_full_song_capture_contract(env)
                    capture = get_live_video_recorder().record(
                        torch,
                        model,
                        observation,
                        outputs,
                        int(contract["capture_step_limit"]),
                    )
                    summary = strike_full_song_capture_summary(
                        contract, capture)
                finally:
                    env.wrong_crossing_termination_enabled = wrong_termination
                    env.failure_mining_updates_enabled = (
                        failure_mining_updates)
                    trainer.obs = _restore_strike_runtime(
                        env, runtime_state)
                report = {
                    "schema": "tab2body.strike_full_song_rollout.v2",
                    "capture_mode": "paused_live_training_full_song",
                    "capture_reason": str(reason),
                    "iteration": iteration,
                    "checkpoint": str(saved_checkpoint),
                    "goal": str(args.goal),
                    "grip_reference": str(args.grip_reference),
                    "checkpoint_contract_sha256": checkpoint_contract[
                        "sha256"],
                    "curriculum_stage": "S3_SONG_INTEGRATION",
                    "timing_tolerance_ms": runtime_state[
                        "timing_tolerance_ms"],
                    "tempo_lambda": 1.0,
                    "evaluation_scope": "full_song_original_tempo",
                    "wrong_crossing_termination_suppressed": (
                        wrong_termination),
                    "irrecoverable_safety_termination_preserved": True,
                    "training_runtime_restored_after_capture": True,
                    "training_rng_restored_before_reset": True,
                    **summary,
                    **capture,
                }
                write_json_object_atomic(outputs["report"], report)
                if not strike_full_song_rollout_is_complete(
                        saved_checkpoint):
                    raise RuntimeError(
                        "S3 rollout ended before the original song duration")
                best_policy = _update_best_full_song(
                    layout, report, outputs["report"])
                produced = {
                    f"{artifact_name}_{key}": str(path.resolve())
                    for key, path in outputs.items()
                }
                produced["best_full_song_record"] = best_policy[
                    "best_record"]
                record_artifact_result(
                    layout, produced, resolved_errors=(artifact_name,))
                _append_periodic_video_event(layout, {
                    "status": "completed",
                    "kind": "s3_full_song",
                    "started_at_utc": started_at,
                    "completed_at_utc": datetime.now(
                        timezone.utc).isoformat(),
                    "iteration": iteration,
                    "checkpoint": str(saved_checkpoint),
                    "reason": str(reason),
                    "artifacts": produced,
                    "best_policy": best_policy,
                })
                print(
                    f"[strike full song] iteration {iteration}: "
                    "original-tempo remembered/current videos completed; "
                    f"best={best_policy['best_iteration']}"
                    + (" regression=warning"
                       if best_policy["regression_warning"] else ""),
                    flush=True)
                return outputs
            except Exception as exc:
                record_artifact_error(layout, artifact_name, exc)
                _append_periodic_video_event(layout, {
                    "status": "failed",
                    "kind": "s3_full_song",
                    "started_at_utc": started_at,
                    "completed_at_utc": datetime.now(
                        timezone.utc).isoformat(),
                    "iteration": iteration,
                    "checkpoint": str(saved_checkpoint),
                    "reason": str(reason),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                })
                print(
                    f"[strike full song] iteration {iteration} failed: "
                    f"{exc}",
                    flush=True)
                return None

        def capture_periodic_video(saved_checkpoint, reason):
            saved_checkpoint = Path(saved_checkpoint).resolve()
            iteration = strike_checkpoint_iteration(saved_checkpoint)
            artifact_name = f"periodic_rollout_{iteration:06d}"
            started_at = datetime.now(timezone.utc).isoformat()
            stage = str(env.curriculum_stage)
            paired_practice = stage in STRIKE_PAIRED_PRACTICE_STAGES
            outputs = (
                strike_paired_rollout_artifact_paths(saved_checkpoint)
                if paired_practice
                else strike_rollout_artifact_paths(saved_checkpoint))
            tolerance = float(env.timing_tolerance_ms)
            tempo_lambda = float(env.tempo_lambda)
            strum_span = int(env.strum_span)
            evaluation_full_song = bool(env.evaluation_full_song)
            runtime_state = _strike_runtime_state(env)
            failure_mining_updates = bool(
                env.failure_mining_updates_enabled)
            try:
                env.failure_mining_updates_enabled = False
                if paired_practice:
                    camera_outputs = {
                        direction: {
                            view: paths[view]
                            for view in ("remembered", "current")
                        }
                        for direction, paths in outputs.items()
                    }
                    try:
                        captures, restored_observation = (
                            get_live_video_recorder()
                            .record_practice_direction_pair(
                                torch,
                                model,
                                camera_outputs,
                                int(STRIKE["artifact_max_steps"]),
                                snapshot_runtime=_strike_runtime_state,
                                restore_runtime=_restore_strike_runtime,
                            ))
                        trainer.obs = restored_observation
                    finally:
                        env.failure_mining_updates_enabled = (
                            failure_mining_updates)
                        trainer.obs = _restore_strike_runtime(
                            env, runtime_state)
                    common_metadata = {
                        "capture_mode": (
                            "paused_live_training_direction_pair"),
                        "capture_reason": str(reason),
                        "iteration": iteration,
                        "checkpoint": str(saved_checkpoint),
                        "goal": str(args.goal),
                        "grip_reference": str(args.grip_reference),
                        "checkpoint_contract_sha256": checkpoint_contract[
                            "sha256"],
                        "timing_tolerance_ms": tolerance,
                        "tempo_lambda": tempo_lambda,
                        "strum_span": strum_span,
                        "evaluation_scope": (
                            "training_phrase_direction_matched"),
                        "training_observation_reset_after_capture": True,
                    }
                    for direction, capture in captures.items():
                        report = build_strike_practice_direction_report(
                            direction=direction,
                            curriculum_stage=stage,
                            capture=capture,
                            metadata=common_metadata,
                        )
                        write_json_object_atomic(
                            outputs[direction]["report"], report)
                    if not strike_paired_rollout_is_complete(
                            saved_checkpoint):
                        raise RuntimeError(
                            "paired strike rollout is missing a direction, "
                            "video or report")
                    produced = {
                        f"{artifact_name}_{direction}_{key}": str(
                            path.resolve())
                        for direction, paths in outputs.items()
                        for key, path in paths.items()
                    }
                else:
                    try:
                        observation = env.reset()
                        capture = get_live_video_recorder().record(
                            torch,
                            model,
                            observation,
                            outputs,
                            int(STRIKE["artifact_max_steps"]),
                        )
                    finally:
                        env.failure_mining_updates_enabled = (
                            failure_mining_updates)
                        trainer.obs = _restore_strike_runtime(
                            env, runtime_state)
                    report = {
                        "schema": "tab2body.strike_rollout_artifacts.v2",
                        "capture_mode": "paused_live_training",
                        "capture_reason": str(reason),
                        "iteration": iteration,
                        "checkpoint": str(saved_checkpoint),
                        "goal": str(args.goal),
                        "grip_reference": str(args.grip_reference),
                        "checkpoint_contract_sha256": checkpoint_contract[
                            "sha256"],
                        "curriculum_stage": stage,
                        "timing_tolerance_ms": tolerance,
                        "tempo_lambda": tempo_lambda,
                        "strum_span": strum_span,
                        "evaluation_scope": (
                            "full_song_original_tempo"
                            if evaluation_full_song
                            else "training_phrase_current_tempo"),
                        "training_observation_reset_after_capture": True,
                        "training_rng_restored_before_reset": True,
                        **capture,
                    }
                    write_json_object_atomic(outputs["report"], report)
                    if not strike_rollout_is_complete(saved_checkpoint):
                        raise RuntimeError(
                            "periodic strike rollout is missing a video or "
                            "report")
                    produced = {
                        f"{artifact_name}_{key}": str(path.resolve())
                        for key, path in outputs.items()
                    }
                if not strike_periodic_rollout_is_complete(saved_checkpoint):
                    raise RuntimeError(
                        "periodic strike rollout failed completion validation")
                video_schedule.mark_completed(iteration)
                if not paired_practice:
                    capture_s3_full_song(saved_checkpoint, reason)
                record_artifact_result(
                    layout, produced, resolved_errors=(artifact_name,))
                _append_periodic_video_event(layout, {
                    "status": "completed",
                    "started_at_utc": started_at,
                    "completed_at_utc": datetime.now(
                        timezone.utc).isoformat(),
                    "iteration": iteration,
                    "checkpoint": str(saved_checkpoint),
                    "reason": str(reason),
                    "artifacts": produced,
                })
                print(
                    f"[strike video] iteration {iteration}: "
                    + ("paired down/up remembered/current videos completed"
                       if paired_practice
                       else "remembered/current videos completed"),
                    flush=True)
                return True
            except Exception as exc:
                record_artifact_error(layout, artifact_name, exc)
                _append_periodic_video_event(layout, {
                    "status": "failed",
                    "started_at_utc": started_at,
                    "completed_at_utc": datetime.now(
                        timezone.utc).isoformat(),
                    "iteration": iteration,
                    "checkpoint": str(saved_checkpoint),
                    "reason": str(reason),
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                })
                print(
                    f"[strike video] iteration {iteration} failed; "
                    f"the next saved checkpoint will retry: {exc}",
                    flush=True)
                return False

        transition = {"value": None}
        reward_alignment_monitor = StrikeRewardAlignmentMonitor(window=300)

        def before_iteration(_iteration):
            state, reset_observation = curriculum_runtime.apply(env)
            if reset_observation is not None:
                trainer.obs = reset_observation
            return state

        def after_result(stats):
            state, reset_observation, changed = (
                curriculum_runtime.after_iteration(stats, env))
            if reset_observation is not None:
                trainer.obs = reset_observation
            transition["value"] = changed
            alignment_input = dict(stats)
            for key, value in state.items():
                alignment_input.setdefault(key, value)
            state.update(reward_alignment_monitor.update(alignment_input))
            return state

        def post_iteration(iteration, stats):
            last_stats["value"] = dict(stats)
            changed = transition["value"]
            if changed is not None:
                trainer.save(iteration)
                if changed["from"] != changed["to"]:
                    label = (
                        f"{changed['from']}_to_{changed['to']}")
                elif (not changed["from_complete"]
                      and changed["to_complete"]):
                    label = f"{changed['to']}_complete"
                elif changed["from_strum_span"] != changed["to_strum_span"]:
                    label = (
                        f"{changed['to']}_span_"
                        f"{changed['from_strum_span']}_to_"
                        f"{changed['to_strum_span']}")
                elif changed["from_tempo_lambda"] != changed["to_tempo_lambda"]:
                    label = (
                        f"{changed['to']}_tempo_"
                        f"{changed['from_tempo_lambda']:.2f}_to_"
                        f"{changed['to_tempo_lambda']:.2f}")
                elif changed["from_s2_profile"] != changed["to_s2_profile"]:
                    action = (
                        "rollback"
                        if changed["to_rollback_count"]
                        > changed["from_rollback_count"]
                        else "profile")
                    label = (
                        f"{changed['to']}_{action}_"
                        f"{changed['from_s2_profile']}_to_"
                        f"{changed['to_s2_profile']}")
                elif (changed["from_s2_endpoint_recovery_active"]
                      != changed["to_s2_endpoint_recovery_active"]
                      or changed["from_s2_focus_direction"]
                      != changed["to_s2_focus_direction"]):
                    status = (
                        "focus_active"
                        if changed["to_s2_endpoint_recovery_active"]
                        else "focus_released")
                    label = (
                        f"{changed['to']}_{status}_"
                        f"{changed['to_s2_focus_direction']}")
                elif changed["from_stalled"] != changed["to_stalled"]:
                    status = (
                        "stalled_continue" if changed["to_stalled"]
                        else "stalled_recovered")
                    label = f"{changed['to']}_{status}"
                else:
                    label = (
                        f"{changed['to']}_timing_"
                        f"{changed['from_tolerance_ms']:.0f}_to_"
                        f"{changed['to_tolerance_ms']:.0f}ms")
                target = layout.evaluations / (
                    f"curriculum_{iteration:06d}_{label}.json")
                write_json_object_atomic(target, {
                    "iteration": iteration,
                    **changed,
                    "stats": stats,
                    "curriculum": curriculum.state(),
                })
                transition["value"] = None
            full_song_interval = int(
                STRIKE["evaluation"]["full_song_interval_iterations"])
            if (not args.smoke
                    and env.curriculum_stage == "S3_SONG_INTEGRATION"
                    and (iteration == 1
                         or iteration % full_song_interval == 0)):
                try:
                    evaluate_s3_full_song_metrics(iteration)
                except Exception as exc:
                    record_artifact_error(
                        layout,
                        f"full_song_evaluation_{int(iteration):06d}",
                        exc,
                    )
                    print(
                        f"[strike evaluation] iteration {iteration} | "
                        f"full-song-F1=ERROR | {exc}",
                        flush=True,
                    )
            saved_checkpoint = (
                layout.checkpoints / f"strike_{iteration:06d}.pt")
            if (not args.no_auto_video
                    and video_schedule.is_due(saved_checkpoint)):
                capture_periodic_video(
                    saved_checkpoint, "checkpoint_interval")
        if not args.eval:
            try:
                trainer.learn(
                    args.iterations,
                    iteration_callback=before_iteration,
                    iteration_result_callback=after_result,
                    post_iteration_callback=post_iteration,
                    history_limit=0,
                )
            except KeyboardInterrupt:
                if trainer.iteration < 1:
                    raise
                trainer.save(trainer.iteration)
                saved_checkpoint = (
                    layout.checkpoints
                    / f"strike_{trainer.iteration:06d}.pt")
                if (not args.no_auto_video
                        and video_schedule.is_due(saved_checkpoint)):
                    capture_periodic_video(
                        saved_checkpoint, "training_interrupted")
                interruption_artifact = layout.logs / (
                    f"interrupted_{trainer.iteration:06d}.json")
                write_json_object_atomic(interruption_artifact, {
                    "schema": "tab2body.training_interruption.v1",
                    "task": "strike",
                    "iteration": int(trainer.iteration),
                    "checkpoint": str(saved_checkpoint.resolve()),
                    "recorded_at_utc": datetime.now(
                        timezone.utc).isoformat(),
                })
                print(
                    "\n[strike] interruption requested; saved iteration "
                    f"{trainer.iteration} and continuing final evaluation/"
                    "artifact generation",
                    flush=True)
        checkpoint_path = (
            layout.checkpoints / f"strike_{trainer.iteration:06d}.pt")
        if args.eval:
            checkpoint_path = Path(args.initialize_from if args.eval_policy_transfer else args.checkpoint)
        elif not checkpoint_path.is_file():
            raise RuntimeError(
                f"final strike checkpoint was not saved: {checkpoint_path}")

        base_artifacts = {
            "checkpoint": str(Path(checkpoint_path).resolve())}
        if interruption_artifact is not None:
            base_artifacts["interruption"] = str(
                interruption_artifact.resolve())
        for name, path in (
                ("metrics", layout.metrics),
                ("training_log", layout.training_log)):
            if path.is_file():
                base_artifacts[name] = str(path.resolve())
            elif not args.eval:
                raise RuntimeError(
                    f"strike training did not create required {name}: {path}")
        artifacts.update(base_artifacts)
        record_artifact_result(layout, base_artifacts)
        try:
            if args.eval_metrics_only:
                env.set_curriculum_stage(
                    S3_SONG_INTEGRATION,
                    float(STRIKE["curriculum"]["timing_tolerances_ms"][-1]),
                    tempo_lambda=1.0,
                    s2_profile_name=env.curriculum_s2_profiles[-1]["name"],
                    zone_active=True)
                env.wrong_crossing_termination_enabled = False
                env.failure_mining_updates_enabled = False
                env.set_evaluation_mode(True, reset=False)
            evaluation = evaluate_strike(
                torch, env, model, args.eval_episodes,
                metrics_only=args.eval_metrics_only, seed=args.eval_seed)
            evaluation["policy_source"] = {
                "checkpoint": str(checkpoint_path.resolve()),
                "checkpoint_sha256": file_sha256(checkpoint_path),
                "mode": "actor_normalization_transfer" if args.eval_policy_transfer else "strict_checkpoint",
                "training_performed": not args.eval,
            }
            evaluation["evaluation_contract_sha256"] = checkpoint_contract["sha256"]
            evaluation["goal_sha256"] = file_sha256(args.goal)
            evaluation["timing_tolerance_ms"] = float(env.timing_tolerance_ms)
            evaluation_path = layout.evaluations / (
                f"{Path(checkpoint_path).stem}.eval.json")
            write_json_object_atomic(evaluation_path, evaluation)
            evaluation_artifact = {
                "evaluation": str(evaluation_path.resolve())}
            artifacts.update(evaluation_artifact)
            record_artifact_result(layout, evaluation_artifact)
        except Exception as exc:
            record_artifact_error(layout, "evaluation", exc)
            raise
        if (not args.no_auto_video
                and env.curriculum_stage == "S3_SONG_INTEGRATION"):
            full_song_outputs = capture_s3_full_song(
                checkpoint_path, "final_s3_evaluation")
            if not full_song_outputs:
                raise RuntimeError(
                    "S3 final full-song video capture did not complete")
            artifacts.update({
                f"full_song_{key}": str(path.resolve())
                for key, path in full_song_outputs.items()
            })
    finally:
        env.close()
        if writer_lease is not None:
            writer_lease.close()

    del checkpoint, trainer, model, env
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    artifact_errors = {}

    artifacts.update(_attempt_artifact(
        layout,
        "analysis",
        lambda: {"analysis": _write_analysis(
            layout, checkpoint_path, evaluation,
            last_stats["value"])},
        artifact_errors,
    ))

    if not args.no_auto_artifacts and layout.metrics.exists():
        artifacts.update(_attempt_artifact(
            layout,
            "training_plot",
            lambda: {"training_plot": _run_plot(layout)},
            artifact_errors,
        ))

    if not args.no_auto_artifacts:
        artifacts.update(_attempt_artifact(
            layout,
            "motion_diagnostics",
            lambda: {"motion_diagnostics": _run_motion_audit(
                layout, checkpoint_path, args.goal,
                args.grip_reference, args.device)},
            artifact_errors,
        ))

    if not args.no_auto_video:
        artifacts.update(_attempt_artifact(
            layout,
            "rollout_videos",
            lambda: {
                f"rollout_{name}": path
                for name, path in _run_videos(
                    layout, checkpoint_path, args.goal,
                    args.grip_reference, args.device).items()
            },
            artifact_errors,
            resolved_errors=("rollout_videos",),
        ))

    if artifact_errors:
        summary = "; ".join(
            f"{name}: {type(error).__name__}: {error}"
            for name, error in artifact_errors.items())
        raise RuntimeError(
            "strike training completed, but one or more automatic "
            f"artifacts failed ({summary}); successful outputs and errors "
            f"are recorded in {layout.manifest}")

    print(json.dumps({
        "run": str(layout.root),
        "stage": evaluation["stage"],
        "timing_tolerance_ms": evaluation["timing_tolerance_ms"],
        "passed": evaluation["gates"]["passed"],
        "artifacts": artifacts,
    }, indent=2, ensure_ascii=False))
    return artifacts


if __name__ == "__main__":
    main()
