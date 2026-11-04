"""Render the three-policy framework design, not an experimental result."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as MplPath


OUT = Path(__file__).resolve().parents[1] / "images"
FONT = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
plt.rcParams.update({"svg.fonttype": "path", "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(18, 12))
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
ax.set(xlim=(0, 18), ylim=(0, 12))
ax.axis("off")
INK, MUTED, BLUE, PURPLE = "#172C40", "#526678", "#256592", "#73529A"
PALE, LILAC, GRAY = "#EFF6FB", "#F5F0FA", "#F5F7F9"


def text(x, y, value, size=13, color=INK, ha="center", **kwargs):
    return ax.text(x, y, value, fontproperties=FONT, fontsize=size,
                   color=color, ha=ha, va="center", linespacing=1.6, **kwargs)


def box(x, y, w, h, title, detail="", fill=PALE, design=False, size=16):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.09",
        facecolor=fill, edgecolor="#AAB9C7", linewidth=1.2,
        linestyle=(0, (5, 3)) if design else "solid", zorder=3))
    text(x+w/2, y+h*(.69 if detail else .5), title, size, zorder=4)
    if detail:
        text(x+w/2, y+h*.30, detail, 12, MUTED, zorder=4)


def arrow(points, color=BLUE, dashed=False, width=1.65):
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO]*(len(points)-1))
    ax.add_patch(FancyArrowPatch(
        path=path, arrowstyle="-|>", mutation_scale=13, linewidth=width,
        color=color, linestyle=(0, (5, 3)) if dashed else "solid", zorder=2))


def label(x, y, value, color=MUTED, size=11):
    text(x, y, value, size, color, bbox={"facecolor": "white", "edgecolor": "none", "pad": 2}, zorder=5)


text(.55, 11.55, "기타 연주 프레임워크 · Overview", 24, ha="left")
text(.55, 11.10, "전체 설계  |  상태 피드백으로 연주하고, 수집한 경험으로 정책을 학습", 14, MUTED, ha="left")
text(.55, 10.53, "A   실행 루프", 16, ha="left")
text(17.45, 10.53, "실선: 실행·평가    보라 점선: 학습 경로    점선 상자: 통합 설계", 11, MUTED, ha="right")

# Musical goals are prepared independently of the online physical loop.
box(.6, 9.30, 2.15, .85, "오디오", size=16)
box(3.30, 9.30, 3.35, .85, "전사·운지·타현 계획", size=15)
box(7.20, 9.30, 4.25, .85, "음악적 목표", "줄·프렛·손가락·방향·시각")
arrow([(2.75, 9.72), (3.30, 9.72)])
arrow([(6.65, 9.72), (7.20, 9.72)])
arrow([(9.32, 9.30), (9.32, 8.96), (2.55, 8.96), (2.55, 8.50)])
label(5.3, 8.97, "압현·타현 시간표")

# Each policy owns different joints; the body policy gets no musical goals.
box(.6, 4.98, 3.9, 3.52, "", fill=GRAY, design=True)
text(2.55, 7.75, "통합 실행관리", 17, zorder=4)
text(2.55, 6.50, "공통 연주 시계\n현재·예정 목표 선택\n정책별 관측 구성\n진행 관리·종료 환경 초기화", 13, MUTED, zorder=4)
box(6.45, 7.50, 3.15, 1.05, "압현 정책 · 33축", "왼팔·왼손")
box(6.45, 6.12, 3.15, 1.05, "타현 정책 · 27축", "오른쪽 팔꿈치·손목·손")
box(6.45, 4.74, 3.15, 1.05, "전신 정책 · 37축", "자세·기타 지지 | 설계", fill=GRAY, design=True)
for y, content in [(8.025, "상태 + 압현 목표"), (6.645, "상태 + 타현 목표"), (5.265, "상태만")]:
    arrow([(4.5, y), (6.45, y)])
    label(5.48, y+.18, content)

box(10.40, 5.95, 2.15, 1.38, "명령 결합", "관절별 배치\n33 + 27 + 37 = 97", design=True, size=15)
for y in [8.025, 6.645, 5.265]:
    arrow([(9.60, y), (10.02, y), (10.02, 6.645), (10.40, 6.645)])
box(13.05, 5.95, 1.95, 1.38, "관절 제어", "목표각 변환·제한\n유한 구동", size=15)
box(15.50, 5.95, 1.95, 1.38, "물리 시뮬레이션", "신체·기타·접촉", size=14)
arrow([(12.55, 6.645), (13.05, 6.645)])
arrow([(15.0, 6.645), (15.50, 6.645)])
arrow([(16.475, 5.95), (16.475, 4.28), (2.55, 4.28), (2.55, 4.98)])
label(9.6, 4.28, "실제 상태와 수행 이력 → 다음 정책 관측")

# Evaluation runs during training and inference; PPO updates only during training.
ax.plot([.55, 17.45], [3.88, 3.88], color="#D3DCE4", linewidth=1)
text(.55, 3.53, "B   평가·기록과 학습", 16, ha="left")
text(17.45, 3.53, "위 실행에서 얻은 자료를 사용 · PPO 및 가치망 갱신은 학습 시에만 수행", 11, MUTED, ha="right")
box(.6, 1.90, 3.20, 1.10, "실행 결과와 목표", "물리 상태·접촉\n현재 목표·진행 정보", fill=GRAY, size=15)
box(4.30, 1.90, 3.10, 1.10, "보상·비용·종료 판정", "목표 달성·이탈·실패 평가", fill=GRAY, size=14)
box(8.0, 1.90, 4.00, 1.10, "학습 경험 수집", "관측·행동·보상·비용\n다음 관측·종료 여부", fill=LILAC, size=15)
box(12.60, 1.90, 4.85, 1.10, "각 정책의 PPO·가치망 학습", "정책 파라미터와 가치 추정기 갱신", fill=LILAC, size=15)
arrow([(3.80, 2.45), (4.30, 2.45)])
arrow([(7.40, 2.45), (8.00, 2.45)], color=PURPLE, dashed=True)
arrow([(12.0, 2.45), (12.60, 2.45)], color=PURPLE, dashed=True)
arrow([(15.02, 1.90), (15.02, 1.25), (12.70, 1.25)], color=PURPLE, dashed=True)
text(12.5, 1.25, "위 실행의 해당 정책에 반영", 12, PURPLE, ha="right")
arrow([(5.85, 1.90), (5.85, 1.30)])
text(5.85, 1.03, "로그·평가 기록", 13)
arrow([(4.95, 1.90), (4.95, 1.60), (1.8, 1.60), (1.8, 1.49)])
text(.6, 1.14, "종료 판정 → 실행관리\n종료한 환경만 초기화", 12, MUTED, ha="left")

text(.55, .47, "현재 구현: 압현·타현은 개별 실행 경로. 전신 37축 학습과 세 정책 공동 실행은 설계 단계.", 12, ha="left")
text(.55, .15, "물리 조건: 인간 Root 고정·자유 기타. 접촉·통과 판정은 실제 현 압력·음향 성공과 구분.", 11, MUTED, ha="left")

OUT.mkdir(exist_ok=True)
for extension in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"framework_overview_v5.{extension}", dpi=180, facecolor="white")
plt.close(fig)
