"""검증된 연속 목표 6종을 동일 시간축 모음과 구간별 상세 그림으로 저장한다."""
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/press_combined_mpl")
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
COLORS = {1: "#2a78d6", 2: "#1baf7a", 3: "#eda100", 4: "#008300"}
TEXT_COLORS = {1: "white", 2: "#04342c", 3: "#412402", 4: "white"}
FINGERS = {1: "검지", 2: "중지", 3: "약지", 4: "소지"}
TITLES = ["단일 압현", "동시 압현", "같은 손가락 전환", "손가락 교대",
          "유지 + 추가", "일부 해제", "유지 + 나머지 전환", "전체 전환", "해제 후 재압현"]


def draw_timeline(ax, document, sections, limits, detailed=False):
    ax.set_facecolor("white")
    for i, section in enumerate(sections):
        ax.axvspan(section["start"], section["end"],
                   color="#eaf0f5" if i % 2 == 0 else "#f4f7fa", zorder=0)
        label = section["case_id"]
        if detailed:
            label += "  " + TITLES[int(section["case_id"][1:]) - 1]
        ax.text((section["start"] + section["end"]) / 2, 6.0, label,
                ha="center", va="center", fontsize=12, color="#41596b", weight="bold")
    for string in range(6):
        ax.axhline(5 - string, color="#cfd9e1", lw=.8, zorder=1)
    for event in document["presses"]:
        start, stop = event["t_press"], event["t_release"]
        if stop <= limits[0] or start >= limits[1]:
            continue
        y, finger = 5 - event["string"], event["finger"]
        ax.add_patch(Rectangle((start, y - .30), stop - start, .60,
                               facecolor=COLORS[finger], edgecolor="white", lw=.7, zorder=2))
        ax.text((start + stop) / 2, y, str(event["fret"]),
                color=TEXT_COLORS[finger], fontsize=13, weight="bold",
                ha="center", va="center", zorder=3)
    for note in document["notes"]:
        if limits[0] <= note["t_on"] <= limits[1]:
            y = 5 - note["string"]
            ax.plot([note["t_on"]] * 2, [y - .40, y + .40],
                    color="#172532", lw=1.3, zorder=4)
    ax.set_xlim(*limits)
    ax.set_ylim(-.6, 6.55)
    ax.set_yticks(range(6), ["1번 e", "2번 B", "3번 G", "4번 D", "5번 A", "6번 E"])
    ax.set_xticks(range(int(limits[0]) + (int(limits[0]) % 2), int(limits[1]) + 1, 2))
    ax.tick_params(length=0, labelsize=11, pad=6)
    ax.grid(axis="x", color="#e6edf2", lw=.7, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def legend(fig, y):
    handles = [Patch(facecolor=COLORS[f], label=f"{f} {FINGERS[f]}") for f in range(1, 5)]
    handles.append(Line2D([0], [0], color="#172532", lw=1.3, label="목표 음 시작"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(.055, y),
               ncol=5, frameon=False, fontsize=12)


def save(fig, stem):
    paths = []
    for suffix in ("png", "svg"):
        path = ROOT / "이미지" / (stem + "." + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, facecolor=fig.get_facecolor())
        paths.append(str(path.relative_to(ROOT)))
    plt.close(fig)
    return paths


def main():
    for font in font_manager.fontManager.ttflist:
        if font.name == "NanumGothic":
            plt.rcParams["font.family"] = font.name
            break
    plt.rcParams["axes.unicode_minus"] = False
    sources = sorted((ROOT / "입력").glob("C*.fingering.json"))
    if len(sources) != 6:
        raise ValueError("Expected six validated combined goals")
    documents = [json.loads(source.read_text()) for source in sources]
    report = {"input_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sources}, "images": [], "physical_simulation": False}
    for document in documents:
        meta = document["metadata"]
        pair = " + ".join(FINGERS[f] for f in meta["finger_pair"])
        sections = meta["sections"]
        fig, axes = plt.subplots(3, 1, figsize=(22, 10), dpi=160)
        fig.patch.set_facecolor("#f6f8fa")
        fig.text(.06, .955, f"{meta['version_id']}  {pair} · 하나로 이어지는 압현 목표",
                 fontsize=25, weight="bold", color="#182a3a")
        fig.text(.06, .915, "9개 과제 · 첫 음 1.00초 / 마지막 해제 43.75초 · 과제 사이 음 간격 1.75초",
                 fontsize=13, color="#526775")
        legend(fig, .89)
        edges = [0, (sections[2]["end"] + sections[3]["start"]) / 2,
                 (sections[5]["end"] + sections[6]["start"]) / 2, sections[-1]["end"] + .75]
        for row, ax in enumerate(axes):
            draw_timeline(ax, document, sections[row * 3:row * 3 + 3],
                          (edges[row], edges[row + 1]), detailed=True)
            ax.set_xlabel("전체 시퀀스 시간 (초)", fontsize=11)
        fig.text(.06, .045, "막대 = 누름 시작~해제 · 숫자 = 프렛 · 색 = 손가락 · 위→아래: 6번줄→1번줄",
                 fontsize=12, color="#526775")
        fig.text(.06, .018, "읽기 편하도록 같은 연속 목표를 세 행으로 나눔(행마다 표시 시간 범위가 다름). 운지 규칙 검증 완료 · 물리 수행 미검증.",
                 fontsize=11, color="#526775")
        fig.subplots_adjust(left=.065, right=.975, top=.80, bottom=.11, hspace=.40)
        report["images"] += save(fig, "개별/" + meta["version_id"])

    fig, axes = plt.subplots(6, 1, figsize=(24, 21), dpi=160)
    fig.patch.set_facecolor("#f6f8fa")
    fig.text(.06, .966, "하나의 연속 목표 × 손가락 조합 6종", fontsize=29, weight="bold", color="#182a3a")
    fig.text(.06, .941, "P1→P9를 한 시간축으로 결합 · 같은 줄·프렛·시각에서 손가락 배정을 바꾼 6가지 목표",
             fontsize=15, color="#526775")
    legend(fig, .927)
    for ax, document in zip(axes, documents):
        meta = document["metadata"]
        draw_timeline(ax, document, meta["sections"], (0, 44.5))
        pair = " + ".join(FINGERS[f] for f in meta["finger_pair"])
        ax.set_title(meta["version_id"] + "  " + pair, loc="left", pad=16,
                     fontsize=18, weight="bold", color="#182a3a")
    axes[-1].set_xlabel("전체 시퀀스 시간 (초) — 6개 목표 모두 같은 시간축", fontsize=13)
    fig.text(.06, .061, "P1 단일 압현   ·   P2 동시 압현   ·   P3 같은 손가락 전환   ·   P4 손가락 교대   ·   P5 유지 + 추가",
             fontsize=13, color="#41596b")
    fig.text(.06, .042, "P6 일부 해제   ·   P7 유지 + 나머지 전환   ·   P8 전체 전환   ·   P9 해제 후 재압현",
             fontsize=13, color="#41596b")
    fig.text(.06, .020, "막대 = 누름 구간 · 숫자 = 프렛 · 검은 선 = 음 시작 · 운지 규칙을 검사한 합성 목표이며 학습·물리 수행 결과는 아님",
             fontsize=12, color="#526775")
    fig.subplots_adjust(left=.065, right=.975, top=.875, bottom=.115, hspace=.65)
    report["images"] += save(fig, "연속목표_6조합_모음")
    report["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (ROOT / "검증" / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Rendered 6 detailed timelines and comparison overview (PNG + SVG)")


if __name__ == "__main__":
    main()
