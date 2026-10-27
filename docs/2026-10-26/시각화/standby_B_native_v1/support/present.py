"""Label native Isaac Gym camera frames and summarize measured B-pose tracking."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont


FINGERS = ("검지", "중지", "약지", "소지")
COLORS = ("#62a9ff", "#66d4a0", "#ffb45e", "#ce94ff")
BG = "#111922"
FG = "#edf2f7"
MUTED = "#b5c4d1"
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
# Fixed pixel crops of the native 1280x720 frames, chosen after inspecting both
# initial/final views. All frames retain the same crop; full-body frames are intact.
HAND_CROPS = {"front": (360, 120, 1000, 480), "oblique": (350, 180, 990, 540)}


def font(size):
    return ImageFont.truetype(FONT, size)


def put(draw, xy, value, size=28, fill=FG):
    draw.text(xy, str(value), font=font(size), fill=fill)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,duration",
         "-of", "json", str(path)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)["streams"][0]


def decode(path):
    return subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)


def read_frame(process, width=1280, height=720):
    expected = width * height * 3
    data = bytearray()
    while len(data) < expected:
        chunk = process.stdout.read(expected - len(data))
        if not chunk:
            raise RuntimeError("Native camera video ended before the expected frame count")
        data.extend(chunk)
    return Image.frombytes("RGB", (width, height), bytes(data))


def encode(path, width, height):
    return subprocess.Popen(
        ["ffmpeg", "-n", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "%dx%d" % (width, height), "-r", "30", "-i", "-", "-an",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)


def finish(process, pipe):
    pipe.close()
    if process.wait() != 0:
        raise RuntimeError("ffmpeg failed")


def stage(time_s):
    if time_s <= 1 + 1e-9:
        return "초기 자세 유지"
    if time_s <= 5 + 1e-9:
        return "B 목표로 천천히 이동"
    return "B 목표 유지·도달 확인"


def legend(draw, y, x=28, spacing=250):
    for index, (name, color) in enumerate(zip(FINGERS, COLORS)):
        put(draw, (x + index * spacing, y), "● " + name, 27, color)
    put(draw, (x + 4 * spacing, y), "엄지: 회색·목표 유지", 25, MUTED)


def hand_frame(front, oblique, time_s, angles, inside):
    image = Image.new("RGB", (1920, 900), BG)
    draw = ImageDraw.Draw(image)
    put(draw, (28, 16), "왼손 B 대기 자세 · 실제 Isaac Gym 물리 실행", 36)
    put(draw, (28, 64), "진단용 목표 이동 · 학습된 동작 아님", 25, MUTED)
    put(draw, (1370, 25), "%.3f초 | %s" % (time_s, stage(time_s)), 25)
    image.paste(front.crop(HAND_CROPS["front"]).resize((960, 540), Image.Resampling.LANCZOS), (0, 110))
    image.paste(oblique.crop(HAND_CROPS["oblique"]).resize((960, 540), Image.Resampling.LANCZOS), (960, 110))
    draw.rectangle((14, 120, 248, 161), fill=BG)
    draw.rectangle((974, 120, 1270, 161), fill=BG)
    put(draw, (25, 124), "정면 근접 카메라", 25)
    put(draw, (985, 124), "사선 근접 카메라", 25)
    legend(draw, 670)
    put(draw, (28, 718), "실제 굽힘각 MCP / PIP / DIP (도)  ·  B 판정은 각 중심 ±15°", 26, MUTED)
    for finger in range(4):
        x = 28 + finger * 472
        values = " / ".join("%5.1f" % value for value in angles[finger])
        put(draw, (x, 763), FINGERS[finger] + "  " + values, 27, COLORS[finger])
        put(draw, (x, 809), "B 대역 " + ("안" if inside[finger] else "밖"), 26)
    put(draw, (28, 859), "엄지·팔 명령 유지 · 기존 하체 안정화 제어 · 자유 기타", 24, MUTED)
    return image


def full_frame(frame, time_s):
    image = Image.new("RGB", (1280, 840), BG)
    draw = ImageDraw.Draw(image)
    put(draw, (24, 14), "B 대기 자세 진단 · 전신 / 실제 Isaac Gym", 31)
    put(draw, (24, 59), "%.3f초 | %s · 학습된 동작 아님" % (time_s, stage(time_s)), 24, MUTED)
    image.paste(frame, (0, 110))
    return image


def analyze(data, metadata):
    times = data["time_s"]
    angles = np.rad2deg(data["angles"])
    q = np.rad2deg(data["q"])
    target = np.rad2deg(data["target"])
    names = metadata["joint_names"]
    finger_names = np.asarray(metadata["finger_joint_names"]).reshape(-1).tolist()
    joint_ids = [names.index(name) for name in finger_names]
    errors = q[:, joint_ids] - target[:, joint_ids]
    inside = data["band_inside"].astype(bool)
    final_second = times > times[-1] - 1 + 1e-10
    force = np.linalg.norm(data["segment_net_force"], axis=-1)
    records = []
    for finger, name in enumerate(FINGERS):
        hits = np.flatnonzero(inside[:, finger])
        outside = np.flatnonzero(~inside[:, finger])
        stable_from = None
        if inside[-1, finger]:
            start = int(outside[-1]) + 1 if len(outside) else 0
            stable_from = float(times[start])
        f_error = errors[-1, finger * 4:(finger + 1) * 4]
        records.append({
            "finger": name,
            "B_native_degrees": metadata["B_native_degrees"][finger],
            "B_geometric_degrees": metadata["B_geometric_degrees"][finger],
            "final_geometric_degrees": angles[-1, finger].tolist(),
            "final_native_degrees": q[-1, joint_ids[finger * 4:(finger + 1) * 4]].tolist(),
            "final_target_degrees": target[-1, joint_ids[finger * 4:(finger + 1) * 4]].tolist(),
            "final_target_error_degrees": f_error.tolist(),
            "first_band_entry_s": float(times[hits[0]]) if len(hits) else None,
            "final_continuous_band_start_s": stable_from,
            "last_one_second_band_fraction": float(inside[final_second, finger].mean()),
            "final_quality": float(data["quality"][-1, finger]),
            "last_one_second_max_segment_net_force_N": float(force[final_second, finger].max()),
            "final_segment_net_force_N": force[-1, finger].tolist(),
        })
    movement = {}
    initial = np.asarray(metadata["initial_body_state"], dtype=float)
    bodies = metadata["body_names"]
    for label, body_name in (("guitar_root", next(name for name in bodies if name.startswith("guitar/"))),
                             ("left_palm", "human/LH:palm")):
        body_id = bodies.index(body_name)
        states = data["body_state"][:, body_id]
        displacement = states[:, :3] - initial[body_id, :3]
        displacement_norm = np.linalg.norm(displacement, axis=-1)
        rotation = states[:, 3:7] / np.linalg.norm(states[:, 3:7], axis=-1, keepdims=True)
        initial_rotation = initial[body_id, 3:7] / np.linalg.norm(initial[body_id, 3:7])
        rotation_delta = np.rad2deg(2 * np.arccos(np.clip(np.abs(rotation @ initial_rotation), 0, 1)))
        movement[label] = {
            "logical_body_name": body_name, "frame": "Native simulation world, relative to prepared t=0 state",
            "final_displacement_xyz_m": displacement[-1].tolist(),
            "final_displacement_m": float(displacement_norm[-1]),
            "max_displacement_m": float(displacement_norm.max()),
            "final_rotation_delta_degrees": float(rotation_delta[-1]),
            "max_rotation_delta_degrees": float(rotation_delta.max()),
        }
    all_inside = np.flatnonzero(inside.all(-1))
    return {
        "purpose": "Actual native physics B-pose target diagnostic, not a trained policy rollout",
        "physics_samples": int(len(times)), "physics_hz": 240,
        "video_hz": 30, "first_video_time_s": float(times[7]),
        "last_video_time_s": float(times[-1]),
        "frame_source": "Native Isaac Gym camera at each eighth physics endpoint; no pose interpolation",
        "hand_panel_fixed_pixel_crop_xyxy": HAND_CROPS,
        "hand_panel_resize": "Each fixed 640x360 crop enlarged to 960x540; unchanged aspect ratio",
        "renderer_limitation": "Native renderer emitted six visual-geometry load errors; some guitar string/fret visuals absent. No synthesized replacements.",
        "all_fingers_in_band_at_final": bool(inside[-1].all()),
        "first_all_fingers_band_entry_s": float(times[all_inside[0]]) if len(all_inside) else None,
        "all_fingers_in_band_for_last_one_second": bool(inside[final_second].all()),
        "final_16_axis_target_error_rms_degrees": float(np.sqrt(np.mean(errors[-1] ** 2))),
        "final_16_axis_target_error_max_degrees": float(np.abs(errors[-1]).max()),
        "last_one_second_16_axis_target_error_rms_degrees": float(np.sqrt(np.mean(errors[final_second] ** 2))),
        "last_one_second_16_axis_target_error_max_degrees": float(np.abs(errors[final_second]).max()),
        "fingers": records, "body_movement": movement,
        "limitations": [
            "B band measures projected flexion only; spread is a direct diagnostic target, not part of the active B reward.",
            "Rigid-body net force does not identify contact pairs or certify lack of self-intersection.",
            "One controlled target diagnostic does not establish learned-policy recovery or musical performance.",
        ],
    }


def snapshot(front, oblique, full, analysis):
    result = Image.new("RGB", (1920, 1270), BG)
    draw = ImageDraw.Draw(result)
    put(draw, (25, 13), "B 대기 자세 · 실제 Isaac Gym 최종 상태 (8.000초)", 36)
    legend(draw, 63)
    result.paste(front.crop(HAND_CROPS["front"]).resize((960, 540), Image.Resampling.LANCZOS), (0, 110))
    result.paste(oblique.crop(HAND_CROPS["oblique"]).resize((960, 540), Image.Resampling.LANCZOS), (960, 110))
    result.paste(full.resize((960, 540), Image.Resampling.LANCZOS), (0, 680))
    draw.rectangle((14, 120, 245, 161), fill=BG)
    draw.rectangle((974, 120, 1270, 161), fill=BG)
    put(draw, (25, 124), "정면 근접 카메라", 25)
    put(draw, (985, 124), "사선 근접 카메라", 25)
    put(draw, (986, 680), "측정된 최종 굽힘각 (도)", 31)
    put(draw, (986, 726), "MCP / PIP / DIP · B 중심 ±15°", 25, MUTED)
    for index, finger in enumerate(analysis["fingers"]):
        y = 784 + index * 79
        put(draw, (986, y), finger["finger"], 29, COLORS[index])
        put(draw, (1090, y), " / ".join("%.1f" % value for value in finger["final_geometric_degrees"]), 28)
        put(draw, (1090, y + 35), "마지막 1초 B 대역 %.0f%%" % (100 * finger["last_one_second_band_fraction"]), 23, MUTED)
    put(draw, (986, 1120), "학습된 동작 아님 · 진단용 16축 목표 이동", 25)
    put(draw, (986, 1163), "엄지·팔 명령 유지 / 기존 하체 안정화 제어", 25, MUTED)
    put(draw, (25, 1232), "접촉 하중은 몸체별 합력이며, 손가락 간 끼임·관통이 없다는 판정은 아닙니다.", 23, MUTED)
    return result


def write_report(phase, analysis):
    rows = []
    for finger in analysis["fingers"]:
        first = finger["first_band_entry_s"]
        angles = " / ".join("%.2f" % value for value in finger["final_geometric_degrees"])
        rows.append("| %s | %s | %.1f%% | %s | %.3f N |" % (
            finger["finger"], "없음" if first is None else "%.3f초" % first,
            finger["last_one_second_band_fraction"] * 100, angles,
            finger["last_one_second_max_segment_net_force_N"]))
    guitar = analysis["body_movement"]["guitar_root"]
    palm = analysis["body_movement"]["left_palm"]
    text = """# B 대기 자세의 실제 Isaac Gym 도달 진단

