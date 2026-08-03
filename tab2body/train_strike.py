"""Train, evaluate and archive the rebuilt right-hand strike policy.

Examples
--------
Smoke-test the complete simulator/PPO/checkpoint path::

    python -m tab2body.train_strike --smoke --run-name strike_smoke

Run 500 PPO epochs and automatically create logs, plots, evaluation and the
two frozen-camera rollout videos::

    python -m tab2body.train_strike --iterations 500 --run-name strike_500
"""
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

# Isaac Gym must register its torch bridge before importing the learning
# package (whose model modules import torch).
import isaacgym  # noqa: F401

from tab2body.strike_cfg import STRIKE
from tab2body.learning.checkpoint_contract import (
    build_strike_contract_payload,
    checkpoint_evaluation_hyperparameters,
    file_sha256,
    fingerprint_file_set,
    seal_checkpoint_contract,
)
from tab2body.learning.run_layout import (
    default_strike_video_paths,
    has_training_history,
    layout_for,
    resolve_run_dir,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

STRIKE_IMPLEMENTATION_FILES = (
    "strike_cfg.py",
    "train.py",
    "train_strike.py",
    "env/base.py",
    "env/strike_detector.py",
    "env/strike_events.py",
    "env/strike_goals.py",
    "env/rewards/strike.py",
    "env/tasks/task_strike.py",
    "learning/checkpoint_contract.py",
    "learning/models.py",
    "learning/ppo.py",
    "learning/run_layout.py",
    "learning/strike_curriculum.py",
    "learning/strike_evaluation.py",
    "tools/audit_strike_runtime.py",
    "tools/build_strike_training_data.py",
    "tools/plot_strike_training.py",
    "tools/record_strike_rollout.py",
)


def build_parser():
    from tab2body.learning.strike_curriculum import STRIKE_STAGES

    parser = argparse.ArgumentParser(
        description="right-hand virtual-pick strike training")
    parser.add_argument("--goal", default=STRIKE["goal_path"])
    parser.add_argument(
        "--song", default=None,
        help="data/song_bundles 아래의 song_id; 지정하면 해당 strike 입력을 사용")
    parser.add_argument(
        "--grip-reference", default=STRIKE["grip_reference_path"])
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
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--no-random-start", action="store_true")
    parser.add_argument("--no-curriculum", action="store_true")
    parser.add_argument(
        "--curriculum-stage", choices=STRIKE_STAGES, default=None)
    parser.add_argument(
        "--timing-tolerance-ms", type=float, default=None,
        help="fixed-stage timing tolerance; A3/A4 only")
    parser.add_argument(
        "--smoke", action="store_true",
        help="8 env × 4 steps × 1 PPO update/checkpoint contract test")
    parser.add_argument("--no-auto-video", action="store_true")
    parser.add_argument("--no-auto-artifacts", action="store_true")
    return parser


def _song_identity(path):
    from tab2body.song_bundles import song_id_from_training_path

    path = Path(path).resolve()
    suffix = ".strike_training.json"
    song_id = song_id_from_training_path(path, suffix)
    return path, song_id


def _semantic_strike_config(config):
    """Keep task semantics in the contract and omit launch-only settings."""
    selected = (
        "action_scale", "action_alpha", "reset_noise",
        "reset_soft_limit_fraction", "failure_termination_penalty",
        "control_prefixes", "zone", "trajectory", "detector", "reward",
        "episode", "curriculum", "evaluation",
    )
    result = {key: deepcopy(config[key]) for key in selected}
    result["direction_profile"] = "down_only_v1"
    result["pick_representation"] = {
        "body": "RH:pick",
        "tip": "RH:pick origin",
        "physical_geometry": False,
        "attachment": "fixed_to_thumb_index_pose",
    }
    result["string_representation"] = "six_fixed_finite_segments"
    result["success_event"] = "debounced_release_immediately_after_crossing"
    return result


def build_runtime_checkpoint_contract(
        env, model, goal_path, *, config=STRIKE, ppo_config=None):
    """Seal every semantic input needed to safely reuse a strike policy.

    This helper is public because the dual-camera recorder reconstructs the
    same live environment before loading model weights.
    """
    import torch

    tab2body_root = Path(__file__).resolve().parent
    goal_path = Path(goal_path).resolve()
    grip_path = Path(config["grip_reference_path"]).resolve()
    asset_fingerprint = fingerprint_file_set(
        tab2body_root, ("assets", "_gen/mjcf_gains.json"))
    implementation_fingerprint = fingerprint_file_set(
        tab2body_root, STRIKE_IMPLEMENTATION_FILES)
    initial_std = model.log_std.detach().exp().cpu()
    if initial_std.numel() != env.num_actions or not torch.allclose(
            initial_std, initial_std[:1].expand_as(initial_std)):
        raise ValueError(
            "strike contract requires one shared initial policy std")
    controlled_names = [
        env.dof_names[index]
        for index in env.ctrl_idx.detach().cpu().tolist()]
    payload = build_strike_contract_payload(
        controlled_dof_names=controlled_names,
        num_obs=env.num_obs,
        num_actions=env.num_actions,
        value_dim=env.value_dim,
        action_scale=env.action_scale,
        action_alpha=env.action_alpha,
        reset_soft_limit_fraction=env.reset_soft_limit_fraction,
        policy_init_std=float(initial_std[0]),
        strike_config=_semantic_strike_config(config),
        ppo_config=deepcopy(
            ppo_config if ppo_config is not None else config["ppo"]),
        observation_manifest=env.observation_manifest,
        goal_sha256=file_sha256(goal_path),
        grip_reference_sha256=file_sha256(grip_path),
        asset_fingerprint=asset_fingerprint,
        implementation_fingerprint=implementation_fingerprint,
        policy_distribution_version=getattr(
            model, "POLICY_DISTRIBUTION_VERSION",
            "tanh_squashed_diagonal_gaussian.v1"),
        sim_hz=env.SIM_HZ,
        sim_substeps=env.SUBSTEPS,
    )
    return seal_checkpoint_contract(payload)


def _nearest_existing_parent(path):
    path = Path(path).resolve()
    while not path.exists():
        if path.parent == path:
            raise RuntimeError(f"no existing output parent for {path}")
        path = path.parent
    return path


def _available_ram_bytes():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("cannot read MemAvailable from /proc/meminfo")


def training_resource_preflight(torch, device, out_dir, num_envs, smoke=False):
    limits = STRIKE["resource_guard"]
    if num_envs <= 0:
        raise ValueError("--num-envs must be positive")
    if num_envs > int(limits["max_num_envs"]):
        raise ValueError(
            f"--num-envs {num_envs} exceeds validated ceiling "
            f"{limits['max_num_envs']}")
    device = torch.device(device)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("strike Isaac Gym training requires CUDA")
    free_vram, total_vram = torch.cuda.mem_get_info(device)
    props = torch.cuda.get_device_properties(device)
    ram = _available_ram_bytes()
    disk = shutil.disk_usage(_nearest_existing_parent(out_dir)).free
    gib = 1024 ** 3
    # Smoke runs are deliberately tiny; keep disk/RAM protection but permit a
    # busy GPU to exercise the pipeline.
    min_vram = 1.0 if smoke else float(limits["min_free_vram_gib"])
    required = {
        "free_vram": min_vram * gib,
        "available_ram": float(limits["min_available_ram_gib"]) * gib,
        "free_disk": float(limits["min_free_disk_gib"]) * gib,
    }
    actual = {
        "free_vram": free_vram,
        "available_ram": ram,
        "free_disk": disk,
    }
    failures = [
        f"{name}={actual[name] / gib:.1f}GiB < {minimum / gib:.1f}GiB"
        for name, minimum in required.items()
        if actual[name] < minimum]
    if failures:
        raise RuntimeError(
            "insufficient resources before strike allocation: "
            + ", ".join(failures))
    return {
        "gpu_name": props.name,
        "gpu_total_vram_gib": round(total_vram / gib, 2),
        "gpu_free_vram_gib": round(free_vram / gib, 2),
        "available_ram_gib": round(ram / gib, 2),
        "free_disk_gib": round(disk / gib, 2),
        "num_envs": int(num_envs),
    }


def _curriculum_from_config(num_envs):
    from tab2body.learning.strike_curriculum import (
        StrikeCurriculum,
        StrikeCurriculumConfig,
    )

    curriculum = STRIKE["curriculum"]
    if isinstance(num_envs, bool) or not isinstance(num_envs, int) or num_envs < 1:
        raise ValueError("num_envs must be a positive integer")
    evidence_fraction = float(
        curriculum.get("terminal_evidence_fraction", 1.0))
    if (not math.isfinite(evidence_fraction)
            or not 0.0 < evidence_fraction <= 1.0):
        raise ValueError(
            "terminal_evidence_fraction must be finite and in (0, 1]")
    minimum = curriculum["min_iterations"]
    maximum = curriculum["max_iterations"]
    config = StrikeCurriculumConfig(
        grip_min_iterations=int(minimum["A0_PICK_GRIP"]),
        grip_max_iterations=int(maximum["A0_PICK_GRIP"]),
        ready_min_iterations=int(minimum["A1_TIP_READY"]),
        ready_max_iterations=int(maximum["A1_TIP_READY"]),
        crossing_min_iterations=int(minimum["A2_FREE_CROSSING"]),
        crossing_max_iterations=int(maximum["A2_FREE_CROSSING"]),
        timed_min_iterations=int(minimum["A3_TIMED_CROSSING"]),
        timed_max_iterations=int(maximum["A3_TIMED_CROSSING"]),
        zone_min_iterations=int(minimum["A4_ZONE_CONTROL"]),
        zone_max_iterations=int(maximum["A4_ZONE_CONTROL"]),
        promotion_windows=int(curriculum["promotion_windows"]),
        terminal_evidence_episodes=max(
            1, int(math.ceil(num_envs * evidence_fraction))),
        grip_success_gate=float(curriculum["grip_success_rate"]),
        tip_ready_success_gate=float(curriculum["ready_success_rate"]),
        release_recall_gate=float(curriculum["release_recall"]),
        false_positive_rate_gate=float(curriculum["max_wrong_rate"]),
        strike_f1_gate=float(curriculum["timed_f1_by_level"][-1]),
        timing_tolerances_ms=tuple(
            int(value) for value in curriculum["timing_tolerances_ms"]),
        timed_f1_by_level=tuple(
            float(value) for value in curriculum["timed_f1_by_level"]),
        zone_f1_gate=float(curriculum["zone_f1"]),
        zone_success_gate=float(curriculum["zone_success_rate"]),
    )
    return StrikeCurriculum(config)


def _set_fixed_curriculum(curriculum, stage, tolerance_ms=None):
    from tab2body.learning.strike_curriculum import (
        A3_TIMED_CROSSING,
        A4_ZONE_CONTROL,
    )

    curriculum.stage = stage
    curriculum.stage_iteration = 0
    curriculum.total_iteration = 0
    curriculum.stalled = False
    curriculum.promotion_streak = 0
    curriculum.timing_streak = 0
    curriculum._reset_terminal_evidence()
    schedule = curriculum.config.timing_tolerances_ms
    if stage == A4_ZONE_CONTROL:
        curriculum.timing_level = len(schedule) - 1
    elif stage == A3_TIMED_CROSSING:
        desired = schedule[0] if tolerance_ms is None else int(
            round(tolerance_ms))
        if desired not in schedule:
            raise ValueError(
                f"A3 tolerance must be one of {schedule}, got {desired}")
        curriculum.timing_level = schedule.index(desired)
    else:
        curriculum.timing_level = 0
        if tolerance_ms is not None:
            raise ValueError(
                "--timing-tolerance-ms applies only to A3/A4")
    if (stage == A4_ZONE_CONTROL and tolerance_ms is not None
            and abs(float(tolerance_ms) - schedule[-1]) > 1e-6):
        raise ValueError(
            f"A4 keeps the final {schedule[-1]} ms tolerance")


def _create_task(StrikeTask, args):
    return StrikeTask(
        goal_path=str(args.goal),
        grip_reference_path=str(args.grip_reference),
        num_envs=args.num_envs,
        device=args.device,
        headless=True,
        seed=args.seed,
        action_alpha=STRIKE["action_alpha"],
        action_scale=STRIKE["action_scale"],
        reset_noise=STRIKE["reset_noise"],
        reset_soft_limit_fraction=STRIKE["reset_soft_limit_fraction"],
        zone=STRIKE["zone"],
        trajectory=STRIKE["trajectory"],
        detector=STRIKE["detector"],
        reward=STRIKE["reward"],
        episode=STRIKE["episode"],
        failure_termination_penalty=STRIKE[
            "failure_termination_penalty"],
        random_start=not args.no_random_start,
    )


def _load_checkpoint(torch, path, device):
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def evaluate_strike(torch, env, model, episodes):
    """Run deterministic stage-appropriate episodes and return explicit gates."""
    from tab2body.learning.strike_evaluation import (
        strike_evaluation_gate_summary,
    )

    episodes = int(episodes)
    if episodes < 1:
        raise ValueError("evaluation episodes must be positive")
    env.set_evaluation_mode(
        full_song=(env.curriculum_stage == "A4_ZONE_CONTROL"), reset=False)
    obs = env.reset()
    rows = []
    max_steps = env.max_episode_length * (
        math.ceil(episodes / env.num_envs) + 2)
    with torch.no_grad():
        for _ in range(max_steps):
            action, _, _ = model.act(obs, deterministic=True)
            obs, _reward, done, info = env.step(action)
            metric_count = info[env.episode_metric_keys[0]].numel()
            if metric_count:
                ids = torch.nonzero(done).squeeze(-1)
                if ids.numel() != metric_count:
                    raise RuntimeError(
                        "strike episode metrics are not aligned with done")
                for local, _env_id in enumerate(ids.detach().cpu().tolist()):
                    row = {
                        key: float(info[key][local].detach().cpu())
                        for key in env.episode_metric_keys}
                    row.update({
                        key: bool(info[f"episode_{key}"][local].item())
                        for key in env.episode_reason_keys})
                    timing_count = info.get("episode_timing_count")
                    timing_values = info.get("episode_timing_abs_ms")
                    if timing_count is not None and timing_values is not None:
                        count = int(timing_count[local].detach().cpu())
                        row["_timing_abs_ms"] = (
                            timing_values[local, :count]
                            .detach().cpu().tolist())
                    rows.append(row)
                    if len(rows) >= episodes:
                        break
            if len(rows) >= episodes:
                break
    if len(rows) < episodes:
        raise RuntimeError(
            f"evaluation completed only {len(rows)}/{episodes} episodes")
    episode_aggregate = {
        key: sum(row[key] for row in rows) / len(rows)
        for key in env.episode_metric_keys}
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
    aggregate = {
        "grip_success_rate":
            episode_aggregate["strike_grip_success_rate"],
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
        "zone_success_rate":
            episode_aggregate["strike_zone_success_rate"],
        "zone_mean_quality":
            episode_aggregate["strike_zone_mean_quality"],
        "curriculum_success_rate":
            episode_aggregate["curriculum_success_rate"],
    }
    safety_passed = all(
        not row["failure_termination"] for row in rows)
    gates_cfg = STRIKE["evaluation"]
    gate_timing_tolerance_ms = env.timing_tolerance_ms
    if env.curriculum_stage == "A4_ZONE_CONTROL":
        gate_timing_tolerance_ms = min(
            gate_timing_tolerance_ms,
            float(gates_cfg["timing_p95_ms"]))
    gates = strike_evaluation_gate_summary(
        aggregate,
        rows,
        stage=env.curriculum_stage,
        timing_tolerance_ms=gate_timing_tolerance_ms,
        safety_passed=safety_passed,
        grip_success_gate=STRIKE["curriculum"]["grip_success_rate"],
        tip_ready_success_gate=STRIKE["curriculum"]["ready_success_rate"],
        precision_gate=gates_cfg["precision"],
        release_recall_gate=gates_cfg["recall"],
        false_positive_rate_gate=gates_cfg["max_wrong_rate"],
        strike_f1_gate=gates_cfg["f1"],
        zone_success_gate=gates_cfg["zone_success_rate"],
    )
    return {
        "schema": "tab2body.strike_evaluation.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": env.curriculum_stage,
        "timing_tolerance_ms": env.timing_tolerance_ms,
        "evaluation_gate_timing_p95_ms": gate_timing_tolerance_ms,
        "direction_profile": env.direction_profile,
        "episodes": len(rows),
        "timing_sample_count": len(timing_samples),
        "metrics": aggregate,
        "gates": gates,
        "episode_rows": rows,
    }


def _write_run_metadata(layout, contract, args, resources):
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
        "direction_profile": "down_only_v1",
        "resources_at_start": resources,
        "artifacts": {},
    }
    if layout.manifest.exists():
        existing = json.loads(layout.manifest.read_text(encoding="utf-8"))
        if existing.get("checkpoint_contract_sha256") != contract["sha256"]:
            raise RuntimeError(
                "run directory belongs to a different strike contract")
    else:
        layout.manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    with layout.sessions.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "evaluation" if args.eval else "training",
            "iterations": args.iterations,
            "checkpoint": args.checkpoint,
        }, ensure_ascii=False) + "\n")


