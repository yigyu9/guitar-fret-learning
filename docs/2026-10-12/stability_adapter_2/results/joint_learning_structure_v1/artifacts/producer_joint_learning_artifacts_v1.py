#!/usr/bin/env python3
"""Build saved-data-only architecture and native-frame montage artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1"
OUT = PHASE / "artifacts"
META = OUT / "joint_learning_artifact_metadata_v1.json"
FONT = Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
INPUTS = [
    PHASE / "mean_verification_v1.json",
    PHASE / "native_mean_v2/learning_abi.json",
    PHASE / "native_mean_v2/report.json",
    PHASE / "native_mean_v2/initial_values.json",
    PHASE / "native_mean_v2/joint_events.json",
    PHASE / "native_mean_v2/media/capture.json",
    PHASE / "native_mean_v2/media/videos.json",
    *(PHASE / f"native_mean_v2/media/frames/{view}/{idx}.png"
      for view in ("whole_body", "hands") for idx in ("00000", "00060", "00150")),
    FONT,
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size=size)


def rounded(draw, box, fill, outline="#C8D3E0", radius=22, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, lines, fnt, fill="#17263C", spacing=7):
    x0, y0, x1, y1 = box
    text = "\n".join(lines)
    bb = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.multiline_text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2), text,
                        font=fnt, fill=fill, spacing=spacing, align="center")


def arrow(draw, a, b, color="#51677E", width=5):
    draw.line((a, b), fill=color, width=width)
    import math
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    r = 16
    points = [b,
              (b[0] - r * math.cos(angle - 0.5), b[1] - r * math.sin(angle - 0.5)),
              (b[0] - r * math.cos(angle + 0.5), b[1] - r * math.sin(angle + 0.5))]
    draw.polygon(points, fill=color)


def architecture(path: Path):
    im = Image.new("RGB", (1920, 1240), "#F5F8FC")
    d = ImageDraw.Draw(im)
    d.text((70, 48), "공동 음악 관측 기반 81관절 정책 구조", font=font(48), fill="#13243A")
    d.text((72, 112), "구조 연결은 구현됨 · native PPO/reward 학습 gate는 미완료 · 최적화 0회",
           font=font(27), fill="#A23B36")

    # observation assembly
    rounded(d, (65, 200, 500, 970), "#EAF1FB", outline="#8BA8C8")
    d.text((100, 222), "관측 739D", font=font(32), fill="#173B66")
    blocks = [
        ("물리 상태", "548"), ("공동 음악", "28"), ("event timing / required", "6 + 6"),
        ("방향 / event 시작·끝", "2 + 2"), ("측정 press cell", "132"),
        ("detector state / rearm", "6 + 6"), ("previous pick tip", "3"),
    ]
    y = 282
    for title, n in blocks:
        rounded(d, (95, y, 470, y + 74), "#FFFFFF", outline="#CBD6E3", radius=13, width=2)
        d.text((115, y + 18), title, font=font(21), fill="#30465F")
        d.text((420, y + 17), n, font=font(21), fill="#1E5A8A", anchor="ra")
        y += 89
    d.text((100, 915), "순서·크기는 frozen ABI manifest 기준", font=font(17), fill="#53677B")

    # actor / critic lanes
    rounded(d, (570, 200, 1145, 580), "#EAF7F3", outline="#77B8A2")
    d.text((610, 225), "Actor · stochastic Gaussian", font=font(30), fill="#155A49")
    actor_boxes = [(610, 315, 755, 410, "739"), (805, 315, 925, 410, "512\nELU"),
                   (975, 315, 1080, 410, "256\nELU"), (1115, 315, 1125, 410, "")]
    # Last output is represented as a compact label to keep the pipeline legible.
    for box in actor_boxes[:3]:
        rounded(d, box[:4], "#FFFFFF", outline="#8AB9AA", radius=14)
        center_text(d, box[:4], box[4].split("\n"), font(24), fill="#214B40")
    arrow(d, (755, 362), (805, 362)); arrow(d, (925, 362), (975, 362))
    d.text((990, 435), "mean + logσ", font=font(20), fill="#27634F")
    rounded(d, (610, 475, 1090, 548), "#D8EEE6", outline="#77B8A2", radius=14)
    center_text(d, (610, 475, 1090, 548), ["tanh Gaussian latent · 81D", "PPO rollout에는 tanh 이전 latent 저장"],
                font(21), fill="#174C3E")

    rounded(d, (570, 630, 1145, 900), "#F1ECFA", outline="#A99ACB")
    d.text((610, 655), "Critic · value", font=font(30), fill="#4A3675")
    cx = [610, 770, 910, 1050]
    labels = ["739", "512\nELU", "256\nELU", "1"]
    for x, label in zip(cx, labels):
        box = (x, 755, x + 115, 845)
        rounded(d, box, "#FFFFFF", outline="#B6A8D4", radius=14)
        center_text(d, box, label.split("\n"), font(23), fill="#49396B")
    for x in (725, 865, 1005):
        arrow(d, (x, 800), (x + 45, 800), color="#6E5C91", width=4)
    d.text((612, 860), "Actor / Critic: 별도 MLP 경로", font=font(18), fill="#615279")

    # action conversion and environment
    rounded(d, (1230, 250, 1855, 410), "#FFF5E6", outline="#D6A95F")
    center_text(d, (1250, 260, 1835, 400), ["81D action", "absolute-anchor codec", "group별 rate limit → native PD target"],
                font(25), fill="#68491A")
    rounded(d, (1230, 500, 1855, 690), "#E8F1F8", outline="#85A9C4")
    center_text(d, (1250, 515, 1835, 675), ["실제상태 feedback", "PhysX 240 Hz · control 60 Hz", "root/하체 고정 · 기타 자유 · strap OFF"],
                font(25), fill="#244A67")
    rounded(d, (1230, 790, 1855, 960), "#FFF0EE", outline="#D99A93")
    center_text(d, (1250, 800, 1835, 950), ["native 학습 연결: 비활성", "reward / PPO update gate 미완료", "기존 actor weight/action 복사 없음"],
                font(24), fill="#813B35")
    arrow(d, (1090, 510), (1230, 330), color="#3B9277")
    arrow(d, (1542, 410), (1542, 500), color="#B18336")
    arrow(d, (1542, 690), (1542, 790), color="#8B6DAD")
    d.text((72, 1085), "81 target 구성: body 9 · head 6 · arms 24 · fingers 42", font=font(25), fill="#233B55")
    d.text((72, 1130), "이 도식은 ABI/구현 구조를 요약하며 학습 완료·연주 성공·물리 인증을 나타내지 않습니다.",
           font=font(22), fill="#596B7E")
    im.save(path, format="PNG", optimize=True)


def montage(path: Path):
    times = [("00000", "0초 · step 0"), ("00060", "2초 · step 480"), ("00150", "5초 · step 1200")]
    views = [("whole_body", "전신"), ("hands", "양손")]
    cell_w, cell_h, gap = 640, 390, 20
    im = Image.new("RGB", (2 * cell_w + 4 * gap, 2 * cell_h + 5 * gap + 120), "#F5F8FC")
    d = ImageDraw.Draw(im)
    d.text((32, 22), "초기 평균 정책 native 진단 · 학습/연주 성공 아님", font=font(36), fill="#17304B")
    for ri, (view, view_label) in enumerate(views):
        for ci, (idx, caption) in enumerate(times):
            x = gap + ci * (cell_w + gap)
            y = 100 + ri * (cell_h + gap)
            d.text((x + 8, y), f"{view_label} · {caption}", font=font(22), fill="#243C55")
            src = PHASE / f"native_mean_v2/media/frames/{view}/{idx}.png"
            frame = Image.open(src).convert("RGB")
            frame.thumbnail((cell_w, cell_h - 40), Image.Resampling.LANCZOS)
            px = x + (cell_w - frame.width) // 2
            py = y + 38 + (cell_h - 40 - frame.height) // 2
            im.paste(frame, (px, py))
            d.rounded_rectangle((x, y + 34, x + cell_w, y + cell_h), radius=8, outline="#BFCBD7", width=2)
    d.text((32, im.height - 55), "평균 정책의 초기 자세 진단 영상에서 추출한 실제 Isaac Gym native frame · PPO 업데이트 0회",
           font=font(21), fill="#596B7E")
    im.save(path, format="PNG", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    output_paths = [OUT / "joint_learning_architecture_v1.png", OUT / "mean_policy_native_montage_v1.png"]
    input_hashes = {str(p): sha(p) for p in INPUTS}
    metadata = {
        "schema": "joint_learning_structure_artifacts_v1",
        "status": "prepared_before_render",
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "inputs_sha256_before": input_hashes,
        "outputs": [str(p) for p in output_paths],
        "native_calls": 0,
        "physics_steps": 0,
    }
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    baseline = json.loads((PHASE / "mean_verification_v1.json").read_text(encoding="utf-8"))
    if (baseline["samples"] != 301 or baseline["maximum_displacement_mm"] != 46.30631891363679
            or baseline["maximum_rotation_deg"] != 9.178642120694857
            or baseline["settled_events"] != 9 or baseline["joint_success_events"] != 0
            or baseline["native_training_updates"] != 0):
        raise RuntimeError("mean verification baseline differs from approved brief")

    architecture(output_paths[0])
    montage(output_paths[1])
    input_hashes_after = {str(p): sha(p) for p in INPUTS}
    if input_hashes_after != input_hashes:
        raise RuntimeError("an input changed while rendering")
    for view in ("whole_body", "hands"):
        for idx in ("00000", "00060", "00150"):
            src = PHASE / f"native_mean_v2/media/frames/{view}/{idx}.png"
            with Image.open(src) as im:
                im.verify()
    metadata.update({
        "status": "complete",
        "inputs_sha256_after": input_hashes_after,
        "output_sha256": {str(p): sha(p) for p in output_paths},
        "output_dimensions_px": {str(p): list(Image.open(p).size) for p in output_paths},
        "native_frame_sources": [str(p) for p in INPUTS if "/frames/" in str(p)],
        "baseline_summary": {
            k: baseline[k] for k in ("samples", "maximum_displacement_mm", "maximum_rotation_deg",
                                      "settled_events", "joint_success_events", "native_training_updates")
        },
        "native_calls": 0,
        "physics_steps": 0,
    })
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
