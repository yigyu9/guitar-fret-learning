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
    parser.add_argument("--out", type=Path, default=PHASE / "artifacts" / "contact_regions.png")
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

    fig = plt.figure(figsize=(10, 7), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
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
        ax.text(*(center + np.array([0.0, 0.0, 0.003])), LABELS[name], color=COLORS[name], fontsize=9, ha="center")
        ax.quiver(*center, *desired, length=0.025, normalize=True, color=COLORS[name], linewidth=2, arrow_length_ratio=0.22)
        ax.quiver(*center, *outward, length=0.018, normalize=True, color="#333333", linewidth=1.3, arrow_length_ratio=0.25, linestyle="dashed")

    pts = np.asarray(all_points)
    midpoint = pts.mean(axis=0)
    ax.set_xlim(midpoint[0] - 0.055, midpoint[0] + 0.055)
    ax.set_ylim(midpoint[1] - 0.045, midpoint[1] + 0.045)
    ax.set_zlim(midpoint[2] - 0.04, midpoint[2] + 0.055)
    ax.set_box_aspect((1.2, 1.0, 1.0))
    ax.view_init(elev=23, azim=-55)
    ax.set_xlabel("World X (m)", labelpad=9)
    ax.set_ylabel("World Y (m)", labelpad=9)
    ax.set_zlabel("World Z (m)", labelpad=7)
    ax.set_title("Illustrative guitar contact regions and desired hand normals", pad=18)
    ax.text2D(0.02, 0.02, "Colored arrows: desired hand normals   |   Dashed dark arrows: guitar outward normals\nSource-defined targets only; no hand pose or PhysX contact is shown.", transform=ax.transAxes, fontsize=9)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight")
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
