"""왼손 fret 학습 내부 실행기.

예:
  python -m tab2body.train --task fret --iterations 5000
  python -m tab2body.train --task fret --smoke

사용자는 공용 ``train.py``를 호출한다. 이 모듈과 ``train_strike.py``는
동일한 ``build_parser()``/``main()`` runner 인터페이스를 제공한다.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.learning.checkpoint_contract import file_sha256


def _add_local_isaacgym_path():
    local_python = PROJECT_ROOT / "isaacgym" / "python"
    package = local_python / "isaacgym" / "__init__.py"
    if package.is_file() and str(local_python) not in sys.path:
        sys.path.insert(0, str(local_python))


def _load_fret_runtime():
    """Load the fret implementation only after public task dispatch.

    Isaac Gym must still precede torch for the fret runner, but a strike
    command must not initialize or depend on the left-hand task first.
    """
    global torch, FRET, FretTask, configured_kwargs
    global ActorCritic, FingertipApproachCurriculum
    global FingertipApproachCurriculumConfig, PPOConfig, PPOTrainer
    global configure_finger_flexion_policy
    global build_fret_contract_payload, fingerprint_file_set
    global seal_checkpoint_contract, evaluation_gate_summary
    global default_evaluation_path, default_video_path
    global has_training_history, layout_for, resolve_run_dir
    global record_artifact_error, record_artifact_result
    global record_run_metadata, shared_training_resource_preflight
    global utc_now_iso

    _add_local_isaacgym_path()
    import isaacgym  # noqa: F401
    import torch as torch_module

    from tab2body.cfg import FRET as fret_config
    from tab2body.env.tasks import FretTask as fret_task
    from tab2body.env.config import configured_kwargs as make_kwargs
    from tab2body.learning import (
        ActorCritic as actor_critic,
        FingertipApproachCurriculum as fingertip_curriculum,
        FingertipApproachCurriculumConfig as fingertip_curriculum_config,
        PPOConfig as ppo_config,
        PPOTrainer as ppo_trainer,
        configure_finger_flexion_policy as configure_flexion,
    )
    from tab2body.learning.checkpoint_contract import (
        build_fret_contract_payload as build_fret_payload,
        fingerprint_file_set as fingerprint_files,
        seal_checkpoint_contract as seal_contract,
    )
    from tab2body.learning.evaluation import (
        evaluation_gate_summary as fret_evaluation_gate_summary,
    )
    from tab2body.learning.run_layout import (
        default_evaluation_path as fret_default_evaluation_path,
        default_video_path as fret_default_video_path,
        has_training_history as run_has_training_history,
        layout_for as make_layout,
        resolve_run_dir as resolve_training_run_dir,
    )
    from tab2body.learning.run_io import (
        record_artifact_error as write_artifact_error,
        record_artifact_result as write_artifact_result,
        record_run_metadata as write_run_metadata,
        training_resource_preflight as shared_resource_preflight,
        utc_now_iso as current_utc_iso,
    )

    torch = torch_module
    FRET = fret_config
    FretTask = fret_task
    configured_kwargs = make_kwargs
    ActorCritic = actor_critic
    FingertipApproachCurriculum = fingertip_curriculum
    FingertipApproachCurriculumConfig = fingertip_curriculum_config
    PPOConfig = ppo_config
    PPOTrainer = ppo_trainer
    configure_finger_flexion_policy = configure_flexion
    build_fret_contract_payload = build_fret_payload
    fingerprint_file_set = fingerprint_files
    seal_checkpoint_contract = seal_contract
    evaluation_gate_summary = fret_evaluation_gate_summary
    default_evaluation_path = fret_default_evaluation_path
    default_video_path = fret_default_video_path
    has_training_history = run_has_training_history
    layout_for = make_layout
    resolve_run_dir = resolve_training_run_dir
    record_artifact_error = write_artifact_error
    record_artifact_result = write_artifact_result
    record_run_metadata = write_run_metadata
    shared_training_resource_preflight = shared_resource_preflight
    utc_now_iso = current_utc_iso


FRET_REWARD_SAFETY_KEYS = (
    "future_context_lookahead",
    "failure_termination_penalty",
    "wrist_weight", "smooth_weight",
    "wrong_press_penalty", "wrong_press_avoidance_weight",
    "wrong_press_termination_frames", "joint_limit_diagnostic_fraction",
    "press_near_miss_penalty", "press_near_miss_distance",
    "press_class_weight", "no_press_class_weight",
    "no_press_failure_credit", "press_hold_min_frames",
    "chord_bridge_bottleneck_weight",
    "chord_fine_joint_weight", "chord_fine_depth_start",
    "static_chord_bottleneck_weight", "static_chord_joint_weight",
    "static_chord_no_press_failure_credit",
    "static_chord_no_press_completion_power",
    "press_hold_full_frames", "press_dropout_penalty",
    "static_chord_min_duration_seconds",
    "press_position_dense_scale", "press_precision_gate_floor",
    "next_goal_weight", "goal_pair_transition_next_goal_weight",
    "goal_pair_context_next_goal_weight",
    "chord_fine_success_pose_guide_weight",
    "goal_pair_success_pose_guide_weight",
    "goal_pair_success_pose_focus_weight",
    "goal_pair_success_pose_proximal_fraction",
    "next_goal_lookahead_s",
    "next_goal_progress_weight",
    "next_goal_progress_near", "next_goal_progress_far",
    "next_goal_preservation_weight",
    "next_goal_unprotected_progress_scale",
    "goal_pair_transition_time_gate_floor",
    "next_goal_prepress_clearance",
    "finger_arch_reward_weight",
    "thumb_weight", "thumb_pad_radius",
    "thumb_approach_scale", "thumb_reach_scale",
    "thumb_contact_on_force", "thumb_contact_off_force",
    "thumb_force_soft_limit", "thumb_force_decay_scale",
    "thumb_compression_free_depth", "thumb_compression_decay_scale",
    "thumb_overforce_penalty", "thumb_gate_full_distance",
    "thumb_gate_zero_distance", "thumb_press_gate_weight",
    "thumb_base_saturation_threshold",
    "thumb_base_saturation_penalty_weight",
    "thumb_seed_action_limit",
    "thumb_force_termination_threshold",
    "thumb_compression_termination_threshold",
    "thumb_force_termination_frames",
    "proximal_weight", "proximal_transition",
    "isolated_press_lock_after_frames",
    "hover_weight", "hover_free_gap", "hover_decay_scale",
    "hover_position_weight", "hover_release_pose_weight",
    "hover_release_blend_time", "hover_release_relaxed_pip_deg",
    "hover_release_relaxed_dip_deg", "hover_release_tolerance_deg",
    "hover_free_outward_speed",
    "hover_speed_decay_scale", "hover_move_release_time",
    "finger_coupling_weight", "finger_coupling_coefficients",
    "finger_coupling_min_speed_deg", "finger_coupling_full_speed_deg",
    "finger_coupling_tolerance_deg_s",
    "reference_motion_prior_weight",
    "reference_motion_prior_finger_fraction",
    "reference_motion_prior_exemplars",
    "finger_synergy_coefficients", "finger_synergy_min_driver_delta_deg",
    "finger_synergy_full_driver_delta_deg",
    "finger_synergy_max_induced_delta_deg",
    "slip_weight", "slip_stable_frames", "slip_free_distance",
    "slip_decay_scale",
    "wrist_safety_bounds_min", "wrist_safety_bounds_max", "wrist_safety_frames",
    "finger_back_soft_limit_z", "finger_back_soft_scale",
    "finger_back_soft_penalty", "finger_back_limit_z",
    "finger_back_proximal_limit_z", "finger_back_frames",
    "finger_back_samples_per_segment", "finger_back_min_fraction",
    "palm_down_threshold", "palm_down_frames",
    "penetration_threshold", "penetration_frames",
    "penetration_soft_threshold", "penetration_soft_penalty",
    "penetration_termination",
    "finger_capsule_radius", "finger_overlap_tolerance",
    "sustain_boundary_grace_frames", "sustain_hold_threshold",
    "sustain_max_dropout_frames", "pressed_drag_threshold",
    "success_rsi_probability", "success_rsi_min_quality",
    "success_rsi_min_thumb_quality",
    "success_finger_pose_min_quality",
    "success_finger_pose_guide_scale_fraction",
    "success_action_teacher_min_pose_quality",
    "chord_fine_action_teacher_min_pose_quality",
    "success_action_teacher_proximal_fraction",
    "goal_pair_action_routing", "goal_pair_action_release_frames",
    "evaluation_f1_gate", "evaluation_no_press_accuracy_gate",
    "evaluation_wrong_press_rate_gate",
    "evaluation_max_finger_overlap_env_frames",
    "curriculum_settling_frames",
)

FRET_IMPLEMENTATION_FILES = (
    "cfg.py",
    "song_bundles.py",
    "train.py",
    "train_fret.py",
    "assets/guitar_asset.xml",
    "assets/smpl_mpl_hands_body.xml",
    "env/__init__.py",
    "env/base.py",
    "env/config.py",
    "env/collision.py",
    "env/goals.py",
    "env/metrics.py",
    "env/rewards/__init__.py",
    "env/rewards/common.py",
    "env/rewards/fret.py",
    "env/rewards/motion.py",
    "env/rewards/reference_posture.py",
    "env/rewards/thumb.py",
    "env/safety.py",
    "env/tasks/__init__.py",
    "env/tasks/task_fret.py",
    "learning/__init__.py",
    "learning/checkpoint_contract.py",
    "learning/curriculum.py",
    "learning/evaluation.py",
    "learning/models.py",
    "learning/ppo.py",
    "learning/run_io.py",
    "learning/run_layout.py",
)

FRET_THUMB_OBSERVATION_DIM = 6
THUMB_GEOMETRY_OBSERVATION_VERSION = 4
THUMB_SUPPORT_SEED_VERSION = 3


def thumb_base_exploration_floor(
        iteration, initial_std, target_std, warmup_iterations,
        ramp_iterations):
    """Keep the inherited policy stable, then raise thumb-base exploration."""
    initial_std = float(initial_std)
    target_std = float(target_std)
    warmup_iterations = int(warmup_iterations)
    ramp_iterations = int(ramp_iterations)
    if (not math.isfinite(initial_std) or not math.isfinite(target_std)
            or initial_std <= 0.0 or target_std < initial_std):
        raise ValueError("thumb exploration std schedule is invalid")
    if warmup_iterations < 0 or ramp_iterations < 1:
        raise ValueError("thumb exploration iteration schedule is invalid")
    progress = min(max(
        (int(iteration) - warmup_iterations) / float(ramp_iterations),
        0.0), 1.0)
    return initial_std + progress * (target_std - initial_std)


def finger_exploration_ceiling(
        iteration, initial_std, target_std, warmup_iterations,
        ramp_iterations):
    """정밀 코드 단계가 진행될수록 손가락 탐색 분산을 줄인다."""
    initial_std = float(initial_std)
    target_std = float(target_std)
    warmup_iterations = int(warmup_iterations)
    ramp_iterations = int(ramp_iterations)
    if (not math.isfinite(initial_std) or not math.isfinite(target_std)
            or not 0.0 < target_std <= initial_std):
        raise ValueError("finger exploration std schedule is invalid")
    if warmup_iterations < 0 or ramp_iterations < 1:
        raise ValueError("finger exploration iteration schedule is invalid")
    progress = min(max(
        (int(iteration) - warmup_iterations) / float(ramp_iterations),
        0.0), 1.0)
    return initial_std + progress * (target_std - initial_std)


FINGER_PRECISION_STAGES = {
    "chord_fine_reach", "static_chord", "frozen_context", "goal_pair",
    "transition_window", "coverage", "integration", "full_song",
}


def finger_precision_schedule(state):
    """Return whether precision annealing is active, its age, and focus fingers."""
    stage = str(state.get("curriculum_stage", ""))
    if stage not in FINGER_PRECISION_STAGES:
        return False, 0, ()
    age = max(0, int(state.get(
        "curriculum_chord_focus_total_iteration", 0)))
    if stage != "chord_fine_reach":
        age += max(0, int(state.get("curriculum_stage_iteration", 0)))
    focus = ()
    if stage == "chord_fine_reach":
        index = int(state.get("curriculum_chord_focus_index", -1))
        catalog = state.get("curriculum_chord_available_sets", ())
        if 0 <= index < len(catalog):
            focus = tuple(int(finger) for finger in catalog[index])
    elif stage == "frozen_context":
        finger = int(state.get(
            "curriculum_frozen_context_focus_finger", 0))
        focus = (finger,) if 1 <= finger <= 4 else ()
    elif stage == "goal_pair":
        finger = int(state.get("curriculum_goal_pair_focus_finger", 0))
        focus = (finger,) if 1 <= finger <= 4 else ()
    return True, age, focus


def summarize_goal_finger_coverage(goals):
    """Summarize whether one song can exercise all four fretting fingers."""
    fret = goals.fret.detach().cpu()
    finger = goals.finger.detach().cpu()
    events = tuple(getattr(goals, "sustain_events", ()))
    stable_chords = getattr(
        goals, "practice_chord_frames_by_finger_set", {})
    names = ("index", "middle", "ring", "pinky")
    rows = {}
    active_counts = []
    for finger_number, name in enumerate(names, start=1):
        active = ((fret > 0) & (finger == finger_number)).any(dim=1)
        active_frames = int(active.sum().item())
        active_counts.append(active_frames)
        starts = sum(
            int(event.get("finger", 0)) == finger_number
            for event in events)
        targets = sorted({
            (int(event["string"]), int(event["fret"]))
            for event in events
            if int(event.get("finger", 0)) == finger_number
        })
        stable_runs = sum(
            int(catalog.numel())
            for finger_set, catalog in stable_chords.items()
            if finger_number in finger_set)
        rows[name] = {
            "finger": finger_number,
            "active_frames": active_frames,
            "press_start_events": starts,
            "unique_string_fret_targets": [list(target) for target in targets],
            "stable_chord_runs": stable_runs,
        }
    maximum = max(active_counts, default=0)
    underrepresented = [
        name for name, row in rows.items()
        if (row["active_frames"] == 0
            or (maximum > 0 and row["active_frames"] < 0.20 * maximum)
            or row["press_start_events"] < 5
            or row["stable_chord_runs"] == 0)
    ]
    return {
        "fingers": rows,
        "active_frame_imbalance_ratio": (
            float(maximum) / max(1.0, float(min(
                (count for count in active_counts if count > 0),
                default=1)))),
        "underrepresented_fingers": underrepresented,
        "warning": bool(underrepresented),
    }


def load_fret_initialization_model(
        model, checkpoint_state,
        appended_obs_dim=FRET_THUMB_OBSERVATION_DIM,
        calibration_observations=None):
    """Strictly warm-start a fret model with appended observation blocks."""
    if not isinstance(checkpoint_state, Mapping):
        raise TypeError("initialization model state must be a mapping")
    appended_obs_dim = int(appended_obs_dim)
    if appended_obs_dim <= 0:
        raise ValueError("appended observation block must be positive")

    target_state = model.state_dict()
    source_keys = set(checkpoint_state)
    target_keys = set(target_state)
    if source_keys != target_keys:
        missing = sorted(target_keys - source_keys)
        unexpected = sorted(source_keys - target_keys)
        raise ValueError(
            "initialization model keys do not match current policy: "
            f"missing={missing}, unexpected={unexpected}")

    rms_keys = ("obs_rms.mean", "obs_rms.var")
    input_weight_keys = ("actor.0.weight", "critic.0.weight")
    source_mean = checkpoint_state[rms_keys[0]]
    target_mean = target_state[rms_keys[0]]
    if source_mean.ndim != 1 or target_mean.ndim != 1:
        raise ValueError("observation RMS mean must be one-dimensional")
    source_obs_dim = int(source_mean.numel())
    target_obs_dim = int(target_mean.numel())
    if source_obs_dim == target_obs_dim:
        model.load_state_dict(checkpoint_state, strict=True)
        return {
            "expanded": False,
            "source_obs_dim": source_obs_dim,
            "target_obs_dim": target_obs_dim,
        }
    appended = target_obs_dim - source_obs_dim
    if (appended <= 0 or appended % appended_obs_dim != 0
            or appended > 2 * appended_obs_dim):
        raise ValueError(
            "initialization observation dimension is incompatible: "
            f"checkpoint={source_obs_dim}, current={target_obs_dim}, "
            f"expected 1-2 appended blocks of {appended_obs_dim}")

    calibration_mean = None
    calibration_var = None
    if calibration_observations is not None:
        if hasattr(calibration_observations, "detach"):
            calibration = calibration_observations.detach().to(
                device=target_mean.device, dtype=target_mean.dtype)
        else:
            calibration = target_mean.new_tensor(calibration_observations)
        if calibration.ndim < 2:
            raise ValueError(
                "observation calibration must contain a batch dimension")
        calibration = calibration.reshape(-1, calibration.shape[-1])
        if calibration.shape[0] < 2:
            raise ValueError(
                "observation calibration requires at least two samples")
        if calibration.shape[1] == target_obs_dim:
            calibration = calibration[:, source_obs_dim:]
        elif calibration.shape[1] != appended:
            raise ValueError(
                "observation calibration width must match the target "
                "observation or appended suffix")
        if not calibration.isfinite().all():
            raise ValueError("observation calibration must be finite")
        calibration_mean = calibration.mean(dim=0)
        calibration_var = calibration.var(
            dim=0, unbiased=False).clamp_min(1e-8)

    expanded = {}
    for key, target in target_state.items():
        source = checkpoint_state[key]
        if key in rms_keys:
            if (source.ndim != 1 or target.ndim != 1
                    or source.numel() != source_obs_dim
                    or target.numel() != target_obs_dim):
                raise ValueError(
                    f"{key} does not match the observation dimensions")
            value = (
                target.new_zeros(target.shape)
                if key.endswith(".mean")
                else target.new_ones(target.shape))
            value[:source_obs_dim].copy_(
                source.to(device=target.device, dtype=target.dtype))
            if calibration_mean is not None:
                suffix = (
                    calibration_mean
                    if key.endswith(".mean") else calibration_var)
                value[source_obs_dim:].copy_(
                    suffix.to(device=target.device, dtype=target.dtype))
        elif key in input_weight_keys:
            if (source.ndim != 2 or target.ndim != 2
                    or source.shape[0] != target.shape[0]
                    or source.shape[1] != source_obs_dim
                    or target.shape[1] != target_obs_dim):
                raise ValueError(
                    f"{key} cannot be expanded along its observation axis")
            value = target.new_zeros(target.shape)
            value[:, :source_obs_dim].copy_(
                source.to(device=target.device, dtype=target.dtype))
        else:
            if source.shape != target.shape:
                raise ValueError(
                    f"initialization tensor shape changed outside the "
                    f"observation prefix: {key} {tuple(source.shape)} != "
                    f"{tuple(target.shape)}")
            value = source.detach().clone()
        expanded[key] = value

    model.load_state_dict(expanded, strict=True)
    return {
        "expanded": True,
        "source_obs_dim": source_obs_dim,
        "target_obs_dim": target_obs_dim,
    }


def _configure_initial_policy(model, env, *, seed_mean, repair_thumb_base):
    controlled_names = [
        env.dof_names[index]
        for index in env.ctrl_idx.detach().cpu().tolist()]
    configure_finger_flexion_policy(
        model, controlled_names,
        env.ctrl_mid[0], env.ctrl_half[0], env.action_scale,
        FRET["articulation_flexion_init_std"],
        FRET["articulation_seed_pip_deg"],
        FRET["articulation_seed_dip_deg"],
        seed_mean=seed_mean,
        thumb_exploration_std=FRET["thumb_exploration_init_std"],
        thumb_base_exploration_std=FRET["thumb_base_exploration_init_std"],
        repair_saturated_thumb_base=repair_thumb_base,
        thumb_base_action_limit=FRET["thumb_seed_action_limit"],
    )


def _initial_policy_context():
    return {
        "curriculum_schema_version":
            FingertipApproachCurriculum.SCHEMA_VERSION,
        "finger_flexion_initialized": True,
        "articulation_flexion_init_std":
            FRET["articulation_flexion_init_std"],
        "thumb_exploration_init_std": FRET["thumb_exploration_init_std"],
        "thumb_base_exploration_init_std":
            FRET["thumb_base_exploration_init_std"],
        "thumb_base_exploration_target_std":
            FRET["thumb_base_exploration_target_std"],
        "thumb_support_seed_version": THUMB_SUPPORT_SEED_VERSION,
        "thumb_geometry_observation_version":
            THUMB_GEOMETRY_OBSERVATION_VERSION,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="left-hand fret physics-RL training")
    parser.add_argument("--goal", default=FRET["goal_path"])
    parser.add_argument(
        "--song", default=None,
        help="data/song_bundles 아래의 song_id; 지정하면 해당 fret 입력을 사용")
    parser.add_argument("--hand-targets", default=None,
                        help="미지정 시 goal 옆의 같은 이름 hand target을 자동 탐색")
    parser.add_argument("--num-envs", type=int, default=FRET["num_envs"])
    parser.add_argument("--device", default=FRET["device"])
    parser.add_argument("--iterations", type=int, default=FRET["iterations"])
    parser.add_argument("--minibatch-size", type=int,
                        default=FRET["ppo"]["minibatch_size"])
    parser.add_argument("--seed", type=int, default=FRET["seed"])
    parser.add_argument("--out", default=None,
                        help="실행 루트 직접 지정; --run-name과 함께 사용 불가")
    parser.add_argument(
        "--run-name", default=None,
        help=("fret/training/runs 아래의 실험 이름 "
              "(기본값: YYYYMMDD_HHMM_노래이름)"))
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument(
        "--migrate-contract", action="store_true",
        help="checkpoint의 상태를 새 계약으로 명시적으로 마이그레이션해 resume")
    parser.add_argument("--initialize-from", default=None,
                        help="이전 checkpoint의 정책 가중치만 가져와 새 계약으로 학습")
    parser.add_argument(
        "--initialize-optimizer", action="store_true",
        help="--initialize-from 사용 시 호환되는 PPO optimizer 상태도 warm-start")
    parser.add_argument("--eval", action="store_true",
                        help="checkpoint를 deterministic full-song episode로 평가")
    parser.add_argument("--eval-episodes", type=int, default=1)
    parser.add_argument("--eval-out", default=None)
    parser.add_argument("--no-random-start", action="store_true")
    parser.add_argument("--no-curriculum", action="store_true",
                        help="손끝 접근 및 곡별 시간 커리큘럼 비활성")
    parser.add_argument("--curriculum-stage",
                        choices=FingertipApproachCurriculum.STAGES, default=None,
                        help="자동 스케줄 대신 한 단계로 고정")
    parser.add_argument("--coverage-iterations", type=int,
                        default=FRET["curriculum"]["coverage_iterations"])
    parser.add_argument("--integration-iterations", type=int,
                        default=FRET["curriculum"]["integration_iterations"])
    parser.add_argument("--preparation-seconds", type=float,
                        default=FRET["preparation_frames"] / 60.0,
                        help="goal clock을 멈추고 선택된 첫 목표에 접근하는 시간")
    parser.add_argument("--smoke", action="store_true",
                        help="8 env × 4 steps × 1 update로 전체 배관 검증")
    parser.add_argument("--no-auto-video", action="store_true",
                        help="주기적 영상과 학습 종료 후 최종 영상 생성을 모두 건너뜀")
    parser.add_argument("--video-interval", type=int,
                        default=FRET["video_interval"],
                        help="rollout 영상을 만들 epoch 간격; 0이면 주기 영상 비활성")
    return parser


def goal_identity(path):
    from tab2body.song_bundles import song_id_from_training_path

    path = Path(path).resolve()
    digest = file_sha256(path)
    suffix = ".fret_training.json"
    song_id = song_id_from_training_path(path, suffix)
    return path, song_id, digest


def canonical_song_bundle_for_goal(path):
    from tab2body.song_bundles import SONG_BUNDLES_ROOT

    path = Path(path).resolve()
    root = SONG_BUNDLES_ROOT.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
    if len(relative.parts) < 3:
        return None
    return root / relative.parts[0]


def resolve_hand_targets(goal_path, explicit=None):
    if explicit:
        path = Path(explicit).resolve()
        if not path.exists():
            raise FileNotFoundError(f"hand target not found: {path}")
        return str(path)
    if goal_path.name == "fret_training.json":
        candidate = goal_path.with_name("hand_position_targets.json")
        if candidate.exists():
            return str(candidate)
    suffix = ".fret_training.json"
    if goal_path.name.endswith(suffix):
        candidate = goal_path.with_name(
            goal_path.name[:-len(suffix)] + ".hand_position_targets.json")
        if candidate.exists():
            return str(candidate)
    default_goal = Path(FRET["goal_path"]).resolve()
    default_hand = Path(FRET["hand_targets_path"]).resolve()
    if goal_path == default_goal and default_hand.exists():
        return str(default_hand)
    return None


def resolve_out_dir(song_id, explicit=None, run_name=None, checkpoint=None):
    workspace_root = Path(__file__).resolve().parent.parent
    return str(resolve_run_dir(
        workspace_root, song_id, explicit=explicit, run_name=run_name,
        checkpoint=checkpoint))


def protect_new_run_output(out_dir, checkpoint=None, evaluating=False):
    """Refuse to mix a fresh experiment into an existing checkpoint history."""
    if checkpoint or evaluating:
        return
    layout = layout_for(out_dir)
    if has_training_history(layout):
        raise FileExistsError(
            f"training output already contains a run: {layout.root}. "
            "Resume it with --checkpoint or choose a new --run-name/--out.")


def generate_training_plots(layout):
    """Render the standard plots from the run's append-only metric log."""
    plot_specs = (
        ("training_curves", "plot_fret_training.py", "training_curves.png"),
        ("fingertip_curriculum", "plot_fingertip_curriculum.py",
         "fingertip_curriculum.png"),
        ("fret_diagnostics", "plot_fret_diagnostics.py",
         "fret_diagnostics.png"),
    )
    generated = {}
    for key, script, filename in plot_specs:
        output = layout.plots / filename
        command = [
            sys.executable,
            str(Path(__file__).resolve().parent / "tools" / script),
            str(layout.metrics), "--out", str(output),
        ]
        with layout.artifact_log.open("a") as stream:
            stream.write(f"\n[plot:{key}] {' '.join(command)}\n")
            stream.flush()
            subprocess.run(
                command, check=True, stdout=stream,
                stderr=subprocess.STDOUT)
        generated[key] = str(output.resolve())
        if key == "fret_diagnostics":
            summary = output.with_suffix(".summary.json")
            if summary.is_file():
                generated["fret_diagnostics_summary"] = str(
                    summary.resolve())
    return generated


