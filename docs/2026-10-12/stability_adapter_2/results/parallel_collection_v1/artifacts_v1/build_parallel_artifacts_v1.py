#!/usr/bin/env python3
"""Copy four sealed evaluation videos and make native-frame comparison panels."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3/docs/2026-10-12')
BASE = ROOT / 'stability_adapter_2/results/parallel_collection_v1'
ART = BASE / 'artifacts_v1'
VID = ROOT / 'video/parallel_validation_v1'
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
EVALUATIONS = {
    'CP315': 'initial_000000',
    'CP316': 'update_000316',
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


video_records = []
for checkpoint, evaluation in EVALUATIONS.items():
    media = BASE / 'smoke_v1/evaluations' / evaluation / 'native/episode_0001/media'
    for view in ('whole_body', 'hands'):
        source = media / f'{view}.mp4'
        destination = VID / f'{checkpoint}_{view}.mp4'
        expected_source_sha = sha(source)
        if destination.exists():
            raise FileExistsError(f'new archive destination already exists: {destination}')
        shutil.copyfile(source, destination)
        source_after = sha(source)
        destination_sha = sha(destination)
        if expected_source_sha != source_after or destination_sha != expected_source_sha:
            raise RuntimeError(f'video copy/source SHA mismatch: {source}')
        probe = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames',
            '-show_entries', 'format=duration', '-of', 'json', str(destination),
        ], capture_output=True, text=True)
        try:
            ffprobe = json.loads(probe.stdout) if probe.returncode == 0 else None
        except json.JSONDecodeError:
            ffprobe = None
        video_records.append({
            'checkpoint': checkpoint, 'evaluation': evaluation, 'view': view,
            'source': str(source), 'destination': str(destination),
            'source_sha256_before': expected_source_sha,
            'source_sha256_after': source_after,
            'destination_sha256': destination_sha,
            'bytes': source.stat().st_size,
            'ffprobe': ffprobe,
            'ffprobe_error': probe.stderr.strip() if probe.returncode else None,
        })

manifest = {
    'scope': 'four sealed scalar native evaluation videos; source files preserved',
    'videos': video_records,
    'totals': {'files': len(video_records), 'bytes': sum(r['bytes'] for r in video_records)},
}
(VID / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

font_sha256 = sha(FONT_PATH)
font = ImageFont.truetype(str(FONT_PATH), 24)
label_font = ImageFont.truetype(str(FONT_PATH), 20)
timepoints = [('0초', 0, '00000'), ('2초', 60, '00060'), ('마지막 16.3667초', 491, '00491')]
panel_w, panel_h, label_h, margin = 720, 405, 42, 24
canvas = Image.new('RGB', (margin * 2 + panel_w * 3, margin * 2 + (panel_h + label_h) * 4), 'white')
draw = ImageDraw.Draw(canvas)
for view_row, (view_ko, view) in enumerate((('전신', 'whole_body'), ('손', 'hands'))):
    for cp_index, (checkpoint, evaluation) in enumerate(EVALUATIONS.items()):
        media = BASE / 'smoke_v1/evaluations' / evaluation / 'native/episode_0001/media'
        capture = json.loads((media / 'capture.json').read_text())
        for col, (time_ko, frame_index, frame_name) in enumerate(timepoints):
            frame_path = media / 'frames' / view / f'{frame_name}.png'
            declared = capture['frames'][frame_index]['image_sha256'][str(frame_path)]
            if sha(frame_path) != declared:
                raise RuntimeError(f'capture frame SHA mismatch: {frame_path}')
            x = margin + col * panel_w
            y = margin + (view_row * 2 + cp_index) * (panel_h + label_h)
            image = Image.open(frame_path).convert('RGB')
            image.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
            tile = Image.new('RGB', (panel_w, panel_h), 'white')
            tile.paste(image, ((panel_w - image.width) // 2, (panel_h - image.height) // 2))
            canvas.paste(tile, (x, y + label_h))
            draw.text((x + 8, y + 7), f'{checkpoint} · {view_ko} · {time_ko}', fill='#111111', font=label_font)
canvas.save(ART / 'cp315_cp316_native_frames_v1.png', optimize=True)
print(json.dumps({
    'video_count': len(video_records),
    'video_bytes': manifest['totals']['bytes'],
    'font_sha256': font_sha256,
    'panel_sha256': sha(ART / 'cp315_cp316_native_frames_v1.png'),
}, ensure_ascii=False))
