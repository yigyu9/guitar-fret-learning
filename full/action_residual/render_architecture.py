"""Render the Action Residual architecture as SVG and high-resolution PNG."""
from __future__ import annotations

import os
from pathlib import Path


_MPL_CACHE = Path("/tmp/tab2body-action-residual-matplotlib")
_MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE))

import matplotlib


matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle


OUTPUT_DIR = Path(__file__).resolve().parent / "diagrams"

COLORS = {
    "background": "#F7F8FC",
    "text": "#162033",
    "muted": "#566176",
    "frozen_fill": "#E7EAF0",
    "frozen_edge": "#667085",
    "input_fill": "#FFF1D6",
    "input_edge": "#C77913",
    "train_fill": "#E5F6EA",
    "train_edge": "#258653",
    "rule_fill": "#E7F0FF",
    "rule_edge": "#346DB0",
    "critic_fill": "#EEE9FF",
    "critic_edge": "#7256A8",
    "protect_fill": "#FCEBE8",
    "protect_edge": "#B34A3C",
    "arrow": "#485568",
}


def _configure_font() -> None:
    candidates = (
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            family = font_manager.FontProperties(fname=str(path)).get_name()
            plt.rcParams["font.family"] = family
            break
    plt.rcParams["axes.unicode_minus"] = False


def _box(
        ax, x: float, y: float, width: float, height: float,
        title: str, body: str, *, kind: str,
        title_size: float = 13.0, body_size: float = 10.7,
        linewidth: float = 1.6, zorder: int = 3) -> None:
    fill = COLORS[f"{kind}_fill"]
    edge = COLORS[f"{kind}_edge"]
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.04,rounding_size=0.14",
        facecolor=fill, edgecolor=edge, linewidth=linewidth,
        zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2, y + height * 0.72, title,
        ha="center", va="center", fontsize=title_size,
        fontweight="bold", color=COLORS["text"], zorder=zorder + 1,
    )
    ax.text(
        x + width / 2, y + height * 0.35, body,
        ha="center", va="center", fontsize=body_size,
        color=COLORS["muted"], linespacing=1.25, zorder=zorder + 1,
    )


def _arrow(
        ax, start: tuple[float, float], end: tuple[float, float], *,
        color: str | None = None, dashed: bool = False,
        connection: str = "arc3,rad=0.0", width: float = 1.55,
        zorder: int = 2) -> None:
    patch = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=13,
        linewidth=width, color=color or COLORS["arrow"],
        linestyle=(0, (4, 3)) if dashed else "solid",
        connectionstyle=connection, shrinkA=2.0, shrinkB=2.0,
        zorder=zorder,
    )
    ax.add_patch(patch)


def _label(ax, x: float, y: float, text: str, *, size: float = 9.6,
           color: str | None = None, rotation: float = 0.0) -> None:
    ax.text(
        x, y, text, ha="center", va="center", fontsize=size,
        color=color or COLORS["muted"], rotation=rotation, zorder=5,
        bbox={"facecolor": COLORS["background"], "edgecolor": "none",
              "pad": 1.0},
    )


