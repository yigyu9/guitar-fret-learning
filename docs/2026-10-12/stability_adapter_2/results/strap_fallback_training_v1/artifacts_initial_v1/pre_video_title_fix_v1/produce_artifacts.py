#!/usr/bin/env python3
"""Create comparison videos, raw-camera contact sheet, and measured trace plots."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
CONDITIONS = ("smoke_off_v1", "smoke_on_v1")
CAMERA_VIEWS = ("whole_body", "hands")
TIMES = (0.0, 2.0, 5.0, None)
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ep_path(condition: str) -> Path:
    return BASE / condition / "evaluations/initial_000000/native/episode_0001"


def selected_raw_frames() -> dict[str, list[tuple[float, Path, str]]]:
    selected = {}
    for condition in CONDITIONS:
        capture = load(ep_path(condition) / "media/capture.json")
        frames = capture["frames"]
        chosen = []
        for target in TIMES[:3]:
            match = min(frames, key=lambda frame: abs(frame["time_s"] - target))
            if abs(match["time_s"] - target) > 1e-6:
                raise ValueError(f"No exact native capture at requested {target}s")
            chosen.append((target, match))
        chosen.append((frames[-1]["time_s"], frames[-1]))
        selected[condition] = []
        for time_s, frame in chosen:
            for view in CAMERA_VIEWS:
                source = next(Path(p) for p in frame["raw_image_sha256"] if f"/{view}/" in p)
                expected = frame["raw_image_sha256"][str(source)]
                if not source.is_file() or sha256(source) != expected:
                    raise ValueError(f"Raw capture SHA mismatch: {source}")
                selected[condition].append((time_s, source, expected))
    return selected


def input_paths() -> list[Path]:
    paths = [BASE / "initial_comparison_v1.json", BASE / "initial_policy_ON_OFF_equivalence_v1.json"]
    for condition in CONDITIONS:
        ep = ep_path(condition)
        paths += [
            ep / "controls.json", ep / "trace.json", ep / "initial_values.json",
            ep / "media/capture.json", ep / "media/whole_body.mp4", ep / "media/hands.mp4",
        ]
    for entries in selected_raw_frames().values():
        paths.extend(path for _, path, _ in entries)
    return sorted(set(paths))


def render_video_pair(view: str):
    off = ep_path(CONDITIONS[0]) / f"media/{view}.mp4"
    on = ep_path(CONDITIONS[1]) / f"media/{view}.mp4"
    output = OUT / f"comparison_{view}.mp4"
    font = FONT_PATH.replace(":", "\\:")
    filter_graph = (
        f"[0:v]drawtext=fontfile='{font}':text='STRAP OFF':x=24:y=18:fontsize=32:fontcolor=white:box=1:boxcolor=0x17365D@0.85[a];"
        f"[1:v]drawtext=fontfile='{font}':text='STRAP ON':x=24:y=18:fontsize=32:fontcolor=white:box=1:boxcolor=0x9A3D20@0.85[b];"
        "[a][b]hstack=inputs=2[outv]"
    )
    command = [
        "ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(off), "-i", str(on),
        "-filter_complex", filter_graph, "-map", "[outv]", "-an", "-vsync", "0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        str(output),
    ]
    subprocess.run(command, check=True)
    return command, output


def render_contact_sheet(frames):
    width, height, header = 480, 270, 54
    outer = 24
    title_h = 76
    rows = [(CONDITIONS[0], "whole_body"), (CONDITIONS[1], "whole_body"),
            (CONDITIONS[0], "hands"), (CONDITIONS[1], "hands")]
    sheet = Image.new("RGB", (outer * 2 + width * 4, title_h + outer + (height + header) * 4 + outer), "#f4f5f7")
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(FONT_PATH, 32)
    label_font = ImageFont.truetype(FONT_PATH, 22)
    small_font = ImageFont.truetype(FONT_PATH, 19)
    draw.text((outer, 18), "초기 native Isaac Gym 카메라 원본 프레임 비교", font=title_font, fill="#17202a")
    display_times = [0.0, 2.0, 5.0, None]
    for col, t in enumerate(display_times):
        txt = "마지막 · 16.3667 s" if t is None else f"t = {t:g} s"
        draw.text((outer + col * width + 8, title_h - 5), txt, font=label_font, fill="#34495e")
    for row, (condition, view) in enumerate(rows):
        y0 = title_h + outer + row * (height + header)
        cond_label = "스트랩 OFF" if condition == CONDITIONS[0] else "스트랩 ON"
        view_label = "전신 카메라" if view == "whole_body" else "손 확대 카메라"
        draw.text((outer, y0 + 10), f"{cond_label} · {view_label}", font=label_font, fill="#17202a")
        entries = frames[condition]
        view_entries = [entry for entry in entries if f"/{view}/" in str(entry[1])]
        for col, (time_s, path, _) in enumerate(view_entries):
            img = Image.open(path).convert("RGB")
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (width, height), "#ffffff")
            cell.paste(img, ((width - img.width) // 2, (height - img.height) // 2))
            x = outer + col * width
            y = y0 + header
            sheet.paste(cell, (x, y))
            draw.rectangle((x, y, x + width - 1, y + height - 1), outline="#bdc3c7", width=1)
    output = OUT / "native_raw_contact_sheet.png"
    sheet.save(output, optimize=True)
    return output


def finite_vector(values, label):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or not np.isfinite(arr).all():
        raise ValueError(f"Empty or nonfinite values in {label}")
    return arr


def measured_series():
    result = {}
    for condition in CONDITIONS:
        ep = ep_path(condition)
        controls = load(ep / "controls.json")
        trace = load(ep / "trace.json")
        if not controls or not trace:
            raise ValueError(f"Empty measurements for {condition}")
        ctime = np.asarray([r["physics_step"] / 240.0 for r in controls])
        pout = finite_vector([r["position_outside_m"] for r in controls], f"{condition} position_outside_m")
        pout_norm_mm = np.linalg.norm(pout, axis=1) * 1000.0
        tension = finite_vector([r["strap"]["last_applied_tension_n"] for r in controls], f"{condition} last_applied_tension_n")
        if len(ctime) != len(pout_norm_mm) or len(ctime) != len(tension):
            raise ValueError(f"Mismatched 60Hz control samples for {condition}")

        q0 = finite_vector(trace[0]["quaternion_xyzw"], f"{condition} initial quaternion")
        q0 /= np.linalg.norm(q0)
        t30, angle30 = [], []
        for r in trace:
            if r["physics_step"] % 8 != 0:
                continue
            q = finite_vector(r["quaternion_xyzw"], f"{condition} trace quaternion")
            q /= np.linalg.norm(q)
            dot = min(1.0, max(-1.0, abs(float(np.dot(q, q0)))))
            t30.append(r["physics_step"] / 240.0)
            angle30.append(math.degrees(2.0 * math.acos(dot)))
        t30 = finite_vector(t30, f"{condition} 30Hz timestamps")
        angle30 = finite_vector(angle30, f"{condition} exact orientation angle")
        if len(angle30) != 492:
            raise ValueError(f"Expected 492 30Hz native samples for {condition}, got {len(angle30)}")
        result[condition] = {"time60": finite_vector(ctime, "60Hz time"),
                             "outside_mm": finite_vector(pout_norm_mm, "position outside norm mm"),
                             "tension_n": tension, "time30": t30, "rotation_deg": angle30,
                             "controls": controls, "trace": trace}
    return result


def plot_measurements(series):
    colors = {CONDITIONS[0]: "#2b6cb0", CONDITIONS[1]: "#c05621"}
    names = {CONDITIONS[0]: "STRAP OFF", CONDITIONS[1]: "STRAP ON"}
    fig, axes = plt.subplots(3, 1, figsize=(12.4, 10.0), sharex=True, constrained_layout=True)
    for condition in CONDITIONS:
        s = series[condition]
        axes[0].plot(s["time60"], s["outside_mm"], color=colors[condition], lw=1.25, label=names[condition])
        axes[1].plot(s["time30"], s["rotation_deg"], color=colors[condition], lw=1.45, label=names[condition])
        axes[2].plot(s["time60"], s["tension_n"], color=colors[condition], lw=1.25, label=names[condition])
    axes[0].set_ylabel("position_outside_norm (mm)")
    axes[0].set_title("Control source vector norm: sqrt(x²+y²+z²) from position_outside_m × 1000")
    axes[1].set_ylabel("Exact angle from initial (deg)")
    axes[1].set_title("Shortest-arc SO(3) angle from trace quaternion_xyzw; every 8 physics steps = 30 Hz")
    axes[2].set_ylabel("last_applied_tension (N)")
    axes[2].set_title("60 Hz pre-integration cable command; commanded tension, not sensor force")
    axes[2].set_xlabel("Native episode time (physics_step / 240 s)")
    for ax in axes:
        ax.grid(True, alpha=.25)
        ax.legend(loc="upper right")
        ax.set_xlim(0.0, max(float(series[c]["time60"][-1]) for c in CONDITIONS))
    for ax, key in zip(axes, ("outside_mm", "rotation_deg", "tension_n")):
        values = np.concatenate([series[c][key] for c in CONDITIONS])
        low, high = float(values.min()), float(values.max())
        pad = max((high - low) * .04, abs(high) * .04, 0.2)
        ax.set_ylim(min(0.0, low - pad), high + pad)
    output = OUT / "measured_control_and_rotation_traces.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def build_readme(comparison, equivalence, series, video_records, contact_path, plot_path, frame_selection):
    off = comparison["conditions"]["off"]
    on = comparison["conditions"]["on"]
    frame_captions = []
    for condition in CONDITIONS:
        condition_label = "OFF" if condition == CONDITIONS[0] else "ON"
        items = [f"`{time_s:.4f}s`: {path.name} (SHA-256 `{digest}`)" for time_s, path, digest in frame_selection[condition]]
        frame_captions.append(f"- {condition_label}: " + "; ".join(items))
    lines = [
        "# 스트랩 OFF/ON 초기 정책 비교 산출물", "",
        "두 조건은 초기 정책 checkpoint 상태다. 기록된 입력 대조에서 ON/OFF의 초기 모델과 RMS는 모든 key가 exact 일치하고, 양쪽 Adam 상태는 비었으며 update/transitions는 모두 0이다. 초기 native 상태도 exact 일치했다. 아래 결과는 스트랩 fallback OFF에서 ON으로 바꾼 비교 관측이다.", "",
        "## 비교 영상", "",
        "각 쌍은 같은 시각의 원본 whole_body/hands MP4 492 frames를 그대로 입력해 좌우 분할(hstack)로 다시 인코딩했다. 프레임을 잘라내거나 늘리지 않았다. 왼쪽은 OFF, 오른쪽은 ON이며 영상 길이는 16.4초(30 fps)다.", "",
        "### 전신 카메라", "",
        f"![전신 카메라 OFF 왼쪽, ON 오른쪽]({(OUT / 'comparison_whole_body.mp4').as_posix()})", "",
        f"[전신 좌우 비교 MP4]({(OUT / 'comparison_whole_body.mp4').as_posix()})", "",
        "### 손 확대 카메라", "",
        f"![손 확대 카메라 OFF 왼쪽, ON 오른쪽]({(OUT / 'comparison_hands.mp4').as_posix()})", "",
        f"[손 확대 좌우 비교 MP4]({(OUT / 'comparison_hands.mp4').as_posix()})", "",
        "## 실제 native Isaac Gym 원본 프레임", "",
        "Contact sheet는 `media/raw/frames`에 저장된 native 카메라 원본 픽셀을 사용했다. 각 행의 시각은 같은 capture metadata의 프레임을 짝지었다. 프레임 자체에는 경로나 글자를 합성하지 않았고, 시트 바깥의 한국어 캡션만 추가했다.", "",
        f"![OFF/ON 전신 및 손 확대의 t0, 2초, 5초, 마지막 native 원본 프레임]({(OUT / contact_path.name).as_posix()})", "",
        "원본 프레임과 SHA-256:", *frame_captions, "",
        "## 실제 측정 시계열", "",
        "아래 그래프는 native 수치 기록이며 렌더 이미지 분석이 아니다. 상단은 `controls.json`의 `position_outside_m` 3성분 벡터를 각 제어 시점마다 유클리드 norm 후 mm로 환산했다. 가운데는 `trace.json`의 `quaternion_xyzw`를 t=0 quaternion과 비교한 shortest-arc 각도 `2 acos(|q·q0|)`이며 30 Hz(physics_step 간격 8)만 표시한다. 하단은 `controls.json`의 `strap.last_applied_tension_n` 60 Hz 값이다. 모든 점을 finite/비어있지 않음으로 확인하고 원자료 관측 범위를 축에 포함했다.", "",
        f"![60Hz 범위이탈·30Hz 초기 대비 정확 회전·60Hz 적용 명령 장력]({(OUT / plot_path.name).as_posix()})", "",
        "## 결과 비교", "",
        "| 측정 항목 | 스트랩 OFF | 스트랩 ON |", "|---|---:|---:|",
        f"| 최대 초기 translation | {off['max_initial_translation_m']:.6f} m | {on['max_initial_translation_m']:.6f} m |",
        f"| 최대 초기 회전 | {off['max_initial_rotation_deg']:.5f}° | {on['max_initial_rotation_deg']:.5f}° |",
        f"| actor-root 범위 이탈 | {off['position_outside_percent']:.5f}% | {on['position_outside_percent']:.5f}% |",
        f"| 연속 범위 밖 최장 시간 | {off['longest_position_outside_s']:.2f} s | {on['longest_position_outside_s']:.2f} s |",
        f"| 최대 position outside norm | {off['max_position_outside_norm_m']:.6f} m | {on['max_position_outside_norm_m']:.6f} m |",
        f"| 양수 last-applied 장력 endpoint 비율 | {off['last_applied_tension_positive_percent_control_endpoints']:.5f}% | {on['last_applied_tension_positive_percent_control_endpoints']:.5f}% |",
        f"| 최대 last-applied 장력 endpoint 명령 | {off['last_applied_tension_max_n_control_endpoints']:.6f} N | {on['last_applied_tension_max_n_control_endpoints']:.6f} N |",
        f"| strap rest length / 초기 slack | {off['strap_rest_length_m']:.9f} m / {off['initial_slack_m']*1000:.6f} mm | {on['strap_rest_length_m']:.9f} m / {on['initial_slack_m']*1000:.6f} mm |",
        f"| physics/control steps; 경과 | {off['physics_steps']}/{off['control_steps']}; {off['actual_physics_seconds']:.4f} s | {on['physics_steps']}/{on['control_steps']}; {on['actual_physics_seconds']:.4f} s |",
        f"| settled events / joint success / accepted crossings | {off['settled_events']} / {off['joint_success_events']} / {off['accepted_crossings']} | {on['settled_events']} / {on['joint_success_events']} / {on['accepted_crossings']} |",
        "",
        "두 조건 모두 3928 physics steps, 982 control steps, full 16.3667 s episode, 42 events를 완료했으며 joint success 0회와 accepted crossings 0회다. ON에서 최대 초기 translation/회전과 최대 position outside norm은 줄었지만 범위 이탈 비율은 84.01222%에서 84.62322%로 늘고 최장 이탈 시간도 12.55초에서 12.60초로 늘었다. 관측은 strap 낙하 감소와 일치하지만 자연스러운 연주 자세·범위 유지 또는 음악적 성공을 보여주지 않는다.", "",
        "초기 fallback baseline에서 OFF의 strap force calls는 0이며 zero-force submissions도 집계했다. ON의 양수 장력 비율과 최대값은 `last_applied_tension_n`의 60 Hz 제어 endpoint 기록이다. 이는 integration 직전 케이블 명령값이며 센서 측정 힘도, 전체 240 Hz 물리 스텝의 최대 힘도 아니다. 현재 계산 장력과 last-applied 명령은 서로 다른 시점의 값이므로 혼합하지 않았다.", "",
        "### 이미지/overlay/물리량의 출처", "",
        "- `media/raw/frames`: native Isaac Gym 카메라의 raw RGB 프레임. contact sheet가 사용한 원본이다.",
        "- `media/frames`: 카메라 캡처에 strap route 표시와 상태 문구를 덧그린 시각화 프레임이며, depth map이 아니다. 선의 진함/희미함은 화면상 가시성 projection overlay를 나타낼 뿐 접촉/관통 검증이 아니다.",
        "- `controls.json` 및 `trace.json`: 범위 밖 변위, orientation quaternion, last-applied cable command 같은 수치 측정의 근거다. overlay 픽셀에서 이 수치를 추정하지 않았다.",
        "- 제어 장력은 commanded force scalar로 표기했다. 센서 힘으로 부르지 않는다.", "",
        "initial state equivalence 기록은 초기 model+RMS 전체 key exact 동일, Adam empty, update/transitions 0을 표시한다. 별도 smoke run 뒤 병렬 진행 중인 12-update 학습 결과는 이 산출물의 측정치나 확정 결과로 포함하지 않았다.", "",
        "### 입력 무결성", "",
        "실행 전후 producer 및 아래 raw report/JSON/영상/사용 프레임 SHA-256은 [input_hashes.json](input_hashes.json)에 기록했다. 비교 영상은 저장된 원본 MP4를 재인코딩한 산출물이며 native physics 재실행은 하지 않았다.", "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    initial_frames = selected_raw_frames()
    frozen = {str(p): sha256(p) for p in input_paths()}
    (OUT / "input_hashes.json").write_text(json.dumps({"before": frozen}, indent=2) + "\n", encoding="utf-8")
    comp = load(BASE / "initial_comparison_v1.json")
    equiv = load(BASE / "initial_policy_ON_OFF_equivalence_v1.json")
    if not comp["same_initial_native_state_exact"] or not equiv["initial_model_and_RMS_all_keys_exact"]:
        raise ValueError("Approved initial-condition equivalence is not present")
    video_records = {}
    for view in CAMERA_VIEWS:
        command, output = render_video_pair(view)
        video_records[view] = {"command": command, "output": str(output), "sha256": sha256(output)}
    contact = render_contact_sheet(initial_frames)
    series = measured_series()
    plot = plot_measurements(series)
    build_readme(comp, equiv, series, video_records, contact, plot, initial_frames)
    after = {str(p): sha256(p) for p in input_paths()}
    unchanged = frozen == after
    record = {"before": frozen, "after": after, "inputs_unchanged": unchanged,
              "producer_sha256": sha256(Path(__file__).resolve()),
              "generated_comparison_videos": video_records,
              "native_physics_reexecuted": False}
    (OUT / "input_hashes.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if not unchanged:
        raise SystemExit("Raw input SHA mismatch after artifact generation")


if __name__ == "__main__":
    main()