def rollout_video_command(checkpoint, goal_path, hand_targets_path,
                          preparation_frames):
    command = [
        sys.executable,
        str(PACKAGE_ROOT / "tools" / "record_fret_rollout.py"),
        "--checkpoint", str(checkpoint),
        "--goal", str(goal_path),
        "--show-frets", "--view", "closeup",
        "--camera-distance-scale", "1.25",
        "--preparation-seconds", str(preparation_frames / 60.0),
    ]
    if hand_targets_path is not None:
        command += ["--hand-targets", str(hand_targets_path)]
    if goal_path.name == "fret_training.json":
        audio_path = goal_path.parent.parent / "source" / "audio.wav"
    else:
        audio_path = goal_path.with_name(
            goal_path.name.replace(".fret_training.json", "_mic.wav"))
    if audio_path.exists():
        command += ["--audio", str(audio_path)]
    return command


def generate_rollout_video(layout, checkpoint, goal_path, hand_targets_path,
                           preparation_frames, label):
    output = default_video_path(checkpoint)
    report = output.with_suffix(".stability.json")
    if output.exists() and report.exists():
        frames_dir = output.with_suffix("") / "frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
        try:
            frames_dir.parent.rmdir()
        except OSError:
            pass
        return str(output.resolve())
    command = rollout_video_command(
        checkpoint, goal_path, hand_targets_path, preparation_frames)
    with layout.artifact_log.open("a") as stream:
        stream.write(f"\n[{label}] {' '.join(command)}\n")
        stream.flush()
        subprocess.run(
            command, check=True, stdout=stream, stderr=subprocess.STDOUT,
            cwd=PROJECT_ROOT)
    return str(output.resolve())


