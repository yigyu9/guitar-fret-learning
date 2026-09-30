"""Isaac-free checkpoint setup and evidence aggregation for fret rollouts."""
from copy import deepcopy
from pathlib import Path

from tab2body.learning.checkpoint_contract import (
    canonical_sha256, file_sha256, validate_contract_document,
)


def rollout_configuration(checkpoint, defaults, *, goal, hand_targets, root):
    payload = validate_contract_document(checkpoint["checkpoint_contract"])["payload"]
    if payload.get("task") != "fret":
        raise ValueError("rollout requires a fret checkpoint")
    for name, path in (("goal", goal), ("hand_targets", hand_targets)):
        actual = file_sha256(path) if path else None
        if actual != payload["inputs"][name + "_sha256"]:
            raise ValueError(f"rollout {name} differs from checkpoint input")
    for entry in payload["fingerprints"]["asset"]["manifest"]:
        path = Path(root) / entry["path"]
        if not path.is_file() or file_sha256(path) != entry["sha256"]:
            raise ValueError(f"rollout asset differs from checkpoint: {path}")
    config = deepcopy(defaults)
    config.update(deepcopy(payload["config"]["reward_safety"]))
    config.update(deepcopy(payload["control"]))
    config["curriculum"] = config.pop("fingertip_approach_curriculum", {})
    config["observation_contract"] = payload["observation"]["schema"]
    config["preparation_frames"] = payload["config"]["timing"]["preparation_frames"]
    for path_key, hash_key in (
        ("human_hard_limit_path", "human_hard_limit_profile_sha256"),
        ("reference_motion_prior_path", "reference_motion_prior_sha256"),
    ):
        digest = config.get(hash_key)
        if digest and file_sha256(config[path_key]) != digest:
            raise ValueError(f"rollout {path_key} differs from checkpoint")
    return config, payload


def verify_rollout_model(env, model, payload):
    expected = payload["model"]
    for name in ("num_obs", "num_actions", "value_dim"):
        if int(getattr(env, name)) != expected[name]:
            raise ValueError(f"rollout {name} differs from checkpoint")
    for key, actual in (
        ("model_architecture_version", getattr(model, "MODEL_ARCHITECTURE_VERSION", "actor_critic.mlp.v1")),
        ("policy_distribution_version", model.POLICY_DISTRIBUTION_VERSION),
    ):
        if actual != expected[key]:
            raise ValueError(f"rollout {key} differs from checkpoint")
    if canonical_sha256(env.observation_manifest) != payload["observation"]["manifest_sha256"]:
        raise ValueError("rollout observation manifest differs from checkpoint")
    names = [env.dof_names[i] for i in env.ctrl_idx.detach().cpu().tolist()]
    if names != payload["control"]["controlled_dof_names"]:
        raise ValueError("rollout joint order differs from checkpoint")
    for key in ("action_scale", "action_alpha", "reset_soft_limit_fraction"):
        if float(getattr(env, key)) != payload["control"][key]:
            raise ValueError(f"rollout {key} differs from checkpoint")
    timing = payload["config"]["timing"]
    if env.SIM_HZ != timing["sim_hz"] or env.SUBSTEPS != timing["sim_substeps"]:
        raise ValueError("rollout simulation timing differs from checkpoint")


class EventEvidence:
    """Per-finger evidence, attributed to an event only when assignment is unique."""

    METRICS = ("target_distance", "target_region_inside_rate",
               "precision_press_frame_rate", "precision_position_frame_rate",
               "precision_arch_frame_rate", "precision_precise_frame_rate",
               "fine_longitudinal_quality", "fine_lateral_quality",
               "fine_normal_quality")

    def __init__(self):
        self.events = {}

    def update(self, frame, goal, info):
        for string, (fret, finger, event) in enumerate(zip(
                goal["fret"], goal["finger"], goal["sustain_event_id"])):
            if fret <= 0 or finger <= 0 or event < 0:
                continue
            row = self.events.setdefault(event, {
                "event_id": event, "string_index": string, "fret": fret,
                "finger": finger, "first_observed_frame": frame,
                "last_observed_frame": frame, "observed_frames": 0,
                "eligible_frames": 0, "ambiguous_frames": 0,
                "unique_assignment_frames": 0, "first_press_frame": None,
                "metric_sums": {name: 0.0 for name in self.METRICS},
            })
            row["last_observed_frame"] = frame
            row["observed_frames"] += 1
            row["eligible_frames"] += int(goal["sustain_eligible"][string])
            if sum(f == finger and v > 0 for f, v in zip(goal["finger"], goal["fret"])) > 1:
                row["ambiguous_frames"] += 1
                continue
            row["unique_assignment_frames"] += 1
            for name in self.METRICS:
                value = float(info[f"finger_{finger}_{name}"])
                row["metric_sums"][name] += value
                if name == "precision_press_frame_rate" and value >= 1.0 and row["first_press_frame"] is None:
                    row["first_press_frame"] = frame

    def report(self):
        rows = []
        for row in self.events.values():
            row = deepcopy(row)
            count = row["unique_assignment_frames"]
            row["means"] = {name: value / count if count else None
                            for name, value in row.pop("metric_sums").items()}
            rows.append(row)
        return sorted(rows, key=lambda row: (row["first_observed_frame"], row["string_index"]))
