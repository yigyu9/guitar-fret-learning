#!/usr/bin/env python3
"""Version 2 layout: readable condition labels and a single, separated plot legend."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig_preload_artifact_v1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
RESULTS = BASE.parent
FOUNDATION = RESULTS / "environment_foundation_v1"
ANALYSIS = BASE / "preload_analysis_v2.json"
FONT_PATH = Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
OUT_COMPARISON = BASE / "preload_comparison_v2.png"
OUT_CURVES = BASE / "preload_curves_v2.png"
OUT_NOTE = BASE / "preload_artifact_note_v2.md"
OUT_MANIFEST = BASE / "preload_artifact_manifest_v2.json"
FRAME_IDS = (0, 60, 150)
TIMES = (0.0, 2.0, 5.0)
COLORS = {"neutral0": "#2457a7", "preload050": "#d66a18", "preload100": "#16804a"}

CONDITIONS = (
    {
        "key": "neutral0", "label": "기준 중립 (preload 0)",
        "run": FOUNDATION / "native_neutral_v2", "series": "neutral0",
        "position_key": "guitar_position_W_m", "quaternion_key": "guitar_quaternion_xyzw",
        "log": FOUNDATION / "native_neutral_v2.log",
    },
    {
        "key": "preload050", "label": "preload 0.5", "run": BASE / "preload050_v2", "series": "preload050",
        "position_key": "position_W_m", "quaternion_key": "quaternion_xyzw",
        "log": BASE / "preload050_v2.log",
    },
    {
        "key": "preload100", "label": "preload 1.0 · 선택", "run": BASE / "preload100_v2", "series": "preload100",
        "position_key": "position_W_m", "quaternion_key": "quaternion_xyzw",
        "log": BASE / "preload100_v2.log",
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text())


def source_paths() -> list[Path]:
    paths = [ANALYSIS, BASE / "analyze_preload_v2.py"]
    for condition in CONDITIONS:
        run = condition["run"]
        paths.extend((run / "report.json", run / "initial_values.json", run / "trace.json",
                      run / "media/capture.json", condition["log"]))
        for frame_id in FRAME_IDS:
            paths.append(run / "media/frames/whole_body" / f"{frame_id:05d}.png")
    return paths


def quat_normalized(q: list[float]) -> tuple[float, float, float, float]:
    n = math.sqrt(sum(float(v) * float(v) for v in q))
    assert n > 0
    return tuple(float(v) / n for v in q)


def derive_curves(rows: list[dict], position_key: str, quaternion_key: str):
    first_position = rows[0][position_key]
    first_quaternion = quat_normalized(rows[0][quaternion_key])
    times, displacement_mm, rotation_deg = [], [], []
    for row in rows:
        step = int(row["physics_step"])
        times.append(step / 240.0)
        p = row[position_key]
        displacement_mm.append(1000.0 * math.sqrt(sum((float(p[i]) - float(first_position[i])) ** 2 for i in range(3))))
        q = quat_normalized(row[quaternion_key])
        dot = abs(sum(first_quaternion[i] * q[i] for i in range(4)))
        rotation_deg.append(math.degrees(2.0 * math.acos(max(-1.0, min(1.0, dot)))))
    return times, displacement_mm, rotation_deg


def check_source_data(analysis: dict):
    assert analysis["inputs_unchanged"] is True
    assert analysis["same_initial_native_state"] is True
    assert analysis["selected_condition"] == "preload100"
    assert float(analysis["selected_factor"]) == 1.0
    assert analysis["stability_success"] is False and analysis["training_ready"] is False

    calculated = {}
    captures = {}
    traces = {}
    for condition in CONDITIONS:
        run = condition["run"]
        report = load_json(run / "report.json")
        trace = load_json(run / "trace.json")
        capture = load_json(run / "media/capture.json")
        initial = load_json(run / "initial_values.json")
        assert report["completed"] is True and report["failure"] is None
        assert int(report["physics_steps"]) == 1200
        assert int(report["control_steps"]) == 300
        assert report["training_ready"] is False
        if "training_updates" in report:
            assert int(report["training_updates"]) == 0
        assert len(trace) == 301
        assert capture["renderer"] == "Isaac Gym native camera"
        assert int(capture["fps"]) == 30 and len(capture["frames"]) == 151
        assert initial.get("strap_enabled") is False or initial.get("strap_force_enabled") is False

        # Verify the relevant input digests already recorded by the frozen analysis.
        digest_map = analysis["input_sha256"]
        for source in (run / "trace.json", run / "report.json", run / "initial_values.json"):
            assert digest_map[str(source)] == sha256(source), f"analysis/source SHA mismatch: {source}"

        for frame_id, expected_step, expected_time in zip(FRAME_IDS, (0, 480, 1200), TIMES):
            metadata = capture["frames"][frame_id]
            assert int(metadata["physics_step"]) == expected_step
            assert float(metadata["time_s"]) == expected_time
            image_path = run / "media/frames/whole_body" / f"{frame_id:05d}.png"
            expected_sha = metadata["image_sha256"][str(image_path.resolve())]
            assert sha256(image_path) == expected_sha, f"captured frame SHA mismatch: {image_path}"

        times, disp, rot = derive_curves(trace, condition["position_key"], condition["quaternion_key"])
        assert len(times) == 301 and abs(times[-1] - 5.0) < 1e-12
        result = analysis["conditions"][condition["series"]]
        checks = (
            (max(disp), result["guitar_max_displacement_from_initial_mm"], 1e-7),
            (disp[-1], result["guitar_final_displacement_from_initial_mm"], 1e-7),
            (max(rot), result["guitar_max_rotation_from_initial_deg"], 1e-7),
            (rot[-1], result["guitar_final_rotation_from_initial_deg"], 1e-7),
        )
        for observed, expected, tolerance in checks:
            assert abs(observed - float(expected)) <= tolerance, (observed, expected)
        calculated[condition["key"]] = {
            "times_s": times, "displacement_mm": disp, "rotation_deg": rot,
            "metrics": result,
        }
        captures[condition["key"]] = capture
        traces[condition["key"]] = trace
    return calculated, captures, traces


def draw_montage(captures: dict) -> tuple[int, int]:
    font_title = ImageFont.truetype(str(FONT_PATH), 30)
    font_sub = ImageFont.truetype(str(FONT_PATH), 19)
    font_row = ImageFont.truetype(str(FONT_PATH), 21)
    font_col = ImageFont.truetype(str(FONT_PATH), 19)
    font_cap = ImageFont.truetype(str(FONT_PATH), 16)
    tile_w, tile_h = 500, 281
    left, gap = 335, 16
    top, row_gap = 177, 34
    row_h = tile_h + 43
    width = left + 3 * tile_w + 2 * gap + 35
    height = top + 3 * row_h + 2 * row_gap + 33
    canvas = Image.new("RGB", (width, height), "#f4f6f8")
    draw = ImageDraw.Draw(canvas)
    draw.text((28, 19), "상체 preload 조건별 native 기타 자세", font=font_title, fill="#172b4d")
    draw.text((30, 62), "Isaac Gym native camera · CPU PhysX · Vulkan software graphics · strap OFF · root/하체 fixed · 기타 자유",
              font=font_sub, fill="#44546a")
    draw.rounded_rectangle((28, 103, width - 28, 150), radius=8, fill="#e8f5e9", outline="#16804a", width=2)
    draw.text((43, 114), "진단 선택 preload=1.0 · 세 조건 동일 초기 상태 · 물리 5초 · 안정성/음악 인증 아님",
              font=font_sub, fill="#1b4332")

    for col, (frame_id, time_s, step) in enumerate(zip(FRAME_IDS, TIMES, (0, 480, 1200))):
        x = left + col * (tile_w + gap)
        draw.text((x, top - 31), f"t={time_s:.1f}초 · frame {frame_id:05d} · physics step {step}",
                  font=font_col, fill="#172b4d")

    for row, condition in enumerate(CONDITIONS):
        y = top + row * (row_h + row_gap)
        result = load_json(ANALYSIS)["conditions"][condition["series"]]
        draw.rounded_rectangle((24, y + 75, left - 20, y + 200), radius=12,
                               fill=("#e7effb" if row == 0 else ("#fff0df" if row == 1 else "#e3f4e9")),
                               outline="#8795a8", width=2)
        draw.text((42, y + 91), condition["label"], font=font_row, fill="#172b4d")
        draw.text((42, y + 130), f"최대 이동 {result['guitar_max_displacement_from_initial_mm']:.3f} mm",
                  font=font_cap, fill="#344563")
        draw.text((42, y + 158), f"최대 회전 {result['guitar_max_rotation_from_initial_deg']:.3f}°",
                  font=font_cap, fill="#344563")
        capture = captures[condition["key"]]
        for col, frame_id in enumerate(FRAME_IDS):
            x = left + col * (tile_w + gap)
            image_path = condition["run"] / "media/frames/whole_body" / f"{frame_id:05d}.png"
            frame = Image.open(image_path).convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
            canvas.paste(frame, (x, y))
            draw.rectangle((x, y, x + tile_w - 1, y + tile_h - 1), outline="#8492a6", width=2)
            draw.text((x + 4, y + tile_h + 6), f"{condition['label']} · t={TIMES[col]:.1f}초",
                      font=font_cap, fill="#344563")

    canvas.save(OUT_COMPARISON, format="PNG", optimize=True)
    return canvas.size


def draw_curves(curves: dict) -> tuple[int, int]:
    korean = FontProperties(fname=str(FONT_PATH))
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=150)
    fig.suptitle("저장 native trace: 기타 초기값 대비 이동", fontproperties=korean, fontsize=19, y=0.98, color="#172b4d")
    fig.text(0.5, 0.925, "301개 60 Hz 표본 · 5.000초 · 왼쪽은 위치 이동, 오른쪽은 quaternion geodesic 회전",
             ha="center", fontproperties=korean, fontsize=11, color="#44546a")
    for key, label in (("neutral0", "중립 (preload 0)"), ("preload050", "preload 0.5"), ("preload100", "preload 1.0 · 선택")):
        series = curves[key]
        axes[0].plot(series["times_s"], series["displacement_mm"], color=COLORS[key], linewidth=2.4, label=label)
        axes[1].plot(series["times_s"], series["rotation_deg"], color=COLORS[key], linewidth=2.4, label=label)
    axes[0].set_title("위치 변위", fontproperties=korean, fontsize=15)
    axes[0].set_ylabel("초기 위치 대비 이동 (mm)", fontproperties=korean)
    axes[1].set_title("회전 변화", fontproperties=korean, fontsize=15)
    axes[1].set_ylabel("초기 quaternion 대비 geodesic 회전 (°)", fontproperties=korean)
    for ax in axes:
        ax.set_xlabel("물리 시간 (초)", fontproperties=korean)
        ax.set_xlim(0.0, 5.0)
        ax.grid(True, color="#d9e0e8", linewidth=0.8)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(korean)
        ax.tick_params(colors="#44546a")
        for spine in ax.spines.values():
            spine.set_color("#aab4c0")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.065), ncol=3,
               frameon=False, prop=korean, fontsize=12)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.18, top=0.82, wspace=0.25)
    fig.savefig(OUT_CURVES, dpi=150, facecolor="white")
    size = (round(fig.get_figwidth() * fig.dpi), round(fig.get_figheight() * fig.dpi))
    plt.close(fig)
    return size


def write_note(analysis: dict, sizes: dict) -> None:
    rows = []
    for c in CONDITIONS:
        m = analysis["conditions"][c["series"]]
        rows.append(
            f"| {c['label']} | {m['guitar_max_displacement_from_initial_mm']:.3f} | "
            f"{m['guitar_final_displacement_from_initial_mm']:.3f} | "
            f"{m['guitar_max_rotation_from_initial_deg']:.3f} | {m['guitar_final_rotation_from_initial_deg']:.3f} | "
            f"{m['position_box_max_outside_norm_mm']:.3f} | {m['position_box_outside_samples']}/{m['samples']} |"
        )
    note = f"""# Native preload 비교 결과