새로 만든 단일 환경에서 준비된 초기 상태를 불러오고, 검지~소지의 16개 관절을 B 목표로 천천히 이동했다. 이는 학습된 정책의 동작이나 대기 보상만으로 얻은 복귀가 아니라, 선택한 B 자세 자체의 물리적 도달과 외형을 살펴보는 진단이다.

초기 1초 유지 → 4초 동안 B 목표로 이동 → 마지막 3초 목표 유지다. 엄지 목표와 팔의 정책 명령을 유지했고, 손가락 이외의 정책 행동은 0이다. 기존 하체 안정화 제어의 발목 목표 조정과 유한한 위치 제어, 자유 기타 물리를 사용했다. 자세를 매 프레임 덮어써서 연출하지 않았다.

[두 방향 근접 영상](standby_B_hand_views.mp4) · [전신 영상](standby_B_fullbody.mp4) · [최종 사진](snapshot.png)

![실제 Isaac Gym 최종 B 자세](snapshot.png)

## 측정 결과

| 손가락 | B 대역 최초 진입 | 마지막 1초 대역 내 비율 | 최종 MCP / PIP / DIP | 마지막 1초 최대 마디 합력 |
|---|---:|---:|---:|---:|
%s

최종 16축 목표 대비 실제각 오차는 RMS **%.3f도**, 최대 **%.3f도**다. 마지막 1초 동안 네 손가락이 모두 B 대역에 머문 여부는 **%s**다. B 판정은 보상에서 사용하는 실제 기하 굽힘각의 각 중심 ±15도이며, 각 관절의 native 목표각과는 구분한다.

