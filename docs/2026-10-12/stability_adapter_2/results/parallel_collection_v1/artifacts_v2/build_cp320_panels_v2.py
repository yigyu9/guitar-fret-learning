#!/usr/bin/env python3
"""Make frame-only CP316/CP320 panels from sealed native images; no video/archive writes."""
from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1')
OUT = BASE / 'artifacts_v2/cp316_cp320_native_frames_v2.png'
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FONT_SHA256 = '48a28e97b34fc8e5b157657633670cd1b7de126cfc414da65ce9c3d5bc8be733'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

if sha(FONT_PATH) != FONT_SHA256:
    raise RuntimeError('pinned NanumGothic font SHA mismatch')
checks = [('CP316 초기', 'initial_000000'), ('CP320 cutoff', 'cutoff_000320')]
frames = [('0초', 0, '00000'), ('2초', 60, '00060'), ('마지막 16.3667초', 491, '00491')]
views = [('전신', 'whole_body'), ('손', 'hands')]
pw, ph, lh, margin = 720, 405, 42, 24
canvas = Image.new('RGB', (margin * 2 + pw * 3, margin * 2 + (ph + lh) * 4), 'white')
draw = ImageDraw.Draw(canvas)
label_font = ImageFont.truetype(str(FONT_PATH), 20)
for vrow, (vlabel, view) in enumerate(views):
    for cpcol, (cplabel, evaluation) in enumerate(checks):
        media = BASE / 'long_v1/evaluations' / evaluation / 'native/episode_0001/media'
        capture = json.loads((media / 'capture.json').read_text())
        for col, (tlabel, idx, frame_id) in enumerate(frames):
            frame_path = media / 'frames' / view / f'{frame_id}.png'
            declared = capture['frames'][idx]['image_sha256'][str(frame_path)]
            if sha(frame_path) != declared:
                raise RuntimeError(f'sealed frame SHA mismatch: {frame_path}')
            x, y = margin + col * pw, margin + (vrow * 2 + cpcol) * (ph + lh)
            image = Image.open(frame_path).convert('RGB')
            image.thumbnail((pw, ph), Image.Resampling.LANCZOS)
            tile = Image.new('RGB', (pw, ph), 'white')
            tile.paste(image, ((pw-image.width)//2, (ph-image.height)//2))
            canvas.paste(tile, (x, y + lh))
            draw.text((x + 8, y + 7), f'{cplabel} · {vlabel} · {tlabel}', fill='#111111', font=label_font)
canvas.save(OUT, optimize=True)
print(json.dumps({'path':str(OUT), 'sha256':sha(OUT), 'font_sha256':sha(FONT_PATH)}, ensure_ascii=False))
