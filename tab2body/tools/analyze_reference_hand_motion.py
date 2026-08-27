"""사람 왼손 reference JSON의 관절 분포와 손가락 연동을 요약한다."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.metrics import adjacent_finger_motion_correlations
from env.rewards.reference_posture import FINGERS, load_reference_postures


def _distribution(values, names):
    quantiles = torch.quantile(
        torch.rad2deg(values.float()),
        torch.tensor([0.05, 0.50, 0.95]), dim=0)
    degrees = torch.rad2deg(values.float())
    return {
        name: {
            "min_deg": float(degrees[:, index].min()),
            "p05_deg": float(quantiles[0, index]),
            "median_deg": float(quantiles[1, index]),
            "p95_deg": float(quantiles[2, index]),
            "max_deg": float(degrees[:, index].max()),
        }
        for index, name in enumerate(names)
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("motion", type=Path)
    parser.add_argument("--max-exemplars", type=int, default=512)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    source = args.motion.resolve()
    output = (args.out.resolve() if args.out else
              ROOT.parent / "fret" / "diagnostics" /
              "reference_hand_motion.json")
    finger, thumb = load_reference_postures(
        source, max_exemplars=args.max_exemplars)
    finger_names = tuple(
        f"{finger_name}_{joint}"
        for finger_name in FINGERS for joint in ("mcp", "pip", "dip"))
    thumb_names = ("thumb1_x", "thumb1_y", "thumb1_z", "thumb2", "thumb3")
    report = {
        "source": str(source),
        "frames": int(finger.shape[0]),
        "finger_joint_distribution": _distribution(
            finger.flatten(1), finger_names),
        "thumb_joint_distribution": _distribution(thumb, thumb_names),
        "adjacent_finger_motion_correlation":
            adjacent_finger_motion_correlations(finger),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    values = torch.rad2deg(finger).flatten(1).numpy()
    fig, axis = plt.subplots(figsize=(14, 6), dpi=150)
    axis.boxplot(values, labels=finger_names, showfliers=False)
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_ylabel("degrees")
    axis.set_title("Reference left-hand joint distribution")
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    image = output.with_suffix(".png")
    fig.savefig(image)
    print(f"saved: {output}")
    print(f"plot: {image}")


if __name__ == "__main__":
    main()
