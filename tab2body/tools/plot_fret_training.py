"""PPO metrics.jsonl을 학습 곡선 PNG로 렌더한다.

  python tools/plot_fret_training.py \
      ../fret/training/runs/jazz1_pilot/logs/metrics.jsonl
"""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.run_layout import default_plot_path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--out", type=Path, default=None,
                        help="기본값: 해당 run의 plots/training_curves.png")
    args = parser.parse_args(argv)
    rows = [json.loads(line) for line in args.metrics.read_text().splitlines() if line.strip()]
    if not rows:
        raise SystemExit("metrics file is empty")
    x = [r["steps"] for r in rows]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), dpi=140)
    series = [
        ("reward", "Mean reward"),
        ("value_loss", "Value loss"),
        ("kl", "Approx. KL"),
        ("f1_l", "Completed-episode left-hand F1"),
    ]
    for ax, (key, title) in zip(axes.flat, series):
        xx, yy = zip(*[(r["steps"], r[key]) for r in rows if key in r]) \
            if any(key in r for r in rows) else ([], [])
        if xx:
            ax.plot(xx, yy, lw=1.4)
        if key == "f1_l":
            ax.axhline(0.9, color="tab:red", ls="--", lw=1, label="gate 0.9")
            ax.set_ylim(-0.02, 1.02)
            ax.legend()
        ax.set_title(title)
        ax.set_xlabel("environment samples")
        ax.grid(alpha=0.25)
    fig.tight_layout()
    out = args.out.resolve() if args.out else default_plot_path(args.metrics)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
