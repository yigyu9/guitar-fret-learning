"""Configuration for the rebuilt virtual-pick strike task."""
from __future__ import annotations

from pathlib import Path

from tab2body.song_bundles import DEFAULT_SONG_ID, strike_goal_path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_BUNDLE = strike_goal_path(DEFAULT_SONG_ID)


STRIKE = {
    "goal_path": str(DEFAULT_BUNDLE),
    "grip_reference_path": str(
        PROJECT_ROOT / "strike" / "02_physical_control"
        / "pick-grip-reference.json"
    ),
    "num_envs": 512,
    "device": "cuda:0",
    "seed": 42,
    "iterations": 3000,
    "action_scale": 1.0,
    "action_alpha": 0.5,
    "reset_noise": 0.0,
    "reset_soft_limit_fraction": 0.02,
    "policy_init_std": 0.04,
    "failure_termination_penalty": -10.0,
    "zone": {
        "allowed_y_min_m": -0.385,
        "allowed_y_max_m": -0.255,
        "preferred_y_min_m": -0.355,
        "preferred_y_max_m": -0.295,
        "phrase_lane_y_m": -0.325,
        "lane_core_half_width_m": 0.006,
        "lane_allowed_half_width_m": 0.0125,
    },
    "trajectory": {
        "ready_across_offset_m": 0.003,
        "entry_across_offset_m": 0.0015,
        "exit_across_offset_m": 0.003,
        "ready_height_m": 0.008,
        "crossing_depth_m": 0.0015,
        "ready_distance_m": 0.010,
        "entry_distance_m": 0.006,
        "ready_hold_frames": 6,
        "recovery_frames": 12,
        "follow_through_min_frames": 1,
        "approach_lead_s": 0.20,
    },
    "detector": {
        "min_depth_m": 0.001,
        "min_across_speed_m_s": 0.05,
        "parallel_epsilon": 1e-9,
        "min_displacement_m": 1e-5,
        "rearm_distance_m": 0.003,
        "rearm_min_frames": 2,
    },
    "safety": {
        "penetration_threshold_m": 0.005,
        "penetration_frames": 3,
        "penetration_termination": False,
    },
    "wrong_crossing_termination": {
        "enabled": True,
        "minimum_tempo_lambda": 0.75,
        "minimum_resolved_events": 4,
        "max_count": 3,
        "max_rate": 0.20,
        "consecutive_event_limit": 2,
    },
    "joint_limits": {
        "diagnostic_fraction": 0.90,
        "soft_penalty_start_fraction": 0.95,
        "soft_penalty_weight": 0.01,
    },
    "reward": {
        "grip_weight": {
            "A0_PICK_GRIP": 1.00,
            "A1_TIP_READY": 0.05,
            "A2_FREE_CROSSING": 0.005,
            "A3_TIMED_CROSSING": 0.003,
            "A4_ZONE_CONTROL": 0.003,
            # X0 candidate: identical to A4 (grip is already mastered by A4;
            # unverified until measured against a real X0 rollout).
            "X0_MINI_STRUM": 0.003,
        },
        "reach_weight": 0.20,
        "reach_discount": 0.95,
        "ready_quality_weight": {
            "A0_PICK_GRIP": 0.00,
            "A1_TIP_READY": 0.75,
            "A2_FREE_CROSSING": 0.05,
            "A3_TIMED_CROSSING": 0.03,
            "A4_ZONE_CONTROL": 0.02,
            "X0_MINI_STRUM": 0.02,
        },
        "crossing_reward": 1.00,
        "completion_reward": {
            "A0_PICK_GRIP": 0.00,
            "A1_TIP_READY": 0.15,
            "A2_FREE_CROSSING": 0.50,
            "A3_TIMED_CROSSING": 0.35,
            "A4_ZONE_CONTROL": 0.25,
            "X0_MINI_STRUM": 0.25,
        },
        "wrong_crossing_penalty": 0.35,
        "unprepared_crossing_penalty": 1.00,
        "miss_penalty": 0.50,
        "zone_weight": 0.20,
        "timing_core_ms": 20.0,
    },
    "episode": {
        "A0_PICK_GRIP": 120,
        "A1_TIP_READY": 180,
        "A2_FREE_CROSSING": 240,
        "A3_TIMED_CROSSING": 240,
        "A4_ZONE_CONTROL": 600,
        # X0 candidate: same event quota (a4_events_per_episode) and horizon
        # as A4 since it reuses the same event-driven episode shape.
        "X0_MINI_STRUM": 600,
        "a4_events_per_episode": 8,
        "timed_lead_frames": 30,
    },
    "curriculum": {
        "min_iterations": {
            "A0_PICK_GRIP": 50,
            "A1_TIP_READY": 100,
            "A2_FREE_CROSSING": 150,
            "A3_TIMED_CROSSING": 200,
            "A4_ZONE_CONTROL": 300,
            # X0 candidates below are unverified starting points, not
            # measured thresholds -- retune once real X0 rollouts exist.
            "X0_MINI_STRUM": 300,
        },
        "max_iterations": {
            "A0_PICK_GRIP": 500,
            "A1_TIP_READY": 1000,
            "A2_FREE_CROSSING": 1500,
            "A3_TIMED_CROSSING": 2500,
            "A4_ZONE_CONTROL": 5000,
            "X0_MINI_STRUM": 5000,
        },
        "promotion_windows": 3,
        "terminal_evidence_fraction": 1.0,
        "timing_tolerances_ms": (100, 67, 50),
        "tempo_lambdas": (0.0, 0.25, 0.5, 0.75, 0.9, 1.0),
        "grip_success_rate": 0.90,
        "ready_success_rate": 0.85,
        "release_recall": 0.80,
        "max_wrong_rate": 0.05,
        "timed_f1_by_level": (0.80, 0.90, 0.95),
        "zone_f1": 0.98,
        "zone_success_rate": 0.95,
    },
    "evaluation": {
        "f1": 0.99,
        "precision": 0.99,
        "recall": 0.99,
        "max_wrong_rate": 0.01,
        "timing_p95_ms": 50.0,
        "zone_success_rate": 0.99,
        "strum_completion_rate": 0.95,
        "strum_traversal_recall": 0.99,
        "strum_order_accuracy": 0.99,
        "strum_direction_accuracy": 0.99,
        "strum_max_protected_rate": 0.01,
    },
    "ppo": {
        "horizon": 32,
        "epochs": 5,
        "minibatch_size": 2048,
        "gamma": 0.95,
        "gae_lambda": 0.95,
        "clip_ratio": 0.2,
        "value_coef": 1.0,
        "entropy_coef": 0.001,
        "actor_learning_rate": 3e-6,
        "learning_rate": 3e-4,
        "max_grad_norm": 1.0,
        "target_kl": 0.03,
        "save_interval": 500,
        "log_interval": 1,
    },
    "artifact_max_steps": 900,
    "resource_guard": {
        "max_num_envs": 1024,
        "min_free_vram_gib": 8.0,
        "min_available_ram_gib": 8.0,
        "min_free_disk_gib": 10.0,
    },
}