def training_resource_preflight(device, out_dir, num_envs):
    """공용 검증기로 fret 학습 전 GPU·RAM·디스크 여유를 확인한다."""
    return shared_training_resource_preflight(
        torch, device, out_dir, num_envs, FRET["resource_guard"],
        task_name="fret")


def build_runtime_checkpoint_contract(env, model, trainer, *, goal_sha256,
                                      hand_targets_sha256, preparation_frames):
    """Seal every semantic input needed to safely reuse a fret policy."""
    tab2body_root = Path(__file__).resolve().parent
    asset_fingerprint = fingerprint_file_set(
        tab2body_root, ("assets", "_gen/mjcf_gains.json"))
    implementation_fingerprint = fingerprint_file_set(
        tab2body_root, FRET_IMPLEMENTATION_FILES)
    reward_safety = {key: FRET[key] for key in FRET_REWARD_SAFETY_KEYS}
    reward_safety["reference_motion_prior_sha256"] = file_sha256(
        FRET["reference_motion_prior_path"])
    reward_safety["preparation_frames"] = int(preparation_frames)
    reward_safety["fingertip_approach_curriculum"] = FRET["curriculum"]
    controlled_names = [
        env.dof_names[index] for index in env.ctrl_idx.detach().cpu().tolist()]
    active_string_mask = (
        (env.goals.fret != 0).any(dim=0).detach().cpu().tolist())
    initial_std = model.log_std.detach().exp().cpu()
    if initial_std.numel() != env.num_actions or not torch.allclose(
            initial_std, initial_std[:1].expand_as(initial_std)):
        raise ValueError(
            "fret checkpoint contract currently requires one shared policy init_std")
    payload = build_fret_contract_payload(
        controlled_dof_names=controlled_names,
        num_obs=env.num_obs,
        num_actions=env.num_actions,
        value_dim=env.value_dim,
        action_scale=env.action_scale,
        action_alpha=env.action_alpha,
        reset_soft_limit_fraction=getattr(
            env, "reset_soft_limit_fraction",
            FRET.get("reset_soft_limit_fraction", 0.0)),
        policy_init_std=float(initial_std[0]),
        raw_reward_weights=env.reward_weights.detach().cpu().tolist(),
        active_string_mask=active_string_mask,
        actor_reward_weights=trainer.actor_reward_weights.detach().cpu().tolist(),
        reward_safety_config=reward_safety,
        ppo_config=vars(trainer.cfg),
        preparation_frames=preparation_frames,
        sim_hz=env.SIM_HZ,
        sim_substeps=env.SUBSTEPS,
        goal_sha256=goal_sha256,
        hand_targets_sha256=hand_targets_sha256,
        asset_fingerprint=asset_fingerprint,
        implementation_fingerprint=implementation_fingerprint,
        policy_distribution_version=getattr(
            model, "POLICY_DISTRIBUTION_VERSION",
            "diagonal_gaussian_policy_implementation_fingerprinted.v1"),
    )
    return seal_checkpoint_contract(payload)


