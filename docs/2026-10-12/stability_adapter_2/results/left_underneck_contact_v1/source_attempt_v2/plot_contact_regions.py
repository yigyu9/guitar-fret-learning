#!/usr/bin/env python3
"""Plot the saved world-space contact-region targets as an explanatory diagram."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


PHASE = Path(__file__).resolve().parent
DEFAULT_INPUT = PHASE / "verification_v2" / "verification.json"
COLORS = {"palm": "#4c9f70", "thumb": "#dd8a37", "front": "#547dbf"}
LABELS = {"palm": "Palm side", "thumb": "Thumb rear", "front": "Finger front"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=PHASE / "artifacts" / "contact_regions_v2.png")
    args = parser.parse_args()
    src, out = args.input.resolve(), args.out.resolve()
    manifest = out.with_suffix(".manifest.json")
    if out.exists() or manifest.exists():
        raise FileExistsError(f"refusing to overwrite output: {out} or {manifest}")

    before = {str(src): sha256(src), str(Path(__file__).resolve()): sha256(Path(__file__).resolve())}
    data = json.loads(src.read_text())
    checks = data.get("checks", {})
    if not checks or not all(value is True for value in checks.values()):
        raise ValueError("verification checks must all be true")
    regions = data["regions_W"]
    required = ("palm", "thumb", "front")
    if set(regions) != set(required):
        raise ValueError(f"expected regions {required}, got {tuple(regions)}")

    fig = plt.figure(figsize=(11, 7.2))
    ax = fig.add_axes([0.035, 0.10, 0.70, 0.82], projection="3d")
    all_points = []
    for name in required:
        item = regions[name]
        poly = np.asarray(item["polygon_W_m"], dtype=float)
        outward = np.asarray(item["outward_normal_W"], dtype=float)
        desired = np.asarray(item["desired_hand_normal_W"], dtype=float)
        if poly.shape != (4, 3) or not np.isfinite(poly).all() or not np.isfinite(outward).all() or not np.isfinite(desired).all():
            raise ValueError(f"invalid region geometry: {name}")
        all_points.extend(poly)
        ax.add_collection3d(Poly3DCollection([poly], facecolor=COLORS[name], edgecolor=COLORS[name], alpha=0.58, linewidth=2))
        center = poly.mean(axis=0)
        ax.quiver(*center, *desired, length=0.020, normalize=True, color=COLORS[name], linewidth=2.4, arrow_length_ratio=0.28)

    pts = np.asarray(all_points)
    midpoint = pts.mean(axis=0)
    ax.set_xlim(midpoint[0] - 0.055, midpoint[0] + 0.055)
    ax.set_ylim(midpoint[1] - 0.045, midpoint[1] + 0.045)
    ax.set_zlim(midpoint[2] - 0.04, midpoint[2] + 0.055)
    ax.set_box_aspect((1.2, 1.0, 1.0))
    ax.view_init(elev=23, azim=-48)
    ax.set_xlabel("World X (m)", labelpad=8)
    ax.set_ylabel("World Y (m)", labelpad=8)
    ax.set_zlabel("World Z (m)", labelpad=5)
    ax.set_title("Source-defined guitar regions (concept view)", pad=12)
    handles = [Patch(facecolor=COLORS[name], edgecolor=COLORS[name], alpha=0.65, label=LABELS[name]) for name in required]
    handles.append(Line2D([0], [0], color="#333333", linewidth=2.4, marker=">", label="Arrow = desired_hand_normal_W"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.755, 0.86), frameon=False, fontsize=10)
    fig.text(0.76, 0.55, "Polygons and arrows come from\nsaved world-space verification data.\n\nArrows show desired hand-normal\ndirections, not an actual hand pose.\n\nNo hand, contact, or PhysX\ncollision geometry is shown.", va="top", fontsize=10, linespacing=1.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)

    after = {path: sha256(Path(path)) for path in before}
    if before != after:
        out.unlink(missing_ok=True)
        raise RuntimeError("an input changed during plotting")
    record = {
        "input_sha256": before,
        "output_sha256": {str(out): sha256(out)},
        "producer_sha256": sha256(Path(__file__).resolve()),
        "regions": list(required),
        "checks": checks,
        "scope": "illustrative world-space target polygons; not hand placement, native render, or PhysX contact validation",
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(out)
    print(manifest)


if __name__ == "__main__":
    main()
