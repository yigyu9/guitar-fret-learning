#!/usr/bin/env python3
"""Build an aspect-preserving gallery from three native whole-body frame crops."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
ART = ROOT / 'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1'
MEDIA = ROOT / 'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/native_elbow10_static/media'
CAPTURE = MEDIA / 'capture.json'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
SCRIPT = ART / 'build_upper_timeline_v4.py'
OUTPUT = ART / 'selected_upper_crop_0_2_5_v4.png'
FRAME_INDICES = (0, 60, 150)
PHYSICS_STEPS = (0, 480, 1200)
TIMES = ('0초', '2초', '5초')
ROI = (390, 125, 930, 555)  # 540x430 native pixels
PANEL = (360, 287)  # aspect ratio 1.25436, source ratio 1.25581; ~0.12% rounding


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    frames = [MEDIA / f'frames/whole_body/{index:05d}.png' for index in FRAME_INDICES]
    inputs = frames + [CAPTURE, FONT, SCRIPT]
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise FileNotFoundError('\n'.join(missing))
    before = {str(p): sha(p) for p in inputs}
    cap = json.loads(CAPTURE.read_text(encoding='utf-8'))
    for index, physics_step, frame in zip(FRAME_INDICES, PHYSICS_STEPS, frames):
        meta = cap['frames'][index]
        if meta['physics_step'] != physics_step:
            raise ValueError(f'unexpected native frame {index} physics step {meta["physics_step"]}')
        if meta['image_sha256'][str(frame)] != before[str(frame)]:
            raise ValueError(f'frame {step} hash mismatch against native capture metadata')
    font = ImageFont.truetype(str(FONT), 24)
    crops = []
    for frame in frames:
        im = Image.open(frame).convert('RGB')
        if im.size != (1280, 720):
            raise ValueError(f'unexpected source frame size {im.size}: {frame}')
        crop = im.crop(ROI)
        if crop.size != (540, 430):
            raise ValueError(f'unexpected ROI dimensions {crop.size}')
        crops.append(crop.resize(PANEL, Image.Resampling.LANCZOS))
    margin, gap, title_h, footer_h = 20, 18, 54, 44
    width = margin * 2 + PANEL[0] * 3 + gap * 2
    height = margin * 2 + title_h + PANEL[1] + footer_h
    canvas = Image.new('RGB', (width, height), '#f5f3ef')
    draw = ImageDraw.Draw(canvas)
    for i, crop in enumerate(crops):
        x = margin + i * (PANEL[0] + gap)
        draw.text((x + 4, margin + 8), f'native frame {FRAME_INDICES[i]} · {TIMES[i]}', font=font, fill='#202020')
        canvas.paste(crop, (x, margin + title_h))
    draw.text((margin, margin + title_h + PANEL[1] + 12), '동일 ROI crop · 원본 540×430 px, 확대 시 종횡비 유지', font=font, fill='#444444')
    canvas.save(OUTPUT, format='PNG', optimize=False)
    after = {str(p): sha(p) for p in inputs}
    changed = [p for p in inputs if before[str(p)] != after[str(p)]]
    if changed:
        raise RuntimeError(f'input changed during generation: {changed}')
    provenance = {
        'schema': 'upper_timeline_provenance_v4',
        'method': 'native whole_body source-frame crops, uniform aspect-preserving resize, labels outside source pixels; no pose synthesis',
        'source': {'run': 'native_elbow10_static', 'fps': 30, 'native_frame_indices': list(FRAME_INDICES), 'physics_steps': list(PHYSICS_STEPS), 'times_s': [0.0, 2.0, 5.0], 'source_frame_px': [1280, 720], 'roi_xyxy_exclusive': list(ROI), 'roi_px': [540, 430], 'panel_px': list(PANEL), 'source_to_panel_scale': [PANEL[0]/540, PANEL[1]/430], 'rounding_aspect_error_fraction': abs((PANEL[0]/PANEL[1])/(540/430)-1)},
        'inputs': [{'path': str(p), 'sha256_before': before[str(p)], 'sha256_after': after[str(p)], 'unchanged': before[str(p)] == after[str(p)]} for p in inputs],
        'output': {'path': str(OUTPUT), 'sha256': sha(OUTPUT), 'dimensions_px': list(canvas.size)},
    }
    (ART / 'provenance_upper_v4.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