def render() -> tuple[Path, Path]:
    _configure_font()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(28, 18), dpi=120)
    fig.patch.set_facecolor(COLORS["background"])
    ax.set_facecolor(COLORS["background"])
    ax.set_xlim(0, 28)
    ax.set_ylim(0, 18)
    ax.axis("off")

    ax.text(
        14, 17.35, "Full Action Residual Coordinator",
        ha="center", va="center", fontsize=24, fontweight="bold",
        color=COLORS["text"],
    )
    ax.text(
        14, 16.82,
        "현재 profile: Frozen Fret 30 + Frozen Strike 30 + Body 15 = Joint Action 75D",
        ha="center", va="center", fontsize=13.5,
        color=COLORS["muted"],
    )
    ax.text(
        14, 16.36,
        "75D / no-gaze 독립 기준선 · 모든 입력은 같은 Full snapshot과 공통 song/event supervisor에서 생성",
        ha="center", va="center", fontsize=10.8,
        color=COLORS["muted"],
    )

    _box(
        ax, 0.45, 13.35, 5.25, 2.25,
        "LOCKED  Frozen Fret",
        "native observation 425\nRMS → Actor 425→512→256→30\n출력: pre-tanh μF[30], log σF[30]",
        kind="frozen", title_size=14, body_size=10.8,
    )
    _box(
        ax, 0.45, 10.25, 5.25, 2.25,
        "LOCKED  Frozen Strike",
        "native observation 327\nRMS → Actor 327→512→256→30\n출력: pre-tanh μS[30], log σS[30]",
        kind="frozen", title_size=14, body_size=10.8,
    )
    ax.text(
        3.08, 9.78, "source hidden activation 접근 없음",
        ha="center", va="center", fontsize=10.2,
        color=COLORS["protect_edge"], fontweight="bold",
    )

    _box(
        ax, 0.45, 6.65, 5.25, 2.35,
        "Base mean assembler",
        "관절 이름으로 Fret 30 + Strike 30 배치\n신규 body 15에는 seated-hold neutral\nμbase[75] · source 이름/순서/SHA exact 검증",
        kind="rule", title_size=13.5, body_size=10.5,
    )

    encoder_x = 6.35
    encoder_w = 5.05
    encoder_h = 1.38
    encoders = (
        (14.13, "Source Intent Encoder", "μF[30] + μS[30] = 60 → 128 → 64"),
        (12.28, "Goal / Score Encoder", "goal window 128 → 128 → 64"),
        (10.43, "Readiness Encoder", "fret-ready · pick 거리/속도 · phase 64 → 128 → 64"),
        (8.58, "Joint / History Encoder", "상체 q · qdot · limit · 이전 action/residual 600 → 256 → 128"),
        (6.73, "Guitar / Support Encoder", "pose/twist · contact/slip · tether/mode 128 → 128 → 64"),
    )
    for y, title, body in encoders:
        _box(
            ax, encoder_x, y, encoder_w, encoder_h,
            title, body, kind="input", title_size=11.8, body_size=9.2,
            linewidth=1.35,
        )

    _box(
        ax, 12.38, 9.35, 3.45, 3.30,
        "Trainable fusion",
        "64 + 64 + 64 + 128 + 64\n= concat 384\n\nMLP 384 → 512 → 256\nELU · 약 0.60M trunk/encoder",
        kind="train", title_size=13.6, body_size=10.7,
    )

    _box(
        ax, 16.72, 12.02, 3.65, 2.13,
        "Arm residual head",
        "256 → 128 → 18\n양쪽 shoulder/elbow/wrist\n마지막 Linear: exact zero-init",
        kind="train", title_size=12.4, body_size=9.8,
    )
    _box(
        ax, 16.72, 8.72, 3.65, 2.13,
        "Body residual head",
        "256 → 128 → 15\nL/R Thorax + Torso/Spine/Chest\n마지막 Linear: exact zero-init",
        kind="train", title_size=12.4, body_size=9.7,
    )
    _box(
        ax, 16.72, 6.78, 3.65, 1.18,
        "Protected fingers 42D",
        "LH 21 + RH 21 · residual은 항상 정확히 0",
        kind="protect", title_size=10.9, body_size=8.9,
    )

    _box(
        ax, 21.03, 10.00, 3.32, 3.22,
        "Deterministic rules",
        "raw Δμ[33] → tanh\n× stage/phase authority mask\n× curriculum cap scale [0,1]\n× per-joint pre-tanh logit cap\n→ name scatter Δμjoint[75]",
        kind="rule", title_size=12.8, body_size=10.0,
    )
    _box(
        ax, 20.72, 6.63, 3.95, 2.24,
        "Runtime stage contract  (미연결)",
        "G0: arm timing, body masked\nG1: body cap을 점진 개방\nG2: 검증된 권한만 · 위험 시 strike skip",
        kind="input", title_size=11.7, body_size=9.5,
    )

    plus = Circle(
        (25.20, 7.90), 0.30,
        facecolor=COLORS["rule_fill"], edgecolor=COLORS["rule_edge"],
        linewidth=1.6, zorder=4,
    )
    ax.add_patch(plus)
    ax.text(
        25.20, 7.90, "+", ha="center", va="center",
        fontsize=18, fontweight="bold", color=COLORS["rule_edge"], zorder=5,
    )
    _label(ax, 25.20, 9.38, "μjoint = μbase + Δμjoint", size=9.8)

    _box(
        ax, 25.72, 6.88, 1.88, 2.15,
        "Joint policy",
        "μ[75]\nsource σ + new σ\nONE TanhNormal sample",
        kind="rule", title_size=10.6, body_size=8.8,
    )
    _box(
        ax, 24.72, 3.98, 2.88, 2.02,
        "PLANNED execution pipeline",
        "source별 deterministic transform\n→ inactive seated-neutral override\n→ common EMA 1회 → PD target",
        kind="rule", title_size=11.2, body_size=9.1,
    )
    _box(
        ax, 24.72, 1.22, 2.88, 1.82,
        "PLANNED Full environment",
        "Fret + Strike + 기타 6DoF 물리\nG0 fixed → G1 tether → G2 free",
        kind="input", title_size=11.5, body_size=9.4,
    )

    _box(
        ax, 6.35, 2.05, 11.52, 3.20,
        "Central multi-head critic  (Actor와 parameter 공유 없음)",
        "actor-visible encoding 384 + privileged encoding 64 = 448 → 512 → 256 → V[11]\n"
        "Fret 6 · Strike 1 · joint event 1 · guitar pose/twist 1 · support/slip/force 1 · assist/safety 1\n"
        "privileged 128: 정확한 tether wrench, mass/inertia, simulator-only contact · PPO 학습 때만 사용",
        kind="critic", title_size=13.0, body_size=10.2,
    )
    _box(
        ax, 18.35, 3.05, 5.18, 2.10,
        "GAE / PPO wrapper  (미연결)",
        "reward·done + V[11] → advantage/return\n"
        "actor loss → 모든 green encoder/fusion/head\n"
        "critic loss → 별도 purple critic",
        kind="critic", title_size=11.8, body_size=9.3,
    )

    # Source flow.
    _arrow(ax, (5.70, 14.48), (6.35, 14.82))
    _arrow(ax, (5.70, 11.38), (6.35, 14.52), connection="arc3,rad=-0.22")
    _arrow(ax, (3.05, 13.35), (3.05, 9.00), connection="arc3,rad=0.18")
    _arrow(ax, (3.45, 10.25), (3.65, 9.00), connection="arc3,rad=-0.08")

    # Five encoder outputs into the concatenation/fusion block.
    target_y = (11.98, 11.58, 11.18, 10.78, 10.38)
    for (y, _, _), dest_y in zip(encoders, target_y):
        _arrow(
            ax, (encoder_x + encoder_w, y + encoder_h / 2),
            (12.38, dest_y),
            connection="arc3,rad=0.0", width=1.25,
        )

    # Fusion to zero-initialized heads and rule composer.
    _arrow(ax, (15.83, 11.52), (16.72, 13.08))
    _arrow(ax, (15.83, 10.46), (16.72, 9.78))
    _arrow(ax, (20.37, 13.08), (21.03, 12.35))
    _arrow(ax, (20.37, 9.78), (21.03, 10.78))
    _arrow(ax, (22.70, 8.87), (22.70, 10.00), color=COLORS["input_edge"])

    # Base + residual, one distribution and execution path.
    ax.plot(
        [5.70, 6.10, 24.84], [7.30, 6.23, 6.23],
        color=COLORS["arrow"], linewidth=1.55, zorder=2,
    )
    _arrow(ax, (24.84, 6.23), (25.13, 7.58), width=1.55)
    _label(ax, 15.30, 6.23, "μbase[75]", size=9.7)
    _arrow(ax, (24.35, 10.65), (25.20, 8.22), connection="arc3,rad=-0.12")
    _arrow(ax, (25.50, 7.90), (25.72, 7.90))
    _arrow(ax, (26.66, 6.88), (26.26, 6.00))
    _arrow(ax, (26.16, 3.98), (26.16, 3.04))

    # Critic inputs and the external GAE/PPO training loop.
    _arrow(
        ax, (8.85, 6.73), (8.85, 5.25),
        color=COLORS["critic_edge"], dashed=True,
        connection="arc3,rad=0.0", width=1.45,
    )
    _label(
        ax, 10.75, 5.72, "같은 packed contexts + privileged state",
        size=8.8, color=COLORS["critic_edge"])
    _arrow(
        ax, (17.87, 4.02), (18.35, 4.02),
        color=COLORS["critic_edge"], dashed=True,
        connection="arc3,rad=0.0", width=1.45,
    )
    _label(ax, 18.10, 4.34, "V[11]", size=8.8,
           color=COLORS["critic_edge"])
    _arrow(
        ax, (24.72, 2.30), (23.53, 3.45),
        color=COLORS["critic_edge"], dashed=True,
        connection="arc3,rad=-0.10", width=1.45,
    )
    _label(ax, 24.15, 2.95, "reward/done", size=8.6,
           color=COLORS["critic_edge"])
    ax.plot(
        [20.20, 16.10, 16.10], [5.15, 5.62, 8.68],
        color=COLORS["critic_edge"], linewidth=1.45,
        linestyle=(0, (4, 3)), zorder=2,
    )
    _arrow(
        ax, (16.10, 8.68), (15.62, 9.35),
        color=COLORS["critic_edge"], dashed=True,
        connection="arc3,rad=0.0", width=1.45,
    )
    _label(ax, 18.10, 5.48, "actor loss → all green blocks", size=8.8,
           color=COLORS["critic_edge"])

    # Legend and identity.
    legend_y = 0.52
    legend = (
        (1.05, "frozen", "동결 source"),
        (4.55, "train", "학습 model"),
        (8.05, "rule", "고정 composer/rule"),
        (12.25, "input", "환경·context"),
        (16.15, "critic", "training critic"),
        (20.25, "protect", "보호된 관절"),
    )
    for x, kind, text in legend:
        rect = FancyBboxPatch(
            (x, legend_y - 0.13), 0.42, 0.26,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=COLORS[f"{kind}_fill"],
            edgecolor=COLORS[f"{kind}_edge"], linewidth=1.1,
        )
        ax.add_patch(rect)
        ax.text(
            x + 0.55, legend_y, text, ha="left", va="center",
            fontsize=9.3, color=COLORS["muted"],
        )
    ax.text(
        27.60, 0.52, "architecture_id: full.action_residual.pre_tanh.v1",
        ha="right", va="center", fontsize=9.1, color=COLORS["muted"],
    )

    png_path = OUTPUT_DIR / "action_residual_architecture.png"
    svg_path = OUTPUT_DIR / "action_residual_architecture.svg"
    fig.savefig(png_path, dpi=120, facecolor=fig.get_facecolor())
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    return png_path, svg_path


if __name__ == "__main__":
    png, svg = render()
    print(png)
    print(svg)
