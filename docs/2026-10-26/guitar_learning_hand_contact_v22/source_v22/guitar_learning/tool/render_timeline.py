"""fingering.json → 운지 타임라인 PNG (가로 = 시간, 6줄 레인, 손가락별 색).

실행: python -m guitar_learning.tool.render_timeline <fingering.json> <out.png> [strike_training.json]
(matplotlib 필요 — tab2fm에 포함. 산출물은 _gen/에 저장 권장.)
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def render_timeline(source, out, strike_source=None, *, rearm_min_frames=2,
                    follow_through_min_frames=1,
                    initial_timing_tolerance_ms=100.0):
    SRC, OUT = Path(source), Path(out)
    STRIKE_SRC = Path(strike_source) if strike_source is not None else None
    d = json.loads(SRC.read_text())

    strum_groups = []
    if STRIKE_SRC is not None:
        from guitar_learning.tool._strike_goal_compiler import (
            GESTURE_STRUM, compile_strike_events)

        strike_data = json.loads(STRIKE_SRC.read_text())
        compiled = compile_strike_events(
            strike_data["events"],
            fps=int(strike_data["metadata"]["fps"]),
            rearm_min_frames=rearm_min_frames,
            follow_through_min_frames=follow_through_min_frames,
            initial_timing_tolerance_ms=initial_timing_tolerance_ms,
        )
        strum_groups = [
            event for event in compiled.events
            if event.gesture == GESTURE_STRUM
        ]

    for f in font_manager.fontManager.ttflist:
        if "NanumGothic" == f.name or "Noto Sans CJK KR" in f.name:
            plt.rcParams["font.family"] = f.name
            break
    plt.rcParams["axes.unicode_minus"] = False

    FCOL = {1: "#2a78d6", 2: "#1baf7a", 3: "#eda100", 4: "#008300",
            0: "#b4b2a9", None: "#d03b3b"}
    FTXT = {1: "#ffffff", 2: "#04342c", 3: "#412402", 4: "#ffffff",
            0: "#2c2c2a", None: "#ffffff"}
    # 실제 연주 자세의 물리적 위→아래: low-E, A, D, G, B, high-e.
    # matplotlib y는 아래에서 위로 증가하므로 s0(low-E)를 y=5에 둔다.
    YTICK_LABELS = ["e", "B", "G", "D", "A", "E"]
    DUR = max(n["t_off"] for n in d["notes"])

    fig_w = max(16.0, DUR * 0.9)
    fig, ax = plt.subplots(figsize=(fig_w, 5.2), dpi=150)

    # 그립 밴드 (y=6.6 부근)
    merged = []
    for h in d["hand"]:
        g = h["grip"]
        if merged and merged[-1][2] == g:
            merged[-1][1] = h["t"]
        else:
            merged.append([h["t"], h["t"], g])
    for t0, t1, g in merged:
        if not g:
            continue
        w = max(t1 - t0, 0.0) + 0.45
        ax.add_patch(Rectangle((t0, 6.35), w, 0.5, color="#f1efe8", zorder=1))
        lab = (g.replace(":5/", "5 ").replace(":maj/", "maj ").replace(":min/", "min ")
                 .replace("E-form@", "E폼@").replace("A-form@", "A폼@")
                 .replace("P1@", "@").replace("P2@", "@"))
        if w >= 0.055 * len(lab) + 0.1:            # 폭에 들어갈 때만 라벨 (겹침 방지)
            ax.text(t0 + 0.06, 6.6, lab, fontsize=8, color="#444441", va="center", zorder=2)

    # 줄 레인 (실제 기타 자세와 동일: E=위, e=아래)
    for s in range(6):
        y = 5 - s                           # s0(low-E)=위, s5(high-e)=아래
        ax.axhline(y, color="#e1e0d9", lw=0.8, zorder=0)

    presses = d.get("presses")
    if presses:
        # ---- 막대 = 왼손 누름 구간 (타현보다 선행 시작, 재타현 동안 유지) ----
        for ev in presses:
            y = 5 - ev["string"]
            c = FCOL.get(ev["finger"], "#d03b3b")
            w = max(ev["t_release"] - ev["t_press"], 0.04)
            ax.add_patch(Rectangle((ev["t_press"], y - 0.28), w, 0.56, color=c,
                                   zorder=3, ec="white", lw=0.6))
            lab = f"{ev['fret']}" + ("B" if ev["barre"] else "")
            if w >= 0.14:
                ax.text(ev["t_press"] + w / 2, y, lab, fontsize=7.5, ha="center",
                        va="center", color=FTXT.get(ev["finger"], "#fff"), zorder=4)
        for n in d["notes"]:                       # 개방현(왼손 무관)·미배정 노트
            y, t0 = 5 - n["string"], n["t_on"]
            if n["fret"] == 0:
                ax.add_patch(Rectangle((t0, y - 0.18), max(n["t_off"] - t0, 0.04),
                                       0.36, color=FCOL[0], alpha=0.6, zorder=2))
            elif n["finger"] is None:
                ax.add_patch(Rectangle((t0, y - 0.28), max(n["t_off"] - t0, 0.04),
                                       0.56, color=FCOL[None], zorder=3, ec="white", lw=0.6))
        for n in d["notes"]:                       # 타현(strike) = 소리 onset
            y, t0 = 5 - n["string"], n["t_on"]
            ax.plot([t0, t0], [y - 0.40, y + 0.40], color="#0b0b0b", lw=1.2,
                    zorder=5, solid_capstyle="butt")
    else:                                          # (구버전 fingering.json 폴백)
        for n in d["notes"]:
            fr, fg = n["fret"], n["finger"]
            y = 5 - n["string"]
            t0, tf = n["t_on"], n["t_off"]
            te = n.get("t_cut", tf)
            c = FCOL.get(fg, "#d03b3b")
            if tf > te + 0.03:
                ax.add_patch(Rectangle((te, y - 0.18), tf - te, 0.36, color=c,
                                       alpha=0.18, zorder=2))
            w = max(te - t0, 0.04)
            ax.add_patch(Rectangle((t0, y - 0.28), w, 0.56, color=c, zorder=3,
                                   ec="white", lw=0.6))
            ax.plot([t0, t0], [y - 0.40, y + 0.40], color="#0b0b0b", lw=1.2,
                    zorder=5, solid_capstyle="butt")
            lab = f"{fr}" + ("B" if n["barre"] else "")
            if w >= 0.14:
                ax.text(t0 + w / 2, y, lab, fontsize=7.5, ha="center", va="center",
                        color=FTXT.get(fg, "#fff"), zorder=4)

    for group_index, event in enumerate(strum_groups, start=1):
        group_notes = [d["notes"][int(index)] for index in event.source_event_ids]
        times = [float(note["t_on"]) for note in group_notes]
        rows = [5 - int(note["string"]) for note in group_notes]
        center = 0.5 * (min(times) + max(times))
        width = max(max(times) - min(times) + 0.08, 0.13)
        left = center - 0.5 * width
        bottom = min(rows) - 0.46
        height = max(rows) - min(rows) + 0.92
        ax.add_patch(Rectangle(
            (left, bottom), width, height,
            facecolor="#9c27b0", edgecolor="#6a1b9a", alpha=0.16,
            lw=1.4, zorder=4.6))
        ax.add_patch(Rectangle(
            (left, bottom), width, height,
            facecolor="none", edgecolor="#6a1b9a",
            lw=1.15, zorder=6))
        ax.text(
            left + 0.015, bottom + height - 0.04, f"S{group_index:02d}",
            fontsize=5.5, color="#4a148c", ha="left", va="top",
            zorder=7, bbox={
                "facecolor": "#ffffff", "edgecolor": "none",
                "alpha": 0.72, "pad": 0.25})

    ax.set_yticks(range(6))
    ax.set_yticklabels(YTICK_LABELS, fontsize=10)
    ax.set_ylim(-0.6, 7.0)
    ax.set_xlim(-0.15, DUR + 0.2)
    ax.set_xticks(range(0, int(DUR) + 1, 1))
    ax.set_xticklabels([f"{t}" for t in range(0, int(DUR) + 1)], fontsize=8)
    ax.set_xlabel("시간 (초)", fontsize=10)
    ax.grid(axis="x", color="#f1efe8", lw=0.6, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)

    legend = [Patch(color=FCOL[1], label="1 검지"), Patch(color=FCOL[2], label="2 중지"),
              Patch(color=FCOL[3], label="3 약지"), Patch(color=FCOL[4], label="4 소지"),
              Patch(color=FCOL[0], label="0 개방현"), Patch(color=FCOL[None], label="배정 불가"),
              Patch(color="#f1efe8", label="상단 띠 = 그립"),
              Line2D([0], [0], color="#0b0b0b", lw=1.2, label="| 타현(strike)")]
    if strum_groups:
        legend.append(Patch(
            facecolor="#9c27b0", edgecolor="#6a1b9a", alpha=0.16,
            label="보라 박스 = 하나의 strum"))
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.0, 1.10),
              ncol=8, frameon=False, fontsize=9)
    fig.suptitle("운지 타임라인 — 막대=왼손 누름(타현 선행·재타현 유지), "
                 "검은 세로선=타현(strike), 회색=개방현"
                 + (f", 보라 박스={len(strum_groups)}개 strum 그룹"
                    if strum_groups else ""),
                 fontsize=11, y=0.995, color="#52514e")
    fig.subplots_adjust(top=0.82)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight", facecolor="#fcfcfb")
    print(f"saved: {OUT}")
    plt.close(fig)
    return OUT


def main(argv=None):
    parser = argparse.ArgumentParser(description="운지·타현·strum 그룹 타임라인 PNG")
    parser.add_argument("fingering", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("strike_input", type=Path, nargs="?")
    parser.add_argument("--rearm-min-frames", type=int, default=2)
    parser.add_argument("--follow-through-min-frames", type=int, default=1)
    parser.add_argument("--initial-timing-tolerance-ms", type=float, default=100.0)
    args = parser.parse_args(argv)
    return render_timeline(
        args.fingering, args.out, args.strike_input,
        rearm_min_frames=args.rearm_min_frames,
        follow_through_min_frames=args.follow_through_min_frames,
        initial_timing_tolerance_ms=args.initial_timing_tolerance_ms)


if __name__ == "__main__":
    main()
