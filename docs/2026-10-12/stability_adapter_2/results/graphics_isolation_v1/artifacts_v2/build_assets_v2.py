#!/usr/bin/env python3
"""Archive the ten sealed videos and make CP241/CP242 native frame panels."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3/docs/2026-10-12')
G = ROOT / 'stability_adapter_2/results/graphics_isolation_v1'
OUT = G / 'artifacts_v2'
ARCH = ROOT / 'video/archive_v4'
BRIEF = G / 'archive_brief_v1.json'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


brief = json.loads(BRIEF.read_text())
records = []
for name, item in brief['videos'].items():
    src = Path(item['source'])
    dst = ARCH / name
    before = sha(src)
    if before != item['sha256']:
        raise RuntimeError(f'source SHA mismatch: {src}')
    if not dst.exists():
        shutil.copyfile(src, dst)
    after_src = sha(src)
    copied = sha(dst)
    if before != after_src or copied != before:
        raise RuntimeError(f'copy/hash mismatch: {src} -> {dst}')
    size = src.stat().st_size
    probe = subprocess.run([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames',
        '-show_entries', 'format=duration', '-of', 'json', str(dst),
    ], capture_output=True, text=True)
    try:
        probe_data = json.loads(probe.stdout) if probe.returncode == 0 else None
        probe_error = None if probe.returncode == 0 else probe.stderr.strip()
    except json.JSONDecodeError:
        probe_data, probe_error = None, 'ffprobe returned invalid JSON'
    records.append({
        'name': name, 'source': str(src), 'destination': str(dst),
        'sha256_source_before': before, 'sha256_source_after': after_src,
        'sha256_destination': copied, 'bytes': size,
        'ffprobe': probe_data, 'ffprobe_error': probe_error,
        'declared_duration_s': item.get('duration_s'),
        'declared_frames': item.get('frames'),
    })

manifest = {
    'scope': brief['scope'], 'source_brief': str(BRIEF),
    'source_brief_sha256': sha(BRIEF), 'videos': records,
    'totals': {'files': len(records), 'bytes': sum(r['bytes'] for r in records)},
}
(ARCH / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

font = ImageFont.truetype(FONT, 24)
small = ImageFont.truetype(FONT, 19)
times = [('0초', '00000'), ('2초', '00060'), ('16.3667초', '00491')]
views = [('전신', 'whole_body'), ('손', 'hands')]
episodes = [
    ('CP241 초기', G / 'smoke_on_v1/evaluations/initial_000000/native/episode_0001/media'),
    ('CP242 1회 갱신', G / 'smoke_on_v1/evaluations/update_000242/native/episode_0001/media'),
]
panel_w, panel_h = 720, 405
margin, label_h = 26, 43
grid = Image.new('RGB', (margin * 2 + panel_w * 3, margin * 2 + (panel_h + label_h) * 4), 'white')
draw = ImageDraw.Draw(grid)
for row, (view_label, view) in enumerate(views):
    for cp_col, (cp_label, media) in enumerate(episodes):
        for time_col, (time_label, frame) in enumerate(times):
            x = margin + time_col * panel_w
            y = margin + (row * 2 + cp_col) * (panel_h + label_h)
            im = Image.open(media / 'frames' / view / f'{frame}.png').convert('RGB')
            im.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
            tile = Image.new('RGB', (panel_w, panel_h), 'white')
            tile.paste(im, ((panel_w - im.width) // 2, (panel_h - im.height) // 2))
            grid.paste(tile, (x, y + label_h))
            draw.text((x + 8, y + 5), f'{cp_label} · {view_label} · {time_label}', fill='#111111', font=small)
grid.save(OUT / 'cp241_cp242_native_frames_v2.png', optimize=True)

print(json.dumps({'archive_files': len(records), 'archive_bytes': manifest['totals']['bytes'],
                  'image': str(OUT / 'cp241_cp242_native_frames_v2.png'),
                  'image_sha256': sha(OUT / 'cp241_cp242_native_frames_v2.png')}, ensure_ascii=False))
