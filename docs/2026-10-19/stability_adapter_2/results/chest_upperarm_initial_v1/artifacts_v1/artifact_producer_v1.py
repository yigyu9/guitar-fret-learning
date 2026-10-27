from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image

ROOT = Path("/home/ajou/yigyu/3")
BASE = ROOT / "docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1"
ART = BASE / "artifacts_v1"
VIDEO = ROOT / "docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1"
CASES = [
    ("native_hold_v2", "초기 지지 유지 · 무타현"),
    ("native_strike_near_v1", "왼손 근접 준비 · EW6 타현"),
    ("native_strike_left_clear_v1", "왼손 6.02 cm 이격 · 비독립"),
    ("native_strike_left_far_v1", "왼손 10.630 cm 이격 · 왼팔/손 접촉 없음"),
]
VIEWS = ["whole_body", "hands", "chest_arm_close"]
INITIAL_VIEWS = ["initial_native", "initial_support_side", "initial_strings"]
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_read(path: Path):
    return json.loads(path.read_text())


def source_files() -> list[Path]:
    files = [
        BASE / "analysis_v1.json",
        BASE / "analysis_v1_before.json",
        BASE / "metadata_scope_correction_v1.json",
        BASE / "source_path_v1.json",
        BASE / "finger_search_v2/left_clear_head_audit.json",
        BASE / "strike_detector_v1.json",
        BASE / "strike_detector_v2.json",
        BASE / "native_hold_v1/report.json",
        ROOT / "stability_adapter_2/analyze_chest_upperarm_initial_v1.py",
        ROOT / "stability_adapter_2/chest_upperarm_pose_test_v1/README_v2.md",
    ]
    for run, _label in CASES:
        run_dir = BASE / run
        files.extend([
            run_dir / "report.json",
            run_dir / "attempt.json",
            run_dir / "initial_values.json",
            run_dir / "actual_contacts.json",
            run_dir / "media/capture.json",
            run_dir / "media/videos.json",
            *(run_dir / "media" / f"{name}.png" for name in INITIAL_VIEWS),
            *(run_dir / "media" / f"{name}.mp4" for name in VIEWS),
        ])
        for view in VIEWS:
            files.append(run_dir / "media/frames" / view / "00150.png")
    return files


def read_before_pins() -> dict[str, str]:
    data = json_read(ART / "artifact_before_v1.json")
    return {x["path"]: x["sha256"] for x in data["inputs"]}


def make_contact_sheet(rows, out: Path) -> None:
    width, height, gap = 400, 300, 12
    columns = len(rows[0])
    sheet = Image.new("RGB", (columns * width + (columns + 1) * gap,
                               len(rows) * height + (len(rows) + 1) * gap), "white")
    for ri, row in enumerate(rows):
        for ci, path in enumerate(row):
            image = Image.open(path).convert("RGB")
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            x = gap + ci * (width + gap) + (width - image.width) // 2
            y = gap + ri * (height + gap) + (height - image.height) // 2
            sheet.paste(image, (x, y))
    sheet.save(out, format="PNG", optimize=False)


