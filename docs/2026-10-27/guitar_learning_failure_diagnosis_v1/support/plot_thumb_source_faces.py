"""Plot the frozen source-face audit; this is not a cooked-collision plot."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "04_ablation/thumb_geometry_audit/geometry_summary.json"
OUT = ROOT / "figures"


def rear_z(plane, y):
    assert abs(plane[0]) < 1e-9
    return -(plane[1] * y + plane[3]) / plane[2]


def main():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    data = json.loads(SOURCE.read_text())
    plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    witness = np.asarray(data["existing_witness"]["point_G_m"])
    windows = np.asarray([t["thumb_requested_y_window_m"] for t in data["guide_track"]["targets"]])
    band = windows.min(), windows.max()
    limits = [(-.25, .265), (-.10, .12)]
    for axis, (low, high) in zip(axes, limits):
        y = np.linspace(low, high, 300)
        axis.plot(y * 1000, rear_z(np.asarray(data["current_rear_plane_G"]), y) * 1000,
                  "--", color="#c84d38", linewidth=2, label="현재 안내면: OBJ의 모든 꼭짓점")
        for index, mesh in enumerate(data["neck_meshes"]):
            bounds = mesh["face_only_y_bounds_m"]
            values = np.linspace(*bounds, 100)
            axis.plot(values * 1000,
                      rear_z(np.asarray(mesh["face_only_hull_rear_planes"][0]), values) * 1000,
                      color="#167d63" if index == 0 else "#315c9e", linewidth=3,
                      label="OBJ 면의 후면: " + ("연주용 넥" if index == 0 else "헤드 전환부"))
        axis.axvspan(band[0] * 1000, band[1] * 1000, alpha=.08, color="#6c59a6",
                     label="현재 67음의 안내 영역 합집합")
        axis.scatter(witness[1] * 1000, witness[2] * 1000, s=45, color="#222222", zorder=5,
                     label="이전 엄지 검사 표본")
        axis.set(xlim=(low * 1000, high * 1000), ylim=(-18, -6),
                 xlabel="기타 길이 방향 Gy (mm)", ylabel="기타 깊이 Gz (mm)")
        axis.grid(alpha=.2)
    gap = data["existing_witness"]["distance_behind_neck1_source_rear_m"] * 1000
    axes[0].set_title("원본 넥 구간 전체 · 세로축 확대")
    axes[1].set_title("현재 곡 안내 구간 확대")
    axes[1].annotate("", xy=(witness[1] * 1000, -8),
                     xytext=(witness[1] * 1000, witness[2] * 1000),
                     arrowprops={"arrowstyle": "<->", "color": "#222222"})
    axes[1].text(witness[1] * 1000 + 3, -10.8, f"원본 면과 {gap:.3f} mm", fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=9,
               bbox_to_anchor=(.5, .055), frameon=False)
    fig.suptitle("엄지 안내면과 OBJ 후면의 위치 비교", fontsize=16)
    fig.text(.5, .02, "원본 면에 대한 기하 비교입니다. PhysX가 만든 충돌면과 실제 접촉은 별도 검사 대상입니다.",
             ha="center", fontsize=10)
    fig.subplots_adjust(bottom=.28, top=.85, wspace=.26)
    OUT.mkdir(exist_ok=True)
    path = OUT / "thumb_source_faces.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == digest
    result = dict(source=str(SOURCE), source_sha256=digest, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  plot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), gap_mm=gap,
                  guide_window_y_bounds_m=list(band), source_unchanged=True,
                  scope="Source-face side profile only; not native collision/pressure evidence")
    (OUT / "thumb_source_faces.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
