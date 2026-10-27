#!/usr/bin/env python3
"""Create source-only rear-facet comparison artifacts from the approved brief."""
from __future__ import print_function

import hashlib
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon
import numpy as np


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE = os.path.join(ROOT, "docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2")
BRIEF = os.path.join(PHASE, "artifact_brief.json")
ANALYSIS = os.path.join(PHASE, "analysis.json")
PROPOSAL = os.path.join(PHASE, "proposal.json")
EXECUTION = os.path.join(PHASE, "search_execution.json")
RECOVERY_REVIEW = os.path.join(PHASE, "recovery_review.md")
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
OUTDIR = os.path.join(PHASE, "artifacts")
PNG = os.path.join(OUTDIR, "rear_facet_source_comparison.png")
MANIFEST = os.path.join(OUTDIR, "artifact_manifest.json")


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


def input_closure(producer_path, analysis):
    paths = set(analysis["input_sha256"].keys())
    paths.update([BRIEF, ANALYSIS, PROPOSAL, EXECUTION, RECOVERY_REVIEW,
                  producer_path, FONT])
    before = {}
    for path in sorted(paths):
        require(os.path.isfile(path), "missing sealed input: " + path)
        before[path] = sha256(path)
    for path, expected in analysis["input_sha256"].items():
        require(before[path] == expected, "analysis input SHA mismatch: " + path)
    return before


