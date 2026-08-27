from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

from tab2body.strike_cfg import STRIKE
from tab2body.strike_checkpoint import (
    build_runtime_checkpoint_contract,
)
from tab2body.strike_contract import STRIKE_STAGES, SONG_GOAL_STAGES
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
)
from tab2body.learning.run_io import (
    record_artifact_error,
    record_artifact_result,
    record_run_metadata,
)
from tab2body.learning.run_layout import (
    default_strike_video_paths,
    has_training_history,
    layout_for,
    resolve_run_dir,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

STRIKE_TOOLING_PROVENANCE_FILES = (
    "strike_cfg.py",
    "train.py",
    "train_strike.py",
    "learning/run_io.py",
    "learning/run_layout.py",
    "learning/strike_evaluation.py",
    "tools/audit_strike_runtime.py",
    "tools/audit_strike_motion.py",
    "tools/audit_strike_string_alignment.py",
    "tools/build_strike_training_data.py",
    "tools/plot_strike_training.py",
    "tools/record_strike_rollout.py",
    "tools/record_strike_visualized_rollout.py",
    "tools/strike_visualization.py",
)


class _StrikeCurriculumStalled(RuntimeError):
    pass


def _curriculum_stalled(stats):
    return bool(stats.get("next_curriculum_stalled", False))


def _full_song_evaluation_ready(env):
    return bool(
        # env.curriculum_stage == "A4_ZONE_CONTROL"
        env.curriculum_stage in SONG_GOAL_STAGES
        and abs(float(env.tempo_lambda) - 1.0) <= 1e-9)


def _add_local_isaacgym_path():
    local_python = PROJECT_ROOT / "isaacgym" / "python"
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
        "--curriculum-stage",
        choices=STRIKE_STAGES,
        default=None)
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
    ))


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
    full_song = _full_song_evaluation_ready(env)
    evaluated_tempo_lambda = float(env.tempo_lambda)
    env.set_evaluation_mode(full_song=full_song, reset=False)
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
    for count_key, metric_keys in (
            ("strike_single_event_count", (
                "strike_single_precision", "strike_single_recall",
                "strike_single_f1")),
            ("strike_strum_event_count", (
                "strike_strum_completion_rate",
                "strike_strum_traversal_recall",
                "strike_strum_order_accuracy",
                "strike_strum_direction_accuracy",
                "strike_strum_protected_crossing_rate",
                "strike_strum_duplicate_crossing_rate"))):
        total = sum(float(row[count_key]) for row in rows)
        if total > 0.0:
            for key in metric_keys:
                episode_aggregate[key] = sum(
                    float(row[key]) * float(row[count_key])
                    for row in rows) / total
        episode_aggregate[count_key] = total
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
        "strum_protected_crossing_rate": episode_aggregate[
            "strike_strum_protected_crossing_rate"],
        "strum_duplicate_crossing_rate": episode_aggregate[
            "strike_strum_duplicate_crossing_rate"],
        "strum_event_count": episode_aggregate["strike_strum_event_count"],
    }
    safety_passed = all(
        not row["failure_termination"] for row in rows)
    gates_cfg = STRIKE["evaluation"]
    gate_timing_tolerance_ms = env.timing_tolerance_ms
    # if env.curriculum_stage == "A4_ZONE_CONTROL":
    if env.curriculum_stage in SONG_GOAL_STAGES:
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
        strum_completion_gate=gates_cfg["strum_completion_rate"],
        strum_traversal_recall_gate=gates_cfg["strum_traversal_recall"],
        strum_order_accuracy_gate=gates_cfg["strum_order_accuracy"],
        strum_direction_accuracy_gate=gates_cfg["strum_direction_accuracy"],
        strum_max_protected_rate=gates_cfg["strum_max_protected_rate"],
    )
    return {
        "schema": "tab2body.strike_evaluation.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": env.curriculum_stage,
        "evaluation_scope": (
            "full_song_original_tempo"
            if full_song else "training_phrase_current_tempo"),
        "tempo_lambda": evaluated_tempo_lambda,
        "timing_tolerance_ms": env.timing_tolerance_ms,
        "evaluation_gate_timing_p95_ms": gate_timing_tolerance_ms,
        "direction_profile": env.direction_profile,
        "episodes": len(rows),
        "timing_sample_count": len(timing_samples),
        "metrics": aggregate,
        "gates": gates,
        "episode_rows": rows,
    }