def make_outputs() -> dict:
    pins = read_before_pins()
    changed_before = [path for path, expected in pins.items() if sha(Path(path)) != expected]
    if changed_before:
        raise SystemExit(f"pinned input changed before producer: {changed_before}")

    copy_entries = []
    initial_sheet_rows = []
    final_sheet_rows = []
    run_summaries = {}

    for run, label in CASES:
        run_dir = BASE / run
        report = json_read(run_dir / "report.json")
        capture = json_read(run_dir / "media/capture.json")
        if not report.get("completed") or report.get("physics_steps") != 1200:
            raise SystemExit(f"not a completed 5s native run: {run}")
        if len(capture.get("frames", [])) != 151 or capture.get("fps") != 30:
            raise SystemExit(f"unexpected capture frame metadata: {run}")
        out_frames = ART / "native_frames_v1" / run
        out_frames.mkdir(parents=True, exist_ok=True)
        initial_paths, final_paths = [], []

        for view in INITIAL_VIEWS:
            src = run_dir / "media" / f"{view}.png"
            dst = out_frames / f"{view}.png"
            shutil.copy2(src, dst)
            digest = sha(src)
            if sha(dst) != digest:
                raise SystemExit(f"initial native image copy mismatch: {src}")
            copy_entries.append({"kind": "native_initial_image", "run": run,
                                 "source": str(src), "copy": str(dst), "sha256": digest})
            initial_paths.append(dst)

        final_record = next(x for x in capture["frames"] if x["time_s"] == 5.0)
        for view in VIEWS:
            src = run_dir / "media/frames" / view / "00150.png"
            source_abs = src.resolve()
            expected = final_record["image_sha256"].get(str(source_abs))
            if expected is None or sha(src) != expected:
                raise SystemExit(f"capture frame hash mismatch: {src}")
            dst = out_frames / f"final_{view}.png"
            shutil.copy2(src, dst)
            if sha(dst) != expected:
                raise SystemExit(f"final native image copy mismatch: {src}")
            copy_entries.append({"kind": "native_final_frame", "run": run,
                                 "time_s": 5.0, "physics_step": final_record["physics_step"],
                                 "view": view, "source": str(src), "copy": str(dst),
                                 "sha256": expected, "expected_sha256_from_capture": expected})
            final_paths.append(dst)

        initial_sheet_rows.append(initial_paths)
        final_sheet_rows.append(final_paths)

        video_case = VIDEO / run
        video_case.mkdir(parents=True, exist_ok=True)
        for view in VIEWS:
            src = run_dir / "media" / f"{view}.mp4"
            dst = video_case / f"{view}.mp4"
            shutil.copy2(src, dst)
            expected = report["videos"][view]["sha256"]
            if expected != sha(dst):
                raise SystemExit(f"video copy hash mismatch: {run}/{view}")
            copy_entries.append({"kind": "native_video", "run": run, "view": view,
                                 "source": str(src), "copy": str(dst),
                                 "sha256": expected, "expected_sha256_from_report": expected})

        run_summaries[run] = {
            "label": label,
            "completed": report["completed"],
            "physics_steps": report["physics_steps"],
            "physics_seconds": report["physics_seconds"],
            "guitar_BB_initial_W_m": json_read(BASE / "analysis_v1.json")["cases"][run]["body_BB_centre_initial_W_m"],
        }

    make_contact_sheet(initial_sheet_rows, ART / "initial_three_view_comparison_v1.png")
    make_contact_sheet(final_sheet_rows, ART / "final_three_view_comparison_v1.png")

    analysis = json_read(BASE / "analysis_v1.json")
    rows = []
    for run, label in CASES:
        c = analysis["cases"][run]
        times = c["trajectory"]["time_s"]
        bb = c["trajectory"]["delta_mm"]
        so3 = c["trajectory"]["SO3_deg"]
        if not (len(times) == len(bb) == len(so3) == 1201):
            raise SystemExit(f"unexpected 240Hz analysis series length: {run}")
        rows.extend({"run": run, "label": label, "time_s": t,
                     "guitar_BB_center_displacement_mm": d,
                     "guitar_SO3_rotation_deg": r}
                    for t, d, r in zip(times, bb, so3))
    with (ART / "motion_samples_v1.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
    korean_font = FontProperties(fname=str(FONT_PATH)) if FONT_PATH.exists() else None
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True)
    for (run, label), color in zip(CASES, colors):
        c = analysis["cases"][run]["trajectory"]
        axes[0].plot(c["time_s"], c["delta_mm"], color=color, lw=1.3, label=label)
        axes[1].plot(c["time_s"], c["SO3_deg"], color=color, lw=1.3, label=label)
    title_font = {"fontproperties": korean_font} if korean_font else {}
    axes[0].set_title("기타 body BB 중심 변위", **title_font)
    axes[0].set_ylabel("t=0 대비 거리 (mm)", **title_font)
    axes[1].set_title("기타 자세 변화", **title_font)
    axes[1].set_ylabel("SO(3) 회전거리 (deg)", **title_font)
    for ax in axes:
        ax.set_xlabel("시간 (s)", **title_font)
        ax.set_xlim(0, 5)
        ax.grid(True, alpha=0.25)
        ax.margins(x=0.01, y=0.08)
    leg_kwargs = {"prop": korean_font} if korean_font else {}
    fig.legend(loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.015), **leg_kwargs)
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    fig.savefig(ART / "guitar_BB_motion_SO3_240Hz_v1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    joint_rows = []
    for run, _label in CASES:
        init = json_read(BASE / run / "initial_values.json")
        names, q_ref = init["joint_names"], init["q_ref_rad"]
        qpos = [x["pos"] for x in init["native_initial_state"]["human_dof_states"]]
        if not (len(names) == len(q_ref) == len(qpos) == 81):
            raise SystemExit(f"unexpected initial joint table length: {run}")
        for i, (name, actual, ref) in enumerate(zip(names, qpos, q_ref)):
            joint_rows.append({"run": run, "index0": i, "joint_name": name,
                               "actual_initial_qpos_rad": actual,
                               "actual_initial_qpos_deg": actual * 180.0 / 3.141592653589793,
                               "q_ref_rad": ref, "qpos_minus_q_ref_rad": actual - ref})
    with (ART / "initial_joint_angles_81_v1.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(joint_rows[0]))
        writer.writeheader()
        writer.writerows(joint_rows)

    write_readmes(run_summaries)

    pins_after = {path: sha(Path(path)) for path in pins}
    mismatches = [p for p, h in pins.items() if pins_after[p] != h]
    if mismatches:
        raise SystemExit(f"pinned input changed during producer: {mismatches}")
    producer = ART / "artifact_producer_v1.py"
    producer_sha = sha(producer)
    before = json_read(ART / "artifact_before_v1.json")
    if before["producer"]["sha256"] != producer_sha:
        raise SystemExit("producer source changed after before-pin")

    derived = []
    for name, source_note in [
        ("initial_three_view_comparison_v1.png", "four runs × three native initial camera views; layout-only contact sheet"),
        ("final_three_view_comparison_v1.png", "four runs × three native t=5s camera frames; layout-only contact sheet"),
        ("guitar_BB_motion_SO3_240Hz_v1.png", "analysis_v1.json cases[].trajectory time_s/delta_mm/SO3_deg"),
        ("motion_samples_v1.csv", "analysis_v1.json cases[].trajectory time_s/delta_mm/SO3_deg"),
        ("initial_joint_angles_81_v1.csv", "native_* initial_values.json qpos/ref arrays"),
    ]:
        p = ART / name
        derived.append({"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size, "derived_from": source_note})
    manifest = {
        "schema": "chest_upperarm_initial_v1_artifact_copy_manifest_v1",
        "producer": {"path": str(producer), "sha256_before": producer_sha, "sha256_after": sha(producer)},
        "input_pin_before": before["inputs"],
        "input_pin_after": [{"path": p, "sha256": h} for p, h in pins_after.items()],
        "all_input_pins_unchanged": True,
        "copies": copy_entries,
        "derived_artifacts": derived,
        "all_copy_hashes_verified": True,
        "environment": {"python": sys.version, "matplotlib": matplotlib.__version__},
    }
    (ART / "copy_manifest_v1.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def write_readmes(run_summaries: dict) -> None:
    P = "/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1"
    A = P + "/artifacts_v1"
    video_labels = {
        "native_hold_v2": "기존 지지 · 무타현",
        "native_strike_near_v1": "근접 준비 · 사용자 기본 선택",
        "native_strike_left_clear_v1": "왼손 6.02 cm 이격 · 독립 지지 실패",
        "native_strike_left_far_v1": "왼손/손 10.630 cm 이격 · 접촉 독립 영상",
    }
    readme = f'''# 가슴·오른쪽 위팔 초기 지지 비교

## 결과 범위

4개 실제 native 실행이 각 5초(1,200 physics step) 정상 완료됐다. 기타는 자유 동역학이며 strap·강제 부착·인위적 기타 힘은 없고 humanoid root/하체는 고정, self-collision은 켰다. 오른쪽 위팔의 유한한 제어 지지는 유지했다. 공통 초기 기타 body BB 중심은 W=[0.143238, −0.001125, 0.683019] m이며 actor-root 값은 실행별로 다를 수 있다. 다른 75개 관절 목표는 유지했지만 실제 관절 상태까지 고정한 것은 아니다.

| run | 조건 | LH arm/hand 기타 접촉 | 최대 기타 BB 변위 | 최대 SO(3) |
|---|---|---:|---:|---:|
| `native_hold_v2` | 지지 유지, 무타현 | 804 / 1,200 | 2.759 mm | 0.680° |
| `native_strike_near_v1` | 왼손 근접 준비, EW6 타현 | 1,090 / 1,200 | 4.287 mm | 1.219° |
| `native_strike_left_clear_v1` | 실제 초기 이격 6.02 cm, EW6 | 326 / 1,200 | 4.601 mm | 2.486° |
| `native_strike_left_far_v1` | 목표 이격 G=[0.070, 0.080, 0] m, norm 10.630 cm, EW6 | 0 / 1,200; RH hand 0 / 1,200 | 4.915 mm | 2.833° |

Near는 왼손 넥 준비를 기본으로 보는 사용자 선택안이다. Clear의 왼팔/손 접촉 326회 때문에 독립 지지 증거가 아니다. Far만 5초 동안 LH arm/hand와 RH wrist/hand 모두 기타에 닿지 않았지만 L_Hip 접촉이 있었으므로 전신의 왼쪽 접촉이 전혀 없었다고 말하지 않는다. 홀드 실행은 타현을 하지 않았고 EW6 가상 피크 타현은 나머지 세 실행에서만 동작했다. 6줄 하향 6→1 및 상향 1→6 통과는 선별된 원시 시퀀스 분석 결과이지 학습된 곡 연주 성공이 아니다.

Far의 양의 raw contact lambda 표본 수는 다음과 같다. lambda는 보정된 힘(N)이 아니다.

| 실제 구간 (physics step 기준) | 표본 | Chest | R_Shoulder (오른쪽 위팔) | R_Hip (오른쪽 허벅지) | L_Hip (왼쪽 허벅지) |
|---|---:|---:|---:|---:|---:|
| 0–2.0 s | 480 | 448 | 474 | 477 | 1 |
| 2.0–3.75 s | 420 | 297 | 420 | 420 | 11 |
| 3.75–5.0 s | 300 | 0 | 300 | 300 | 259 |

따라서 상승 타현 3.75–5초에는 Chest 접촉이 끊기지만 오른쪽 위팔·허벅지와 왼쪽 허벅지 접촉은 남는다. 상태 변화는 기타 body BB 중심 변위와 SO(3) 회전으로 [240 Hz 전체 시계열 표](<{A}/motion_samples_v1.csv>) 및 [그래프](<{A}/guitar_BB_motion_SO3_240Hz_v1.png>)에 표시했다.

## 초기 자세와 이미지 비교

오른손 ring/pinky 세 관절의 −0.21/−0.30/−0.18 rad 값은 각각 1x/2/3의 **기존 준비각 대비 보정량**이며 절대 초기각이 아니다. 네 native 시작 상태의 실제 81개 qpos와 q_ref는 [전체 표](<{A}/initial_joint_angles_81_v1.csv>)에 run별로 기록했다. 실제 자세 시점마다 원본 카메라 이미지를 사용했으며, 비교 시트에는 글자나 캡션을 넣지 않았다.

초기 시트는 행 순서가 hold, near, clear, far이고 열은 native overview, support side, string view다. 아래 이미지는 native 카메라 원본을 축소·배치한 비교 시트다.

![4실행의 실제 초기 native 카메라 3-view 비교; 행/열 안내는 본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_three_view_comparison_v1.png)

최종 시트도 같은 행 순서이며 열은 5초 시점 whole body, hands, chest/arm close다. 캡션은 이미지 밖에 두었다.

![4실행의 5초 실제 native 카메라 3-view 비교; 행/열 안내는 본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/final_three_view_comparison_v1.png)

모든 이미지·영상은 Isaac Gym native camera의 실제 캡처이며 줄 endpoint 사이 비물리적 6개 선 표시를 포함한다. 합성 시 원본 이미지는 잘라내거나 덧그리지 않았다. 캡처 원본과 바이트 보존 복사 SHA는 [manifest](<{A}/copy_manifest_v1.json>)에 있다.

## 초기 각도 보정 및 한계

| 오른손 관절 그룹 | 기존 준비각 대비 변경량 |
|---|---:|
| `RH:ring1_x`, `RH:pinky1_x` | 각 −0.21 rad |
| `RH:ring2`, `RH:pinky2` | 각 −0.30 rad |
| `RH:ring3`, `RH:pinky3` | 각 −0.18 rad |

− 값은 flexion 증가가 아니라 기존 준비에서 덜 말리도록 하는 변경이다. source geometry query는 초기 자세와 61개 정적 경로 표본에 대한 proxy이며 0.2 mm 초기 clearance는 PhysX cooked 형상/연속경로 인증이 아니다. Native 실제 접촉 자료는 별도 증거로 집계했고 force N을 제공하지 않는다.

초기 native_hold_v1은 support_side camera key 누락으로 0 physics step에서 실패했으며 완료 실행에 포함하지 않았다 ([원본 report](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_hold_v1/report.json>)). V7 phase detector가 반영된 [preferred analysis](<{P}/analysis_v1.json>)의 down/up 6줄 집계를 사용한다. 오래된 detector 판정은 V7의 실제 상승 종료 3.75 s에 적용하지 않는다. Near가 선호 사용자 준비 영상, Far가 LH arm/hand 접촉 분리 영상이다. 두 경우 모두 passive equilibrium, force closure, 강건성, 학습 음악 성공을 입증하지 않는다.

[scope correction](<{P}/metadata_scope_correction_v1.json>) · [61-sample source path proxy](<{P}/source_path_v1.json>) · [근접 자세 source audit](<{P}/finger_search_v2/left_clear_head_audit.json>) · [preferred test-space 안내(V2)](/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/README_v2.md)

[전체 영상 index](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1/README.md) · [작성 전 input pin](<{A}/artifact_before_v1.json>)
'''
    (ART / "README.md").write_text(readme)

    rows = []
    labels = [video_labels[name] for name, _label in CASES]
    for run, _label in CASES:
        lines = [f"## {video_labels[run]}", ""]
        for view, label in zip(VIEWS, ["전신", "손", "가슴·위팔 확대"]):
            path = VIDEO / run / f"{view}.mp4"
            lines.append(f"### {label}")
            lines.append(f"![{video_labels[run]} — {label}, native 5초 영상]({path})")
            lines.append("")
        rows.extend(lines)
    index = "# 가슴·오른쪽 위팔 초기 자세 비교 영상\n\n"
    index += "4개 영상 묶음은 각 5초, 30 fps, 151 frames의 실제 native Isaac Gym 캡처다. 캡처에는 비물리적 6개 string endpoint 선 표시가 있다. Hold는 정지 관찰, 나머지 세 run만 EW6 가상 피크 타현을 한다.\n\n"
    index += "Near는 사용자가 기본으로 고를 왼손 넥 준비이고, Far는 LH arm/hand 접촉이 없는 구간을 포함하는 분리 영상이다. Far에도 Chest와 오른쪽 위팔·허벅지, 후기 왼쪽 허벅지 접촉은 남는다. 상세 지표와 한계는 [한국어 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/README.md)에서 확인한다.\n\n"
    index += "\n".join(rows)
    (VIDEO / "README.md").write_text(index)


if __name__ == "__main__":
    make_outputs()
