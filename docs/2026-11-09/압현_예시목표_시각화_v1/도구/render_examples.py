"""검증된 예시 JSON으로 기존 운지 타임라인과 9과제 모음 이미지를 만든다."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/press_mapping_examples_mpl")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from guitar_learning.tool.render_timeline import render_timeline


# 현행 render_timeline과 같은 색·줄 순서를 사용하고 문자 범례를 함께 둔다.
COLORS = {1: "#2a78d6", 2: "#1baf7a", 3: "#eda100", 4: "#008300"}
TEXT_COLORS = {1: "white", 2: "#04342c", 3: "#412402", 4: "white"}
FINGERS = {1: "검지", 2: "중지", 3: "약지", 4: "소지"}
TITLES = {
    "P1": "단일 압현", "P2": "두 손가락 동시 압현",
    "P3": "같은 손가락 목표 전환", "P4": "다른 손가락으로 교대",
    "P5": "기존 압현 유지 + 추가", "P6": "일부만 해제",
    "P7": "일부 유지 + 나머지 전환", "P8": "다중 목표 전체 전환",
    "P9": "해제 후 같은 목표 재압현",
}


def draw_case(ax, document):
    case_id = document["metadata"]["case_id"]
    ax.set_facecolor("#ffffff")
    for string in range(6):
        ax.axhline(5 - string, color="#dfe4e8", lw=1, zorder=0)
    for event in document["presses"]:
        y = 5 - event["string"]
        finger = event["finger"]
        start, stop = event["t_press"], event["t_release"]
        ax.add_patch(Rectangle(
            (start, y - .29), stop - start, .58,
            facecolor=COLORS[finger], edgecolor="white", lw=.7, zorder=2))
        ax.text((start + stop) / 2, y, str(event["fret"]),
                color=TEXT_COLORS[finger], fontsize=13,
                ha="center", va="center", weight="bold", zorder=3)
    for note in document["notes"]:
        y, onset = 5 - note["string"], note["t_on"]
        ax.plot([onset, onset], [y - .4, y + .4], color="#161b22", lw=1.4,
                zorder=4, solid_capstyle="butt")
    used = sorted({note["finger"] for note in document["notes"]})
    allocation = " · ".join(FINGERS[finger] for finger in used)
    ax.set_title(case_id + "  " + TITLES[case_id], loc="left",
                 fontsize=16, fontweight="bold", pad=24, color="#182a3a")
    ax.text(0, 1.025, "이번 추출: " + allocation, transform=ax.transAxes,
            fontsize=10, color="#627382", va="bottom")
    ax.set_xlim(0, 6)
    ax.set_ylim(-.65, 5.65)
    ax.set_xticks(range(7))
    ax.set_yticks(range(6))
    ax.set_yticklabels(["1번 e", "2번 B", "3번 G", "4번 D", "5번 A", "6번 E"])
    ax.set_xlabel("시간 (초)", fontsize=10, labelpad=5)
    ax.tick_params(axis="both", length=0, labelsize=10, pad=6)
    ax.grid(axis="x", color="#eef1f4", lw=.7, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main():
    sources = [ROOT / "입력" / (case_id + ".fingering.json")
               for case_id in TITLES]
    documents = [json.loads(path.read_text()) for path in sources]
    for font in font_manager.fontManager.ttflist:
        if font.name == "NanumGothic":
            plt.rcParams["font.family"] = font.name
            break
    plt.rcParams["axes.unicode_minus"] = False
    image_root = ROOT / "이미지"
    image_root.mkdir(parents=True, exist_ok=True)
    # 원 시각화 함수를 그대로 사용한 개별 이미지도 함께 제공한다.
    for source in sources:
        render_timeline(source, image_root / "개별" / (source.stem.split(".")[0] + ".png"))

    fig, axes = plt.subplots(3, 3, figsize=(20, 13), dpi=180)
    fig.patch.set_facecolor("#f6f8fa")
    for ax, document in zip(axes.flat, documents):
        draw_case(ax, document)
    fig.suptitle("압현 학습 과제 · 무작위 손가락 배정 예시", x=.05, y=.97,
                 ha="left", fontsize=27, weight="bold", color="#182a3a")
    fig.text(.05, .928,
             "기존 finger mapping 후보 규칙과 누름 일정을 검사한 9개 예시 · 바레 제외 · 1~14프렛",
             fontsize=13, color="#526775")
    legend = [Patch(facecolor=COLORS[f], label=str(f) + " " + FINGERS[f])
              for f in range(1, 5)]
    legend.append(Line2D([0], [0], color="#161b22", lw=1.4, label="목표 음 시작"))
    fig.legend(handles=legend, loc="upper left", bbox_to_anchor=(.045, .909),
               ncol=5, frameon=False, fontsize=12)
    fig.text(.05, .043,
             "막대 = 누름 시작~해제 · 숫자 = 프렛 · 위→아래: 6번줄(E)→1번줄(e) · 모든 패널의 시간축은 동일",
             fontsize=12, color="#526775")
    fig.text(.05, .019,
             "기본 선행 누름 120ms 적용. 손가락은 예시마다 추출하며 과제 중 배정 유지. 운지 규칙 검증이며 물리 수행 결과는 아님.",
             fontsize=11, color="#526775")
    fig.subplots_adjust(left=.06, right=.975, top=.82, bottom=.10,
                        wspace=.22, hspace=.60)
    for suffix in ("png", "svg"):
        fig.savefig(image_root / ("압현_9과제_모음." + suffix),
                    facecolor=fig.get_facecolor())
    plt.close(fig)
    report = {
        "input_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sources},
        "source_renderer": "guitar_learning/tool/render_timeline.py",
        "individual_images": 9, "overview_size_px": [3600, 2340],
        "physical_simulation": False,
    }
    (ROOT / "검증" / "render_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Rendered 9 native timeline images and PNG/SVG overview")


if __name__ == "__main__":
    main()
