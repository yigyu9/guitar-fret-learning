from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


STRING_LABELS = ("1 high-e", "2 B", "3 G", "4 D", "5 A", "6 low-E")


def _panels(duration, panel_seconds):
    count = max(1, int(math.ceil(duration / panel_seconds)))
    return [(index * panel_seconds, min(duration, (index + 1) * panel_seconds))
            for index in range(count)]


def _axes(duration, panel_seconds, title):
    windows = _panels(duration, panel_seconds)
    figure, axes = plt.subplots(
        len(windows), 1, figsize=(20, 2.6 * len(windows)),
        sharey=True, constrained_layout=True)
    if len(windows) == 1:
        axes = [axes]
    figure.suptitle(title, fontsize=17, fontweight="bold")
    for axis, (start, end) in zip(axes, windows):
        axis.set_xlim(start, end)
        axis.set_ylim(-0.5, 5.5)
        axis.set_yticks(range(6), STRING_LABELS)
        axis.set_xlabel("Time (s)")
        axis.set_ylabel("Guitar string")
        axis.grid(axis="x", alpha=0.22, linewidth=0.7)
        axis.grid(axis="y", alpha=0.12, linewidth=0.6)
        axis.text(
            0.995, 0.04, f"{start:.1f}–{end:.1f} s",
            transform=axis.transAxes, ha="right", va="bottom", fontsize=9)
    return figure, axes, windows


def _visible(window, values):
    return max(values) >= window[0] and min(values) <= window[1]


def plot_before(raw, plan, out, panel_seconds):
    duration = max(event["time"] for event in raw["events"]) + 0.25
    figure, axes, windows = _axes(
        duration, panel_seconds,
        "Before correction — raw onsets and compiler strum groups")
    strum_source_ids = {
        source_id
        for event in plan["events"] if event["gesture"] == "strum"
        for source_id in event["source_event_ids"] if isinstance(source_id, int)}
    for axis, window in zip(axes, windows):
        ordinary = [
            (index, event) for index, event in enumerate(raw["events"])
            if index not in strum_source_ids and window[0] <= event["time"] <= window[1]]
        grouped = [
            (index, event) for index, event in enumerate(raw["events"])
            if index in strum_source_ids and window[0] <= event["time"] <= window[1]]
        if ordinary:
            axis.scatter(
                [event["time"] for _, event in ordinary],
                [event["string"] for _, event in ordinary],
                s=22, color="#4c78a8", label="single/raw onset", zorder=3)
        if grouped:
            axis.scatter(
                [event["time"] for _, event in grouped],
                [event["string"] for _, event in grouped],
                s=28, color="#e45756", label="raw onset in strum group", zorder=4)
        for event in plan["events"]:
            if event["gesture"] != "strum":
                continue
            source = [raw["events"][index] for index in event["source_event_ids"]]
            times = [item["time"] for item in source]
            strings = [item["string"] for item in source]
            if not _visible(window, times):
                continue
            axis.plot(times, strings, color="#e45756", alpha=0.45, linewidth=1.2)
            pad_x = max(0.004, (max(times) - min(times)) * 0.12)
            axis.add_patch(Rectangle(
                (min(times) - pad_x, min(strings) - 0.28),
                max(times) - min(times) + 2 * pad_x,
                max(strings) - min(strings) + 0.56,
                facecolor="#e45756", edgecolor="#e45756",
                alpha=0.10, linewidth=0.8))
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(handles, labels, loc="upper right", ncol=2, frameon=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=180)
    plt.close(figure)