def _record_artifacts(layout, artifacts):
    manifest = json.loads(layout.manifest.read_text(encoding="utf-8"))
    manifest["artifacts"] = {
        **manifest.get("artifacts", {}),
        **artifacts,
    }
    layout.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    with layout.sessions.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "artifact_generation",
            "artifacts": artifacts,
        }, ensure_ascii=False) + "\n")


def _record_artifact_error(layout, name, error):
    manifest = json.loads(layout.manifest.read_text(encoding="utf-8"))
    errors = dict(manifest.get("artifact_errors", {}))
    record = {
        "type": type(error).__name__,
        "message": str(error),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    errors[str(name)] = record
    manifest["artifact_errors"] = errors
    layout.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    with layout.sessions.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "artifact_error",
            "artifact": str(name),
            "error": record,
        }, ensure_ascii=False) + "\n")


def _write_analysis(layout, checkpoint, evaluation, last_stats=None):
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    lines = [
        "# Strike 학습 자동 분석",
        "",
        f"- checkpoint: `{checkpoint}`",
        f"- 평가 단계: `{evaluation['stage']}`",
        f"- 시간 허용 오차: `{evaluation['timing_tolerance_ms']:.0f} ms`",
        f"- 평가 episode: `{evaluation['episodes']}`",
        f"- 단계 목표 통과: `{'PASS' if gates['task_passed'] else 'NOT YET'}`",
        f"- 안전 gate 통과: `{'PASS' if gates['safety_passed'] else 'FAIL'}`",
        "",
        "## 핵심 지표",
        "",
        f"- grip success: `{metrics['grip_success_rate']:.3f}`",
        f"- ready success: `{metrics['tip_ready_success_rate']:.3f}`",
        f"- precision: `{metrics['precision']:.3f}`",
        f"- release recall: `{metrics['release_recall']:.3f}`",
        f"- false positive rate: `{metrics['false_positive_rate']:.3f}`",
        f"- strike F1: `{metrics['strike_f1']:.3f}`",
        f"- timing p95: `{metrics['timing_p95_ms']:.2f} ms`",
        f"- zone success: `{metrics['zone_success_rate']:.3f}`",
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
        ]
    target = layout.root / "ANALYSIS.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _run_plot(layout):
    target = layout.plots / "strike_training_curves.png"
    command = [
        sys.executable,
        str(PACKAGE_ROOT / "tools" / "plot_strike_training.py"),
        str(layout.metrics),
        "--out", str(target),
    ]
    with layout.artifact_log.open("a", encoding="utf-8") as stream:
        subprocess.run(
            command, check=True, stdout=stream, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
    return target


def _run_videos(layout, checkpoint, goal, grip, device):
    outputs = default_strike_video_paths(checkpoint)
    command = [
        sys.executable,
        str(PACKAGE_ROOT / "tools" / "record_strike_rollout.py"),
        "--checkpoint", str(checkpoint),
        "--goal", str(goal),
        "--grip-reference", str(grip),
        "--device", str(device),
        "--out-remembered", str(outputs["remembered"]),
        "--out-current", str(outputs["current"]),
    ]
    with layout.artifact_log.open("a", encoding="utf-8") as stream:
        subprocess.run(
            command, check=True, stdout=stream, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
    return outputs


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.song:
        from tab2body.song_bundles import strike_goal_path

        if args.goal != STRIKE["goal_path"]:
            raise SystemExit("--song and --goal cannot be used together")
        args.goal = str(strike_goal_path(args.song))
    if args.eval and not args.checkpoint:
        raise SystemExit("--eval requires --checkpoint")
    if args.iterations < 1 and not args.eval:
        raise SystemExit("--iterations must be positive")
    if args.eval_episodes < 1:
        raise SystemExit("--eval-episodes must be positive")
    args.goal, song_id = _song_identity(args.goal)
    args.grip_reference = Path(args.grip_reference).resolve()
    if not args.goal.is_file():
        raise FileNotFoundError(f"strike goal not found: {args.goal}")
    if not args.grip_reference.is_file():
        raise FileNotFoundError(
            f"pick-grip reference not found: {args.grip_reference}")
    if args.checkpoint:
        args.checkpoint = str(Path(args.checkpoint).resolve())
    out_dir = resolve_run_dir(
        PROJECT_ROOT, song_id, explicit=args.out,
        run_name=args.run_name, checkpoint=args.checkpoint,
        task_name="strike")
    layout = layout_for(out_dir, create=True)
    if (not args.checkpoint and not args.eval
            and has_training_history(layout, task_name="strike")):
        raise FileExistsError(
            f"strike run already exists at {layout.root}; use --checkpoint "
            "or choose another --run-name")

    import torch

    from tab2body.env.tasks import StrikeTask
    from tab2body.learning import ActorCritic, PPOConfig, PPOTrainer

    if args.smoke:
        args.num_envs = min(args.num_envs, 8)
        args.iterations = 1
        args.eval_episodes = min(args.eval_episodes, args.num_envs)
        args.no_auto_video = True
    resources = training_resource_preflight(
        torch, args.device, layout.root, args.num_envs, smoke=args.smoke)
    env = _create_task(StrikeTask, args)
    history = []
    evaluation = None
    checkpoint_path = None
    artifacts = {}
    try:
        checkpoint = (
            _load_checkpoint(torch, args.checkpoint, args.device)
            if args.checkpoint else None)
        policy_init_std = float(STRIKE["policy_init_std"])
        saved_eval_ppo = None
        if args.eval:
            policy_init_std, saved_eval_ppo = (
                checkpoint_evaluation_hyperparameters(checkpoint))
        model = ActorCritic(
            env.num_obs,
            env.num_actions,
            value_dim=env.value_dim,
            init_std=policy_init_std,
            init_mean=env.grip_hold_action[0],
        ).to(args.device)
        ppo_values = dict(STRIKE["ppo"])
        ppo_values["minibatch_size"] = args.minibatch_size
        if saved_eval_ppo is not None:
            ppo_values = saved_eval_ppo
        elif args.smoke:
            ppo_values.update(
                horizon=4, epochs=1, minibatch_size=32,
                save_interval=1, log_interval=1)
        ppo_config = PPOConfig(**ppo_values)
        trainer = PPOTrainer(env, model, ppo_config, out_dir=layout.root)
        contract_config = deepcopy(STRIKE)
        contract_config["grip_reference_path"] = str(args.grip_reference)
        checkpoint_contract = build_runtime_checkpoint_contract(
            env, model, args.goal, config=contract_config,
            ppo_config=vars(ppo_config))
        trainer.set_checkpoint_contract(checkpoint_contract)

        curriculum = _curriculum_from_config(args.num_envs)
        fixed_stage = args.curriculum_stage
        if args.no_curriculum and fixed_stage is None:
            fixed_stage = "A0_PICK_GRIP"
        if fixed_stage is not None:
            _set_fixed_curriculum(
                curriculum, fixed_stage, args.timing_tolerance_ms)

        if checkpoint is not None:
            if fixed_stage is None:
                curriculum.load_context(
                    checkpoint.get("training_context", {}))
            trainer.resume(
                checkpoint, purpose="evaluate" if args.eval else "resume")
        initial_state = curriculum.apply(env)
        reset_obs = initial_state.pop("_reset_observation", None)
        if reset_obs is not None:
            trainer.obs = reset_obs
        trainer.training_context.update(initial_state)
        _write_run_metadata(layout, checkpoint_contract, args, resources)

        transition = {
            "changed": False,
            "from": None,
            "to": None,
            "from_tolerance_ms": None,
            "to_tolerance_ms": None,
            "from_complete": False,
            "to_complete": False,
        }

        def before_iteration(_iteration):
            return curriculum.apply(env)

        def after_result(stats):
            previous = curriculum.stage
            previous_tolerance = curriculum.timing_tolerance_ms
            previous_complete = curriculum.complete
            if fixed_stage is None:
                state = curriculum.after_iteration(stats)
            else:
                curriculum.total_iteration += 1
                curriculum.stage_iteration += 1
                state = curriculum.state()
            applied = curriculum.apply(env)
            reset_observation = applied.pop("_reset_observation", None)
            if reset_observation is not None:
                trainer.obs = reset_observation
            state.update(applied)
            changed = (
                state["curriculum_stage"] != previous
                or state["curriculum_timing_tolerance_ms"]
                != previous_tolerance
                or state["curriculum_complete"] != previous_complete)
            if changed:
                transition.update(
                    changed=True,
                    **{"from": previous},
                    to=state["curriculum_stage"],
                    from_tolerance_ms=previous_tolerance,
                    to_tolerance_ms=state[
                        "curriculum_timing_tolerance_ms"],
                    from_complete=previous_complete,
                    to_complete=state["curriculum_complete"])
            return state

        def post_iteration(iteration, stats):
            if transition["changed"]:
                trainer.save(iteration)
                if transition["from"] != transition["to"]:
                    label = (
                        f"{transition['from']}_to_{transition['to']}")
                elif (not transition["from_complete"]
                      and transition["to_complete"]):
                    label = f"{transition['to']}_complete"
                else:
                    label = (
                        f"{transition['to']}_timing_"
                        f"{transition['from_tolerance_ms']:.0f}_to_"
                        f"{transition['to_tolerance_ms']:.0f}ms")
                target = layout.evaluations / (
                    f"curriculum_{iteration:06d}_{label}.json")
                target.write_text(
                    json.dumps({
                        "iteration": iteration,
                        "from": transition["from"],
                        "to": transition["to"],
                        "from_tolerance_ms":
                            transition["from_tolerance_ms"],
                        "to_tolerance_ms":
                            transition["to_tolerance_ms"],
                        "from_complete": transition["from_complete"],
                        "to_complete": transition["to_complete"],
                        "stats": stats,
                        "curriculum": curriculum.state(),
                    }, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
                transition["changed"] = False

        if not args.eval:
            history = trainer.learn(
                args.iterations,
                iteration_callback=before_iteration,
                iteration_result_callback=after_result,
                post_iteration_callback=post_iteration,
            )
        checkpoint_path = (
            layout.checkpoints / f"strike_{trainer.iteration:06d}.pt")
        if args.eval:
            checkpoint_path = Path(args.checkpoint)
        elif not checkpoint_path.is_file():
            raise RuntimeError(
                f"final strike checkpoint was not saved: {checkpoint_path}")

        # Persist the recoverable training outputs before evaluation.  A
        # deterministic evaluation failure is important and still propagates,
        # but it must not hide the checkpoint/logs or disappear from the run
        # manifest.
        base_artifacts = {
            "checkpoint": str(Path(checkpoint_path).resolve()),
            "metrics": str(layout.metrics.resolve()),
            "training_log": str(layout.training_log.resolve()),
        }
        artifacts.update(base_artifacts)
        _record_artifacts(layout, base_artifacts)

        # Evaluate the exact stage/tolerance stored by the curriculum after the
        # final optimizer update.
        applied = curriculum.apply(env)
        if "_reset_observation" in applied:
            trainer.obs = applied["_reset_observation"]
        try:
            evaluation = evaluate_strike(
                torch, env, model, args.eval_episodes)
            evaluation_path = layout.evaluations / (
                f"{Path(checkpoint_path).stem}.eval.json")
            evaluation_path.write_text(
                json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
            evaluation_artifact = {
                "evaluation": str(evaluation_path.resolve())}
            artifacts.update(evaluation_artifact)
            _record_artifacts(layout, evaluation_artifact)
        except Exception as exc:
            _record_artifact_error(layout, "evaluation", exc)
            raise
    finally:
        env.close()

    artifact_errors = {}

    try:
        analysis = _write_analysis(
            layout, checkpoint_path, evaluation,
            history[-1] if history else None)
        delta = {"analysis": str(analysis.resolve())}
        artifacts.update(delta)
        _record_artifacts(layout, delta)
    except Exception as exc:
        artifact_errors["analysis"] = exc
        _record_artifact_error(layout, "analysis", exc)

    if not args.no_auto_artifacts and layout.metrics.exists():
        try:
            delta = {
                "training_plot": str(_run_plot(layout).resolve())}
            artifacts.update(delta)
            _record_artifacts(layout, delta)
        except Exception as exc:
            artifact_errors["training_plot"] = exc
            _record_artifact_error(layout, "training_plot", exc)

    if not args.no_auto_video:
        try:
            videos = _run_videos(
                layout, checkpoint_path, args.goal,
                args.grip_reference, args.device)
            delta = {
                f"rollout_{view}": str(path.resolve())
                for view, path in videos.items()
            }
            artifacts.update(delta)
            _record_artifacts(layout, delta)
        except Exception as exc:
            artifact_errors["rollout_videos"] = exc
            _record_artifact_error(layout, "rollout_videos", exc)

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
