"""Diagnose the active Fret goal-pair curriculum from append-only metrics.

The tool is deliberately read-only with respect to training.  It selects the
largest suffix with the same stage/phase/difficulty/recovery identity, pools
conditional metrics by their evidence counts, and reports both current-level
and final-promotion deficits.  This prevents global F1 from hiding a weak,
rare finger or chord.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

from tab2body.learning.curriculum import (
    FingertipApproachCurriculum, FingertipApproachCurriculumConfig,
)


FINGER_LABELS = {1: "index", 2: "middle", 3: "ring", 4: "pinky"}


def _number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def load_rows(path: Path):
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                continue
            raise
        if not isinstance(value, Mapping):
            raise ValueError(f"metrics row {index + 1} is not an object")
        rows.append(value)
    if not rows:
        raise ValueError("metrics log is empty")
    return rows


def _field(row, name, default=None):
    next_name = f"next_curriculum_{name}"
    current_name = f"curriculum_{name}"
    return row.get(current_name, row.get(next_name, default))


def load_run_config(metrics_path, manifest_path=None):
    path = (Path(manifest_path) if manifest_path else
            Path(metrics_path).parent.parent / "run_manifest.json")
    if not path.exists():
        return FingertipApproachCurriculumConfig(), {
            "source": "defaults", "warning": "run manifest missing; thresholds unverified"}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    saved = manifest.get("curriculum_config")
    if not isinstance(saved, Mapping):
        raise ValueError(f"curriculum_config missing in {path}")
    defaults = FingertipApproachCurriculumConfig()
    names = {field.name for field in fields(defaults)}
    values = {
        key: tuple(value) if isinstance(getattr(defaults, key), tuple) else value
        for key, value in saved.items() if key in names}
    return FingertipApproachCurriculumConfig(**values), {
        "source": str(path.resolve()),
        "checkpoint_contract_sha256": manifest.get("checkpoint_contract_sha256"),
        "missing_fields_using_defaults": sorted(names - set(saved)),
        "unknown_fields": sorted(set(saved) - names),
    }


def regime_key(row):
    return (
        _field(row, "stage", ""),
        _field(row, "goal_pair_phase", ""),
        int(_field(row, "goal_pair_mixed_level", -1)),
        bool(_field(row, "goal_pair_recovery", False)),
        int(_field(row, "goal_pair_recovery_rollback_count", 0)),
    )


def current_regime(rows, maximum_rows=100):
    key = regime_key(rows[-1])
    start = len(rows) - 1
    while start > 0 and regime_key(rows[start - 1]) == key:
        start -= 1
    selected = rows[start:]
    if maximum_rows > 0:
        selected = selected[-maximum_rows:]
    return selected, key, start


def _mean(rows: Iterable[Mapping], key):
    values = [float(row[key]) for row in rows if _number(row.get(key))]
    return sum(values) / len(values) if values else None


def _weighted(rows, key, count_key):
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        value = row.get(key)
        count = row.get(count_key)
        if _number(value) and _number(count) and float(count) > 0:
            numerator += float(value) * float(count)
            denominator += float(count)
    return (numerator / denominator if denominator else None, denominator)


def _conditional(rows, prefix, count_suffix, fields):
    count_key = prefix + count_suffix
    result = {}
    count = 0.0
    for label, suffix in fields.items():
        value, observed = _weighted(rows, prefix + suffix, count_key)
        result[label] = value
        count = max(count, observed)
    result["count"] = count
    return result


def _short_sequence(rows, finger):
    numerator = denominator = 0.0
    invalid = 0
    for row in rows:
        sequence = f"curriculum_goal_pair_sequence_finger_{finger}_"
        full = f"curriculum_goal_pair_full_song_finger_{finger}_"
        n, f = row.get(sequence + "target_active_count"), row.get(full + "target_active_count")
        rate, full_rate = row.get(sequence + "press_success"), row.get(full + "press_success")
        if not (_number(n) and _number(f) and _number(rate)):
            continue
        if f > 0 and not _number(full_rate):
            continue
        count = n - f
        success = rate * n - (full_rate * f if f else 0.0)
        tolerance = 1e-5 * max(1.0, n)
        if count < 0 or success < -tolerance or success > count + tolerance:
            invalid += 1
            continue
        numerator += min(count, max(0.0, success))
        denominator += count
    return {"success": numerator / denominator if denominator else None,
            "count": denominator, "success_frames": numerator,
            "invalid_rows": invalid,
            "derived_from": "sequence minus full_song; sampled target frames"}


def _gate_report(rows, config):
    latest = rows[-1]
    for key in ("next_curriculum_goal_pair_gate_report",
                "curriculum_goal_pair_gate_report"):
        value = latest.get(key)
        if isinstance(value, str) and value:
            report = json.loads(value)
            if report and report.get("iteration") == latest.get("iteration"):
                return {"source": "runtime_decision", **report}
    if _field(latest, "stage") != "goal_pair":
        return {"source": "not_applicable", "checks": {}, "failures": [],
                "evidence_shortages": []}
    curriculum = FingertipApproachCurriculum(config, forced_stage="goal_pair")
    curriculum.goal_pair_phase = _field(latest, "goal_pair_phase", "retention")
    curriculum.goal_pair_mixed_level = max(0, _field(latest, "goal_pair_mixed_level", 0))
    curriculum.goal_pair_recovery_active = bool(_field(latest, "goal_pair_recovery", False))
    curriculum.goal_pair_recovery_iteration = _field(latest, "goal_pair_recovery_iteration", 0)
    curriculum.goal_pair_recovery_good_windows = _field(latest, "goal_pair_recovery_good_windows", 0)
    curriculum.goal_pair_phase_iteration = _field(latest, "goal_pair_phase_iteration", 0)
    curriculum.goal_pair_mixed_level_iteration = _field(latest, "goal_pair_mixed_level_iteration", 0)
    curriculum.stage_iteration = _field(latest, "stage_iteration", 0)
    curriculum.regression_hold = bool(_field(latest, "regression_hold", False))
    curriculum.total_iteration = latest.get("iteration", 0)
    for row in rows:
        curriculum._accumulate_goal_pair_phase_stats(row)
    pooled = curriculum._goal_pair_aggregated_stats(latest)
    # Sequence checks use their own frame evidence, not episode means.
    for finger in (None, 1, 2, 3, 4):
        prefix = ("curriculum_goal_pair_sequence_" if finger is None else
                  f"curriculum_goal_pair_sequence_finger_{finger}_")
        count_key = prefix + ("active_count" if finger is None else "target_active_count")
        suffixes = ("press_success", "no_press_success", "wrong_press", "penetration",
                    "thumb_support") if finger is None else (
                        "press_success", "target_distance", "hold_quality",
                        "dropout_rate", "wrong_press")
        counts = [row[count_key] for row in rows if _number(row.get(count_key))]
        if not counts:
            continue
        pooled[count_key] = sum(counts)
        for suffix in suffixes:
            value, _ = _weighted(rows, prefix + suffix, count_key)
            if value is not None:
                pooled[prefix + suffix] = value
    report = curriculum.goal_pair_gate_diagnostics(pooled)
    # Scalar-only old logs cannot reconstruct hidden mastery/bridge state.
    for name, check in report["checks"].items():
        if name.endswith(("_mastered", "_streak")) or name == "bridge_windows":
            check.update(value=None, passed=None)
    counter_fields = {
        "stage_age": "stage_iteration", "regression_clear": "regression_hold",
        "recovery_age": "goal_pair_recovery_iteration",
        "recovery_good_windows": "goal_pair_recovery_good_windows",
        "phase_age": ("goal_pair_phase_iteration" if curriculum.goal_pair_phase == "retention"
                      else "goal_pair_mixed_level_iteration"),
        "difficulty_ready": "goal_pair_phase_iteration",
    }
    for name, field in counter_fields.items():
        if name in report["checks"] and _field(latest, field) is None:
            report["checks"][name].update(value=None, passed=None)
    report["failures"] = [name for name, check in report["checks"].items()
                          if check["passed"] is False and not check.get("evidence")
                          and check.get("blocks_promotion", True)]
    report["evidence_shortages"] = [
        name for name, check in report["checks"].items()
        if check.get("blocks_promotion", True)
        and (check["passed"] is None or (check.get("evidence") and not check["passed"]))]
    return {"source": "sampled_window_reconstruction",
            "limitation": "Missing mastery/bridge history; this is not the original promotion decision.",
            **report}


def _threshold_result(value, threshold, *, lower_bound=True):
    if value is None:
        return {"passed": False, "value": None, "threshold": threshold,
                "deficit": None}
    deficit = (threshold - value if lower_bound else value - threshold)
    return {"passed": deficit <= 0.0, "value": value,
            "threshold": threshold, "deficit": max(0.0, deficit)}


def diagnose(rows, *, window=100, config=None, config_provenance=None):
    config = config or FingertipApproachCurriculumConfig()
    selected, key, regime_start = current_regime(rows, maximum_rows=window)
    stage, phase, level, recovery, rollback_count = key
    latest = selected[-1]
    gate_report = _gate_report(selected, config)
    preview_only = (
        phase == "mixed" and level < config.goal_pair_preview_levels)
    level_index = min(max(level, 0),
                      len(config.goal_pair_mixed_press_rates) - 1)
    summary = {
        name: _mean(selected, metric) for name, metric in {
            "reward": "reward", "f1": "f1_l",
            "press_success": "press_success_rate",
            "chord_ready": "chord_ready_rate",
            "sustain_success": "sustain_event_success_rate_pooled",
            "wrong_press": "wrong_press_rate",
            "press_dropout": "press_dropout_rate",
            "value_loss": "value_loss", "kl": "kl",
        }.items()
    }
    summary["ppo_early_stop_rate"] = _mean([
        {"v": 1.0 if row.get("ppo_early_stop") else 0.0}
        for row in selected], "v")

    preservation = _conditional(
        selected, "curriculum_goal_pair_pretransition_", "active_count", {
            "quality": "current_press_quality",
            "preserved_rate": "current_press_preserved",
        })
    fingers = {}
    current_failures = []
    final_failures = []
    minimum = config.goal_pair_phase_min_evidence
    for finger, label in FINGER_LABELS.items():
        rehearsal_prefix = f"curriculum_goal_pair_rehearsal_finger_{finger}_"
        transition_prefix = f"curriculum_goal_pair_transition_finger_{finger}_"
        full_prefix = f"curriculum_goal_pair_full_song_finger_{finger}_"
        rehearsal = _conditional(
            selected, rehearsal_prefix, "target_active_count", {
                "success": "press_success", "distance_m": "target_distance",
                "hold_quality": "hold_quality",
                "hold_acquired_frame_rate": "hold_acquired_frame_rate",
                "full_hold_frame_rate": "full_hold_frame_rate",
                "dropout_rate": "dropout_rate",
                "wrong_press": "wrong_press",
            })
        transition_target = _conditional(
            selected, transition_prefix, "target_active_count", {
                "success": "press_success", "distance_m": "target_distance",
                "hold_quality": "hold_quality",
                "hold_acquired_frame_rate": "hold_acquired_frame_rate",
                "full_hold_frame_rate": "full_hold_frame_rate",
                "dropout_rate": "dropout_rate",
                "wrong_press": "wrong_press",
            })
        transition_next = _conditional(
            selected, transition_prefix, "next_active_count", {
                "distance_m": "next_distance", "progress": "next_progress",
            })
        full_song = _conditional(
            selected, full_prefix, "target_active_count", {
                "success": "press_success", "distance_m": "target_distance",
                "hold_quality": "hold_quality",
                "hold_acquired_frame_rate": "hold_acquired_frame_rate",
                "full_hold_frame_rate": "full_hold_frame_rate",
                "dropout_rate": "dropout_rate",
                "wrong_press": "wrong_press",
            })
        sequence = _conditional(
            selected, f"curriculum_goal_pair_sequence_finger_{finger}_",
            "target_active_count", {
                "success": "press_success", "distance_m": "target_distance",
                "hold_quality": "hold_quality",
                "hold_acquired_frame_rate": "hold_acquired_frame_rate",
                "full_hold_frame_rate": "full_hold_frame_rate",
                "dropout_rate": "dropout_rate",
                "wrong_press": "wrong_press",
            })
        current_checks = {
            "rehearsal_evidence": _threshold_result(
                rehearsal["count"], minimum),
            "rehearsal_success": _threshold_result(
                rehearsal["success"], config.goal_pair_rehearsal_press_rate),
            "rehearsal_distance": _threshold_result(
                rehearsal["distance_m"], config.goal_pair_rehearsal_distance,
                lower_bound=False),
            "rehearsal_hold": _threshold_result(
                rehearsal["hold_quality"],
                config.goal_pair_rehearsal_hold_quality),
            "rehearsal_dropout": _threshold_result(
                rehearsal["dropout_rate"],
                config.goal_pair_rehearsal_dropout_rate, lower_bound=False),
            "next_evidence": _threshold_result(
                transition_next["count"], minimum),
            "next_distance": _threshold_result(
                transition_next["distance_m"],
                config.goal_pair_mixed_distances[level_index],
                lower_bound=False),
            "next_progress": _threshold_result(
                transition_next["progress"],
                config.goal_pair_mixed_min_next_progress),
            "full_song_evidence": _threshold_result(
                full_song["count"],
                config.goal_pair_full_song_focus_min_evidence),
            "full_song_success": _threshold_result(
                full_song["success"],
                config.goal_pair_mixed_full_song_press_rates[level_index]),
        }
        if not preview_only:
            current_checks.update({
                "transition_evidence": _threshold_result(
                    transition_target["count"], minimum),
                "transition_success": _threshold_result(
                    transition_target["success"],
                    config.goal_pair_mixed_press_rates[level_index]),
            })
        final_checks = {
            "transition_evidence": _threshold_result(
                transition_target["count"], minimum),
            "next_evidence": _threshold_result(
                transition_next["count"], minimum),
            "transition_success": _threshold_result(
                transition_target["success"],
                config.goal_pair_promotion_transition_press_rate),
            "full_song_success": _threshold_result(
                full_song["success"],
                config.goal_pair_mixed_full_song_press_rates[-1]),
        }
        for check, result in current_checks.items():
            if not result["passed"]:
                current_failures.append(f"{label}.{check}")
        for check, result in final_checks.items():
            if not result["passed"]:
                final_failures.append(f"{label}.{check}")
        fingers[str(finger)] = {
            "label": label, "rehearsal": rehearsal,
            "transition_target": transition_target,
            "transition_next": transition_next, "full_song": full_song,
            "sequence_including_full_song": sequence,
            "short_sequence": _short_sequence(selected, finger),
            "current_level_checks": current_checks,
            "final_promotion_checks": final_checks,
        }

    chord_shapes = {}
    weak_chords = []
    for signature in range(1, 16):
        prefix = f"curriculum_chord_shape_{signature}_"
        row = _conditional(selected, prefix, "target_active_count", {
            "success": "success", "distance_m": "distance",
            "alignment": "alignment",
        })
        if row["count"] > 0:
            chord_shapes[str(signature)] = row
            if row["count"] >= 64 and (row["success"] or 0.0) < 0.50:
                weak_chords.append(signature)

    preservation_check = _threshold_result(
        preservation["quality"],
        config.goal_pair_pretransition_preservation_rate)
    preservation_evidence = _threshold_result(
        preservation["count"], minimum)
    if not preservation_check["passed"]:
        final_failures.append("global.pretransition_preservation")
    if not preservation_evidence["passed"]:
        final_failures.append("global.pretransition_evidence")

    recommendations = []
    sequence_failures = [name for name in gate_report["failures"]
                         if name.startswith("sequence_finger_")]
    if sequence_failures:
        recommendations.append({
            "priority": "P0", "kind": "sequence_transfer",
            "failures": sequence_failures,
            "message": "Use event-level rollout evidence to distinguish short-sequence failures from full-song failures; check arrival and hold before changing weights.",
        })
    weakest_full = min(
        fingers.values(),
        key=lambda item: (item["full_song"]["success"]
                          if item["full_song"]["success"] is not None else -1))
    if (weakest_full["full_song"]["success"] is not None
            and weakest_full["full_song"]["success"]
            < config.goal_pair_mixed_full_song_press_rates[-1]):
        recommendations.append({
            "priority": "P0", "kind": "finger_transfer",
            "finger": weakest_full["label"],
            "message": "Inspect failed song events and evidence for the weakest finger before changing sampling or reward.",
        })
    if not preservation_check["passed"]:
        recommendations.append({
            "priority": "P0", "kind": "press_preservation",
            "message": "Current-note preservation is below the final gate; mine transitions by outgoing held finger and report quality before increasing difficulty.",
        })
    evidence_failures = [name for name in current_failures
                         if name.endswith("evidence")]
    if evidence_failures:
        recommendations.append({
            "priority": "P1", "kind": "evidence_coverage",
            "failures": evidence_failures,
            "message": "The current regime lacks conditional evidence; adjust sampling only after this persists for a complete phase window.",
        })
    if weak_chords:
        recommendations.append({
            "priority": "P1", "kind": "weak_chord_shape",
            "signatures": weak_chords,
            "message": "Add a targeted diagnostic cohort for weak finger-set signatures before changing their reward.",
        })

    sequence_frames = sum(f["sequence_including_full_song"]["count"] for f in fingers.values())
    exposure = {
        str(finger): {
            "sequence_target_frame_fraction": (
                fingers[str(finger)]["sequence_including_full_song"]["count"] / sequence_frames
                if sequence_frames else None),
            "recovery_assignment_fraction": latest.get(
                f"curriculum_goal_pair_sampler_finger_{finger}_actual_fraction"),
        } for finger in range(1, 5)}
    return {
        "schema": "tab2body.fret_goal_pair_diagnosis.v2",
        "configuration": config_provenance or {"source": "caller_or_defaults"},
        "evidence_unit": "sampled target frames, not independent events",
        "gate_report": gate_report,
        "exposure": exposure,
        "source_rows": len(rows),
        "window_rows": len(selected),
        "regime_start_row": regime_start,
        "iteration_range": [selected[0].get("iteration"),
                            selected[-1].get("iteration")],
        "regime": {"stage": stage, "phase": phase,
                   "mixed_level": level, "preview_only": preview_only,
                   "recovery": recovery, "rollback_count": rollback_count,
                   "focus_finger": _field(latest, "goal_pair_focus_finger", 0),
                   "mastered_count": _field(
                       latest, "goal_pair_mastered_count", 0)},
        "summary": summary,
        "preservation": {**preservation, "evidence_check": preservation_evidence,
                         "quality_check": preservation_check},
        "fingers": fingers, "chord_shapes": chord_shapes,
        "current_level_failures": sorted(set(current_failures)),
        "checklist_scope": "legacy per-finger checklist; gate_report uses shared runtime gate code",
        "final_promotion_failures": sorted(set(final_failures)),
        "weak_chord_signatures": weak_chords,
        "recommendations": recommendations,
        "thresholds": {
            key: value for key, value in asdict(config).items()
            if key.startswith("goal_pair_")},
    }


def render_markdown(document, metrics_path):
    regime = document["regime"]
    summary = document["summary"]
    lines = [
        "# Fret goal-pair diagnosis", "",
        f"- metrics: `{metrics_path}`",
        f"- iterations: {document['iteration_range'][0]}–{document['iteration_range'][1]}",
        f"- regime: `{regime['stage']} / {regime['phase']} / level {regime['mixed_level']}`",
        f"- focus/mastered: finger {regime['focus_finger']} / {regime['mastered_count']} of 4",
        f"- configuration: `{document['configuration']['source']}`",
        f"- evidence: {document['evidence_unit']}",
        "", "## Window summary", "",
        "| F1 | press | chord ready | sustain | wrong | dropout |",
        "|---:|---:|---:|---:|---:|---:|",
        "| " + " | ".join(
            "n/a" if summary.get(key) is None else f"{summary[key]:.4f}" for key in (
                "f1", "press_success", "chord_ready", "sustain_success",
                "wrong_press", "press_dropout")) + " |",
        "", "## Conditional finger performance", "",
        "| finger | rehearsal | transition | short sequence | full song | full frames |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for finger in document["fingers"].values():
        def fmt(value):
            return "n/a" if value is None else f"{value:.4f}"
        lines.append(
            f"| {finger['label']} | {fmt(finger['rehearsal']['success'])} | "
            f"{fmt(finger['transition_target']['success'])} | {fmt(finger['short_sequence']['success'])} | "
            f"{fmt(finger['full_song']['success'])} | "
            f"{finger['full_song']['count']:.0f} |")
    lines.extend(["", "## Assignment versus target-frame exposure", "",
                  "These have different denominators; assignment is a latest sampler snapshot.", "",
                  "| finger | recovery assignment | sequence target frames |",
                  "|---|---:|---:|"])
    for finger, values in document["exposure"].items():
        lines.append(f"| {FINGER_LABELS[int(finger)]} | "
                     f"{fmt(values['recovery_assignment_fraction'])} | "
                     f"{fmt(values['sequence_target_frame_fraction'])} |")
    report = document["gate_report"]
    lines.extend(["", "## Shared runtime gate checks", "",
                  f"Source: `{report['source']}`. " + report.get("limitation", ""), "",
                  "| check | value | threshold | result |",
                  "|---|---:|---:|---|"])
    for name, check in report["checks"].items():
        result = "unknown" if check["passed"] is None else "pass" if check["passed"] else "fail"
        lines.append(f"| {name} | {check['value']} | {check['threshold']} | {result} |")
    lines.extend(["", "## Additional per-finger checklist", ""])
    lines.extend(
        f"- current: `{name}`"
        for name in document["current_level_failures"])
    lines.extend(
        f"- final: `{name}`"
        for name in document["final_promotion_failures"])
    lines.extend(["", "## Recommended diagnostics", ""])
    lines.extend(
        f"- {item['priority']} `{item['kind']}`: {item['message']}"
        for item in document["recommendations"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="diagnose Fret goal-pair bottlenecks")
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--window", type=int, default=100)
    parser.add_argument("--manifest", type=Path,
                        help="default: run_manifest.json beside the logs directory")
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args(argv)
    if args.window < 1:
        raise ValueError("window must be positive")
    source = args.metrics.resolve()
    config, provenance = load_run_config(source, args.manifest)
    document = diagnose(load_rows(source), window=args.window,
                        config=config, config_provenance=provenance)
    output_json = (args.out_json.resolve() if args.out_json else
                   source.parents[1] / "diagnostics" /
                   "fret_goal_pair_latest.json")
    output_md = (args.out_md.resolve() if args.out_md else
                 output_json.with_suffix(".md"))
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(
        document, indent=2, ensure_ascii=False), encoding="utf-8")
    output_md.write_text(render_markdown(document, source), encoding="utf-8")
    print(f"diagnosis json: {output_json}")
    print(f"diagnosis markdown: {output_md}")
    return document


if __name__ == "__main__":
    main()
