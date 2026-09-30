"""Create a reproducible, checkpoint-backed Strike stall diagnosis.

The analyzer is CPU-only.  It does not infer physical causality from scalar
metrics; instead it identifies the exact event windows that the Isaac Gym
recorder should replay to separate isolated-target and transition failures.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path


TREND_FIELDS = (
    "strike_episode_f1",
    "uniform_evidence_strike_episode_f1",
    "strike_release_recall",
    "strike_false_positive_rate",
    "strike_timing_mae_ms",
    "reward",
)


def _load_checkpoint(path):
    import torch

    try:
        checkpoint = torch.load(
            str(path), map_location="cpu", weights_only=True)
    except TypeError:
        checkpoint = torch.load(str(path), map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise ValueError("Strike checkpoint must be a mapping")
    environment = checkpoint.get("environment_state")
    if not isinstance(environment, dict):
        raise ValueError("Strike checkpoint has no environment_state")
    return checkpoint


def _latest_checkpoint(run):
    checkpoints = sorted((run / "checkpoints").glob("strike_*.pt"))
    if not checkpoints:
        raise FileNotFoundError("run has no Strike checkpoints")
    return checkpoints[-1]


def _metric_rows(path):
    previous_iteration = -1
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: damaged or incomplete JSONL") from exc
            if not isinstance(row, dict) or not isinstance(row.get("iteration"), int):
                raise ValueError(f"{path}:{line_number}: missing iteration")
            if row["iteration"] <= previous_iteration:
                raise ValueError(f"{path}:{line_number}: non-increasing iteration")
            previous_iteration = row["iteration"]
            if row.get("curriculum_stage") == "S3_SONG_INTEGRATION":
                yield row


def _trend(rows, width=500):
    bins = defaultdict(list)
    for row in rows:
        iteration = int(row["iteration"])
        bins[(iteration // width) * width].append(row)
    result = []
    for start in sorted(bins):
        group = bins[start]
        summary = {
            "iteration_start": int(group[0]["iteration"]),
            "iteration_end": int(group[-1]["iteration"]),
            "samples": len(group),
        }
        for field in TREND_FIELDS:
            values = [
                float(row[field]) for row in group
                if row.get(field) is not None
                and math.isfinite(float(row[field]))
            ]
            if values:
                summary[field] = sum(values) / len(values)
        result.append(summary)
    return result


def _full_song_reports(run):
    reports = []
    for path in sorted((run / "videos").glob("strike_*_full_song.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        summary = document.get("event_trace_summary", {})
        reports.append({
            "iteration": int(document["iteration"]),
            "report": str(path.resolve()),
            "f1": float(summary.get("traversal_f1", 0.0)),
            "precision": float(summary.get("traversal_precision", 0.0)),
            "recall": float(summary.get("traversal_recall", 0.0)),
            "missed_event_indices": [
                int(event["event_index"])
                for event in document.get("event_trace", ())
                if event.get("miss")
            ],
        })
    return reports


def _repeated_evaluations(run):
    reports = []
    previous_outcomes = {}
    previous_protocol = None
    for path in sorted((run / "evaluations").glob("*.full_song.eval.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        metrics = document["metrics"]
        protocol = document.get("case_protocol")
        outcomes = {}
        failures = defaultdict(lambda: {
            "observed_cases": 0, "missed_cases": 0,
            "physical_missed_cases": 0, "physical_outcome_unknown_cases": 0,
            "unobserved_cases": 0, "wrong_crossing_cases": 0})
        for case in document.get("event_diagnostics", []):
            for event in case["events"]:
                index = int(event["event_index"])
                key = (int(case["case_id"]), index)
                clean = bool(event["target_hit"] and not event["miss"]
                             and event["wrong_crossing_count"] == 0)
                outcomes[key] = clean
                summary = failures[index]
                summary["direction"] = event["direction"]
                summary["strings_0_based"] = event["strings_0_based"]
                observed = event["observed_frames"] > 0
                summary["observed_cases"] += int(observed)
                summary["unobserved_cases"] += int(not observed)
                summary["missed_cases"] += int(bool(event["miss"]))
                physical_miss = event.get("physical_miss_count")
                summary["physical_outcome_unknown_cases"] += int(physical_miss is None)
                summary["physical_missed_cases"] += int(
                    physical_miss is not None and physical_miss > 0)
                summary["wrong_crossing_cases"] += int(
                    (event["wrong_crossing_count"] or 0) > 0)
        comparable = protocol is not None and protocol == previous_protocol
        regressions = [
            {"case_id": key[0], "event_index": key[1]}
            for key, clean in outcomes.items()
            if comparable and not clean and previous_outcomes.get(key) is True]
        reports.append({
            "iteration": int(document["iteration"]),
            "report": str(path.relative_to(run)),
            "episodes": int(document["episodes"]),
            "f1": float(metrics["strike_f1"]),
            "recall": float(metrics["release_recall"]),
            "end_to_end_recovery": float(
                metrics["end_to_end_recovery_completion_rate"]),
            "timing_p95_ms": float(metrics["timing_p95_ms"]),
            "evaluation_protocol": protocol,
            "case_summary": document.get("case_summary"),
            "missed_cases_meaning": "raw_rejected_or_missed_gesture_not_physical_FN",
            "event_failures": [{"event_index": index, **summary}
                               for index, summary in sorted(failures.items())],
            "paired_with_previous": comparable,
            "regressed_case_event_count": len(regressions),
            "regressed_case_events": regressions[:200],
        })
        previous_outcomes = outcomes
        previous_protocol = protocol
    return reports


def _quality_maintenance_diagnostics(rows, reports):
    mastered = [row for row in rows if row.get("curriculum_complete")]
    latest = rows[-1] if rows else {}
    evaluations = ([r for r in reports
                    if r["iteration"] >= mastered[0]["iteration"]]
                   if mastered else [])
    gate = float(latest.get("curriculum_strike_f1_gate", 0.99))
    return {
        "first_mastered_iteration": mastered[0]["iteration"] if mastered else None,
        "current_quality_passed": latest.get("curriculum_current_quality_passed"),
        "gate_stopped_after_mastery": bool(
            len(mastered) > 1 and
            mastered[0].get("curriculum_gate_evaluation_count") ==
            mastered[-1].get("curriculum_gate_evaluation_count")),
        "post_mastery_evaluation_count": len(evaluations),
        "post_mastery_evaluations_below_f1_gate": sum(
            row["f1"] < gate for row in evaluations),
        "rehearsal_ever_active": any(row.get(
            "curriculum_s3_original_tempo_rehearsal_active", False) for row in rows),
        "retention_warning_iterations": sum(row.get(
            "curriculum_original_tempo_retention_passed") is False for row in rows),
        "fixed_case_evaluation_available": any(
            row["evaluation_protocol"] is not None for row in reports),
    }


def _transition_sampling_audit(checkpoint, event_rows):
    """Reconstruct sampling probabilities, not measured transition exposure."""
    import torch
    from tab2body.env.metrics import (
        bounded_failure_sampling_probabilities,
        event_predecessor_rehearsal_scores,
    )

    environment = checkpoint["environment_state"]
    config = checkpoint.get("checkpoint_contract", {}).get(
        "payload", {}).get("config", {}).get("strike", {}).get("curriculum", {})
    required = ("stalled_hard_rehearsal_events", "stalled_hard_sample_fraction",
                "stalled_hard_window_probability_cap")
    if not all(key in config for key in required):
        return {"available": False, "reason": "checkpoint sampling config missing"}
    count = len(event_rows)
    quota = min(int(config[required[0]]),
                int(environment["song_events_per_episode"]), count)
    scores = torch.tensor([row["failure_score"] for row in event_rows])
    windows = event_predecessor_rehearsal_scores(scores, quota)
    active = bool((windows > 0).any()) and bool(environment.get("random_start"))
    active = active and environment.get("curriculum_stage") == "S3_SONG_INTEGRATION"
    active = active and not environment.get("evaluation_full_song", False)
    active = active and float(config[required[1]]) > 0.0
    probabilities = (bounded_failure_sampling_probabilities(
        windows, max(float(config[required[2]]), 1.0 / len(windows)))
        if active else torch.zeros_like(windows))
    fraction = float(config[required[1]]) if active else 0.0
    rows = []
    for event in sorted(event_rows, key=lambda row: row["failure_score"],
                        reverse=True)[:15]:
        index = event["event_index"]
        def mass(left, right):
            return sum(float(probability) for start, probability in
                       enumerate(probabilities) if start <= left
                       and right < start + quota)
        rows.append({
            "event_index": index,
            "failure_score": event["failure_score"],
            "event_exposure_mass": event["exposure_mass"],
            "hard_event_probability": mass(index, index),
            "hard_incoming_probability": (
                mass(index - 1, index) if index > 0 else None),
            "hard_incoming_outgoing_probability": (
                mass(index - 1, index + 1) if 0 < index < count - 1 else None),
        })
    return {
        "available": True, "hard_sampling_active": active,
        "hard_episode_fraction": fraction, "hard_window_event_count": quota,
        "probability_scope": "conditional_on_hard_episode",
        "evidence_scope": "reconstructed_from_checkpoint_not_measured_transitions",
        "events": rows,
    }


def analyze(run, checkpoint, goal, focus_event=None):
    checkpoint_document = _load_checkpoint(checkpoint)
    environment = checkpoint_document["environment_state"]
    score = environment["event_failure_score"].reshape(-1).tolist()
    exposure = environment["event_failure_exposure"].reshape(-1).tolist()
    failure_mass = environment["event_failure_mass"].reshape(-1).tolist()
    goal_document = json.loads(goal.read_text(encoding="utf-8"))
    events = goal_document["events"]
    if len(score) != len(events):
        raise ValueError("checkpoint failure vector and Strike plan differ")
    if focus_event is None:
        focus_event = max(range(len(score)), key=score.__getitem__)
    if not 0 <= focus_event < len(events):
        raise ValueError("focus event is outside the Strike plan")

    event_rows = []
    direction_groups = defaultdict(list)
    for index, (event, value, seen, failed) in enumerate(zip(
            events, score, exposure, failure_mass)):
        row = {
            "event_index": index,
            "frame": int(event["frame"]),
            "time_s": float(event["time"]),
            "string": int(event["strings"][0]),
            "direction": str(event["direction"]),
            "failure_score": float(value),
            "failure_mass": float(failed),
            "exposure_mass": float(seen),
            "previous_gap_s": (
                None if index == 0 else
                float(event["time"] - events[index - 1]["time"])),
            "next_gap_s": (
                None if index + 1 == len(events) else
                float(events[index + 1]["time"] - event["time"])),
        }
        event_rows.append(row)
        direction_groups[row["direction"]].append(row)

    direction_summary = {}
    for direction, group in direction_groups.items():
        direction_summary[direction] = {
            "event_count": len(group),
            "mean_failure_score": sum(
                row["failure_score"] for row in group) / len(group),
            "events_above_0_05": sum(
                row["failure_score"] >= 0.05 for row in group),
        }

    metric_rows = list(_metric_rows(run / "logs" / "metrics.jsonl"))
    latest_metric = metric_rows[-1] if metric_rows else {}
    reports = _full_song_reports(run)
    repeated = _repeated_evaluations(run)
    best_report = max(reports, key=lambda item: item["f1"]) if reports else None
    scenarios = []
    for tempo_lambda in (0.0, 1.0):
        for start, count, purpose in (
                (focus_event, 1, "isolated_target_geometry"),
                (max(0, focus_event - 1), 2, "incoming_transition"),
                (max(0, focus_event - 1), 3, "incoming_and_outgoing_transition")):
            scenarios.append({
                "start_event": start,
                "event_count": min(count, len(events) - start),
                "tempo_lambda": tempo_lambda,
                "purpose": purpose,
            })

    return {
        "schema": "tab2body.strike_stall_diagnostic.v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run": str(run.resolve()),
        "checkpoint": str(checkpoint.resolve()),
        "checkpoint_iteration": int(checkpoint_document.get("iteration", -1)),
        "goal": str(goal.resolve()),
        "current_stage": latest_metric.get("curriculum_stage"),
        "current_tempo_lambda": latest_metric.get("curriculum_tempo_lambda"),
        "current_gate_failure": latest_metric.get(
            "curriculum_last_gate_failures"),
        "current_gate_f1": latest_metric.get("curriculum_strike_f1_gate"),
        "current_uniform_f1": latest_metric.get(
            "uniform_evidence_strike_episode_f1"),
        "current_release_recall": latest_metric.get("strike_release_recall"),
        "trend_500_iterations": _trend(metric_rows),
        "direction_summary": direction_summary,
        "top_failure_events": sorted(
            event_rows, key=lambda row: row["failure_score"], reverse=True)[:15],
        "focus_event": event_rows[focus_event],
        "physical_replay_scenarios": scenarios,
        "transition_sampling_audit": _transition_sampling_audit(
            checkpoint_document, event_rows),
        "full_song_reports": reports,
        "best_full_song_report": best_report,
        "repeated_evaluation_reports": repeated,
        "quality_maintenance": _quality_maintenance_diagnostics(
            metric_rows, repeated),
        "video_and_repeated_evaluation_are_distinct": True,
    }


def parser():
    result = argparse.ArgumentParser(
        description="analyze a stalled Strike run without allocating Isaac Gym")
    result.add_argument("--run", required=True, type=Path)
    result.add_argument("--checkpoint", type=Path, default=None)
    result.add_argument("--goal", type=Path, default=None)
    result.add_argument("--focus-event", type=int, default=None,
                        help="defaults to the largest checkpoint failure score")
    result.add_argument("--output", type=Path, default=None)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    run = args.run.resolve()
    if not run.is_dir():
        raise FileNotFoundError(f"Strike run does not exist: {run}")
    checkpoint = (
        args.checkpoint.resolve() if args.checkpoint is not None
        else _latest_checkpoint(run))
    if args.goal is None:
        manifest = json.loads(
            (run / "run_manifest.json").read_text(encoding="utf-8"))
        saved_goal = Path(manifest["goal"])
        goal = saved_goal.resolve()
        if not goal.is_file():
            repository = Path(__file__).resolve().parents[2]
            goal = repository / "data" / "song_bundles" / (
                saved_goal.parents[1].name) / "training" / saved_goal.name
    else:
        goal = args.goal.resolve()
    if not goal.is_file():
        raise FileNotFoundError(f"Strike goal does not exist: {goal}")
    report = analyze(run, checkpoint, goal, args.focus_event)
    output = (
        args.output.resolve() if args.output is not None else
        run / "evaluations" /
        f"stall_diagnostic_{report['checkpoint_iteration']:06d}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "focus_event": report["focus_event"],
        "direction_summary": report["direction_summary"],
        "best_full_song_report": report["best_full_song_report"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