네 손가락이 동시에 B 굽힘 대역에 처음 들어온 시점은 **%s**다. 검지의 옆 벌림은 목표 **%.2f도**에 대해 실제 **%.2f도**였고, 마지막 순간 검지 가운데 마디에는 약 **%.2f N**의 합력이 남았다. 따라서 **B의 굽힘 형태에는 도달했지만, 16축의 정확한 목표 추종이나 편안하고 접촉 간섭 없는 자세까지 확인한 것은 아니다.** 접촉 상대는 현재 기록에서 특정할 수 없으며, B 벌림값과 손목 배치를 함께 추가 점검할 필요가 있다.

준비된 0초 상태 대비 기타 루트의 최종 이동은 **%.2f cm**, 회전은 **%.2f도**이며, 실행 중 최대 이동은 **%.2f cm**, 최대 회전은 **%.2f도**였다. 왼손 손바닥의 최종 이동은 **%.2f cm**, 회전은 **%.2f도**였고, 실행 중 최대 이동은 **%.2f cm**였다. 이는 실제 native 월드 좌표계의 몸체 움직임이며, 팔의 정책 명령이 0이어도 실제 몸체가 완전히 고정된다는 뜻은 아니다.

직접 지정한 B native 목표는 검지 25/−14/35/12도, 중지 28/−3/38/14도, 약지 31/3/41/16도, 소지 34/10/44/18도다. 순서는 뿌리 굽힘 / 옆 벌림 / 가운데 굽힘 / 끝 굽힘이다. 옆 벌림은 이 진단에서 지정했지만 현행 B 보상에는 포함되지 않는다.