![세 조건 native whole-body frame 비교]({OUT_COMPARISON})

![60 Hz trace의 위치 변위와 회전 변화]({OUT_CURVES})

세 조건은 같은 초기 native 상태를 사용합니다. 중립 조건은 기존 neutral 저장 run을 재사용했고, `preload=0.5`와 `preload=1.0`은 각각 별도 5초 run입니다. 모든 run은 60 Hz control/trace, 240 Hz 물리, 1200 physics step을 기록했습니다. 그림의 실제 Isaac Gym native camera 프레임은 **frame 00000/step 0/t=0.0초, frame 00060/step 480/t=2.0초, frame 00150/step 1200/t=5.0초**이며 캡처 metadata의 PNG SHA-256과 대조했습니다. 영상은 30 fps로 저장되어 있지만, 표와 곡선의 시간축은 물리 시각입니다.

## 비교값

위치 변위는 기타 actor 위치의 초기값 대비 유클리드 거리(mm), 회전 변화는 초기 quaternion 대비 shortest-path geodesic 각도(deg)입니다. 위치 상자 초과값은 분석기가 보고한 **core actor-root position-box max outside norm (mm)**이고, 회전 허용 영역의 포함 판정은 이 수치에 포함되지 않습니다.

| 조건 | 최대 위치 변위 (mm) | 최종 위치 변위 (mm) | 최대 geodesic 회전 (°) | 최종 geodesic 회전 (°) | core position-box 최대 초과 (mm) | position-box 초과 표본 |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

