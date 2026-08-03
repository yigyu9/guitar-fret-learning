"""tab2body 학습 기본 설정."""
from pathlib import Path

from tab2body.song_bundles import (
    DEFAULT_SONG_ID,
    fret_goal_path,
    hand_targets_path,
)

HERE = Path(__file__).resolve().parent

FRET = {
    "song_id": DEFAULT_SONG_ID,
    "goal_path": str(fret_goal_path(DEFAULT_SONG_ID)),
    "hand_targets_path": str(hand_targets_path(DEFAULT_SONG_ID)),
    # RTX 4070 Ti 12GB profile. A 384-env run used only ~1.4GB VRAM; 1024 is
    # now the validated target, with startup resource guards kept active.
    "num_envs": 1024,
    "device": "cuda:0",
    "headless": True,
    "seed": 42,
    # S0 reset-body state uses a settled PhysX snapshot. Keep q deterministic
    # until a matching forward-kinematic cache supports noisy asynchronous reset.
    "reset_noise": 0.0,
    # Bounded-policy contract: [-1,1] maps one-to-one to the hard joint range.
    # Boundary-authored controlled joints reset 2% inside that range so tanh
    # gradients remain usable.  Initial exploration is deliberately modest;
    # the learned log_std remains trainable.
    "action_scale": 1.0,
    "action_alpha": 0.5,
    "reset_soft_limit_fraction": 0.02,
    "policy_init_std": 0.02,
    # 모든 신규 학습은 약한 PIP/DIP 아치와 넓은 굽힘 탐색으로 시작하고,
    # 모든 커리큘럼 단계에서 거리 게이트 아치 보상을 유지한다.
    "articulation_flexion_init_std": 0.08,
    "thumb_exploration_init_std": 0.05,
    "thumb_base_exploration_init_std": 0.05,
    "thumb_base_exploration_target_std": 0.08,
    "thumb_base_exploration_warmup_iterations": 200,
    "thumb_base_exploration_ramp_iterations": 800,
    # 전용 pad/proxy 이전 정책에서 실제 병목인 thumb1_x 포화만 완화한다.
    # y/z의 관측 의존 자세는 보존해 기존 압현 기하가 무너지지 않게 한다.
    "thumb_seed_action_limit": (0.85, 0.98, 0.98),
    "articulation_seed_pip_deg": 15.0,
    "articulation_seed_dip_deg": 10.0,
    "finger_arch_reward_weight": 0.10,
    # M2: only abnormal/early termination receives this broadcast penalty.
    # Completing the final goal (even when it coincides with the time limit)
    # remains a normal termination.
    "failure_termination_penalty": -25.0,
    "random_start": True,
    "wrist_weight": 0.15,
    # R10 is deferred: keep the existing hook but do not shape the policy yet.
    "smooth_weight": 0.0,
    # 오압현 직전부터 회피 신호를 주고, 실제 오압현은 명확히 감점한다.
    "wrong_press_penalty": 0.35,
    "wrong_press_avoidance_weight": 0.15,
    # 전체 곡에서 NO_PRESS가 PRESS보다 쉬운 해법이 되지 않도록 줄별
    # 감독 보상을 프레임 안에서 재가중한다.
    "press_class_weight": 0.70,
    "no_press_class_weight": 0.30,
    "no_press_failure_credit": 0.10,
    "chord_bridge_bottleneck_weight": 0.75,
    "static_chord_bottleneck_weight": 0.50,
    "static_chord_joint_weight": 0.30,
    "static_chord_no_press_failure_credit": 0.0,
    "static_chord_no_press_completion_power": 1.0,
    # 순간 접촉보다 0.1~0.2초 연속 압현을 우선하고 중간 이탈을 감점한다.
    "press_hold_min_frames": 6,
    "press_hold_full_frames": 12,
    "press_dropout_penalty": 0.15,
    "press_position_dense_scale": 0.20,
    "press_precision_gate_floor": 0.40,
    "next_goal_weight": 0.15,
    # 전환 병목에서는 현재 압현을 보존하면서 다음 위치 접근을 더 크게
    # 반영한다. 기본 압현 단계에는 적용되지 않는다.
    "goal_pair_transition_next_goal_weight": 0.70,
    "next_goal_lookahead_s": 1.50,
    "next_goal_progress_weight": 4.0,
    "next_goal_progress_near": 0.010,
    "next_goal_progress_far": 0.100,
    "next_goal_preservation_weight": 0.60,
    "next_goal_unprotected_progress_scale": 0.0,
    "goal_pair_transition_time_gate_floor": 0.30,
    "next_goal_prepress_clearance": 0.004,
    # 최근 run에서 엄지 접근은 보였지만 실제 후면 지지가 거의 없었다.
    # 압현 보상보다 작게 유지하면서 접근 신호만 조금 강화한다.
    "thumb_weight": 0.20,
    "thumb_pad_radius": 0.010,
    "thumb_approach_scale": 0.015,
    "thumb_reach_scale": 0.100,
    "thumb_contact_on_force": 0.5,
    "thumb_contact_off_force": 0.1,
    # 전용 fixed-body pad의 raw force는 solver impulse에 민감하다. 실제 압력은
    # 후면 평면을 넘은 pad 압축 깊이로 평가하고 raw force는 폭주만 막는다.
    "thumb_force_soft_limit": 50000.0,
    "thumb_force_decay_scale": 100000.0,
    "thumb_compression_free_depth": 0.0005,
    "thumb_compression_decay_scale": 0.002,
    "thumb_overforce_penalty": 0.10,
    "thumb_force_termination_threshold": 150000.0,
    "thumb_compression_termination_threshold": 0.004,
    "thumb_force_termination_frames": 3,
    # Full neck-support credit is unlocked only after a target fingertip is near.
    "thumb_gate_full_distance": 0.025,
    "thumb_gate_zero_distance": 0.080,
    # 접촉을 하드 조건으로 만들지는 않되, 손끝이 목표에 가까울 때 엄지 없는
    # 압현이 충분한 우회 해법이 되지 않도록 성공 보상을 부드럽게 제한한다.
    "thumb_press_gate_weight": 0.45,
    "thumb_base_saturation_threshold": 0.90,
    "thumb_base_saturation_penalty_weight": 0.01,
    # Near a fingertip goal, discourage solving the task with the shoulder or
    # elbow. This is a multiplicative cost, so it creates no idle baseline.
    "proximal_weight": 0.05,
    "proximal_transition": 0.040,
    # A2a: transport with the whole arm, then freeze proximal commands and let
    # only the designated finger plus thumb finish the press.
    "isolated_press_lock_after_frames": 60,
    # R18: released fingers stay near the strings. Position applies throughout
    # release; outward-speed damping yields for an imminent MOVE target.
    "hover_weight": 0.020,
    "hover_free_gap": 0.012,
    "hover_decay_scale": 0.020,
    "hover_position_weight": 0.55,
    "hover_release_pose_weight": 0.30,
    "hover_release_blend_time": 0.30,
    "hover_release_relaxed_pip_deg": 25.0,
    "hover_release_relaxed_dip_deg": 10.0,
    "hover_release_tolerance_deg": (15.0, 20.0, 15.0),
    "hover_free_outward_speed": 0.03,
    "hover_speed_decay_scale": 0.12,
    "hover_move_release_time": 0.25,
    # 인접 손가락 동조는 reward-only이며 현재 PRESS가 모두 유지될 때만 켠다.
    "finger_coupling_weight": 0.015,
    "finger_coupling_coefficients": (0.15, 0.20, 0.25),
    "finger_coupling_min_speed_deg": 5.0,
    "finger_coupling_full_speed_deg": 30.0,
    "finger_coupling_tolerance_deg_s": 15.0,
    # 보상만으로 거의 나타나지 않았던 연동을 비활성 손가락 PD target에
    # 작은 굽힘 변화로 전달한다. 활성 PRESS와 다음 MOVE는 건드리지 않는다.
    "finger_synergy_coefficients": (0.15, 0.20, 0.25),
    "finger_synergy_min_driver_delta_deg": 0.10,
    "finger_synergy_full_driver_delta_deg": 1.00,
    "finger_synergy_max_induced_delta_deg": 2.00,
    # R23: after 3 stable press frames, allow 2mm cumulative tangent slip and
    # softly decay beyond it. This is a 0.5% reward term, never a termination.
    "slip_weight": 0.020,
    "slip_stable_frames": 3,
    "slip_free_distance": 0.002,
    "slip_decay_scale": 0.003,
    # R7: deliberately broad, guitar-local hard safety box; 3-frame debounce.
    "wrist_safety_bounds_min": (-0.20, -0.35, -0.30),
    "wrist_safety_bounds_max": (0.30, 0.35, 0.25),
    "wrist_safety_frames": 3,
    # R8: 확정된 -50 mm 평면 전부터 감점하고, proximal은 조금 더 여유를 둔다.
    "finger_back_soft_limit_z": -0.035,
    "finger_back_soft_scale": 0.015,
    "finger_back_soft_penalty": 0.05,
    "finger_back_limit_z": -0.050,
    "finger_back_proximal_limit_z": -0.060,
    "finger_back_frames": 3,
    "finger_back_samples_per_segment": 5,
    # Ignore a single endpoint grazing the plane; require a clear excursion.
    "finger_back_min_fraction": 0.25,
    # R13: fixed-sign palm inward normal must clearly face world floor for 3 control frames.
    "palm_down_threshold": -0.3,
    "palm_down_frames": 3,
    # R14 phase 1: monitor first; enable termination only after valid-contact calibration.
    "penetration_threshold": 0.005,
    "penetration_frames": 3,
    "penetration_termination": True,
    # R22 diagnostics only: approximate each finger link chain as 6mm capsules.
    # A proxy overlap must exceed 2mm to count; it never affects reward/done.
    "finger_capsule_radius": 0.006,
    "finger_overlap_tolerance": 0.002,
    # R27 evaluation-only: trim 50ms at each boundary of sufficiently long
    # PRESS runs; require >=90% hold and no dropout longer than 50ms.
    "sustain_boundary_grace_frames": 3,
    "sustain_hold_threshold": 0.90,
    "sustain_max_dropout_frames": 3,
    # Final learned-song evaluation gates.  PRESS and release/protection are
    # independent requirements; a high PRESS F1 must not hide wrong fretting.
    "evaluation_f1_gate": 0.90,
    "evaluation_no_press_accuracy_gate": 0.99,
    "evaluation_wrong_press_rate_gate": 0.01,
    # R22 remains diagnostic-only until the capsule proxy is calibrated.
    # This threshold labels the diagnostic report; it is not a delivery gate.
    "evaluation_max_finger_overlap_env_frames": 0,
    # R28 diagnostic only: confirmed pressed travel above 3mm marks a move.
    "pressed_drag_threshold": 0.003,
    # R29: expose and reward the selected first goal for one second while the
    # song clock is frozen; accuracy/sustain metrics start afterward.
    "preparation_frames": 60,
    # Promotion diagnostics use only the final stable half-second of static
    # practice, never the preparation/transport portion.
    "curriculum_settling_frames": 30,
    "iterations": 5000,
    "video_interval": 1000,
    "resource_guard": {
        "max_num_envs": 1024,
        "min_free_vram_gib": 8.0,
        "min_available_ram_gib": 8.0,
        "min_free_disk_gib": 10.0,
    },
    # R26: one policy repeatedly practices one song. Goals/rewards never change;
    # only reset starts transition from in-song coverage to complete takes.
    "curriculum": {
        "coarse_min_iterations": 100,
        "coarse_max_iterations": 1000,
        "fine_min_iterations": 200,
        "fine_max_iterations": 1500,
        "isolated_press_min_iterations": 300,
        "isolated_press_max_iterations": 2000,
        "integrated_press_min_iterations": 300,
        "integrated_press_max_iterations": 2500,
        "chord_reach_min_iterations": 300,
        "chord_reach_max_iterations": 2000,
        "chord_fine_min_iterations": 400,
        "chord_fine_max_iterations": 2000,
        "chord_fine_focus_min_iterations": 100,
        "chord_fine_focus_max_iterations": 1200,
        "chord_fine_focus_probability": 0.95,
        "chord_fine_success_rate": 0.80,
        "chord_fine_p90_distance": 0.010,
        "chord_fine_alignment_rate": 0.80,
        "chord_fine_min_phase_episodes": 256,
        "static_chord_min_iterations": 400,
        "static_chord_max_iterations": 3000,
        "frozen_context_min_iterations": 1000,
        "frozen_context_max_iterations": 2500,
        "goal_pair_min_iterations": 400,
        "goal_pair_max_iterations": 2000,
        "transition_min_iterations": 800,
        "transition_max_iterations": 3000,
        "pair_min_iterations": 500,
        "pair_max_iterations": 3000,
        "frozen_context_duration_frames": 150,
        "goal_pair_duration_frames": 120,
        "goal_pair_retention_rehearsal_probability": 1.0,
        "goal_pair_mixed_rehearsal_probability": 0.35,
        "goal_pair_rehearsal_probability": 1.0 / 3.0,
        # 정적 rehearsal에 치우치지 않도록 MOVE 전환 표본을 단계적으로 늘린다.
        "goal_pair_mixed_transition_fractions": (0.35, 0.50, 0.65),
        "goal_pair_mixed_preservation_rates": (0.20, 0.60, 0.90),
        "goal_pair_mixed_press_rates": (0.00, 0.30, 0.50),
        "goal_pair_mixed_distances": (0.050, 0.035, 0.025),
        # 마지막 goal-pair 단계부터 실제 연속 구간을 섞는다. 그중 20%는
        # 곡 처음부터 끝까지 진행해 짧은 전환 표본의 과적합을 막는다.
        "goal_pair_mixed_sequence_probabilities": (0.0, 0.10, 0.25),
        "goal_pair_full_sequence_probability": 0.35,
        "goal_pair_sequence_duration_frames": 240,
        "goal_pair_sequence_full_song_fraction": 0.20,
        "goal_pair_sequence_min_frames": 1024,
        "goal_pair_sequence_press_rate": 0.75,
        "goal_pair_sequence_no_press_rate": 0.90,
        "goal_pair_sequence_wrong_press_rate": 0.08,
        "goal_pair_sequence_penetration_rate": 0.01,
        "goal_pair_sequence_thumb_support_rate": 0.20,
        "goal_pair_preview_levels": 1,
        "goal_pair_focus_lateral_exploration_std": 0.055,
        "goal_pair_retention_focus_probability": 0.70,
        "goal_pair_mixed_focus_probability": 0.90,
        "goal_pair_retention_min_iterations": 100,
        "goal_pair_mixed_min_iterations": 200,
        "goal_pair_full_min_iterations": 100,
        "goal_pair_phase_min_evidence": 1024,
        "goal_pair_rehearsal_press_rate": 0.80,
        "goal_pair_rehearsal_distance": 0.010,
        "goal_pair_mixed_transition_press_rate": 0.50,
        "goal_pair_mixed_transition_distance": 0.025,
        # 다음 목표 접근 progress는 접촉 샘플링 노이즈로 소폭 음수가
        # 될 수 있으므로, 거리 개선이 유지되는 범위에서 승급을 허용한다.
        "goal_pair_mixed_min_next_progress": -0.010,
        "goal_pair_pretransition_preservation_rate": 0.90,
        "goal_pair_promotion_transition_press_rate": 0.80,
        "frozen_context_initial_real_probability": 0.0,
        "frozen_context_context_warmup_iterations": 200,
        "frozen_context_context_ramp_iterations": 800,
        "transition_window_seconds": (1.0, 1.5, 2.0, 3.0),
        "transition_max_changes": (4, 6, 8, 12),
        "static_chord_min_evidence_episodes": 128,
        "frozen_context_min_evidence_episodes": 128,
        "goal_pair_min_evidence_episodes": 128,
        "transition_min_evidence_episodes": 128,
        "coverage_min_evidence_episodes": 128,
        "integration_min_evidence_episodes": 128,
        "promotion_success_rate": 0.80,
        "promotion_windows": 3,
        "bridge_window_episodes": 4096,
        "bridge_promotion_windows": 2,
        "frozen_context_final_evaluation_iterations": 200,
        "bridge_soft_timeout_fraction": 0.80,
        "bridge_hard_timeout_min_per_finger_rate": 0.20,
        "late_stage_grace_iterations": 500,
        "bridge_f1_rate": 0.95,
        "bridge_per_finger_press_rate": 0.90,
        "bridge_no_press_accuracy": 0.93,
        "bridge_wrong_press_rate": 0.035,
        "bridge_sustain_hold_rate": 0.95,
        "bridge_sustain_event_rate": 0.85,
        "bridge_press_dropout_rate": 0.04,
        "bridge_failure_termination_rate": 0.02,
        "bridge_soft_f1_rate": 0.93,
        "bridge_soft_per_finger_press_rate": 0.85,
        "bridge_soft_no_press_accuracy": 0.90,
        "bridge_soft_wrong_press_rate": 0.05,
        "bridge_soft_sustain_hold_rate": 0.92,
        "bridge_soft_sustain_event_rate": 0.78,
        "bridge_soft_press_dropout_rate": 0.06,
        "bridge_soft_failure_termination_rate": 0.03,
        "regression_f1_drop": 0.04,
        "regression_no_press_drop": 0.03,
        "regression_wrong_press_increase": 0.015,
        "regression_sustain_event_drop": 0.07,
        "regression_per_finger_drop": 0.05,
        "regression_hold_windows": 2,
        "song_f1_rate": 0.85,
        "song_per_finger_press_rate": 0.80,
        "song_no_press_accuracy": 0.99,
        "song_wrong_press_rate": 0.01,
        "song_sustain_hold_rate": 0.90,
        "song_max_dropout_frames": 3.0,
        "song_press_dropout_rate": 0.05,
        "song_min_sustain_events": 1.0,
        "thumb_coarse_distance": 0.050,
        "thumb_fine_distance": 0.025,
        "thumb_integrated_distance": 0.015,
        # 실제 collision 접촉률은 에셋 검증 전까지 진단 전용이다.
        "thumb_contact_gate_enabled": False,
        "thumb_support_rate": 0.80,
        "thumb_wrong_contact_rate": 0.05,
        "coverage_iterations": 1000,
        "integration_iterations": 1000,
    },
    "ppo": {
        "horizon": 32,
        "epochs": 5,
        # 1024 env × horizon 32 = 32,768 samples = 8 equal minibatches.
        "minibatch_size": 4096,
        # 한 음의 접근-압현-유지 결과가 앞선 준비 동작까지 전달되게 한다.
        "gamma": 0.99,
        "gae_lambda": 0.95,
        "clip_ratio": 0.2,
        "value_coef": 1.0,
        "entropy_coef": 0.001,
        "action_saturation_regularization_weight": 0.01,
        "action_saturation_regularization_threshold": 0.80,
        # The initial bounded policy is intentionally narrow for R8 safety.
        # Its actor therefore needs a smaller step than the critic to keep KL
        # inside the trust region instead of destroying the safe initialization.
        "actor_learning_rate": 5e-6,
        "learning_rate": 3e-4,
        "max_grad_norm": 1.0,
        "target_kl": 0.03,
        "save_interval": 500,
        "log_interval": 10,
    },
    "out_dir": str(HERE.parent / "fret" / "training" / "runs" / "fret_s0"),
}