def plot_after(raw, plan, out, panel_seconds):
    duration = max(event["time"] for event in raw["events"]) + 0.25
    figure, axes, windows = _axes(
        duration, panel_seconds,
        "After correction — centered, direction-aligned strum micro-timing")
    colors = {"down": "#4c78a8", "up": "#f58518"}
    for axis, window in zip(axes, windows):
        for event in plan["events"]:
            if event["gesture"] == "single_pick":
                if window[0] <= event["time"] <= window[1]:
                    axis.scatter(
                        [event["time"]], [event["strings"][0]],
                        s=18, color="#8f8f8f", alpha=0.72, zorder=2)
                continue
            if event["gesture"] != "strum":
                continue
            planned_times = [
                event["time"] + offset
                for offset in event["traversal_offsets_s"]]
            if not _visible(window, planned_times):
                continue
            color = colors[event["direction"]]
            source = [raw["events"][index] for index in event["source_event_ids"]]
            axis.scatter(
                [item["time"] for item in source],
                [item["string"] for item in source],
                marker="x", s=20, color="#a0a0a0", alpha=0.58, zorder=2)
            axis.plot(
                planned_times, event["traversal_strings"],
                color=color, linewidth=1.8, alpha=0.86, zorder=3)
            audible = set(event["strings"])
            for time_s, string_index in zip(
                    planned_times, event["traversal_strings"]):
                if string_index in audible:
                    axis.scatter(
                        [time_s], [string_index], s=31, color=color, zorder=4)
                else:
                    axis.scatter(
                        [time_s], [string_index], s=34, facecolors="white",
                        edgecolors=color, linewidths=1.2, zorder=4)
            axis.annotate(
                "", xy=(planned_times[-1], event["traversal_strings"][-1]),
                xytext=(planned_times[0], event["traversal_strings"][0]),
                arrowprops={"arrowstyle": "->", "color": color,
                            "linewidth": 1.2, "alpha": 0.8})
            axis.axvline(
                event["time"], color=color, alpha=0.13, linewidth=0.8)
    axes[0].scatter([], [], color=colors["down"], label="planned down")
    axes[0].scatter([], [], color=colors["up"], label="planned up")
    axes[0].scatter([], [], marker="x", color="#a0a0a0", label="raw source onset")
    axes[0].scatter(
        [], [], facecolors="white", edgecolors="#4c78a8",
        label="traversed protected string")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(
        handles, labels, loc="upper right", ncol=2, frameon=False,
        fontsize=9)
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=180)
    plt.close(figure)