진단 선택 조건은 `preload=1.0`입니다. 세 비교 중 core actor-root 위치 상자 초과가 0.000 mm였고, 초기 대비 기타 이동과 회전도 중립 기준보다 작았습니다. 이는 이 초기화에서 drift가 개선됐다는 뜻입니다. 최대 위치 변위 46.306 mm와 회전 변화 9.179°가 남아 있으며, 원 분석의 `stability_success=false`·`training_ready=false`를 바꾸지 않습니다. SO(3) 허용 영역 전체, 지지 접촉 인증, 음악 detector/이벤트, 두 음악 checkpoint 연결이나 연주 성능의 인증이 아닙니다.

## 실행 범위와 상태

입력 run은 Isaac Gym native camera, CPU PhysX, Vulkan software graphics, strap OFF, root/하체 fixed, 자유 기타 조건입니다. 새 preload 두 run은 각각 5.0 물리 초를 완료했고, 이 후처리에서 새 물리 실행·정책 추론·학습은 하지 않았습니다. 새 run 보고서의 `dual_checkpoints_connected=false`, `training_updates=0` 상태를 유지합니다.

## 원자료 및 실행물

- [preload 분석 JSON]({ANALYSIS})
- [기준 neutral trace]({CONDITIONS[0]['run'] / 'trace.json'})
- [preload 0.5 trace/report]({CONDITIONS[1]['run'] / 'trace.json'}), [report]({CONDITIONS[1]['run'] / 'report.json'})
- [preload 1.0 trace/report]({CONDITIONS[2]['run'] / 'trace.json'}), [report]({CONDITIONS[2]['run'] / 'report.json'})
- [기준 whole-body 영상]({CONDITIONS[0]['run'] / 'media/whole_body.mp4'})
- [preload 0.5 whole-body 영상]({CONDITIONS[1]['run'] / 'media/whole_body.mp4'})
- [preload 1.0 whole-body 영상]({CONDITIONS[2]['run'] / 'media/whole_body.mp4'})