def evaluate(env, model, episodes):
    obs = env.reset()
    rows = []
    target_distance_sum = 0.0
    active_count = 0.0
    wrist_distance_sum = 0.0
    press_depth_sum = 0.0
    press_depth_progress_sum = 0.0
    position_quality_sum = 0.0
    arch_quality_sum = 0.0
    good_position_quality_sum = 0.0
    mcp_flexion_sum = 0.0
    pip_flexion_sum = 0.0
    dip_flexion_sum = 0.0
    tip_contact_sum = 0.0
    non_tip_contact_sum = 0.0
    press_success_sum = 0.0
    all_correct_sum = 0.0
    thumb_reward_sum = 0.0
    thumb_distance_sum = 0.0
    thumb_gap_sum = 0.0
    thumb_force_sum = 0.0
    thumb_contact_sum = 0.0
    thumb_in_back_region_sum = 0.0
    thumb_support_sum = 0.0
    thumb_support_stable_6_sum = 0.0
    thumb_support_stable_12_sum = 0.0
    thumb_wrong_contact_sum = 0.0
    thumb_force_quality_sum = 0.0
    thumb_overforce_sum = 0.0
    thumb_goal_gate_sum = 0.0
    thumb_press_readiness_sum = 0.0
    thumb_base_action_saturation_sum = 0.0
    thumb_eligible_count = 0
    thumb_eligible_support_sum = 0.0
    thumb_eligible_stable_6_sum = 0.0
    max_thumb_contact_force = 0.0
    thumb_overforce_termination_count = 0
    wrong_press_termination_count = 0
    joint_limit_group_names = tuple(env.joint_limit_group_names)
    joint_limit_max_usage = 0.0
    joint_limit_near_sum = 0.0
    joint_limit_max_by_group = {
        group: 0.0 for group in joint_limit_group_names}
    joint_limit_near_sum_by_group = {
        group: 0.0 for group in joint_limit_group_names}
    proximal_reward_sum = 0.0
    proximal_gate_sum = 0.0
    finger_motion_sum = 0.0
    wrist_motion_sum = 0.0
    elbow_motion_sum = 0.0
    shoulder_motion_sum = 0.0
    hover_reward_sum = 0.0
    hover_reward_count = 0
    hover_gap_sum = 0.0
    hover_gate_count = 0
    hover_velocity_reward_sum = 0.0
    hover_velocity_env_count = 0
    hover_outward_speed_sum = 0.0
    hover_velocity_gate_count = 0
    max_hover_outward_speed = 0.0
    slip_reward_sum = 0.0
    slip_reward_count = 0
    slip_distance_sum = 0.0
    slip_gate_count = 0
    max_slip_distance = 0.0
    finger_overlap_env_frames = 0
    finger_initial_overlap_count = 0
    max_finger_penetration = 0.0
    max_support_contact_force = 0.0
    max_inactive_distal_force = 0.0
    max_control_torque_fraction = 0.0
    palm_down_termination_count = 0
    wrist_safety_termination_count = 0
    finger_back_termination_count = 0
    finger_back_termination_by_finger = [0, 0, 0, 0]
    finger_back_min_local_z_by_finger = [float("inf")] * 4
    max_guitar_penetration = 0.0
    max_guitar_swept_penetration = 0.0
    guitar_tunneled_count = 0
    guitar_initial_overlap_count = 0
    guitar_penetration_termination_count = 0
    guitar_penetration_termination_by_chain = [
        0 for _ in env.penetration_monitor.CHAIN_NAMES]
    failure_termination_count = 0
    nonfinite_termination_count = 0
    velocity_blowup_termination_count = 0
    reward_sum = 0.0
    diagnostic_count = 0
    goal_diagnostic_count = 0
    max_steps = ((env.goals.n_frames + env.preparation_frames)
                 * (episodes // env.num_envs + 2))
    for _ in range(max_steps):
        action, _, _ = model.act(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        live = info["goal_metrics_enabled"].float()
        active = info["active_count"].float() * live
        target_distance_sum += float((info["mean_target_distance"] * active).sum().cpu())
        active_count += float(active.sum().cpu())
        press_depth_sum += float((info["mean_press_depth"] * active).sum().cpu())
        press_depth_progress_sum += float(
            (info["mean_press_depth_progress"] * active).sum().cpu())
        position_quality_sum += float((info["mean_position_quality"] * active).sum().cpu())
        arch_quality_sum += float((info["mean_arch_quality"] * active).sum().cpu())
        good_position_quality_sum += float(
            (info["mean_good_position_quality"] * active).sum().cpu())
        mcp_flexion_sum += float(
            (info["mean_mcp_flexion_deg"] * active).sum().cpu())
        pip_flexion_sum += float(
            (info["mean_pip_flexion_deg"] * active).sum().cpu())
        dip_flexion_sum += float(
            (info["mean_dip_flexion_deg"] * active).sum().cpu())
        tip_contact_sum += float((info["tip_contact_rate"] * active).sum().cpu())
        non_tip_contact_sum += float(
            (info["non_tip_contact_rate"] * active).sum().cpu())
        press_success_sum += float((info["press_success_rate"] * active).sum().cpu())
        wrist_distance_sum += float((info["wrist_distance"] * live).sum().cpu())
        all_correct_sum += float((info["all_correct"].float() * live).sum().cpu())
        thumb_reward_sum += float((info["thumb_reward"] * live).sum().cpu())
        thumb_distance_sum += float((info["thumb_distance"] * live).sum().cpu())
        thumb_gap_sum += float((info["thumb_gap"] * live).sum().cpu())
        thumb_force_sum += float(
            (info["thumb_contact_force"] * live).sum().cpu())
        thumb_contact_sum += float(
            (info["thumb_contact"].float() * live).sum().cpu())
        thumb_in_back_region_sum += float(
            (info["thumb_in_back_region"].float() * live).sum().cpu())
        thumb_support_sum += float(
            (info["thumb_support"].float() * live).sum().cpu())
        thumb_support_stable_6_sum += float(
            (info["thumb_support_stable_6"].float() * live).sum().cpu())
        thumb_support_stable_12_sum += float(
            (info["thumb_support_stable_12"].float() * live).sum().cpu())
        thumb_wrong_contact_sum += float(
            (info["thumb_wrong_contact"].float() * live).sum().cpu())
        thumb_force_quality_sum += float(
            (info["thumb_force_quality"] * live).sum().cpu())
        thumb_overforce_sum += float(
            (info["thumb_overforce"] * live).sum().cpu())
        thumb_goal_gate_sum += float(
            (info["thumb_goal_gate"] * live).sum().cpu())
        thumb_press_readiness_sum += float(
            (info["thumb_press_readiness"] * live).sum().cpu())
        thumb_base_action_saturation_sum += float(
            (info["thumb_base_action_saturation"] * live).sum().cpu())
        thumb_eligible = (info["thumb_goal_gate"] >= 0.5) & live.bool()
        thumb_eligible_count += int(thumb_eligible.sum().cpu())
        thumb_eligible_support_sum += float(
            info["thumb_support"][thumb_eligible].float().sum().cpu())
        thumb_eligible_stable_6_sum += float(
            info["thumb_support_stable_6"][
                thumb_eligible].float().sum().cpu())
        max_thumb_contact_force = max(
            max_thumb_contact_force,
            float(info["thumb_contact_force"].max().cpu()))
        thumb_overforce_termination_count += int(
            info["thumb_overforce_termination"].sum().cpu())
        wrong_press_termination_count += int(
            info["wrong_press_termination"].sum().cpu())
        if live.any():
            joint_limit_max_usage = max(
                joint_limit_max_usage,
                float(info["joint_limit_max_usage"][live.bool()].max().cpu()))
        joint_limit_near_sum += float(
            (info["joint_limit_near_rate"] * live).sum().cpu())
        for group in joint_limit_group_names:
            group_max = info[f"joint_limit_{group}_max_usage"]
            if live.any():
                joint_limit_max_by_group[group] = max(
                    joint_limit_max_by_group[group],
                    float(group_max[live.bool()].max().cpu()))
            joint_limit_near_sum_by_group[group] += float(
                (info[f"joint_limit_{group}_near_rate"] * live).sum().cpu())
        proximal_reward_sum += float(info["proximal_reward"].sum().cpu())
        proximal_gate_sum += float(info["proximal_gate"].sum().cpu())
        finger_motion_sum += float(info["finger_motion"].sum().cpu())
        wrist_motion_sum += float(info["wrist_motion"].sum().cpu())
        elbow_motion_sum += float(info["elbow_motion"].sum().cpu())
        shoulder_motion_sum += float(info["shoulder_motion"].sum().cpu())
        hover_gate = info["hover_gate"]
        hover_env_gate = hover_gate.any(dim=1)
        hover_reward_sum += float(info["hover_reward"][hover_env_gate].sum().cpu())
        hover_reward_count += int(hover_env_gate.sum().cpu())
        hover_gap_sum += float((info["hover_gap"] * hover_gate.float()).sum().cpu())
        hover_gate_count += int(hover_gate.sum().cpu())
        hover_velocity_gate = info["hover_velocity_gate"]
        hover_velocity_env_gate = hover_velocity_gate.any(dim=1)
        hover_velocity_reward_sum += float(
            info["hover_velocity_reward"][hover_velocity_env_gate].sum().cpu())
        hover_velocity_env_count += int(hover_velocity_env_gate.sum().cpu())
        hover_outward_speed_sum += float(
            (info["hover_outward_speed"]
             * hover_velocity_gate.float()).sum().cpu())
        hover_velocity_gate_count += int(hover_velocity_gate.sum().cpu())
        if hover_velocity_gate.any():
            max_hover_outward_speed = max(
                max_hover_outward_speed,
                float(info["hover_outward_speed"][hover_velocity_gate].max().cpu()))
        slip_gate = info["slip_gate"]
        slip_env_gate = slip_gate.any(dim=1)
        slip_reward_sum += float(info["slip_reward"][slip_env_gate].sum().cpu())
        slip_reward_count += int(slip_env_gate.sum().cpu())
        slip_distance_sum += float(
            (info["slip_distance"] * slip_gate.float()).sum().cpu())
        slip_gate_count += int(slip_gate.sum().cpu())
        if slip_gate.any():
            max_slip_distance = max(
                max_slip_distance,
                float(info["slip_distance"][slip_gate].max().cpu()))
        finger_overlap_env_frames += int(
            (info["finger_overlapping_pair_count"] > 0).sum().cpu())
        finger_initial_overlap_count += int(info["finger_initial_overlap"].sum().cpu())
        max_finger_penetration = max(
            max_finger_penetration,
            float(info["finger_max_penetration"].max().cpu()))
        max_support_contact_force = max(
            max_support_contact_force,
            float(info["r24_support_contact_force"].max().cpu()))
        max_inactive_distal_force = max(
            max_inactive_distal_force,
            float(info["r24_inactive_distal_force"].max().cpu()))
        max_control_torque_fraction = max(
            max_control_torque_fraction,
            float(info["r24_max_control_torque_fraction"].max().cpu()))
        palm_down_termination_count += int(info["palm_down_termination"].sum().cpu())
        wrist_safety_termination_count += int(
            info["wrist_safety_termination"].sum().cpu())
        finger_back_termination_count += int(
            info["finger_back_termination"].sum().cpu())
        termination_by_finger = info["finger_back_termination_by_finger"]
        minimum_by_finger = info["finger_back_min_local_z"].amin(dim=0)
        for finger_index in range(4):
            finger_back_termination_by_finger[finger_index] += int(
                termination_by_finger[:, finger_index].sum().cpu())
            finger_back_min_local_z_by_finger[finger_index] = min(
                finger_back_min_local_z_by_finger[finger_index],
                float(minimum_by_finger[finger_index].cpu()))
        max_guitar_penetration = max(
            max_guitar_penetration,
            float(info["guitar_penetration_depth"].max().cpu()))
        max_guitar_swept_penetration = max(
            max_guitar_swept_penetration,
            float(info["guitar_swept_penetration_depth"].max().cpu()))
        guitar_tunneled_count += int(info["guitar_tunneled"].sum().cpu())
        guitar_initial_overlap_count += int(info["guitar_initial_overlap"].sum().cpu())
        guitar_penetration_termination_count += int(
            info["guitar_penetration_termination"].sum().cpu())
        termination_by_chain = info[
            "guitar_penetration_termination_by_chain"]
        for chain_index in range(
                len(guitar_penetration_termination_by_chain)):
            guitar_penetration_termination_by_chain[chain_index] += int(
                termination_by_chain[:, chain_index].sum().cpu())
        failure_termination_count += int(info["failure_termination"].sum().cpu())
        nonfinite_termination_count += int(info["nonfinite"].sum().cpu())
        velocity_blowup_termination_count += int(
            info["velocity_blowup"].sum().cpu())
        reward_sum += float(reward.mean(dim=1).sum().cpu())
        diagnostic_count += env.num_envs
        goal_diagnostic_count += int(live.sum().cpu())
        if info["f1_l"].numel():
            done_ids = torch.nonzero(done).squeeze(-1)
            if done_ids.numel() != info["f1_l"].numel():
                raise RuntimeError("episode metrics are not aligned with done environments")
            for i, env_id in enumerate(done_ids.tolist()):
                metric_keys = (
                    "accuracy_l", "precision_l", "recall_l", "f1_l",
                    "no_press_accuracy", "wrong_press_rate",
                    "sustain_hold_rate", "sustain_event_success_rate",
                    "sustain_event_success_count",
                    "sustain_min_event_hold_rate",
                    "sustain_max_dropout_frames",
                    "sustain_interruption_count", "sustain_event_count",
                    "chord_ready_rate", "chord_hold_quality",
                    "press_dropout_rate", "press_max_dropout_frames",
                    *(f"press_finger_{finger}_{field}"
                      for finger in range(1, 5)
                      for field in ("success", "count")),
                )
                row = {
                    key: float(info[key][i].cpu())
                    for key in metric_keys}
                row.update(
                    goal_finished=bool(info["goal_finished"][env_id].item()),
                    failure_termination=bool(
                        info["failure_termination"][env_id].item()),
                    timeout=bool(info["timeout"][env_id].item()),
                    nonfinite=bool(info["nonfinite"][env_id].item()),
                    velocity_blowup=bool(info["velocity_blowup"][env_id].item()),
                )
                rows.append(row)
                if len(rows) >= episodes:
                    break
        if len(rows) >= episodes:
            break
    if not rows:
        raise RuntimeError("evaluation produced no completed episodes")
    result = {k: sum(x[k] for x in rows) / len(rows)
              for k in ("accuracy_l", "precision_l", "recall_l", "f1_l",
                        "no_press_accuracy", "wrong_press_rate",
                        "sustain_hold_rate", "sustain_event_success_rate",
                        "sustain_min_event_hold_rate",
                        "sustain_max_dropout_frames",
                        "sustain_interruption_count", "sustain_event_count")}
    result["sustain_max_dropout_frames"] = max(
        row["sustain_max_dropout_frames"] for row in rows)
    result.update({
        "chord_ready_rate":
            sum(row["chord_ready_rate"] for row in rows) / len(rows),
        "chord_hold_quality":
            sum(row["chord_hold_quality"] for row in rows) / len(rows),
        "press_dropout_rate":
            sum(row["press_dropout_rate"] for row in rows) / len(rows),
        "press_max_dropout_frames":
            max(row["press_max_dropout_frames"] for row in rows),
    })
    for finger in range(1, 5):
        success = sum(
            row[f"press_finger_{finger}_success"] for row in rows)
        count = sum(
            row[f"press_finger_{finger}_count"] for row in rows)
        result[f"finger_{finger}_press_success_rate"] = (
            success / count if count > 0.0 else None)
    penetration_within_threshold = max_guitar_penetration <= FRET["penetration_threshold"]
    penetration_proxy_passed = (
        penetration_within_threshold
        and guitar_tunneled_count == 0
        and guitar_initial_overlap_count == 0
        and guitar_penetration_termination_count == 0
        and palm_down_termination_count == 0
        and wrist_safety_termination_count == 0
        and finger_back_termination_count == 0
        and thumb_overforce_termination_count == 0
    )
    finger_intersection_passed = (
        finger_overlap_env_frames
        <= FRET["evaluation_max_finger_overlap_env_frames"]
        and finger_initial_overlap_count == 0)
    thumb_evaluation_count = max(goal_diagnostic_count, 1)
    thumb_support_rate = thumb_support_sum / thumb_evaluation_count
    thumb_wrong_contact_rate = (
        thumb_wrong_contact_sum / thumb_evaluation_count)
    gates = evaluation_gate_summary(
        result, rows,
        press_applicable=bool((env.goals.fret > 0).any().item()),
        no_press_applicable=bool((env.goals.fret < 0).any().item()),
        expected_sustain_events=env.goals.sustain_n_events,
        penetration_proxy_passed=penetration_proxy_passed,
        finger_intersection_passed=finger_intersection_passed,
        f1_gate=FRET["evaluation_f1_gate"],
        no_press_gate=FRET["evaluation_no_press_accuracy_gate"],
        wrong_press_gate=FRET["evaluation_wrong_press_rate_gate"],
        sustain_hold_gate=FRET["sustain_hold_threshold"],
        sustain_dropout_gate=FRET["sustain_max_dropout_frames"],
        thumb_support_rate=thumb_support_rate,
        thumb_wrong_contact_rate=thumb_wrong_contact_rate,
        thumb_support_gate=FRET["curriculum"]["thumb_support_rate"],
        thumb_wrong_contact_gate=
            FRET["curriculum"]["thumb_wrong_contact_rate"],
        thumb_contact_gate_enabled=
            FRET["curriculum"]["thumb_contact_gate_enabled"],
        thumb_press_readiness=(
            thumb_press_readiness_sum / thumb_evaluation_count),
        thumb_press_readiness_gate=
            FRET["curriculum"]["thumb_press_readiness_rate"],
        thumb_geometry_gate_enabled=
            FRET["curriculum"]["thumb_geometry_gate_enabled"])
    result.update(
        mean_target_distance_m=target_distance_sum / max(active_count, 1.0),
        mean_press_depth_m=press_depth_sum / max(active_count, 1.0),
        mean_press_depth_progress=(
            press_depth_progress_sum / max(active_count, 1.0)),
        mean_position_quality=position_quality_sum / max(active_count, 1.0),
        mean_arch_quality=arch_quality_sum / max(active_count, 1.0),
        mean_good_position_quality=(
            good_position_quality_sum / max(active_count, 1.0)),
        mean_mcp_flexion_deg=mcp_flexion_sum / max(active_count, 1.0),
        mean_pip_flexion_deg=pip_flexion_sum / max(active_count, 1.0),
        mean_dip_flexion_deg=dip_flexion_sum / max(active_count, 1.0),
        tip_contact_rate=tip_contact_sum / max(active_count, 1.0),
        non_tip_contact_rate=non_tip_contact_sum / max(active_count, 1.0),
        press_success_rate=press_success_sum / max(active_count, 1.0),
        mean_wrist_distance_m=wrist_distance_sum / max(goal_diagnostic_count, 1),
        all_correct_rate=all_correct_sum / max(goal_diagnostic_count, 1),
        mean_thumb_reward=thumb_reward_sum / thumb_evaluation_count,
        mean_thumb_distance_m=thumb_distance_sum / thumb_evaluation_count,
        mean_thumb_gap_m=thumb_gap_sum / thumb_evaluation_count,
        mean_thumb_contact_force=thumb_force_sum / thumb_evaluation_count,
        thumb_contact_rate=thumb_contact_sum / thumb_evaluation_count,
        thumb_in_back_region_rate=(
            thumb_in_back_region_sum / thumb_evaluation_count),
        thumb_support_rate=thumb_support_rate,
        thumb_support_stable_6_rate=(
            thumb_support_stable_6_sum / thumb_evaluation_count),
        thumb_support_stable_12_rate=(
            thumb_support_stable_12_sum / thumb_evaluation_count),
        thumb_wrong_contact_rate=thumb_wrong_contact_rate,
        mean_thumb_force_quality=
            thumb_force_quality_sum / thumb_evaluation_count,
        mean_thumb_overforce=thumb_overforce_sum / thumb_evaluation_count,
        mean_thumb_goal_gate=thumb_goal_gate_sum / thumb_evaluation_count,
        mean_thumb_press_readiness=(
            thumb_press_readiness_sum / thumb_evaluation_count),
        thumb_base_action_saturation_rate=(
            thumb_base_action_saturation_sum / thumb_evaluation_count),
        thumb_eligible_support_rate=(
            thumb_eligible_support_sum / max(thumb_eligible_count, 1)),
        thumb_eligible_stable_6_rate=(
            thumb_eligible_stable_6_sum / max(thumb_eligible_count, 1)),
        thumb_eligible_env_frames=thumb_eligible_count,
        max_thumb_contact_force_n=max_thumb_contact_force,
        thumb_overforce_termination_count=thumb_overforce_termination_count,
        wrong_press_termination_count=wrong_press_termination_count,
        max_joint_limit_usage=joint_limit_max_usage,
        mean_joint_limit_near_rate=(
            joint_limit_near_sum / max(goal_diagnostic_count, 1)),
        joint_limit_max_usage_by_group=joint_limit_max_by_group,
        joint_limit_near_rate_by_group={
            group: value / max(goal_diagnostic_count, 1)
            for group, value in joint_limit_near_sum_by_group.items()
        },
        mean_proximal_reward=proximal_reward_sum / max(diagnostic_count, 1),
        mean_proximal_gate=proximal_gate_sum / max(diagnostic_count, 1),
        mean_finger_motion=finger_motion_sum / max(diagnostic_count, 1),
        mean_wrist_motion=wrist_motion_sum / max(diagnostic_count, 1),
        mean_elbow_motion=elbow_motion_sum / max(diagnostic_count, 1),
        mean_shoulder_motion=shoulder_motion_sum / max(diagnostic_count, 1),
        mean_hover_reward=hover_reward_sum / max(hover_reward_count, 1),
        hover_reward_env_frames=hover_reward_count,
        mean_hover_gap_m=hover_gap_sum / max(hover_gate_count, 1),
        hover_diagnostic_samples=hover_gate_count,
        mean_hover_velocity_reward=(
            hover_velocity_reward_sum / max(hover_velocity_env_count, 1)),
        mean_hover_outward_speed_mps=(
            hover_outward_speed_sum / max(hover_velocity_gate_count, 1)),
        max_hover_outward_speed_mps=max_hover_outward_speed,
        hover_velocity_diagnostic_samples=hover_velocity_gate_count,
        mean_slip_reward=slip_reward_sum / max(slip_reward_count, 1),
        slip_reward_env_frames=slip_reward_count,
        mean_slip_distance_m=slip_distance_sum / max(slip_gate_count, 1),
        max_slip_distance_m=max_slip_distance,
        slip_diagnostic_samples=slip_gate_count,
        finger_overlap_env_frames=finger_overlap_env_frames,
        finger_initial_overlap_count=finger_initial_overlap_count,
        max_finger_penetration_m=max_finger_penetration,
        max_support_contact_force_n=max_support_contact_force,
        max_inactive_distal_force_n=max_inactive_distal_force,
        max_control_torque_fraction=max_control_torque_fraction,
        palm_down_termination_count=palm_down_termination_count,
        wrist_safety_termination_count=wrist_safety_termination_count,
        finger_back_termination_count=finger_back_termination_count,
        finger_back_termination_by_finger={
            name: finger_back_termination_by_finger[index]
            for index, name in enumerate(("index", "middle", "ring", "pinky"))
        },
        finger_back_min_local_z_by_finger_m={
            name: finger_back_min_local_z_by_finger[index]
            for index, name in enumerate(("index", "middle", "ring", "pinky"))
        },
        max_guitar_penetration_m=max_guitar_penetration,
        max_guitar_swept_penetration_m=max_guitar_swept_penetration,
        guitar_tunneled_count=guitar_tunneled_count,
        guitar_initial_overlap_count=guitar_initial_overlap_count,
        guitar_penetration_termination_count=guitar_penetration_termination_count,
        guitar_penetration_termination_by_chain={
            name: guitar_penetration_termination_by_chain[index]
            for index, name in enumerate(
                env.penetration_monitor.CHAIN_NAMES)
        },
        failure_termination_count=failure_termination_count,
        nonfinite_termination_count=nonfinite_termination_count,
        velocity_blowup_termination_count=velocity_blowup_termination_count,
        mean_reward=reward_sum / max(diagnostic_count, 1),
        episodes=len(rows),
        preparation_frames=env.preparation_frames,
        preparation_seconds=env.preparation_frames / 60.0,
        expected_full_episode_control_frames=(
            env.preparation_frames + env.goals.n_frames),
        sustain_hold_gate=FRET["sustain_hold_threshold"],
        sustain_event_success_gate=1.0,
        sustain_dropout_gate_frames=FRET["sustain_max_dropout_frames"],
        penetration_gate_m=FRET["penetration_threshold"],
        penetration_within_threshold=penetration_within_threshold,
        safety_scope=(
            "configured termination reasons plus analytical guitar/finger proxies; "
            "not an exact mesh-penetration proof"),
        naturalness_review_required=True,
        naturalness_note=(
            "R18/R23/R24 diagnostics and the uncalibrated R22 capsule proxy "
            "are recorded but not used as pass/fail gates; "
            "inspect their learned-song distributions and rollout video before "
            "claiming natural motion."),
    )
    result.update(gates)
    return result


def main(argv=None):
    _load_fret_runtime()
    args = build_parser().parse_args(argv)
    if args.song:
        from tab2body.song_bundles import fret_goal_path

        if args.goal != FRET["goal_path"]:
            raise SystemExit("--song and --goal cannot be used together")
        args.goal = str(fret_goal_path(args.song))
    if args.eval and not args.checkpoint:
        raise SystemExit("--eval requires --checkpoint")
    if args.checkpoint and args.initialize_from:
        raise ValueError("--checkpoint and --initialize-from are mutually exclusive")
    if args.migrate_contract and not args.checkpoint:
        raise ValueError("--migrate-contract requires --checkpoint")
    if args.eval and args.migrate_contract:
        raise ValueError("--migrate-contract is training-only")
    if args.eval and args.initialize_from:
        raise ValueError("--initialize-from is training-only")
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    ppo_kwargs = dict(FRET["ppo"])
    ppo_kwargs["minibatch_size"] = args.minibatch_size
    goal_path, song_id, goal_sha256 = goal_identity(args.goal)
    song_bundle_path = canonical_song_bundle_for_goal(goal_path)
    hand_targets_path = resolve_hand_targets(goal_path, args.hand_targets)
    hand_targets_sha256 = (file_sha256(hand_targets_path)
                           if hand_targets_path is not None else None)
    out_dir = resolve_out_dir(
        song_id, args.out, args.run_name, args.checkpoint)
    protect_new_run_output(out_dir, checkpoint=args.checkpoint, evaluating=args.eval)
    if args.preparation_seconds < 0.0:
        raise ValueError("--preparation-seconds must be non-negative")
    if args.video_interval < 0:
        raise ValueError("--video-interval must be non-negative")
    preparation_frames = int(round(args.preparation_seconds * 60.0))
    num_envs, iterations = args.num_envs, args.iterations
    if args.smoke:
        num_envs, iterations = min(num_envs, 8), 1
        ppo_kwargs.update(horizon=4, epochs=1, minibatch_size=32,
                          save_interval=1, log_interval=1)
    elif args.eval:
        num_envs = 1
    if iterations <= 0:
        raise ValueError("--iterations must be positive")
    rollout_batch = num_envs * int(ppo_kwargs["horizon"])
    minibatch_size = int(ppo_kwargs["minibatch_size"])
    if not args.eval:
        if minibatch_size <= 0 or minibatch_size > rollout_batch:
            raise ValueError(
                f"minibatch_size must be in [1, rollout batch {rollout_batch}]")
        if rollout_batch % minibatch_size:
            raise ValueError(
                f"rollout batch {rollout_batch} must be divisible by minibatch_size "
                f"{minibatch_size} to avoid a small final optimizer batch")
    resource_snapshot = training_resource_preflight(
        args.device, out_dir, num_envs)

    env = FretTask(**configured_kwargs(
        FretTask, FRET,
        reward_config=FRET,
        goal_path=str(goal_path),
        hand_targets_path=hand_targets_path,
        num_envs=num_envs,
        device=args.device,
        headless=True,
        seed=args.seed,
        reset_noise=0.0 if args.eval else FRET["reset_noise"],
        random_start=(False if args.eval else
                      not args.no_random_start and FRET["random_start"]),
        preparation_frames=preparation_frames,
    ))
    goal_finger_coverage = summarize_goal_finger_coverage(env.goals)
    init_action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
                   (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    model = ActorCritic(env.num_obs, env.num_actions, env.value_dim,
                        init_std=FRET["policy_init_std"],
                        init_mean=init_action).to(args.device)
    trainer = PPOTrainer(env, model, PPOConfig(**ppo_kwargs), out_dir=out_dir)
    checkpoint_contract = build_runtime_checkpoint_contract(
        env, model, trainer,
        goal_sha256=goal_sha256,
        hand_targets_sha256=hand_targets_sha256,
        preparation_frames=preparation_frames)
    trainer.set_checkpoint_contract(checkpoint_contract)

    if args.initialize_from:
        initialization = torch.load(
            args.initialize_from, map_location=args.device, weights_only=True)
        initialization_load = load_fret_initialization_model(
            model, initialization["model"],
            appended_obs_dim=env.future_context_obs_dim,
            calibration_observations=trainer.obs)
        optimizer_warm_started = False
        if args.initialize_optimizer:
            source_optimizer = initialization.get("optimizer")
            if source_optimizer is None:
                raise ValueError(
                    "--initialize-optimizer requires an optimizer state in "
                    "the source checkpoint")
            try:
                trainer.optimizer.load_state_dict(source_optimizer)
            except (KeyError, RuntimeError, ValueError) as exc:
                raise ValueError(
                    "source optimizer is incompatible with the current PPO "
                    "configuration") from exc
            optimizer_warm_started = True
        prior_context = initialization.get("training_context", {})
        prior_stage = prior_context.get("curriculum_stage")
        prior_curriculum_schema = int(
            prior_context.get("curriculum_schema_version", 1))
        migrated_stage = FingertipApproachCurriculum.migrate_stage(
            prior_stage, prior_curriculum_schema)
        prior_flexion_initialized = bool(
            prior_context.get("finger_flexion_initialized", False))
        prior_thumb_seed_version = int(
            prior_context.get("thumb_support_seed_version", 0))
        thumb_seed_repaired = (
            prior_thumb_seed_version < THUMB_SUPPORT_SEED_VERSION)
        _configure_initial_policy(
            model, env, seed_mean=not prior_flexion_initialized,
            repair_thumb_base=thumb_seed_repaired)
        trainer.training_context.update(_initial_policy_context())
        if migrated_stage in FingertipApproachCurriculum.STAGES:
            trainer.training_context.update({
                "curriculum_stage": migrated_stage,
                "curriculum_stage_iteration": 0,
                "curriculum_total_iteration": 0,
                "curriculum_stalled": False,
            })
            # 정책 가중치만 옮기는 재학습에서도 이미 확인한 곡별
            # goal-pair 단계는 유지한다. 새 보상·계약으로 시작하더라도
            # retention부터 다시 돌아가면 병목을 반복하게 된다.
            if migrated_stage == "goal_pair":
                prior_phase = prior_context.get(
                    "curriculum_goal_pair_phase")
                if thumb_seed_repaired:
                    trainer.training_context.update({
                        "curriculum_goal_pair_phase": "retention",
                        "curriculum_goal_pair_mixed_level": 0,
                        "curriculum_goal_pair_focus_finger": 0,
                        "curriculum_goal_pair_phase_iteration": 0,
                        "curriculum_goal_pair_mixed_level_iteration": 0,
                        "curriculum_goal_pair_phase_evidence": {},
                    })
                elif prior_phase in ("retention", "mixed", "full"):
                    trainer.training_context.update({
                        "curriculum_goal_pair_phase": prior_phase,
                        "curriculum_goal_pair_mixed_level": max(
                            0, int(prior_context.get(
                                "curriculum_goal_pair_mixed_level", 0))),
                        "curriculum_goal_pair_focus_finger": max(
                            0, int(prior_context.get(
                                "curriculum_goal_pair_focus_finger", 0))),
                        "curriculum_goal_pair_phase_iteration": 0,
                        "curriculum_goal_pair_mixed_level_iteration": 0,
                    })
        print(
            f"initialized policy weights: {Path(args.initialize_from)} "
            f"(stage={migrated_stage or 'coarse_reach'}, "
            f"observation={initialization_load['source_obs_dim']}"
            f"->{initialization_load['target_obs_dim']}, "
            f"optimizer={'warm' if optimizer_warm_started else 'fresh'})")
    elif not args.checkpoint:
        _configure_initial_policy(
            model, env, seed_mean=True, repair_thumb_base=True)
        trainer.training_context.update(_initial_policy_context())

    if args.checkpoint:
        # Current checkpoints contain tensors plus plain Python containers only;
        # the restricted loader avoids executing arbitrary pickle globals before
        # the semantic contract itself is verified below.
        checkpoint = torch.load(
            args.checkpoint, map_location=args.device, weights_only=True)
        if args.migrate_contract:
            trainer.resume_migrated(checkpoint)
            migrated_context = trainer.training_context
            source_curriculum_schema = int(
                checkpoint.get("training_context", {}).get(
                    "curriculum_schema_version", 1))
            migrated_stage = migrated_context.get("curriculum_stage")
            if migrated_stage in FingertipApproachCurriculum.STAGES:
                # A migrated checkpoint keeps the learned phase/focus, but its
                # old stage clock and evidence must not immediately trigger a
                # timeout in the new run.
                migrated_context.update({
                    "curriculum_stage_iteration": 0,
                    "curriculum_total_iteration": trainer.iteration,
                    "curriculum_stalled": False,
                    "curriculum_recent": [],
                    "curriculum_chord_phase_evidence": {},
                    "curriculum_bridge_windows": [],
                    "curriculum_bridge_accumulator": {},
                    "curriculum_bridge_last_metrics": {},
                    "curriculum_goal_pair_phase_iteration": 0,
                    "curriculum_goal_pair_mixed_level_iteration": 0,
                    "curriculum_goal_pair_phase_evidence": {},
                })
                if (source_curriculum_schema < 37
                        and bool(migrated_context.get(
                            "curriculum_goal_pair_recovery", False))):
                    migrated_context.update({
                        "curriculum_goal_pair_recovery_iteration": 0,
                        "curriculum_goal_pair_recovery_good_windows": 0,
                        "curriculum_goal_pair_recovery_failures": [],
                        "curriculum_goal_pair_focus_finger": 0,
                        "curriculum_goal_pair_focus_iteration": 0,
                        "curriculum_goal_pair_focus_scores": [None] * 4,
                    })
                trainer.training_context = migrated_context
        else:
            trainer.resume(checkpoint, purpose="evaluate" if args.eval else "resume")
        print(f"resumed: {Path(args.checkpoint)} "
              f"(iteration={trainer.iteration}, steps={trainer.global_step}, "
              f"contract={'migrated' if args.migrate_contract else 'verified'})")

    curriculum_config = dict(FRET["curriculum"])
    curriculum_config["coverage_iterations"] = args.coverage_iterations
    curriculum_config["integration_iterations"] = args.integration_iterations
    restored_curriculum_context = dict(trainer.training_context)
    base_context = {
        "training_mode": "per_song_trajectory_optimization",
        "song_id": song_id,
        "song_bundle_path": (
            str(song_bundle_path) if song_bundle_path is not None else None),
        "goal_path": str(goal_path),
        "goal_sha256": goal_sha256,
        "hand_targets_path": hand_targets_path,
        "hand_targets_sha256": hand_targets_sha256,
        "preparation_frames": preparation_frames,
        "goal_finger_coverage": goal_finger_coverage,
        "static_chord_catalog": {
            "min_duration_seconds":
                env.goals.static_chord_min_duration_seconds,
            "min_duration_frames":
                env.goals.static_chord_min_duration_frames,
            "stable_finger_sets": [
                list(values) for values in
                env.goals.practice_available_chord_finger_sets],
            "transient_finger_sets": [
                list(values) for values in
                env.goals.practice_transient_chord_finger_sets],
            "stable_run_count":
                env.goals.practice_static_chord_run_count,
            "transient_run_count":
                env.goals.practice_transient_chord_run_count,
        },
        "checkpoint_contract_schema": checkpoint_contract["payload"]["schema"],
        "checkpoint_contract_sha256": checkpoint_contract["sha256"],
        "initialized_from": (str(Path(args.initialize_from).resolve())
                             if args.initialize_from else None),
        "curriculum_schema_version":
            FingertipApproachCurriculum.SCHEMA_VERSION,
        "curriculum_config": curriculum_config,
    }
    trainer.training_context.update(base_context)
    run_layout = trainer.run_layout
    record_run_metadata(
        run_layout,
        {
            "schema": "tab2body.fret_training_run.v1",
            **base_context,
            "dimensions": {
                "observation": env.num_obs,
                "action": env.num_actions,
                "reward_value": env.value_dim,
            },
            "control": {
                "policy_distribution": getattr(
                    model, "POLICY_DISTRIBUTION_VERSION", None),
                "policy_init_std": FRET["policy_init_std"],
                "articulation_flexion_init_std":
                    FRET["articulation_flexion_init_std"],
                "finger_exploration_target_std":
                    FRET["finger_exploration_target_std"],
                "chord_focus_finger_exploration_std":
                    FRET["chord_focus_finger_exploration_std"],
                "goal_pair_focus_finger_exploration_std":
                    FRET["goal_pair_focus_finger_exploration_std"],
                "articulation_seed_pip_deg":
                    FRET["articulation_seed_pip_deg"],
                "articulation_seed_dip_deg":
                    FRET["articulation_seed_dip_deg"],
                "finger_arch_reward_weight":
                    FRET["finger_arch_reward_weight"],
                "action_scale": env.action_scale,
                "action_alpha": env.action_alpha,
                "reset_soft_limit_fraction": env.reset_soft_limit_fraction,
            },
            "directories": {
                "checkpoints": "checkpoints",
                "logs": "logs",
                "evaluations": "evaluations",
                "videos": "videos",
                "plots": "plots",
            },
            "artifact_policy": {
                "automatic_after_training": [
                    "plots/training_curves.png",
                    "plots/fingertip_curriculum.png",
                    "videos/<final-checkpoint>_rollout.mp4",
                ],
                "periodic_rollout_video_interval": args.video_interval,
                "auto_video_camera_distance_scale": 1.25,
                "delete_source_frames_after_encoding": True,
            },
            "hardware_profile": resource_snapshot,
            "rollout_batch_size": rollout_batch,
            "minibatch_size": minibatch_size,
        },
        {
            "started_at_utc": utc_now_iso(),
            "mode": ("evaluation" if args.eval else
                     "resume" if args.checkpoint else
                     "initialize" if args.initialize_from else "training"),
            "checkpoint": (str(Path(args.checkpoint).resolve())
                           if args.checkpoint else None),
            "requested_iterations": iterations,
            "num_envs": num_envs,
            "rollout_batch_size": rollout_batch,
            "minibatch_size": minibatch_size,
            "resources_at_start": resource_snapshot,
            "seed": args.seed,
            "smoke": args.smoke,
            "curriculum_disabled": args.no_curriculum,
            "curriculum_stage": args.curriculum_stage,
            "video_interval": args.video_interval,
        },
    )
    curriculum = None
    if not args.eval and not args.no_curriculum:
        curriculum = FingertipApproachCurriculum(
            FingertipApproachCurriculumConfig(**curriculum_config),
            forced_stage=args.curriculum_stage)
        curriculum.load_context(restored_curriculum_context)
    elif args.no_random_start or args.curriculum_stage == "full_song":
        env.goals.set_random_start_probability(0.0)
        env.set_curriculum_stage("full_song")

    startup = {
        "task": "fret", "song": song_id, "envs": env.num_envs,
        "song_bundle": (
            str(song_bundle_path) if song_bundle_path is not None else None),
        "goal": str(goal_path),
        "hand_targets": hand_targets_path,
        "observations": env.num_obs, "actions": env.num_actions,
        "reward_value": env.rew_dim, "goal_frames": env.goals.n_frames,
        "requested_iterations": iterations, "run": str(run_layout.root),
        "checkpoints": str(run_layout.checkpoints),
        "metrics": str(run_layout.metrics), "resources": resource_snapshot,
        "goal_finger_coverage": goal_finger_coverage,
    }
    with run_layout.training_log.open("a") as stream:
        stream.write("startup=" + json.dumps(
            startup, ensure_ascii=False, sort_keys=True) + "\n")
    bundle_display = (
        str(song_bundle_path)
        if song_bundle_path is not None else "none (custom --goal)")
    print(f"song={song_id} | song_bundle={bundle_display}")
    print(f"goal={goal_path} | hand_targets={hand_targets_path or 'none'}")
    print(
        "static_chords="
        f"{[list(values) for values in env.goals.practice_available_chord_finger_sets]} "
        f"| transient_chords="
        f"{[list(values) for values in env.goals.practice_transient_chord_finger_sets]} "
        f"| min_duration={env.goals.static_chord_min_duration_frames}frames")
    coverage_rows = goal_finger_coverage["fingers"]
    print(
        "finger_coverage(active/start/stable_chord)="
        + " ".join(
            f"{name}:{row['active_frames']}/"
            f"{row['press_start_events']}/{row['stable_chord_runs']}"
            for name, row in coverage_rows.items()))
    if goal_finger_coverage["warning"]:
        print(
            "warning: underrepresented fingers in this song="
            + ",".join(goal_finger_coverage["underrepresented_fingers"])
            + "; use a better-balanced song for four-finger validation")
    print(f"run={run_layout.root} | envs={env.num_envs} | "
          f"epochs={iterations} | detailed_log={run_layout.training_log}")

    periodic_video_checkpoints = []
    controlled_names = [
        env.dof_names[index]
        for index in env.ctrl_idx.detach().cpu().tolist()]
    thumb_base_policy_indices = [
        index for index, name in enumerate(controlled_names)
        if name.startswith("LH:thumb1_")]
    if len(thumb_base_policy_indices) != 3:
        raise RuntimeError(
            "expected three LH:thumb1_* policy actions for exploration")
    finger_lateral_policy_indices = {
        finger_number: controlled_names.index(f"LH:{finger_name}1_z")
        for finger_number, finger_name in enumerate(
            ("index", "middle", "ring", "pinky"), start=1)
    }
    finger_policy_indices = {
        finger_number: [
            index for index, name in enumerate(controlled_names)
            if name.startswith(f"LH:{finger_name}")]
        for finger_number, finger_name in enumerate(
            ("index", "middle", "ring", "pinky"), start=1)
    }
    all_finger_policy_indices = [
        index for indices in finger_policy_indices.values()
        for index in indices]

    def training_iteration_callback(iteration):
        state = (
            curriculum.apply(env)
            if curriculum is not None else {})
        if args.no_random_start:
            env.goals.set_random_start_probability(0.0)
            state = dict(state)
            state["curriculum_random_start_probability"] = 0.0
        floor = thumb_base_exploration_floor(
            iteration,
            FRET["thumb_base_exploration_init_std"],
            FRET["thumb_base_exploration_target_std"],
            FRET["thumb_base_exploration_warmup_iterations"],
            FRET["thumb_base_exploration_ramp_iterations"])
        with torch.no_grad():
            floor_log = model.log_std.new_tensor(floor).log()
            ceiling_log = model.log_std.new_tensor(
                FRET["thumb_base_exploration_target_std"]).log()
            model.log_std[thumb_base_policy_indices] = torch.clamp(
                model.log_std[thumb_base_policy_indices],
                min=floor_log, max=ceiling_log)
        state = dict(state)
        state["thumb_base_exploration_floor"] = float(floor)
        state["thumb_base_exploration_ceiling"] = float(
            FRET["thumb_base_exploration_target_std"])
        stage_is_goal_pair = (
            state.get("curriculum_stage") == "goal_pair")
        finger_ceiling = FRET["articulation_flexion_init_std"]
        precision_active, precision_age, focus_fingers = (
            finger_precision_schedule(state))
        if precision_active:
            finger_ceiling = finger_exploration_ceiling(
                precision_age,
                FRET["articulation_flexion_init_std"],
                FRET["finger_exploration_target_std"],
                FRET["finger_exploration_warmup_iterations"],
                FRET["finger_exploration_ramp_iterations"])
            with torch.no_grad():
                ceiling_log = model.log_std.new_tensor(
                    finger_ceiling).log()
                model.log_std[all_finger_policy_indices] = torch.minimum(
                    model.log_std[all_finger_policy_indices], ceiling_log)
                focus_std_key = (
                    "goal_pair_focus_finger_exploration_std"
                    if stage_is_goal_pair
                    else "chord_focus_finger_exploration_std")
                focus_log = model.log_std.new_tensor(
                    FRET[focus_std_key]).log()
                for focus_finger in focus_fingers:
                    if focus_finger not in finger_policy_indices:
                        continue
                    indices = finger_policy_indices[focus_finger]
                    model.log_std[indices] = torch.maximum(
                        model.log_std[indices], focus_log)
        state["finger_exploration_ceiling"] = float(finger_ceiling)
        state["finger_exploration_schedule_age"] = int(precision_age)
        state["finger_exploration_focus_fingers"] = list(focus_fingers)
        state["chord_focus_finger_exploration_floor"] = (
            float(FRET["chord_focus_finger_exploration_std"])
            if precision_active and not stage_is_goal_pair and focus_fingers
            else 0.0)
        state["goal_pair_focus_finger_exploration_floor"] = (
            float(FRET["goal_pair_focus_finger_exploration_std"])
            if stage_is_goal_pair and focus_fingers else 0.0)
        lateral_floor = 0.0
        focus_finger = focus_fingers[0] if len(focus_fingers) == 1 else 0
        if (stage_is_goal_pair
                and focus_finger in finger_lateral_policy_indices):
            lateral_floor = float(state[
                "curriculum_goal_pair_focus_lateral_exploration_std"])
            lateral_index = finger_lateral_policy_indices[focus_finger]
            with torch.no_grad():
                lateral_floor_log = model.log_std.new_tensor(
                    lateral_floor).log()
                model.log_std[lateral_index] = torch.maximum(
                    model.log_std[lateral_index], lateral_floor_log)
        state["goal_pair_focus_lateral_exploration_floor"] = lateral_floor
        return state

    def periodic_video_callback(iteration, _stats):
        if (args.smoke or args.no_auto_video or args.video_interval == 0
                or iteration % args.video_interval):
            return
        checkpoint = (
            trainer.checkpoint_dir / f"fret_{iteration:06d}.pt")
        if not checkpoint.exists():
            trainer.save(iteration)
        periodic_video_checkpoints.append((iteration, checkpoint))
        print(f"artifact: queued epoch {iteration} rollout", flush=True)

    auto_video_checkpoint = None
    interrupted = False
    try:
        if args.eval:
            result = evaluate(env, model, args.eval_episodes)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            out = (Path(args.eval_out).resolve() if args.eval_out else
                   default_evaluation_path(args.checkpoint))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"evaluation -> {out}")
        else:
            callback = training_iteration_callback
            result_callback = None
            if curriculum is not None:
                result_callback = curriculum.after_iteration
            trainer.learn(
                iterations,
                iteration_callback=callback,
                iteration_result_callback=result_callback,
                post_iteration_callback=periodic_video_callback,
                history_limit=0,
            )
            if not args.smoke and not args.no_auto_video:
                auto_video_checkpoint = (
                    trainer.checkpoint_dir / f"fret_{trainer.iteration:06d}.pt")
    except KeyboardInterrupt:
        interrupted = True
        if not args.eval and trainer.iteration > 0:
            try:
                trainer.save(trainer.iteration)
                if not args.smoke and not args.no_auto_video:
                    auto_video_checkpoint = (
                        trainer.checkpoint_dir
                        / f"fret_{trainer.iteration:06d}.pt")
                print(
                    f"training interrupted: saved epoch {trainer.iteration}",
                    flush=True)
            except (OSError, RuntimeError, ValueError) as exc:
                print(
                    f"warning: interrupt checkpoint failed: {exc}",
                    file=sys.stderr, flush=True)
    finally:
        env.close()

    if not args.eval:
        artifact_results = {}
        resolved_artifact_errors = []
        try:
            artifact_results.update(generate_training_plots(run_layout))
            resolved_artifact_errors.append("training_plots")
        except (OSError, subprocess.CalledProcessError) as exc:
            record_artifact_error(run_layout, "training_plots", exc)
            print(f"warning: automatic training plots failed: {exc}",
                  file=sys.stderr, flush=True)
    if auto_video_checkpoint is not None:
        queued = [
            item for item in periodic_video_checkpoints
            if item[1] != auto_video_checkpoint]
        if queued:
            print(
                f"artifacts: rendering {len(queued)} periodic rollouts "
                "after releasing the training simulator", flush=True)
        for iteration, checkpoint in queued:
            key = f"rollout_video_{iteration:06d}"
            try:
                artifact_results[key] = generate_rollout_video(
                    run_layout, checkpoint, goal_path, hand_targets_path,
                    preparation_frames, key)
            except (OSError, subprocess.CalledProcessError) as exc:
                record_artifact_error(run_layout, key, exc)
                print(
                    f"warning: epoch {iteration} rollout video failed: {exc}",
                    file=sys.stderr, flush=True)
        print("artifacts: generating final rollout video", flush=True)
        try:
            artifact_results["rollout_video"] = generate_rollout_video(
                run_layout, auto_video_checkpoint, goal_path,
                hand_targets_path, preparation_frames, "rollout_video")
        except (OSError, subprocess.CalledProcessError) as exc:
            # Rendering is an artifact step: preserve the completed checkpoint
            # and report a rerunnable failure instead of losing training output.
            print(f"warning: automatic rollout video failed: {exc}",
                  file=sys.stderr, flush=True)
            record_artifact_error(run_layout, "rollout_video", exc)
    if not args.eval:
        record_artifact_result(
            run_layout, artifact_results,
            resolved_errors=resolved_artifact_errors)
    if interrupted:
        raise KeyboardInterrupt


if __name__ == "__main__":
    main()