def main():
    producer_path = os.path.abspath(__file__)
    require(os.path.isfile(FONT), "NanumGothic font is unavailable")
    require(not os.path.exists(PNG) and not os.path.exists(MANIFEST),
            "output exists; refusing to overwrite")
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)

    brief = read_json(BRIEF)
    analysis = read_json(ANALYSIS)
    proposal = read_json(PROPOSAL)
    require(brief["analysis_path"] == ANALYSIS, "brief analysis path mismatch")
    require(sha256(ANALYSIS) == brief["analysis_sha256"], "brief analysis SHA mismatch")
    require(analysis["counts"]["unique_completed_source_candidates"] == 4,
            "analysis does not describe four completed candidates")
    require(analysis["counts"]["accepted_candidates"] == 0 and
            analysis["counts"]["native_initializations"] == 0 and
            analysis["counts"]["physics_steps"] == 0,
            "analysis native/acceptance counts differ from brief")
    require(len(analysis["summary"]) == 4 and len(proposal["rejected"]) == 4,
            "candidate row count mismatch")

    inputs_before = input_closure(producer_path, analysis)
    summary = analysis["summary"]
    rejected = proposal["rejected"]
    approved = brief["approved_results"]
    labels = [row["label"] for row in summary]
    require(labels == [row["label"] for row in rejected], "candidate ordering mismatch")
    for index, row in enumerate(summary):
        require(abs(row["anchor_goal_error_mm"]["LH:thumb3"] -
                    approved["thumb_errors_mm"][index]) < 1e-9,
                "brief thumb error differs from analysis")
        require(abs(row["anchor_goal_error_mm"]["LH:palm"] -
                    approved["palm_errors_mm"][index]) < 1e-9,
                "brief palm error differs from analysis")
        require(len(row["source_intersections"]) ==
                approved["source_intersection_counts"][index],
                "brief intersection count differs from analysis")

    font_manager.fontManager.addfont(FONT)
    font_name = font_manager.FontProperties(fname=FONT).get_name()
    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 7.6),
                                  gridspec_kw={"width_ratios": [1.18, 1]})
    fig.subplots_adjust(left=.075, right=.98, top=.84, bottom=.17, wspace=.22)

    # Gx/Gy in mm. The selected finite rear patch is represented by its source
    # polygon; the inset is a true perpendicular 2 mm offset from each edge.
    patch = np.asarray(analysis["regions_G_m"]["thumb"], dtype=float)[:, :2] * 1000.0
    ax.add_patch(Polygon(patch, closed=True, facecolor="#d9eaf7", edgecolor="#24608a",
                         linewidth=1.8, alpha=.75, label="후면 패치 경계"))
    center = patch.mean(axis=0)
    inset = []
    for i, vertex in enumerate(patch):
        previous = patch[i - 1]
        following = patch[(i + 1) % len(patch)]
        e1 = following - vertex
        e0 = vertex - previous
        n1 = np.array([-e1[1], e1[0]]) / np.linalg.norm(e1)
        n0 = np.array([-e0[1], e0[0]]) / np.linalg.norm(e0)
        if np.dot(n1, center - vertex) < 0:
            n1 = -n1
        if np.dot(n0, center - vertex) < 0:
            n0 = -n0
        direction = n0 + n1
        direction /= np.linalg.norm(direction)
        inset.append(vertex + direction * (2.0 / np.dot(direction, n1)))
    inset = np.asarray(inset)
    ax.add_patch(Polygon(inset, closed=True, fill=False, edgecolor="#24608a",
                         linestyle="--", linewidth=1.4, label="경계에서 수직 2 mm 안쪽"))

    # Initial anchor and target are the recorded H0 and shared goal, followed
    # by each candidate's saved source anchor and goal.
    initial = analysis["initial_anchors_G_m"]["LH:thumb3"]
    goals = summary[0]["anchor_goal_G_m"]["LH:thumb3"]
    ax.scatter(initial[0] * 1000, initial[1] * 1000, marker="s", s=72,
               color="#333333", label="초기 대표점", zorder=5)
    ax.scatter(goals[0] * 1000, goals[1] * 1000, marker="*", s=150,
               color="#f0a12b", edgecolor="#6e4b0c", label="같은 XY 목표 (Z는 여유별로 다름)", zorder=6)
    colors = ["#2369a8", "#d45c35", "#47864b", "#8b63a9"]
    for i, row in enumerate(summary):
        point = row["anchor_G_m"]["LH:thumb3"]
        goal = row["anchor_goal_G_m"]["LH:thumb3"]
        ax.scatter(point[0] * 1000, point[1] * 1000, s=65, color=colors[i],
                   edgecolor="white", linewidth=.8, label="후보 {} 대표점".format(i + 1), zorder=5)
        require(goal[:2] == goals[:2], "XY target differs between candidates")
        ax.annotate("후보 {}".format(i + 1), (point[0] * 1000, point[1] * 1000),
                    xytext=(-38, 78 - i * 2.5), textcoords="data", color=colors[i], fontsize=9,
                    arrowprops={"arrowstyle": "-", "color": colors[i], "linewidth": .7})
    ax.set_title("넥 후면 왼쪽 경계와 엄지 대표점 (국소 확대)")
    ax.set_xlabel("Gx (mm)")
    ax.set_ylabel("Gy (mm)")
    ax.grid(True, alpha=.22)
    ax.set_xlim(-40, -16)
    ax.set_ylim(50, 82)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="lower right", fontsize=7, frameon=True)

    x = np.arange(4)
    width = .34
    thumb = np.asarray(approved["thumb_errors_mm"], dtype=float)
    palm = np.asarray(approved["palm_errors_mm"], dtype=float)
    bx.bar(x - width / 2, thumb, width, color="#3f79a8", label="엄지 목표 오차")
    bx.bar(x + width / 2, palm, width, color="#d98745", label="손바닥 목표 오차")
    for i in range(4):
        bx.text(i - width / 2, thumb[i] + .22, "{:.2f}".format(thumb[i]),
                ha="center", va="bottom", fontsize=8)
        bx.text(i + width / 2, palm[i] + .22, "{:.2f}".format(palm[i]),
                ha="center", va="bottom", fontsize=8)
        bx.text(i, max(thumb[i], palm[i]) + 1.05,
                "교차 {}".format(approved["source_intersection_counts"][i]),
                ha="center", va="bottom", fontsize=8, color="#7a2922")
    bx.set_xticks(x)
    bx.set_xticklabels(["0.1 / 0.3", "0.1 / 0.7", "0.2 / 0.3", "0.2 / 0.7"])
    bx.set_xlabel("엄지 반경 (rad) / 여유 (mm)")
    bx.set_ylabel("목표 오차 (mm)")
    bx.set_title("네 완료 후보의 목표 오차")
    bx.grid(axis="y", alpha=.22)
    bx.set_ylim(0, max(thumb) + 2.2)
    bx.legend(loc="upper right", fontsize=8)

    fig.suptitle("후면 엄지 source 후보 비교 — 모든 후보 거절, native 실행 없음", fontsize=14)
    fig.text(.5, .025,
             "CPU source 형상 및 G 좌표의 정적 비교. source 반경은 물리적 깊이가 아니며 λ는 힘이 아니다. "
             "그림은 Gym/PhysX 접촉·cooked 형상·해부학적 지지를 인증하지 않는다.",
             ha="center", fontsize=8)
    fig.savefig(PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    require(os.path.isfile(PNG), "PNG was not created")
    inputs_after = input_closure(producer_path, analysis)
    require(inputs_before == inputs_after, "sealed inputs changed during artifact generation")
    manifest = {
        "schema": "rear-facet-artifact-manifest-v1",
        "scope": "source-only static comparison; native_initializations=0; physics_steps=0",
        "producer": producer_path,
        "producer_sha256": inputs_after[producer_path],
        "brief": BRIEF,
        "brief_sha256": inputs_after[BRIEF],
        "analysis": ANALYSIS,
        "analysis_sha256": inputs_after[ANALYSIS],
        "analysis_input_closure_count": len(analysis["input_sha256"]),
        "font": FONT,
        "font_sha256": inputs_after[FONT],
        "sealed_inputs_before": inputs_before,
        "sealed_inputs_after": inputs_after,
        "outputs": {PNG: sha256(PNG)},
        "candidate_labels": labels,
        "accepted_candidates": 0,
        "native_initializations": 0,
        "physics_steps": 0,
        "notes": ["No native/Gym image or video was created.",
                  "QP optimizer success flags are preserved separately; feasible distance bounds do not imply an optimizer optimum."],
    }
    with open(MANIFEST, "x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("rear facet artifact generation failed: {}".format(exc), file=sys.stderr)
        raise
