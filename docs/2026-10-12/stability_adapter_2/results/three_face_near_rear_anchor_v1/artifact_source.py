#!/usr/bin/env python3
"""Plot the saved rear-facet catalog and four rejected near-rear proposals."""
from __future__ import annotations

import hashlib
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np


ROOT = "/home/ajou/yigyu/3"
RESULTS = os.path.join(ROOT, "docs/2026-10-12/stability_adapter_2/results")
CATALOG_DIR = os.path.join(RESULTS, "three_face_rear_facet_catalog_v1")
NEAR_DIR = os.path.join(RESULTS, "three_face_near_rear_anchor_v1")
PHASE = NEAR_DIR
OUTDIR = os.path.join(PHASE, "artifacts")
CATALOG_PNG = os.path.join(OUTDIR, "rear_facet_catalog_Gxy.png")
PROPOSAL_PNG = os.path.join(OUTDIR, "near_rear_rejected_candidates.png")
MANIFEST = os.path.join(OUTDIR, "artifact_manifest.json")

INPUTS = [
    os.path.join(CATALOG_DIR, "catalog.json"),
    os.path.join(CATALOG_DIR, "catalog_execution.json"),
    os.path.join(CATALOG_DIR, "catalog_source.py"),
    os.path.join(CATALOG_DIR, "catalog_execution_producer.py"),
    os.path.join(NEAR_DIR, "proposal.json"),
    os.path.join(NEAR_DIR, "search_execution.json"),
    os.path.join(NEAR_DIR, "search_source.py"),
    os.path.join(NEAR_DIR, "search_execution_producer.py"),
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def input_sha(expected):
    for path in expected:
        require(os.path.isfile(path), "missing sealed input: " + path)
    return {path: sha256(path) for path in expected}


def draw_catalog(catalog):
    rows = catalog["rows"]
    qualified = [r for r in rows if r["rear_facing_qualified"]]
    selected = {int(r["triangle_index"]): r for r in catalog["selected"]}
    largest_idx = int(catalog["reference_largest_triangle"])
    largest = next(r for r in rows if int(r["triangle_index"]) == largest_idx)
    observed = next(r for r in rows if int(r["triangle_index"]) == 786)
    require(not observed["rear_facing_qualified"], "observed reference qualification changed")
    patch = np.asarray(catalog["original_patch_G_m"])[:, :2] * 1000
    inset = np.asarray(catalog["inset_patch_G_m"])[:, :2] * 1000
    qxy = np.asarray([r["centroid_G_m"][:2] for r in qualified]) * 1000
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.subplots_adjust(left=.07, right=.79, bottom=.16, top=.84, wspace=.30)
    for ax in axes:
        ax.add_patch(Polygon(patch, closed=True, facecolor="#dcecf5", edgecolor="#22658b",
                             alpha=.55, linewidth=1.4, label="Rear neck patch"))
        ax.add_patch(Polygon(inset, closed=True, fill=False, edgecolor="#22658b",
                             linestyle="--", linewidth=1.2, label="2 mm inward boundary"))
        ax.scatter(qxy[:, 0], qxy[:, 1], s=12, color="#377da1", alpha=.5,
                   label="367 rear-facing source centroids", zorder=3)
        ox, oy = np.asarray(observed["centroid_G_m"][:2]) * 1000
        ax.scatter([ox], [oy], marker="D", s=45, color="#242424",
                   label="786: unqualified observed reference", zorder=5)
        for index, marker, color in [(303, "o", "#e17c24"), (1462, "s", "#bd4b4b"), (largest_idx, "^", "#684c9a")]:
            row = largest if index == largest_idx else selected[index]
            x, y = np.asarray(row["centroid_G_m"][:2]) * 1000
            ax.scatter([x], [y], marker=marker, s=90, color=color, edgecolor="white",
                       linewidth=.7, zorder=7, label=("Largest reference " if index == largest_idx else "Selected ") + str(index))
            if ax is axes[1]:
                offsets = {303: (12, 20), 1462: (12, -30), largest_idx: (-45, 25)}
                ax.annotate(str(index), (x, y), xytext=offsets[index], textcoords="offset points",
                            fontsize=10, weight="bold", color=color,
                            arrowprops={"arrowstyle": "-", "color": color, "lw": .8})
        ax.set_xlabel("Gx (mm)"); ax.set_ylabel("Gy (mm)")
        ax.set_aspect("equal", adjustable="box"); ax.grid(alpha=.22)
    axes[0].set_title("Finite rear patch: overview")
    axes[1].set_title("Initial thumb source centroids: detail")
    allxy = np.vstack((qxy, np.asarray(observed["centroid_G_m"][:2])[None, :] * 1000,
                       np.asarray([r["diagnostic_goal_G_m"][:2] for r in catalog["selected"]]) * 1000))
    axes[1].set_xlim(allxy[:, 0].min() - 3, allxy[:, 0].max() + 3)
    axes[1].set_ylim(allxy[:, 1].min() - 5, allxy[:, 1].max() + 5)
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.03, 1), fontsize=8)
    fig.suptitle("Rear-facing source catalog in guitar-root frame G", fontsize=14)
    fig.text(.5, .045, "Saved source geometry; XY projection only. No new Gym simulation or physical contact certification.", ha="center", fontsize=9)
    fig.savefig(CATALOG_PNG, dpi=180, bbox_inches="tight"); plt.close(fig)


