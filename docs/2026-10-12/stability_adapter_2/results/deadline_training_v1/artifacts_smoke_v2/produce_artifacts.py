#!/usr/bin/env python3
"""Build a small visual evidence pack from the frozen smoke_v2 outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1] / "smoke_v2"
OUT = Path(__file__).resolve().parent
CONDITIONS = ("initial_000000", "update_000001")


def read_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inputs() -> list[Path]:
    paths = [ROOT / "report.json", ROOT / "training.jsonl"]
    time_scatter = None
    for condition in CONDITIONS:
        episode = ROOT / "evaluations" / condition / "native/episode_0001"
        paths += [
            ROOT / "evaluations" / condition / "report.json",
            episode / "report.json",
            episode / "trace.json",
            episode / "controls.json",
            episode / "joint_events.json",
            episode / "initial_values.json",
            episode / "media/capture.json",
            episode / "media/videos.json",
            episode / "media/whole_body.mp4",
            episode / "media/hands.mp4",
        ]
        capture = read_json(episode / "media/capture.json")
        for frame in (capture["frames"][0], capture["frames"][-1]):
            paths.extend(Path(path) for path in frame["image_sha256"])
    return sorted(set(paths))


def capture_frames(episode: Path):
    capture = read_json(episode / "media/capture.json")
    return capture["frames"][0], capture["frames"][-1]


def plot_positions():
    fig = plt.figure(figsize=(11.6, 8.0), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    colors = {"initial_000000": "#2864a5", "update_000001": "#d45a32"}
    for condition in CONDITIONS:
        trace = read_json(ROOT / "evaluations" / condition / "native/episode_0001/trace.json")
        steps = np.asarray([row["physics_step"] for row in trace], dtype=float)
        xyz = np.asarray([row["position_W_m"] for row in trace], dtype=float)
        seconds = steps / 240.0
        ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], color=colors[condition], lw=1.8,
                label=condition.replace("_", " "))
        ax.scatter(*xyz[0], color=colors[condition], marker="o", s=38, edgecolor="white", linewidth=.7)
        ax.scatter(*xyz[-1], color=colors[condition], marker="X", s=54, edgecolor="white", linewidth=.7)
        # Time encoded as sparse colored markers; the path itself remains easy to read.
        idx = np.arange(0, len(seconds), 60)
        time_scatter = ax.scatter(xyz[idx, 0], xyz[idx, 1], xyz[idx, 2], c=seconds[idx], cmap="viridis",
                                  vmin=0, vmax=float(seconds[-1]), s=9, alpha=.7)

    # Actor-root position box requested in the approved brief.
    xlo, xhi = -0.50, -0.15
    ylo, yhi = -0.15, 0.15
    zlo, zhi = 0.65, 0.8837383985519409
    # Draw a translucent horizontal box outline, with Z bounds at each corner.
    for z in (zlo, zhi):
        corners = [(xlo,ylo),(xhi,ylo),(xhi,yhi),(xlo,yhi),(xlo,ylo)]
        ax.plot([p[0] for p in corners], [p[1] for p in corners], [z]*len(corners),
                color="#555555", lw=1.1, ls="--")
    for x in (xlo, xhi):
        for y in (ylo, yhi):
            ax.plot([x,x],[y,y],[zlo,zhi], color="#555555", lw=1.1, ls="--")
    ref = (-0.230415, 0.086712, 0.700973)
    ax.scatter(*ref, color="#111111", marker="*", s=135, label="nominal reference pW")
    ax.set_xlabel("X actor-root W (m)")
    ax.set_ylabel("Y actor-root W (m)")
    ax.set_zlabel("Z actor-root W (m)")
    ax.set_title("Measured guitar actor-root position paths\nline: physics trace; markers: time every 0.25 s")
    ax.legend(loc="upper left", fontsize=9)
    fig.colorbar(time_scatter, ax=ax, pad=0.10, shrink=0.70, label="Elapsed time (s)")
    ax.view_init(elev=24, azim=-58)
    fig.savefig(OUT / "position_paths_3d.png", dpi=180)
    plt.close(fig)


def build_readme():
    top = read_json(ROOT / "report.json")
    train = json.loads((ROOT / "training.jsonl").read_text().splitlines()[0])
    rows = []
    for condition in CONDITIONS:
        ep = ROOT / "evaluations" / condition / "native/episode_0001"
        report = read_json(ep / "report.json")
        video = read_json(ep / "media/videos.json")
        initial, final = capture_frames(ep)
        first_img = next(path for path in initial["image_sha256"] if "/whole_body/" in path)
        last_img = next(path for path in final["image_sha256"] if "/whole_body/" in path)
        local = ep.relative_to(Path(__file__).resolve().parents[1])
        rows.append((condition, report, video, first_img, last_img, local))
    lines = [
        "# Deadline smoke v2 산출물",
        "",
        "이 문서는 2026-10-12 deadline pilot의 실제 측정 부분집합을 시각화한다. `smoke_v2/report.json`은 256 transitions의 PPO update 1회가 완료됐고, production reward v4 인증은 아니라고 기록한다. 학습은 CUDA, native episode는 CPU PhysX이며, teacher checkpoint는 F035000/S010000이다.",
        "",
        "## 실행 요약",
        "",
        f"| 항목 | 관측값 |\n|---|---:|\n| profile | `{top['profile']}` |\n| 학습 update / transitions | {top['updates']} / {top['transitions']} |\n| update 기록 wall time | {train['wall_s']:.3f} s |\n| initial / post-update native episode | 각 1회, 각 3928 physics steps (16.3667 s) |\n| joint events / success / accepted crossings | 42 / 0 / 0 |\n| teacher checkpoints | F035000 / S010000, 각각 862회 실제 추론 |\n| production reward 인증 | 아니오 |",
        "",
        "두 native episode는 같은 song horizon까지 완료했다. 이는 작은 deadline pilot 측정이며, full reward v4 certification이나 연주·안정성 성공 판정이 아니다.",
        "",
        "## Native Isaac Gym 렌더 프레임",
        "",
        "아래는 저장된 native camera capture의 첫 프레임과 마지막 프레임이다. 렌더 이미지이며 데이터 그래프와 구분한다.",
        "",
    ]
    for condition, _, _, first_img, last_img, _ in rows:
        lines += [f"### {condition.replace('_', ' ')}", "", f"첫 프레임 — [원본 PNG]({first_img})", "", f"![{condition} 첫 native Isaac Gym 프레임]({first_img})", "", f"마지막 프레임 — [원본 PNG]({last_img})", "", f"![{condition} 마지막 native Isaac Gym 프레임]({last_img})", ""]
    lines += [
        "## 실제 episode 영상",
        "",
        "각 환경 녹화는 30 fps, 492 frames, 16.4초 MP4이다. native report의 물리 경과는 16.3667초다.",
        "",
    ]
    for condition, _, _, _, _, local in rows:
        media = Path("/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1") / local / "media"
        lines += [f"### {condition.replace('_', ' ')} — 전신", "", f"![{condition} whole body]({(media / 'whole_body.mp4').as_posix()})", "", f"[전신 MP4 원본]({(media / 'whole_body.mp4').as_posix()})", "", f"### {condition.replace('_', ' ')} — 손 확대", "", f"![{condition} hands]({(media / 'hands.mp4').as_posix()})", "", f"[손 확대 MP4 원본]({(media / 'hands.mp4').as_posix()})", ""]
    lines += [
        "## 실제 측정 위치 궤적",
        "",
        "이 그림은 Isaac 렌더가 아니라 native `trace.json`의 `position_W_m` 데이터 그래프다. 좌표는 기타 actor-root의 W 프레임 위치(m), 시간은 `physics_step / 240`초다. 파선 상자는 brief의 actor-root 범위 X=[−0.50, −0.15], Y=[−0.15, 0.15], Z=[0.65, 0.883738] m를 표시한다. 검은 별은 기존 nominal reference pW=(−0.230415, 0.086712, 0.700973) m다. Z 상한은 initial human body-state slot 11의 측정 Z=0.8837384 m에 대응한다. 상자는 관측 범위 시각화이며 성공 판정이 아니다.",
        "",
        "![두 조건 native actor-root 위치 궤적](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/position_paths_3d.png)",
        "",
        "## 요약 비교",
        "",
        "| 조건 | physics steps | physics 시간 | return | fixed events | joint success | accepted crossings | 완료 |\n|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for condition, report, _, _, _, _ in rows:
        lines.append(f"| {condition.replace('_', ' ')} | {report['physics_steps']} | {report['physics_seconds']:.4f} s | {report['return']:.6f} | {report['settled_events']} | {report['joint_success_events']} | {report['accepted_crossings']} | full horizon |")
    lines += [
        "",
        "두 조건 모두 42 events에서 성공 0회, accepted crossing 0회다. 이 결과는 보상 인증 또는 음악적 성공으로 해석하지 않는다.",
        "",
        "## 원자료",
        "",
        "각 condition의 `report.json`, `trace.json`, `controls.json`, `joint_events.json`, `initial_values.json`, `media/capture.json`, `media/videos.json`을 기준으로 표와 그림을 만들었다. 입력 해시 전후 비교는 `input_hashes.json`에 남겼다.",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    frozen = {str(path): sha256(path) for path in inputs()}
    (OUT / "input_hashes.json").write_text(json.dumps({"before": frozen}, indent=2) + "\n")
    plot_positions()
    build_readme()
    after = {str(path): sha256(path) for path in inputs()}
    unchanged = frozen == after
    hash_record = {"before": frozen, "after": after, "inputs_unchanged": unchanged,
                   "producer_sha256": sha256(Path(__file__).resolve())}
    (OUT / "input_hashes.json").write_text(json.dumps(hash_record, indent=2) + "\n")
    if not unchanged:
        raise SystemExit("Input SHA mismatch after artifact generation")


if __name__ == "__main__":
    main()