그림 픽셀 크기: 비교 몽타주 {sizes['comparison'][0]}×{sizes['comparison'][1]}, 곡선 {sizes['curves'][0]}×{sizes['curves'][1]}.
"""
    OUT_NOTE.write_text(note, encoding="utf-8")


def main() -> None:
    analysis = load_json(ANALYSIS)
    source_files = source_paths()
    source_sha_before = {str(path): sha256(path) for path in source_files}
    curves, captures, _ = check_source_data(analysis)
    sizes = {
        "comparison": draw_montage(captures),
        "curves": draw_curves(curves),
    }
    write_note(analysis, sizes)
    source_sha_after = {str(path): sha256(path) for path in source_files}
    assert source_sha_before == source_sha_after, "a consumed source input changed during rendering"
    generator = Path(__file__).resolve()
    generator_sha = sha256(generator)
    outputs = (OUT_NOTE, OUT_COMPARISON, OUT_CURVES)
    manifest = {
        "artifact": "dual_music_runtime_v1 preload comparison post-processing",
        "producer": str(generator),
        "producer_sha256_before": generator_sha,
        "producer_sha256_after": sha256(generator),
        "inputs_sha256_before": source_sha_before,
        "inputs_sha256_after": source_sha_after,
        "all_source_sha256_unchanged": source_sha_before == source_sha_after,
        "analysis_source_input_hashes_verified": True,
        "capture_png_hashes_verified": True,
        "curve_samples_per_condition": 301,
        "render_frames": {"indices": list(FRAME_IDS), "physics_steps": [0, 480, 1200], "simulation_times_s": list(TIMES)},
        "outputs_sha256": {str(path): sha256(path) for path in outputs},
        "image_sizes_px": sizes,
        "scope": "read-only rendering; no physics simulation, inference, checkpoint load, or training",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sizes": sizes, "outputs_sha256": manifest["outputs_sha256"],
                      "manifest": str(OUT_MANIFEST), "manifest_sha256": sha256(OUT_MANIFEST)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