def draw_candidates(proposal):
    rows = proposal["rejected"]
    require(len(rows) == 4 and all(not r["accepted_for_fresh_native"] for r in rows),
            "proposal must contain four rejected rows")
    thumb = np.asarray([r["anchor_goal_error_mm"]["LH:thumb3"] for r in rows])
    palm = np.asarray([r["anchor_goal_error_mm"]["LH:palm"] for r in rows])
    crossings = np.asarray([len(r["source_intersections"]) for r in rows])
    labels = ["303 / 0.3", "303 / 0.7", "1462 / 0.3", "1462 / 0.7"]
    x = np.arange(4)
    width = .34
    fig, ax = plt.subplots(figsize=(10.5, 6.6))
    fig.subplots_adjust(left=.10, right=.76, bottom=.22, top=.83)
    ax.bar(x - width/2, thumb, width, color="#347ba6", label="Thumb point goal error")
    ax.bar(x + width/2, palm, width, color="#df914d", label="Palm point goal error")
    for i in range(4):
        ax.text(x[i] - width/2, thumb[i] + .12, "{:.3f}".format(thumb[i]),
                ha="center", va="bottom", fontsize=8)
        ax.text(x[i] + width/2, palm[i] + .12, "{:.3f}".format(palm[i]),
                ha="center", va="bottom", fontsize=8)
        ax.text(x[i], max(thumb[i], palm[i]) + .72,
                "Source crossings: {}".format(crossings[i]), ha="center", fontsize=8, color="#812d27")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("triangle index / target clearance (mm)")
    ax.set_ylabel("saved source goal error (mm)")
    ax.set_ylim(0, max(thumb) + 1.35)
    ax.set_title("Four near-rear source candidates: all rejected")
    ax.grid(axis="y", alpha=.22)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=9)
    fig.text(.5, .035,
             "Crossings count saved source intersection rows. "
             "Point errors are static source measures, not guitar drift or physical contact.", ha="center", fontsize=8)
    fig.savefig(PROPOSAL_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    require(not any(os.path.exists(p) for p in (CATALOG_PNG, PROPOSAL_PNG, MANIFEST)),
            "output exists; refusing to overwrite")
    os.makedirs(OUTDIR, exist_ok=True)
    catalog = read_json(INPUTS[0])
    catalog_execution = read_json(INPUTS[1])
    proposal = read_json(INPUTS[4])
    search_execution = read_json(INPUTS[5])
    require(catalog["qualified_count"] == 367 and len(catalog["rows"]) == 368,
            "catalog counts differ from approved scope")
    require(len(proposal["rejected"]) == 4 and
            not proposal["rows"] and
            all(not row["accepted_for_fresh_native"] for row in proposal["rejected"]),
            "proposal rows differ from four rejected source candidates")
    require(proposal["native_initializations"] == 0 and proposal["physics_steps"] == 0,
            "near proposal native/physics counts are not zero")
    require(catalog_execution["native_calls"] == 0 and search_execution["native_calls"] == 0,
            "source artifact inputs report native calls")
    require(catalog_execution["exit_code"] == search_execution["exit_code"] == 0,
            "source executions did not finish normally")
    require(catalog["native_initializations"] == catalog["physics_steps"] == 0,
            "catalog contains actual simulation")
    require(all(catalog["checks"].values()) and all(proposal["checks"].values()),
            "input source checks are incomplete")
    expected = dict(catalog["input_sha256"])
    for path, value in proposal["input_sha256"].items():
        require(path not in expected or expected[path] == value, "inconsistent inherited input")
        expected[path] = value
    expected.update({path: sha256(path) for path in INPUTS + [os.path.abspath(__file__)]})
    before = input_sha(expected)
    require(before == expected, "sealed source input changed before plotting")
    draw_catalog(catalog)
    draw_candidates(proposal)
    after = input_sha(expected)
    require(before == after, "sealed inputs changed during artifact generation")
    for path in (CATALOG_PNG, PROPOSAL_PNG):
        require(os.path.isfile(path) and os.path.getsize(path) > 1000, "missing/empty output: " + path)
    manifest = {
        "schema": "near-rear-source-artifacts-v1",
        "scope": "saved source catalog and rejected proposals; no native/physics execution",
        "producer": os.path.abspath(__file__),
        "producer_sha256": sha256(os.path.abspath(__file__)),
        "input_sha256_before": before,
        "input_sha256_after": after,
        "outputs_sha256": {path: sha256(path) for path in (CATALOG_PNG, PROPOSAL_PNG)},
        "qualified_points": 367,
        "catalog_rows": 368,
        "accepted_candidates": 0,
        "source_candidate_rows": 4,
        "native_initializations": 0,
        "physics_steps": 0,
        "checks": {"counts": True, "all_rejected": True, "source_candidate_rows": 4,
                   "inputs_unchanged": True,
                   "outputs_nonempty": True},
    }
    with open(MANIFEST, "x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"outputs": list(manifest["outputs_sha256"]), "sealed_input_count": len(before), "native_initializations": 0, "physics_steps": 0}))


if __name__ == "__main__":
    main()