## 해석 범위

원본 영상은 Isaac Gym 카메라에서 물리 8회마다 직접 얻은 30fps 영상이다. 첫 영상 프레임은 0.0333초이며 마지막은 8.000초다. 보간한 손 자세나 새로 합성한 손 모양을 사용하지 않았다. 판정과 관절 오차는 영상의 30Hz가 아니라 전체 240Hz 물리 기록으로 계산했다.

손 근접 화면은 원본 1280×720 영상의 고정 영역을 잘라 같은 비율로 확대했다. 정면의 원본 좌표는 (360,120)–(1000,480), 사선은 (350,180)–(990,540)이며 영상 전체에 같은 영역을 사용했다. 전신 화면은 자르지 않았다. 원본 카메라 영상은 `native_run/raw_*.mp4`에 보존했다.

native 렌더러에서 시각용 지오메트리 로드 오류 6건이 기록되어 일부 기타 줄·프렛 모양이 표시되지 않았다. 해당 모양을 새로 합성하거나 그려 넣지 않았다. 이 자료의 목적은 손가락 대기 형태와 실제 도달을 확인하는 것이다.

마디별 하중은 rigid-body net force의 크기다. 접촉 상대를 식별하지 않으므로 특정 손가락끼리 끼었거나 관통하지 않았다고 확정하지 않는다. 한 번의 목표 제어 진단으로 B의 학습 복귀, 압현 영향, 모든 손목 위치에서의 자연스러움을 입증하지 않는다. 외형은 정면·사선·전신 영상을 함께 보고 판단한다.