def plot_comparison(raw, plan, out, panel_seconds):
    duration = max(event["time"] for event in raw["events"]) + 0.25
    windows = _panels(duration, panel_seconds)
    figure, axes = plt.subplots(
        len(windows), 2, figsize=(24, 2.85 * len(windows)),
        sharey=True, constrained_layout=True)
    figure.suptitle(
        "Strum timing correction — raw grouping vs direction-aligned plan",
        fontsize=18, fontweight="bold")
    colors = {"down": "#4c78a8", "up": "#f58518"}
    strum_source_ids = {
        source_id
        for event in plan["events"] if event["gesture"] == "strum"
        for source_id in event["source_event_ids"] if isinstance(source_id, int)}
    for row, window in enumerate(windows):
        before_axis, after_axis = axes[row]
        for axis in (before_axis, after_axis):
            axis.set_xlim(*window)
            axis.set_ylim(-0.5, 5.5)
            axis.set_yticks(range(6), STRING_LABELS)
            axis.set_xlabel("Time (s)")
            axis.grid(axis="x", alpha=0.22, linewidth=0.7)
            axis.grid(axis="y", alpha=0.12, linewidth=0.6)
            axis.text(
                0.99, 0.05, f"{window[0]:.1f}–{window[1]:.1f} s",
                transform=axis.transAxes, ha="right", va="bottom", fontsize=9)
        before_axis.set_ylabel("Guitar string")
        if row == 0:
            before_axis.set_title(
                "BEFORE — raw onset times", fontsize=14, fontweight="bold")
            after_axis.set_title(
                "AFTER — centered down/up sweep", fontsize=14, fontweight="bold")

        ordinary = [
            (index, event) for index, event in enumerate(raw["events"])
            if index not in strum_source_ids
            and window[0] <= event["time"] <= window[1]]
        grouped = [
            (index, event) for index, event in enumerate(raw["events"])
            if index in strum_source_ids
            and window[0] <= event["time"] <= window[1]]
        if ordinary:
            before_axis.scatter(
                [event["time"] for _, event in ordinary],
                [event["string"] for _, event in ordinary],
                s=20, color="#4c78a8", zorder=3)
        if grouped:
            before_axis.scatter(
                [event["time"] for _, event in grouped],
                [event["string"] for _, event in grouped],
                s=27, color="#e45756", zorder=4)

        for event in plan["events"]:
            if event["gesture"] == "strum":
                source = [
                    raw["events"][index]
                    for index in event["source_event_ids"]]
                source_times = [item["time"] for item in source]
                source_strings = [item["string"] for item in source]
                if _visible(window, source_times):
                    before_axis.plot(
                        source_times, source_strings,
                        color="#e45756", alpha=0.50, linewidth=1.25)
                    pad_x = max(
                        0.004, (max(source_times) - min(source_times)) * 0.12)
                    before_axis.add_patch(Rectangle(
                        (min(source_times) - pad_x,
                         min(source_strings) - 0.28),
                        max(source_times) - min(source_times) + 2 * pad_x,
                        max(source_strings) - min(source_strings) + 0.56,
                        facecolor="#e45756", edgecolor="#e45756",
                        alpha=0.10, linewidth=0.8))

                planned_times = [
                    event["time"] + offset
                    for offset in event["traversal_offsets_s"]]
                if not _visible(window, planned_times):
                    continue
                color = colors[event["direction"]]
                after_axis.scatter(
                    source_times, source_strings, marker="x", s=18,
                    color="#a0a0a0", alpha=0.58, zorder=2)
                after_axis.plot(
                    planned_times, event["traversal_strings"],
                    color=color, linewidth=1.8, alpha=0.88, zorder=3)
                audible = set(event["strings"])
                for time_s, string_index in zip(
                        planned_times, event["traversal_strings"]):
                    if string_index in audible:
                        after_axis.scatter(
                            [time_s], [string_index], s=29,
                            color=color, zorder=4)
                    else:
                        after_axis.scatter(
                            [time_s], [string_index], s=32,
                            facecolors="white", edgecolors=color,
                            linewidths=1.1, zorder=4)
                after_axis.annotate(
                    "",
                    xy=(planned_times[-1], event["traversal_strings"][-1]),
                    xytext=(planned_times[0], event["traversal_strings"][0]),
                    arrowprops={
                        "arrowstyle": "->", "color": color,
                        "linewidth": 1.2, "alpha": 0.82})
            elif (event["gesture"] == "single_pick"
                  and window[0] <= event["time"] <= window[1]):
                after_axis.scatter(
                    [event["time"]], [event["strings"][0]],
                    s=17, color="#8f8f8f", alpha=0.70, zorder=2)

    before = axes[0, 0]
    before.scatter([], [], color="#4c78a8", label="single/raw onset")
    before.scatter([], [], color="#e45756", label="raw strum group")
    before.legend(loc="upper right", frameon=False, fontsize=9)
    after = axes[0, 1]
    after.scatter([], [], color=colors["down"], label="planned down")
    after.scatter([], [], color=colors["up"], label="planned up")
    after.scatter([], [], marker="x", color="#a0a0a0", label="raw onset")
    after.scatter(
        [], [], facecolors="white", edgecolors="#4c78a8",
        label="protected traversal")
    after.legend(loc="upper right", ncol=2, frameon=False, fontsize=8.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=180)
    plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--combined", type=Path)
    parser.add_argument("--panel-seconds", type=float, default=10.5)
    args = parser.parse_args(argv)
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    plot_before(raw, plan, args.before, args.panel_seconds)
    plot_after(raw, plan, args.after, args.panel_seconds)
    if args.combined is not None:
        plot_comparison(raw, plan, args.combined, args.panel_seconds)
    print(json.dumps({
        "before": str(args.before.resolve()),
        "after": str(args.after.resolve()),
        "combined": (
            str(args.combined.resolve()) if args.combined is not None else None),
    }, indent=2))


if __name__ == "__main__":
    main()
