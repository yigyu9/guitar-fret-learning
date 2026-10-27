#!/usr/bin/env python3
"""Regenerate only the initial-condition measurement plot with an external legend."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
CONDITIONS = ("smoke_off_v1", "smoke_on_v1")
LABELS = {"smoke_off_v1": "STRAP OFF", "smoke_on_v1": "STRAP ON"}
COLORS = {"smoke_off_v1": "#2b6cb0", "smoke_on_v1": "#c05621"}
STYLES = {"smoke_off_v1": "-", "smoke_on_v1": "--"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def measurement_inputs() -> list[Path]:
    return sorted(
        BASE / condition / "evaluations/initial_000000/native/episode_0001" / filename
        for condition in CONDITIONS
        for filename in ("controls.json", "trace.json")
    )


def runtime_font() -> Path:
    return Path(font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans"))).resolve()


def finite(values, label):
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError(f"empty or non-finite input: {label}")
    return array


def load_series():
    result = {}
    for condition in CONDITIONS:
        episode = BASE / condition / "evaluations/initial_000000/native/episode_0001"
        controls = json.loads((episode / "controls.json").read_text(encoding="utf-8"))
        trace = json.loads((episode / "trace.json").read_text(encoding="utf-8"))
        if not controls or not trace:
            raise ValueError(f"empty raw series: {condition}")

        time60 = finite([row["physics_step"] / 240.0 for row in controls], f"{condition} control time")
        outside_m = finite([row["position_outside_m"] for row in controls], f"{condition} position_outside_m")
        if outside_m.ndim != 2 or outside_m.shape[1] != 3:
            raise ValueError(f"position_outside_m must have 3 components: {condition}")
        outside_mm = finite(np.linalg.norm(outside_m, axis=1) * 1000.0, f"{condition} outside norm mm")
        tension_n = finite([row["strap"]["last_applied_tension_n"] for row in controls], f"{condition} last_applied_tension_n")
        if not (len(time60) == len(outside_mm) == len(tension_n) == 982):
            raise ValueError(f"unexpected control sample count: {condition}")

        q0 = finite(trace[0]["quaternion_xyzw"], f"{condition} initial quaternion")
        q0 /= np.linalg.norm(q0)
        time30, rotation_deg = [], []
        for row in trace:
            if row["physics_step"] % 8:
                continue
            quat = finite(row["quaternion_xyzw"], f"{condition} quaternion")
            quat /= np.linalg.norm(quat)
            dot = float(np.clip(abs(np.dot(q0, quat)), 0.0, 1.0))
            time30.append(row["physics_step"] / 240.0)
            rotation_deg.append(np.degrees(2.0 * np.arccos(dot)))
        time30 = finite(time30, f"{condition} 30Hz timestamps")
        rotation_deg = finite(rotation_deg, f"{condition} exact rotation deg")
        if len(time30) != 492 or len(rotation_deg) != 492:
            raise ValueError(f"unexpected 30Hz sample count: {condition}")
        result[condition] = {"time60": time60, "outside_mm": outside_mm,
                             "tension_n": tension_n, "time30": time30,
                             "rotation_deg": rotation_deg}
    return result


def main():
    font = runtime_font()
    files = measurement_inputs() + [font]
    frozen = {str(path): sha256(path) for path in files}
    (OUT / "input_hashes.json").write_text(json.dumps({"before": frozen}, indent=2) + "\n", encoding="utf-8")
    data = load_series()

    fig, axes = plt.subplots(3, 1, figsize=(12.4, 10.0), sharex=True)
    for condition in CONDITIONS:
        series = data[condition]
        style = dict(color=COLORS[condition], linestyle=STYLES[condition], linewidth=1.35,
                     label=LABELS[condition], zorder=3 if condition == "smoke_off_v1" else 2)
        axes[0].plot(series["time60"], series["outside_mm"], **style)
        axes[1].plot(series["time30"], series["rotation_deg"], **style)
        axes[2].plot(series["time60"], series["tension_n"], **style)

    axes[0].set_ylabel("position outside norm (mm)")
    axes[0].set_title("sqrt(x² + y² + z²) from controls.position_outside_m × 1000")
    axes[1].set_ylabel("Exact angle from initial (deg)")
    axes[1].set_title("Shortest-arc quaternion angle; trace samples every 8 physics steps (30 Hz)")
    axes[2].set_ylabel("last_applied_tension (N)")
    axes[2].set_title("60 Hz pre-integration cable command; not sensor force")
    axes[2].set_xlabel("Native episode time (physics_step / 240 s)")
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.set_xlim(0.0, max(float(data[c]["time60"][-1]) for c in CONDITIONS))

    # Include complete measured extrema in the axes, with no in-axes legend.
    for axis, field in zip(axes, ("outside_mm", "rotation_deg", "tension_n")):
        values = finite(np.concatenate([data[c][field] for c in CONDITIONS]), field)
        low, high = float(values.min()), float(values.max())
        padding = max((high - low) * 0.04, abs(high) * 0.04, 0.2)
        axis.set_ylim(min(0.0, low - padding), high + padding)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.018),
               ncol=2, frameon=True, fontsize=11)
    fig.suptitle("Initial-condition strap OFF / ON measured time series", y=0.985, fontsize=15)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.93, bottom=0.12, hspace=0.34)
    output = OUT / "measured_traces_external_legend.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)

    after = {str(path): sha256(path) for path in files}
    record = {"before": frozen, "after": after, "inputs_unchanged": frozen == after,
              "producer_sha256": sha256(Path(__file__).resolve()),
              "font_path": str(font), "font_sha256": frozen[str(font)],
              "native_physics_reexecuted": False}
    (OUT / "input_hashes.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if frozen != after:
        raise SystemExit("Input SHA changed during plot generation")


if __name__ == "__main__":
    main()
