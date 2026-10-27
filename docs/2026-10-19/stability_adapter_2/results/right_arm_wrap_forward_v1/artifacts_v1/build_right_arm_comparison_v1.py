#!/usr/bin/env python3
"""Build a native-pixel right-arm initial comparison; no resimulation or pose synthesis."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
OUTDIR = ROOT / 'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1'
BASE = ROOT / 'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_static/media'
NEW = ROOT / 'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/native_elbow10_static/media'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
SCRIPT = OUTDIR / 'build_right_arm_comparison_v1.py'
OUTPUT = OUTDIR / 'right_arm_initial_comparison_v1.png'
ROI = (470, 235, 730, 400)  # identical native whole-body pixel coordinates, both runs


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def capture_frame_sha(capture: Path, frame: Path) -> str:
    data = json.loads(capture.read_text(encoding='utf-8'))
    entry = next(x for x in data['frames'] if x['physics_step'] == 0)
    return entry['image_sha256'][str(frame)]


def main() -> None:
    before = [
        BASE / 'frames/whole_body/00000.png', BASE / 'capture.json',
        NEW / 'frames/whole_body/00000.png', NEW / 'capture.json', FONT, SCRIPT,
    ]
    missing = [str(p) for p in before if not p.is_file()]
    if missing:
        raise FileNotFoundError('\n'.join(missing))
    before_sha = {str(p): sha(p) for p in before}
    base_frame, new_frame = before[0], before[2]
    if before_sha[str(base_frame)] != capture_frame_sha(before[1], base_frame):
        raise ValueError('baseline t=0 PNG SHA does not match native capture metadata')
    if before_sha[str(new_frame)] != capture_frame_sha(before[3], new_frame):
        raise ValueError('selected t=0 PNG SHA does not match native capture metadata')

    images = [Image.open(p).convert('RGB') for p in (base_frame, new_frame)]
    if any(im.size != (1280, 720) for im in images):
        raise ValueError(f'unexpected native frame dimensions: {[im.size for im in images]}')
    crops = [im.crop(ROI).resize((780, 495), Image.Resampling.LANCZOS) for im in images]
    margin, header, gap = 28, 92, 22
    w, h = margin * 2 + 780 * 2 + gap, margin * 2 + header + 495 + 105
    canvas = Image.new('RGB', (w, h), '#f5f3ef')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT), 30)
    note_font = ImageFont.truetype(str(FONT), 23)
    x0, x1, y = margin, margin + 780 + gap, margin + header
    draw.text((x0 + 8, margin + 18), '왼쪽 이전', font=font, fill='#202020')
    draw.text((x1 + 8, margin + 18), '오른쪽 새 초기', font=font, fill='#202020')
    canvas.paste(crops[0], (x0, y))
    canvas.paste(crops[1], (x1, y))
    draw.text((margin, y + 495 + 26), '오른손바닥 초기 전방 이동: 9.94 mm', font=note_font, fill='#202020')
    draw.text((margin, y + 495 + 62), '동일 카메라·동일 ROI의 native whole-body 원프레임 crop 확대', font=note_font, fill='#444444')
    canvas.save(OUTPUT, format='PNG', optimize=False)

    after_sha = {str(p): sha(p) for p in before}
    changed = [p for p in before if before_sha[str(p)] != after_sha[str(p)]]
    if changed:
        raise RuntimeError(f'input changed while building: {changed}')
    record = {
        'schema': 'right_arm_comparison_provenance_v1',
        'method': 'two unmodified crops from native Isaac Gym whole_body t=0 PNGs, enlarged and labeled outside source pixels; no pose/image synthesis',
        'native_frame': {'physics_step': 0, 'time_s': 0.0, 'dimensions_px': [1280, 720], 'roi_xyxy_exclusive': list(ROI)},
        'caption_measurement': {'right_palm_forward_shift_mm': 9.9418199, 'display_rounding_mm': 9.94, 'meaning': 'fixed initial guitar-front world direction (+Y approximation), not relative-to-moving-guitar displacement or contact force'},
        'inputs': [{'path': str(p), 'sha256_before': before_sha[str(p)], 'sha256_after': after_sha[str(p)], 'unchanged': before_sha[str(p)] == after_sha[str(p)]} for p in before],
        'output': {'path': str(OUTPUT), 'sha256': sha(OUTPUT), 'dimensions_px': list(canvas.size)},
    }
    (OUTDIR / 'provenance_right_arm_v1.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
