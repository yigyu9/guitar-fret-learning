#!/usr/bin/env python3
"""Create the approved saved-source-geometry contact footprint figure."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2"
ANALYSIS = PHASE / "analysis_v2.json"
BRIEF = PHASE / "artifact_brief_v2.json"
PROPOSAL = PHASE / "proposal.json"
PLAN = ROOT / "stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md"
ANALYSIS_SHA = "7be08f9d08a23a30ba13944a575b136060e0faa56ec08152cfc8f5b957cf612f"
BRIEF_SHA = "004b6a3a709fe0c9d09ab727f8d569f9554e9c4af0701de5c2d16443fda071c5"
OUTPUT = "source_candidate_comparison.png"


def sha256(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    producer = Path(__file__).resolve()

    # Verify the approved brief and analysis before loading plotting libraries.
    hashes = {str(p): sha256(p) for p in (producer, BRIEF, ANALYSIS, PROPOSAL, PLAN)}
    if hashes[str(ANALYSIS)] != ANALYSIS_SHA or hashes[str(BRIEF)] != BRIEF_SHA:
        raise RuntimeError("approved brief or analysis SHA mismatch")
    with open(str(BRIEF), "r") as stream:
        brief = json.load(stream)
    with open(str(ANALYSIS), "r") as stream:
        analysis = json.load(stream)
    with open(str(PROPOSAL), "r") as stream:
        proposal = json.load(stream)
    if brief["analysis_sha256"] != ANALYSIS_SHA or not brief["source_only"]:
        raise AssertionError("brief analysis binding/scope mismatch")
    if analysis["counts"] != {"source_candidates": 4, "native_initializations": 0, "physics_steps": 0}:
        raise AssertionError("analysis counts differ from approved phase")
    if len(analysis["summary"]) != 4 or len(proposal["rejected"]) != 2:
        raise AssertionError("expected four analyzed candidates and two v2 rejections")
    if any(not all(checks.values()) for checks in (analysis["checks"], proposal["checks"])):
        raise AssertionError("analysis or proposal checks incomplete")
    for path, digest in analysis["input_sha256"].items():
        if sha256(path) != digest:
            raise AssertionError("sealed analysis input changed: " + path)
        hashes[path] = digest
    for path, digest in proposal["input_sha256"].items():
        if sha256(path) != digest:
            raise AssertionError("sealed proposal input changed: " + path)
        hashes[path] = digest

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Polygon

    font_properties = font_manager.FontProperties(family="NanumGothic")
    font_path = Path(font_manager.findfont(font_properties, fallback_to_default=False))
    if "NanumGothic" not in font_path.name:
        raise RuntimeError("resolved font is not NanumGothic: " + str(font_path))
    hashes[str(font_path)] = sha256(font_path)
    matplotlib.rcParams["font.family"] = font_properties.get_name()
    matplotlib.rcParams["axes.unicode_minus"] = False
    for path, digest in hashes.items():
        if sha256(path) != digest:
            raise AssertionError("input changed before plotting: " + path)

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / OUTPUT
    if output.exists():
        raise FileExistsError("refusing to overwrite existing artifact: " + str(output))

    candidates = analysis["summary"]
    colors = {"three_face_contact_footprint_v1": "#3973ac",
              "three_face_contact_footprint_v2": "#d1495b"}
    labels = {"three_face_contact_footprint_v1": "V1", "three_face_contact_footprint_v2": "V2"}
    fig, (left, right) = plt.subplots(1, 2, figsize=(14, 6.2), constrained_layout=True)

    # Thumb rear finite patch in guitar-root Gx/Gy. The 2 mm inset is shown
    # from the left boundary; each candidate's source point, goal, and facet
    # direction come directly from saved analysis.
    thumb_patch = proposal["regions_G_m"]["thumb"]
    tx = [p[0] * 1000 for p in thumb_patch]
    ty = [p[1] * 1000 for p in thumb_patch]
    left.add_patch(Polygon(list(zip(tx, ty)), closed=True, facecolor="#f2cc8f",
                           edgecolor="#9a6b22", alpha=.34, linewidth=1.2,
                           label="rear finite patch"))
    xmin, xmax = min(tx), max(tx)
    ymin, ymax = min(ty), max(ty)
    edge_dx, edge_dy = tx[3] - tx[0], ty[3] - ty[0]
    edge_length = (edge_dx * edge_dx + edge_dy * edge_dy) ** .5
    inward_x, inward_y = edge_dy / edge_length, -edge_dx / edge_length
    left.plot([tx[0] + 2 * inward_x, tx[3] + 2 * inward_x],
              [ty[0] + 2 * inward_y, ty[3] + 2 * inward_y], color="#333333", linestyle="--",
              linewidth=1.2, label="requested 2 mm inward margin")
    points_xy = []
    for index, item in enumerate(candidates):
        phase = item["phase"]
        color = colors[phase]
        short = labels[phase] + (" · 0.3 mm" if "0p3" in item["label"] else " · 0.7 mm")
        point = item["anchor_G_m"]["LH:thumb3"]
        goal = item["anchor_goal_G_m"]["LH:thumb3"]
        x, y = point[0] * 1000, point[1] * 1000
        gx, gy = goal[0] * 1000, goal[1] * 1000
        points_xy.extend([(x, y), (gx, gy)])
        left.scatter([x], [y], s=48, color=color, edgecolor="white", linewidth=.6, zorder=4)
        left.scatter([gx], [gy], s=45, color=color, marker="x", linewidth=1.6, zorder=5)
        left.annotate(short, (x, y), xytext=(5, [30, -30, 45, -45][index]),
                      textcoords="offset points", fontsize=8, color=color,
                      arrowprops={'arrowstyle': '-', 'color': color, 'linewidth': .6})
        direction = item["source_facet_outward_G"]["LH:thumb3"]
        left.arrow(x, y, direction[0] * 2.0, direction[1] * 2.0,
                   color=color, width=.012, head_width=.12, length_includes_head=True, zorder=3)
    left.set_xlim(min(p[0] for p in points_xy) - 1.5, max(p[0] for p in points_xy) + 2.5)
    left.set_ylim(min(p[1] for p in points_xy) - 4, max(p[1] for p in points_xy) + 4)
    left.set_aspect("equal", adjustable="box")
    left.set_xlabel("G-root X (mm)")
    left.set_ylabel("G-root Y (mm)")
    left.set_title("Thumb: left boundary zoom (V1 and V2)")
    left.grid(True, alpha=.2)
    left.legend(frameon=False, fontsize=8, loc="best")

    # V2 palm finite patch and both selected source triangles, including the
    # vertices outside its boundary to make the observed overhang visible.
    palm_patch = proposal["regions_G_m"]["palm"]
    py = [p[1] * 1000 for p in palm_patch]
    pz = [p[2] * 1000 for p in palm_patch]
    right.add_patch(Polygon(list(zip(py, pz)), closed=True, facecolor="#d1495b",
                            edgecolor="#8f2434", alpha=.25, linewidth=1.2,
                            label="requested finite palm region"))
    all_palm_z = list(pz)
    for i, item in enumerate(candidates):
        if item["phase"] != "three_face_contact_footprint_v2":
            continue
        color = "#d1495b" if "0p3" in item["label"] else "#7b5aa6"
        short = "V2 · 0.3 mm" if "0p3" in item["label"] else "V2 · 0.7 mm"
        foot = item["source_footprint"]["LH:palm"]
        triangle = foot["triangle_G_m"]
        tri_yz = [(p[1] * 1000, p[2] * 1000) for p in triangle]
        all_palm_z.extend(p[1] for p in tri_yz)
        right.add_patch(Polygon(tri_yz, closed=True, fill=False, edgecolor=color,
                                linewidth=1.5, linestyle="-" if i == 2 else "--",
                                label=short + " source triangle"))
        point = item["anchor_G_m"]["LH:palm"]
        px, pyy, pz0 = point[0] * 1000, point[1] * 1000, point[2] * 1000
        right.scatter([pyy], [pz0], color=color, edgecolor="white", s=50, zorder=5,
                      label=short + " representative point")
        direction = item["source_facet_outward_G"]["LH:palm"]
        right.arrow(pyy, pz0, direction[1] * 2.0, direction[2] * 2.0,
                    color=color, width=.012, head_width=.12, length_includes_head=True,
                    label=short + " SOURCE facet direction")
    right.set_xlim(min(py) - 2, max(py) + 2)
    right.set_ylim(min(all_palm_z) - 2, max(all_palm_z) + 2)
    right.set_aspect("equal", adjustable="box")
    right.set_xlabel("G-root Y (mm)")
    right.set_ylabel("G-root Z (mm)")
    right.set_title("V2 palm: source triangles and observed overhang")
    right.grid(True, alpha=.2)
    right.legend(frameon=False, fontsize=7, loc="best")
    fig.suptitle("Saved source-FK candidate geometry — no native frame or force")
    fig.savefig(str(output), dpi=190)
    plt.close(fig)

    # Recheck all declared data, brief, producer and resolved font after save.
    after = {path: sha256(path) for path in hashes}
    for path, digest in hashes.items():
        if after[path] != digest:
            raise AssertionError("input changed during plotting: " + path)
    if sha256(producer) != hashes[str(producer)]:
        raise AssertionError("producer changed during plotting")
    if sha256(BRIEF) != BRIEF_SHA or sha256(ANALYSIS) != ANALYSIS_SHA:
        raise AssertionError("brief or analysis changed during plotting")
    print(json.dumps({"figure": str(output), "analysis_sha256": ANALYSIS_SHA,
                      "brief_sha256": BRIEF_SHA, "font": str(font_path),
                      "input_count": len(hashes), "native_initializations": 0,
                      "input_sha256_before": hashes, "input_sha256_after": after,
                      "output_sha256": sha256(output),
                      "physics_steps": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
