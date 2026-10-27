#!/usr/bin/env python3
"""Corrected architecture-only producer with explicit independent log-standard-deviation parameter."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/home/ajou/yigyu/3")
PHASE = ROOT / "docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1"
OUT = PHASE / "artifacts"
META = OUT / "joint_learning_artifact_metadata_v3.json"
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
    OUT / "producer_joint_learning_artifacts_v1.py",
    OUT / "joint_learning_artifact_metadata_v1.json",
    OUT / "joint_learning_architecture_v1.png",
    OUT / "mean_policy_native_montage_v1.png",
    OUT / "producer_joint_learning_artifacts_v2.py",
    OUT / "joint_learning_artifact_metadata_v2.json",
    OUT / "joint_learning_architecture_v2.png",
    OUT / "mean_policy_native_montage_v2.png",
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
    import math
    draw.line((a, b), fill=color, width=width)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    r = 16
    draw.polygon([b, (b[0] - r * math.cos(angle - 0.5), b[1] - r * math.sin(angle - 0.5)),
                  (b[0] - r * math.cos(angle + 0.5), b[1] - r * math.sin(angle + 0.5))], fill=color)


def architecture(path: Path):
    im = Image.new("RGB", (1920, 1240), "#F5F8FC")
    d = ImageDraw.Draw(im)
    d.text((70, 48), "공동 음악 관측 기반 81관절 정책 구조", font=font(48), fill="#13243A")
    d.text((72, 112), "구조 연결은 구현됨 · native PPO/reward gate 미완료 · native 최적화 0회 (CPU synthetic optimizer 검증은 별도)",
           font=font(27), fill="#A23B36")
    rounded(d, (65, 200, 500, 970), "#EAF1FB", outline="#8BA8C8")
    d.text((100, 222), "관측 739D", font=font(32), fill="#173B66")
    blocks = [("물리 상태", "548"), ("공동 음악", "28"), ("event timing / required", "6 + 6"),
              ("방향 / event 시작·끝", "2 + 2"), ("측정 press cell", "132"),
              ("detector state / rearm", "6 + 6"), ("previous pick tip", "3")]
    y = 282
    for title, n in blocks:
        rounded(d, (95, y, 470, y + 74), "#FFFFFF", outline="#CBD6E3", radius=13, width=2)
        d.text((115, y + 18), title, font=font(21), fill="#30465F")
        d.text((420, y + 17), n, font=font(21), fill="#1E5A8A", anchor="ra")
        y += 89
    d.text((100, 915), "순서·크기는 frozen ABI manifest 기준", font=font(17), fill="#53677B")

    rounded(d, (570, 200, 1145, 580), "#EAF7F3", outline="#77B8A2")
    d.text((610, 225), "Actor · stochastic Gaussian", font=font(30), fill="#155A49")
    boxes = [(610, 315, 755, 410, ["739"]), (805, 315, 925, 410, ["512", "ELU"]),
             (975, 315, 1090, 410, ["256", "ELU"])]
    for box in boxes:
        rounded(d, box[:4], "#FFFFFF", outline="#8AB9AA", radius=14)
        center_text(d, box[:4], box[4], font(24), fill="#214B40")
    arrow(d, (755, 362), (805, 362)); arrow(d, (925, 362), (975, 362))
    rounded(d, (610, 475, 1090, 548), "#D8EEE6", outline="#77B8A2", radius=14)
    center_text(d, (610, 475, 1090, 548), ["256 → mean Linear head (81D)", "학습 parameter logσ(81D, 관측 독립) · PPO에 tanh 전 latent 저장"],
                font(20), fill="#174C3E")

    rounded(d, (570, 630, 1145, 900), "#F1ECFA", outline="#A99ACB")
    d.text((610, 655), "Critic · value", font=font(30), fill="#4A3675")
    cx = [610, 770, 910, 1050]
    for x, label in zip(cx, (["739"], ["512", "ELU"], ["256", "ELU"], ["1"])):
        box = (x, 755, x + 115, 845)
        rounded(d, box, "#FFFFFF", outline="#B6A8D4", radius=14)
        center_text(d, box, label, font(23), fill="#49396B")
    for x in (725, 865, 1005):
        arrow(d, (x, 800), (x + 45, 800), color="#6E5C91", width=4)
    d.text((612, 860), "Actor / Critic: 별도 MLP 경로", font=font(18), fill="#615279")

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
    im = Image.new("RGB", (3 * cell_w + 4 * gap, 2 * cell_h + 5 * gap + 120), "#F5F8FC")
    d = ImageDraw.Draw(im)
    d.text((32, 22), "초기 평균 정책 native 진단 · 학습/연주 성공 아님", font=font(36), fill="#17304B")
    for ri, (view, view_label) in enumerate(views):
        for ci, (idx, caption) in enumerate(times):
            x = gap + ci * (cell_w + gap)
            y = 100 + ri * (cell_h + gap)
            d.text((x + 8, y), f"{view_label} · {caption}", font=font(22), fill="#243C55")
            src = PHASE / f"native_mean_v2/media/frames/{view}/{idx}.png"
            frame = Image.open(src).convert("RGB")
            frame.thumbnail((cell_w - 12, cell_h - 48), Image.Resampling.LANCZOS)
            px = x + (cell_w - frame.width) // 2
            py = y + 38 + (cell_h - 40 - frame.height) // 2
            im.paste(frame, (px, py))
            d.rounded_rectangle((x, y + 34, x + cell_w, y + cell_h), radius=8, outline="#BFCBD7", width=2)
    d.text((32, im.height - 55), "평균 정책의 초기 자세 진단 영상에서 추출한 실제 Isaac Gym native frame · PPO 업데이트 0회",
           font=font(21), fill="#596B7E")
    im.save(path, format="PNG", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = [OUT / "joint_learning_architecture_v3.png"]
    hashes = {str(p): sha(p) for p in INPUTS}
    metadata = {"schema": "joint_learning_structure_artifacts_v3", "status": "prepared_before_render",
                "producer": str(Path(__file__).resolve()), "producer_sha256": sha(Path(__file__).resolve()),
                "inputs_sha256_before": hashes, "outputs": [str(p) for p in outputs],
                "native_calls": 0, "physics_steps": 0,
                "preserved_prior_artifacts": [str(p) for p in INPUTS if "artifacts/" in str(p)]}
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    baseline = json.loads((PHASE / "mean_verification_v1.json").read_text(encoding="utf-8"))
    expected = {"samples": 301, "maximum_displacement_mm": 46.30631891363679,
                "maximum_rotation_deg": 9.178642120694857, "settled_events": 9,
                "joint_success_events": 0, "native_training_updates": 0}
    if any(baseline[k] != v for k, v in expected.items()):
        raise RuntimeError("mean verification baseline differs from approved brief")
    architecture(outputs[0])
    after = {str(p): sha(p) for p in INPUTS}
    if hashes != after:
        raise RuntimeError("an input changed while rendering")
    for view in ("whole_body", "hands"):
        for idx in ("00000", "00060", "00150"):
            with Image.open(PHASE / f"native_mean_v2/media/frames/{view}/{idx}.png") as im:
                im.verify()
    metadata.update({"status": "complete", "inputs_sha256_after": after,
                     "output_sha256": {str(p): sha(p) for p in outputs},
                     "output_dimensions_px": {str(p): list(Image.open(p).size) for p in outputs},
                     "reused_without_modification": [str(OUT / "mean_policy_native_montage_v2.png")],
                     "native_frame_sources": [str(p) for p in INPUTS if "/frames/" in str(p)],
                     "baseline_summary": expected, "native_calls": 0, "physics_steps": 0})
    META.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
