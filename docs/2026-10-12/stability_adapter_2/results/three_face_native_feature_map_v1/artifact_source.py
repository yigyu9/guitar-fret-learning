#!/usr/bin/env python3
"""Render saved-data feature plots and native-frame montage; never initializes Isaac Gym."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1"
ANALYSIS = PHASE / "analysis_v2.json"
BRIEF = PHASE / "artifact_brief.json"
LABELS = ["stored_reference", "half_slack", "zero_slack"]
LABEL_TEXT = ["기준", "절반 slack", "무 slack"]
FOLDERS = {
    "stored_reference": ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets",
    "half_slack": ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack",
    "zero_slack": ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack",
}
BODY_COLORS = {"LH:thumb3": "#e45756", "LH:index3": "#4c78a8", "LH:middle3": "#59a14f", "LH:palm": "#b279a2"}
BODY_MARKERS = {"LH:thumb3": "o", "LH:index3": "s", "LH:middle3": "^", "LH:palm": "D"}
BODY_PATCH = {"LH:thumb3": "thumb", "LH:index3": "front", "LH:middle3": "front", "LH:palm": "palm"}
EXPECTED_ANALYSIS_SHA = "028e95df7aca0cc4618cf8137bf5c6ed1fb1e77844305a7c83bffba288923959"
FRAMES = [(0.0, "00000"), (0.5, "00015"), (5.0, "00150")]
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
font_manager.fontManager.addfont(str(FONT_PATH))
plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(FONT_PATH)).get_name()
plt.rcParams['axes.unicode_minus'] = False


def sha(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    with open(str(path), "r", encoding="utf-8") as f:
        return json.load(f)


def verify_inputs(analysis, brief):
    if sha(ANALYSIS) != brief["analysis_sha256"] or sha(ANALYSIS) != EXPECTED_ANALYSIS_SHA:
        raise RuntimeError("analysis_v2 SHA does not match the approved brief")
    if analysis.get("counts", {}).get("native_initializations") != 0:
        raise RuntimeError("approved analysis reports a native initialization")
    source_hashes = analysis.get("input_sha256", {})
    manifest_hashes = load_json(PHASE / "input_manifest_v2.json").get("input_sha256", {})
    if any(source_hashes.get(name) != digest for name, digest in manifest_hashes.items()):
        raise RuntimeError("analysis input hashes do not close over input_manifest_v2.json")
    before = {}
    for name, expected in source_hashes.items():
        p = Path(name)
        if not p.is_file():
            raise RuntimeError("missing analysis input: " + name)
        actual = sha(p)
        if actual != expected:
            raise RuntimeError("analysis input SHA mismatch: " + name)
        before[name] = actual
    capture_hashes = {}
    for label in LABELS:
        folder = FOLDERS[label]
        capture = folder / "capture.json"
        metadata = load_json(capture)
        capture_hashes[str(capture)] = sha(capture)
        frames = {round(float(x["time_s"]), 6): x for x in metadata["frames"]}
        for time_s, frame_name in FRAMES:
            if round(time_s, 6) not in frames:
                raise RuntimeError("capture has no selected time: {} {}".format(label, time_s))
            frame = folder / "frames/hands/{}.png".format(frame_name)
            expected = frames[round(time_s, 6)]["image_sha256"].get(str(frame))
            if not frame.is_file() or not expected or sha(frame) != expected:
                raise RuntimeError("selected native-frame SHA mismatch: " + str(frame))
            capture_hashes[str(frame)] = expected
    for path in (Path(__file__).resolve(), FONT_PATH, ANALYSIS, BRIEF):
        before[str(path)] = sha(path)
    return before, capture_hashes


def verify_unchanged(before, capture_hashes):
    for name, expected in before.items():
        if sha(Path(name)) != expected:
            raise RuntimeError("analysis input changed during plotting: " + name)
    for name, expected in capture_hashes.items():
        if sha(Path(name)) != expected:
            raise RuntimeError("capture/frame changed during plotting: " + name)


def polygon_for(ax, coords, dims, color, label, alpha=0.15, linestyle="-"):
    points = [[float(p[dims[0]]) * 1000.0, float(p[dims[1]]) * 1000.0] for p in coords]
    ax.add_patch(Polygon(points, closed=True, facecolor=color, edgecolor=color,
                         alpha=alpha, linewidth=1.1, linestyle=linestyle, label=label))


def plot_feature_map(analysis, out):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex="row", sharey="row")
    dims = [(0, 1), (1, 2)]
    row_names = ["XY · x/y (mm)", "YZ · y/z (mm)"]
    patch_colors = {"front": "#f2cf5b", "thumb": "#e45756", "palm": "#b279a2", "front_outer": "#f28e2b"}
    geo = analysis["source_geometry"]
    for row, dim in enumerate(dims):
        for col, label in enumerate(LABELS):
            ax = axes[row, col]
            ax.set_title(LABEL_TEXT[col] if row == 0 else "")
            for key in ("front", "thumb", "palm", "front_outer"):
                polygon_for(ax, analysis["patches_G_m"][key], dim, patch_colors[key], key,
                            alpha=0.09 if key != "front_outer" else 0.04,
                            linestyle="--" if key == "front_outer" else "-")
            # Separate source mesh and fret proxies from the requested regions.
            for mesh in geo:
                vertices = mesh["vertices_G_m"]
                a, b = dim
                xs = [v[a] * 1000.0 for v in vertices]
                ys = [v[b] * 1000.0 for v in vertices]
                if mesh["body"] == "guitar" or mesh["body"].startswith("G:fret"):
                    edges = set()
                    for face in mesh["faces"]:
                        for i in range(len(face)):
                            edges.add(tuple(sorted((face[i], face[(i + 1) % len(face)]))))
                    segments = [[(xs[i], ys[i]), (xs[j], ys[j])] for i, j in edges]
                    color = "#666666" if mesh["body"] == "guitar" else "#9a9a9a"
                    alpha = 0.4 if mesh["body"] == "guitar" else 0.25
                    ax.add_collection(LineCollection(segments, colors=color, linewidths=0.55, alpha=alpha))
            chosen = [s for s in analysis["samples"] if s["label"] == label and s["raw_lambda"] > 0]
            for body, color in BODY_COLORS.items():
                rows = [s for s in chosen if s["human_body"] == body]
                ax.scatter([s["feature_G_m"][dim[0]] * 1000.0 for s in rows],
                           [s["feature_G_m"][dim[1]] * 1000.0 for s in rows],
                           s=7, alpha=0.48, c=color, marker=BODY_MARKERS[body], linewidths=0)
            ax.grid(True, alpha=0.2)
            if col == 0:
                ax.set_ylabel(row_names[row])
            if row == 1:
                ax.set_xlabel("y (mm)" if row == 1 and dim == (1, 2) else "x (mm)")
    handles = [Line2D([0], [0], marker=BODY_MARKERS[b], color="none", markerfacecolor=c,
                      markersize=7, label=b.replace("LH:", "")) for b, c in BODY_COLORS.items()]
    patch_labels = {"front": "front skin z=9.3 mm", "thumb": "rear thumb", "palm": "palm side",
                    "front_outer": "outer z=11.230006 mm"}
    handles.extend([Line2D([0], [0], color=patch_colors[k], lw=3, alpha=0.7, label=patch_labels[k])
                    for k in ("front", "thumb", "palm", "front_outer")])
    fig.legend(handles=handles, loc="lower center", ncol=8, frameon=False, bbox_to_anchor=(0.5, 0.005))
    fig.suptitle("양의 raw λ feature map · body별 색 / 요청 patch와 source geometry는 proxy", y=0.99)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    fig.savefig(str(out), dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_patch_distance(analysis, out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    for ax, label, title in zip(axes, LABELS, LABEL_TEXT):
        ax.set_title(title)
        rows = [s for s in analysis["samples"] if s["label"] == label and s["raw_lambda"] > 0]
        for body, color in BODY_COLORS.items():
            vals = [s for s in rows if s["human_body"] == body]
            patch = BODY_PATCH[body]
            vals = [s for s in vals if s.get("patch_metrics", {}).get(patch, {}).get("finite_patch_distance_mm") is not None]
            ax.scatter([s["physics_step"] / 240.0 for s in vals],
                       [s["patch_metrics"][patch]["finite_patch_distance_mm"] for s in vals],
                       s=7, alpha=0.42, c=color, marker=BODY_MARKERS[body], linewidths=0)
        ax.axhline(0, color="#555555", lw=0.8)
        ax.grid(True, alpha=0.22)
        ax.set_xlabel("시간 (s), physics_step / 240")
    axes[0].set_ylabel("유한 요청 patch까지 거리 (mm)")
    handles = [Line2D([0], [0], marker=BODY_MARKERS[b], color="none", markerfacecolor=c,
                      markersize=7, label="{} → {}".format(b.replace("LH:", ""), BODY_PATCH[b]))
               for b, c in BODY_COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("양의 raw λ 행의 finite desired-patch 거리 · 점 사이 보간 없음", y=1.02)
    fig.tight_layout(rect=(0, 0.09, 1, 0.95))
    fig.savefig(str(out), dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_native_montage(out):
    cell_w, cell_h, header_h, label_w = 480, 270, 38, 112
    canvas = Image.new("RGB", (label_w + 3 * cell_w, header_h + 3 * cell_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT_PATH), 18)
    for col, label in enumerate(LABELS):
        draw.text((label_w + col * cell_w + 10, 10), LABEL_TEXT[col], fill="#222222", font=font)
        folder = FOLDERS[label]
        metadata = load_json(folder / "capture.json")
        by_time = {round(float(x["time_s"]), 6): x for x in metadata["frames"]}
        for row, (time_s, frame_name) in enumerate(FRAMES):
            frame_path = folder / "frames/hands/{}.png".format(frame_name)
            expected = by_time[round(time_s, 6)]["image_sha256"][str(frame_path)]
            if sha(frame_path) != expected:
                raise RuntimeError("native frame changed before montage: " + str(frame_path))
            image = Image.open(str(frame_path)).convert("RGB")
            image.thumbnail((cell_w, cell_h), Image.LANCZOS)
            x = label_w + col * cell_w + (cell_w - image.width) // 2
            y = header_h + row * cell_h + (cell_h - image.height) // 2
            canvas.paste(image, (x, y))
            draw.text((8, header_h + row * cell_h + 8), "t={:.2f}s".format(time_s), fill="#222222", font=font)
            draw.rectangle((label_w + col * cell_w, header_h + row * cell_h,
                            label_w + (col + 1) * cell_w - 1, header_h + (row + 1) * cell_h - 1),
                           outline="#bbbbbb", width=1)
    canvas.save(str(out), format="PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(PHASE), help="artifact output directory")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ('feature_map.png', 'patch_distance.png', 'native_hands.png')):
        raise FileExistsError('preserve consumed artifacts; use a new output directory')
    analysis = load_json(ANALYSIS)
    brief = load_json(BRIEF)
    before, captures = verify_inputs(analysis, brief)
    plot_feature_map(analysis, out / "feature_map.png")
    plot_patch_distance(analysis, out / "patch_distance.png")
    make_native_montage(out / "native_hands.png")
    verify_unchanged(before, captures)
    print(json.dumps({
        "analysis_sha256": sha(ANALYSIS),
        "input_sha256_before": before,
        "input_sha256_after": {name: sha(Path(name)) for name in before},
        "selected_capture_frame_sha256": captures,
        "native_initializations": 0,
        "outputs": [str(out / name) for name in ("feature_map.png", "patch_distance.png", "native_hands.png")],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
