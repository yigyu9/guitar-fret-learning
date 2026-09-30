"""Fixed evaluation cohorts, case diagnostics and repeated-evaluation ranking."""
import math
import hashlib


EVALUATION_SEED = 1729


def reconcile_event_diagnostics(case, info, local):
    events = case.get("event_diagnostics", [])
    reasons = {key: bool(info["episode_" + key][local].item())
               for key in ("failure_termination", "early_timeout", "goal_finished")
               if "episode_" + key in info}
    early = reasons.get("failure_termination", False) or reasons.get("early_timeout", False)
    for event in events:
        event["observation_status"] = (
            "not_reached_early_termination" if early and not event["observed_frames"]
            else "unobserved" if not event["observed_frames"]
            else "observed_outcome_unknown" if event["physical_miss_count"] is None
                 or event["physical_hit_count"] is None
            else "observed_physical_miss" if event["physical_miss_count"]
            else "observed_physical_hit" if event["physical_hit_count"]
            else "observed_unresolved")
    reconciled = {"count_units": {"true_positive": "resolved_gesture",
                                  "false_negative": "resolved_gesture",
                                  "false_positive": "wrong_crossing"},
                  "termination_reasons": reasons,
                  "raw_miss_event_count": sum(event["miss"] for event in events),
                  "unobserved_event_count": sum(not event["observed_frames"] for event in events)}
    for label, field in (("true_positive", "physical_hit_count"),
                         ("false_negative", "physical_miss_count"),
                         ("false_positive", "wrong_crossing_count")):
        key = "strike_" + label + "_count"
        raw = float(info[key][local].item()) if key in info else None
        available = all(event[field] is not None for event in events)
        total = sum(event[field] for event in events) if available else None
        reconciled[label] = {"episode_count": raw, "event_count": total,
                             "matches": (abs(raw - total) <= 1e-6
                                         if raw is not None and total is not None else None)}
    case["event_reconciliation"] = reconciled


def model_tensor_sha256(model):
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str((value.dtype, tuple(value.shape))).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def fixed_evaluation_cases(torch, env, model, episodes, seed=EVALUATION_SEED):
    if episodes < 1:
        raise ValueError("evaluation episodes must be positive")
    for batch, offset in enumerate(range(0, episodes, env.num_envs)):
        count = min(env.num_envs, episodes - offset)
        env.rng.manual_seed(seed + batch)
        env._reset_generation.zero_()
        obs = env.reset()
        pending = set(range(count))
        conditions = {}
        for env_id in pending:
            case = {"case_id": offset + env_id, "env_id": env_id,
                    "seed": seed + batch, "batch": batch}
            for key in ("target_lane_y", "event_index", "song_time_s",
                        "practice_direction", "_reset_generation"):
                value = getattr(env, key, None)
                if value is not None:
                    case[key.lstrip("_")] = value[env_id].item()
            conditions[env_id] = case
        goals = getattr(env, "goals", None)
        if goals is not None:
            directions = goals.direction.detach().cpu().tolist()
            strings = goals.traversal_mask.detach().cpu().tolist()
            for case in conditions.values():
                case["event_diagnostics"] = [
                    {"event_index": index, "direction": directions[index],
                     "strings_0_based": [s for s, active in enumerate(strings[index]) if active],
                     "observed_frames": 0, "target_hit": False, "miss": False,
                     "wrong_crossing_count": 0.0,
                     "physical_hit_count": 0, "physical_miss_count": 0}
                    for index in range(goals.num_events)]
        with torch.no_grad():
            for _ in range(env.max_episode_length + 2):
                event_indices = (env.event_index[:count].detach().cpu().tolist()
                                 if goals is not None else None)
                action, _, _ = model.act(obs, deterministic=True)
                obs, _, done, info = env.step(action)
                if goals is not None:
                    if "target_event_index_before_step" in info:
                        event_indices = info["target_event_index_before_step"][:count].detach().cpu().tolist()
                    signals = {key: info[key][:count].detach().cpu().tolist()
                               for key in ("target_hit", "miss", "wrong_crossing_count",
                                           "physical_target_hit", "physical_target_miss")
                               if key in info}
                    for env_id in pending:
                        index = int(event_indices[env_id])
                        if not 0 <= index < goals.num_events:
                            continue
                        event = conditions[env_id]["event_diagnostics"][index]
                        event["observed_frames"] += 1
                        for signal, field in (("physical_target_hit", "physical_hit_count"),
                                              ("physical_target_miss", "physical_miss_count")):
                            if signal not in signals:
                                event[field] = None
                            elif event[field] is not None:
                                event[field] += int(bool(signals[signal][env_id]))
                        if "wrong_crossing_count" not in signals:
                            event["wrong_crossing_count"] = None
                        for key, values in signals.items():
                            if key == "wrong_crossing_count":
                                if event[key] is not None:
                                    event[key] += float(values[env_id])
                            elif key in ("target_hit", "miss"):
                                event[key] |= bool(values[env_id])
                ids = torch.nonzero(done).flatten().cpu().tolist()
                if len(ids) != info[env.episode_metric_keys[0]].numel():
                    raise RuntimeError("strike episode metrics are not aligned with done")
                for local, env_id in enumerate(ids):
                    if env_id not in pending:
                        continue
                    pending.remove(env_id)
                    if goals is not None:
                        reconcile_event_diagnostics(conditions[env_id], info, local)
                    yield conditions[env_id], local, info
                if not pending:
                    break
        if pending:
            raise RuntimeError(f"evaluation cases did not finish: {sorted(pending)}")


def repeated_case_summary(rows):
    values = sorted(float(row["strike_episode_f1"]) for row in rows)
    index = (len(values) - 1) * 0.1
    lo, hi = math.floor(index), math.ceil(index)
    clean = sum(
        row.get("strike_false_positive_count", 0) == 0
        and row.get("strike_false_negative_count", 0) == 0
        and row.get("strike_release_recall", 0) >= 1.0 - 1e-6
        and not row.get("failure_termination", False)
        for row in rows)
    return {"f1_mean": sum(values) / len(values),
            "f1_p10": values[lo] + (values[hi] - values[lo]) * (index - lo),
            "clean_full_song_rate": clean / len(rows),
            "case_count": len(rows)}


def repeated_evaluation_quality_key(report):
    summary, metrics = report["case_summary"], report["metrics"]
    eligibility = report["quality_eligibility"]
    key = (bool(eligibility["safety_passed"]), bool(eligibility["grip_passed"]),
           summary["clean_full_song_rate"], summary["f1_p10"],
           metrics["strike_f1"], metrics["release_recall"],
           -metrics["false_positive_rate"], -metrics["timing_p95_ms"])
    if not all(math.isfinite(float(value)) for value in key):
        raise ValueError("repeated evaluation quality must be finite")
    return tuple(float(value) for value in key)
