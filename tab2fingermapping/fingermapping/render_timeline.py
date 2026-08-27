"""fingering.json → 운지 타임라인 PNG (가로 = 시간, 6줄 레인, 손가락별 색).

실행: /home/ajou/anaconda3/envs/tab2fm/bin/python fingermapping/render_timeline.py <fingering.json> <out.png>
(matplotlib 필요 — tab2fm에 포함. 산출물은 _gen/에 저장 권장.)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
d = json.loads(SRC.read_text())

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
ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.0, 1.10),
          ncol=8, frameon=False, fontsize=9)
fig.suptitle("운지 타임라인 — 막대=왼손 누름(타현 선행·재타현 유지), "
             "검은 세로선=타현(strike), 회색=개방현",
             fontsize=11, y=0.995, color="#52514e")
fig.subplots_adjust(top=0.82)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, bbox_inches="tight", facecolor="#fcfcfb")
print(f"saved: {OUT}")
