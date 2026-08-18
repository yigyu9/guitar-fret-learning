"""Render the standard strike-learning diagnostics from ``metrics.jsonl``.

The logger evolves with the task, so this plotter deliberately accepts the
canonical metric name and a small set of older/diagnostic aliases.  A missing
series leaves a labelled empty panel instead of making artifact generation
fail after an otherwise successful training run.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.strike_contract import STRIKE_STAGES

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


STAGES = STRIKE_STAGES
STAGE_COLORS = {
    "A0_PICK_GRIP": "#d9edf7",
    "A1_TIP_READY": "#dff0d8",
    "A2_FREE_CROSSING": "#fcf8e3",
    "A3_TIMED_CROSSING": "#f2dede",
    "A4_ZONE_CONTROL": "#e8ddf2",
}

STEP_KEYS = ("steps", "global_step", "samples", "iteration")
STAGE_KEYS = ("curriculum_stage", "stage")

PANEL_SERIES = (
    (
        "Reward",
        (
            ("reward", ("reward", "mean_reward", "rollout_reward")),
        ),
        None,
    ),
    (
        "Pick grip",
        (
            ("grip quality", (
                "curriculum_grip_quality", "grip_quality",
                "mean_grip_quality")),
            ("grip success", (
                "strike_grip_success_rate",
                "curriculum_grip_success_rate", "grip_success_rate")),
        ),
        (0.0, 1.02),
    ),
    (
        "Tip ready",
        (
            ("ready success", (
                "strike_tip_ready_success_rate",
                "curriculum_tip_ready_success_rate",
                "tip_ready_success_rate",
                "ready_success_rate",
                "curriculum_ready_success_rate")),
        ),
        (0.0, 1.02),
    ),
    (
        "Release / crossing",
        (
            ("release recall", (
                "strike_release_recall", "curriculum_release_recall",
                "release_recall", "strike_recall")),
            ("false positive rate", (
                "strike_false_positive_rate",
                "curriculum_false_positive_rate", "false_positive_rate",
                "release_false_positive_rate",
                "strike_wrong_rate")),
        ),
        (0.0, 1.02),
    ),
    (
        "Strike precision / recall / F1",
        (
            ("precision", ("strike_precision", "precision")),
            ("recall", (
                "strike_release_recall", "curriculum_release_recall",
                "strike_recall", "release_recall", "recall")),
            ("F1", (
                "strike_episode_f1", "curriculum_strike_f1",
                "strike_f1", "f1")),
        ),
        (0.0, 1.02),
    ),
    (
        "Timing",
        (
            ("MAE (ms)", (
                "strike_timing_mae_ms", "timing_mae_ms",
                "curriculum_timing_mae_ms")),
            ("P95 (ms)", (
                "strike_timing_p95_ms", "timing_p95_ms",
                "curriculum_timing_p95_ms")),
            ("tolerance (ms)", (
                "timing_tolerance_ms",
                "curriculum_timing_tolerance_ms")),
        ),
        None,
    ),
    (
        "Strike zone",
        (
            ("zone success", (
                "strike_zone_success_rate", "zone_success_rate",
                "curriculum_zone_success_rate")),
            ("zone quality", (
                "strike_zone_mean_quality", "curriculum_zone_quality",
                "zone_quality", "mean_zone_quality")),
        ),
        (0.0, 1.02),
    ),
    (
        "Motion magnitude diagnostics",
        (
            ("tip speed (m/s)", (
                "curriculum_tip_speed_m_s", "tip_speed_m_s")),
            ("penetration depth (m)", (
                "curriculum_guitar_penetration_depth",
                "guitar_penetration_depth")),
            ("swept penetration depth (m)", (
                "curriculum_guitar_swept_penetration_depth",
                "guitar_swept_penetration_depth")),
        ),
        None,
    ),
    (
        "Motion diagnostic rates",
        (
            ("phase violation", (
                "curriculum_release_phase_violation",
                "release_phase_violation")),
            ("penetration frame", (
                "curriculum_guitar_penetration",
                "guitar_penetration")),
            ("action saturation", (
                "curriculum_action_saturation_fraction",
                "action_saturation_fraction")),
        ),
        (0.0, 1.02),
    ),
    (
        "Failure / timeout",
        (
            ("failure termination", (
                "failure_termination", "failure_termination_rate",
                "failure_rate")),
            ("timeout", (
                "timeout", "early_timeout", "timeout_rate")),
            ("wrong crossing", (
                "strike_false_positive_rate",
                "curriculum_false_positive_rate",
                "false_positive_rate", "release_false_positive_rate",
                "strike_wrong_rate", "wrong_crossing_rate")),
        ),
        (0.0, 1.02),
    ),
)


def read_metric_rows(path):
    """Read JSONL rows with useful line-number errors."""
    rows = []
    path = Path(path)
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "invalid JSON in {} at line {}: {}".format(
                        path, line_number, exc.msg)) from exc
            if not isinstance(row, dict):
                raise ValueError(
                    "metric row {} must be a JSON object".format(line_number))
            rows.append(row)
    if not rows:
        raise ValueError("metrics file is empty")
    return rows


def _finite_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def step_values(rows):
    """Return a monotonic plotting x-axis, tolerating sparse older logs."""
    result = []
    previous = -1.0
    for index, row in enumerate(rows):
        value = None
        for key in STEP_KEYS:
            value = _finite_number(row.get(key))
            if value is not None:
                break
        if value is None:
            value = float(index)
        if value < previous:


            raise ValueError("metric step axis is not monotonic")
        result.append(value)
        previous = value
    return result


def _stage_for(row):
    for key in STAGE_KEYS:
        value = row.get(key)
        if value in STAGES:
            return value
    return None


def stage_spans(rows, x):
    """Return contiguous ``(stage, start, end)`` regions."""
    if len(x) == 1:
        half_width = 0.5
    else:
        positive = [
            later - earlier for earlier, later in zip(x, x[1:])
            if later > earlier
        ]
        half_width = 0.5 * (min(positive) if positive else 1.0)
    edges = [x[0] - half_width]
    edges.extend((a + b) / 2.0 for a, b in zip(x, x[1:]))
    edges.append(x[-1] + half_width)

    spans = []
    active = None
    start = 0
    for index, row in enumerate(rows):
        stage = _stage_for(row)
        if stage == active:
            continue
        if active is not None:
            spans.append((active, edges[start], edges[index]))
        active = stage
        start = index
    if active is not None:
        spans.append((active, edges[start], edges[-1]))
    return spans


def available_series(rows, x, aliases):
    """Pick the first finite alias on each row and return sparse coordinates."""
    xx, yy = [], []
    for step, row in zip(x, rows):
        value = None
        for key in aliases:
            value = _finite_number(row.get(key))
            if value is not None:
                break
        if value is not None:
            xx.append(step)
            yy.append(value)
    return xx, yy


def default_output_path(metrics):
    metrics = Path(metrics).resolve()
    if metrics.parent.name == "logs":
        return metrics.parent.parent / "plots" / "strike_training_curves.png"
    return metrics.with_name("strike_training_curves.png")


def render_plot(metrics, out=None):
    rows = read_metric_rows(metrics)
    x = step_values(rows)
    spans = stage_spans(rows, x)

    columns = 2
    rows_count = math.ceil(len(PANEL_SERIES) / columns)
    fig, axes = plt.subplots(
        rows_count, columns,
        figsize=(15, 3.5 * rows_count), dpi=140,
        constrained_layout=True, squeeze=False)
    for axis, (title, specs, limits) in zip(axes.flat, PANEL_SERIES):
        for stage, start, end in spans:
            axis.axvspan(
                start, end, color=STAGE_COLORS[stage], alpha=0.22,
                linewidth=0)
        plotted = False
        for label, aliases in specs:
            xx, yy = available_series(rows, x, aliases)
            if xx:
                axis.plot(xx, yy, linewidth=1.35, label=label)
                plotted = True
        if plotted:
            axis.legend(loc="best", fontsize=8)
        else:
            axis.text(
                0.5, 0.5, "not logged in this stage yet",
                transform=axis.transAxes, ha="center", va="center",
                color="0.45")
        if limits is not None:
            axis.set_ylim(*limits)
        axis.set_title(title)
        axis.set_xlabel("environment samples")
        axis.grid(alpha=0.25)
    for axis in axes.flat[len(PANEL_SERIES):]:
        axis.set_visible(False)

    transitions = []
    for stage, start, _end in spans:
        if not transitions or transitions[-1][0] != stage:
            transitions.append((stage, start))
    subtitle = "  ·  ".join(
        "{} @ {:g}".format(stage.split("_", 1)[0], start)
        for stage, start in transitions)
    if not subtitle:
        subtitle = "stage not logged"
    fig.suptitle(
        "Virtual-pick strike curriculum\n{}".format(subtitle),
        fontsize=14)

    target = Path(out).resolve() if out is not None else default_output_path(metrics)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(target))
    plt.close(fig)
    return target


def parser():
    ap = argparse.ArgumentParser(
        description="plot A0-A4 virtual-pick strike training diagnostics")
    ap.add_argument("metrics", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    target = render_plot(args.metrics, args.out)
    print("saved: {}".format(target))


if __name__ == "__main__":
    main()