[native 실행 기록](native_run/report.json) · [전체 측정](presentation_analysis.json) · [원시 240Hz 기록](native_run/physics.npz) · [실행 입력과 카메라](native_run/metadata.json)
    """ % ("\n".join(rows), analysis["final_16_axis_target_error_rms_degrees"],
           analysis["final_16_axis_target_error_max_degrees"],
           "예" if analysis["all_fingers_in_band_for_last_one_second"] else "아니오",
           "없음" if analysis["first_all_fingers_band_entry_s"] is None else "%.6f초" % analysis["first_all_fingers_band_entry_s"],
           analysis["fingers"][0]["final_target_degrees"][1],
           analysis["fingers"][0]["final_native_degrees"][1],
           analysis["fingers"][0]["final_segment_net_force_N"][1],
           guitar["final_displacement_m"] * 100, guitar["final_rotation_delta_degrees"],
           guitar["max_displacement_m"] * 100, guitar["max_rotation_delta_degrees"],
           palm["final_displacement_m"] * 100, palm["final_rotation_delta_degrees"],
           palm["max_displacement_m"] * 100)
    (phase / "RESULTS.md").write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    phase = args.phase.resolve()
    native = phase / "native_run"
    for name in ("standby_B_hand_views.mp4", "standby_B_fullbody.mp4", "snapshot.png",
                 "initial_snapshot.png", "presentation_analysis.json", "RESULTS.md"):
        if (phase / name).exists():
            raise FileExistsError("Presentation output already exists; preserve this evidence: " + str(phase / name))
    metadata = json.loads((native / "metadata.json").read_text())
    run_report = json.loads((native / "report.json").read_text())
    scene = run_report.get("scene") or {}
    required = {"completed": True, "native_rendering": True, "training": False,
                "physics_endpoints": 1920, "requested_controls": 480,
                "frames_per_view": 240, "fps": 30, "changed_inputs": [], "failure": None}
    if any(run_report.get(key) != value for key, value in required.items()):
        raise ValueError("Native run is incomplete or input audit failed")
    if not (scene.get("closed") is True and scene.get("physx_use_gpu") is True
            and scene.get("use_gpu_pipeline") is True and scene.get("physics_steps") == 1920
            and scene.get("num_envs") == 1 and scene.get("simulator_count") == 1):
        raise ValueError("Expected a cleanly closed native GPU single-environment run")
    if run_report.get("encoder_exit_codes") != {"front": 0, "oblique": 0, "fullbody": 0}:
        raise ValueError("Native camera encoders did not all complete")
    with np.load(native / "physics.npz", allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    times = data["time_s"]
    if times.shape != (1920,) or not np.allclose(times, np.arange(1, 1921) / 240, atol=1e-7):
        raise ValueError("Expected exactly 1920 endpoints at 240Hz, excluding t=0")
    for name, shape in (("angles", (1920, 4, 3)), ("band_inside", (1920, 4)),
                        ("quality", (1920, 4)), ("q", (1920, 105)), ("target", (1920, 105)),
                        ("segment_net_force", (1920, 4, 3, 3)),
                        ("body_state", (1920, len(metadata["body_names"]), 13))):
        if data[name].shape != shape or not np.isfinite(data[name]).all():
            raise ValueError("Invalid trace field: " + name)
    raw_paths = [native / ("raw_" + name + ".mp4") for name in ("front", "oblique", "fullbody")]
    for path in raw_paths:
        if sha(path) != run_report.get("output_sha256", {}).get(path.name):
            raise ValueError("Native camera SHA differs from completed run report: " + str(path))
        info = probe(path)
        if (int(info["width"]), int(info["height"]), int(info["nb_read_frames"])) != (1280, 720, 240):
            raise ValueError("Unexpected native camera dimensions/frame count: " + str(path))
        numerator, denominator = (float(part) for part in info["avg_frame_rate"].split("/"))
        if abs(numerator / denominator - 30) > 1e-8:
            raise ValueError("Expected native camera at exactly 30fps")
    analysis = analyze(data, metadata)
    analysis["input_sha256"] = {str(path.relative_to(phase)): sha(path) for path in
                                raw_paths + [native / "physics.npz", native / "metadata.json", native / "report.json", Path(__file__).resolve()]}
    readers = [decode(path) for path in raw_paths]
    hand_writer = encode(phase / "standby_B_hand_views.mp4", 1920, 900)
    full_writer = encode(phase / "standby_B_fullbody.mp4", 1280, 840)
    final_frames = None
    for frame_index in range(240):
        frames = [read_frame(reader) for reader in readers]
        sample = (frame_index + 1) * 8 - 1
        time_s = float(times[sample])
        hands = hand_frame(frames[0], frames[1], time_s,
                           np.rad2deg(data["angles"][sample]), data["band_inside"][sample])
        hand_writer.stdin.write(hands.tobytes())
        full_writer.stdin.write(full_frame(frames[2], time_s).tobytes())
        if frame_index == 0:
            hands.save(phase / "initial_snapshot.png")
        final_frames = frames
    for reader in readers:
        if reader.stdout.read(1):
            raise ValueError("Native camera contains more than 240 decoded frames")
        finish(reader, reader.stdout)
    finish(hand_writer, hand_writer.stdin)
    finish(full_writer, full_writer.stdin)
    snapshot(*final_frames, analysis).save(phase / "snapshot.png")
    analysis["output_video_probe"] = {path.name: probe(path) for path in
                                      (phase / "standby_B_hand_views.mp4", phase / "standby_B_fullbody.mp4")}
    (phase / "presentation_analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n")
    write_report(phase, analysis)
    print(json.dumps({"complete": True, "all_final_in_band": analysis["all_fingers_in_band_at_final"],
                      "final_error_max_deg": analysis["final_16_axis_target_error_max_degrees"]}))


if __name__ == "__main__":
    main()