def _write_run_metadata(
        layout, contract, args, resources, goal_validation):
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
        "direction_profile": "down_only_v1",
        "goal_compilation": dict(goal_validation),
        "resources_at_start": resources,
        "provenance": {
            "tooling_fingerprint": tooling_fingerprint,
        },
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
        f"- ready success: `{metrics['tip_ready_success_rate']:.3f}`",
        f"- precision: `{metrics['precision']:.3f}`",
        f"- release recall: `{metrics['release_recall']:.3f}`",
        f"- false positive rate: `{metrics['false_positive_rate']:.3f}`",
        f"- strike F1: `{metrics['strike_f1']:.3f}`",
        f"- timing p95: `{metrics['timing_p95_ms']:.2f} ms`",
        f"- zone success: `{metrics['zone_success_rate']:.3f}`",
        f"- single F1: `{metrics['single_f1']:.3f}`",
        f"- strum events: `{metrics['strum_event_count']:.1f}`",
        f"- strum completion: `{metrics['strum_completion_rate']:.3f}`",
        f"- strum traversal recall: `{metrics['strum_traversal_recall']:.3f}`",
        f"- strum order accuracy: `{metrics['strum_order_accuracy']:.3f}`",
        f"- strum direction accuracy: `{metrics['strum_direction_accuracy']:.3f}`",
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
        sys.executable,
        str(PACKAGE_ROOT / "tools" / "plot_strike_training.py"),
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
        sys.executable,
        str(PACKAGE_ROOT / "tools" / "audit_strike_motion.py"),
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
    outputs = default_strike_video_paths(checkpoint)
    report = outputs["remembered"].with_name(
        f"{Path(checkpoint).stem}_rollout.json")
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
    artifacts = {**outputs, "report": report}
    return _run_logged_tool(layout, command, artifacts)


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
    torch = _load_strike_support_runtime()
    fixed_stage = args.curriculum_stage
    if args.no_curriculum and fixed_stage is None:
        fixed_stage = "A0_PICK_GRIP"
    goal_validation = validate_strike_goal_for_training(
        args.goal,
        STRIKE,
        require_a4=(
            # fixed_stage == "A4_ZONE_CONTROL"
            fixed_stage in SONG_GOAL_STAGES
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
        args.no_auto_video = True
    resources = training_resource_preflight(
        torch, args.device, layout.root, args.num_envs, smoke=args.smoke)
    layout = layout_for(out_dir, create=True)
    StrikeTask, ActorCritic, PPOConfig, PPOTrainer = (
        _load_strike_task_runtime())
    env = _create_task(StrikeTask, args)
    last_stats = {"value": None}
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
        validate_strike_training_alignment(env, ppo_config)
        trainer = PPOTrainer(env, model, ppo_config, out_dir=layout.root)
        contract_config = deepcopy(STRIKE)
        contract_config["grip_reference_path"] = str(args.grip_reference)
        checkpoint_contract = build_runtime_checkpoint_contract(
            env, model, args.goal, config=contract_config,
            ppo_config=vars(ppo_config))
        trainer.set_checkpoint_contract(checkpoint_contract)

        curriculum = build_strike_curriculum(STRIKE, args.num_envs)
        curriculum_runtime = StrikeCurriculumRuntime(
            curriculum,
            fixed_stage=fixed_stage,
            tolerance_ms=args.timing_tolerance_ms)

        if checkpoint is not None:
            curriculum_runtime.restore(
                checkpoint.get("training_context", {}))
            trainer.resume(
                checkpoint, purpose="evaluate" if args.eval else "resume")
        initial_state, reset_obs = curriculum_runtime.apply(env)
        if reset_obs is not None:
            trainer.obs = reset_obs
        trainer.training_context.update(initial_state)
        _write_run_metadata(
            layout, checkpoint_contract, args, resources,
            goal_validation)

        transition = {"value": None}

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
            return state

        def post_iteration(iteration, stats):
            last_stats["value"] = dict(stats)
            changed = transition["value"]
            saved = False
            if changed is not None:
                trainer.save(iteration)
                saved = True
                if changed["from"] != changed["to"]:
                    label = (
                        f"{changed['from']}_to_{changed['to']}")
                elif (not changed["from_complete"]
                      and changed["to_complete"]):
                    label = f"{changed['to']}_complete"
                else:
                    label = (
                        f"{changed['to']}_timing_"
                        f"{changed['from_tolerance_ms']:.0f}_to_"
                        f"{changed['to_tolerance_ms']:.0f}ms")
                target = layout.evaluations / (
                    f"curriculum_{iteration:06d}_{label}.json")
                target.write_text(
                    json.dumps({
                        "iteration": iteration,
                        **changed,
                        "stats": stats,
                        "curriculum": curriculum.state(),
                    }, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
                transition["value"] = None
            if _curriculum_stalled(stats):
                if not saved:
                    trainer.save(iteration)
                raise _StrikeCurriculumStalled(
                    f"strike curriculum stalled at iteration {iteration}")

        if not args.eval:
            try:
                trainer.learn(
                    args.iterations,
                    iteration_callback=before_iteration,
                    iteration_result_callback=after_result,
                    post_iteration_callback=post_iteration,
                    history_limit=0,
                )
            except _StrikeCurriculumStalled as exc:
                message = str(exc)
                with layout.training_log.open("a") as stream:
                    stream.write(message + "\n")
                print(message, flush=True)
        checkpoint_path = (
            layout.checkpoints / f"strike_{trainer.iteration:06d}.pt")
        if args.eval:
            checkpoint_path = Path(args.checkpoint)
        elif not checkpoint_path.is_file():
            raise RuntimeError(
                f"final strike checkpoint was not saved: {checkpoint_path}")

        base_artifacts = {
            "checkpoint": str(Path(checkpoint_path).resolve())}
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
            record_artifact_result(layout, evaluation_artifact)
        except Exception as exc:
            record_artifact_error(layout, "evaluation", exc)
            raise
    finally:
        env.close()

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
