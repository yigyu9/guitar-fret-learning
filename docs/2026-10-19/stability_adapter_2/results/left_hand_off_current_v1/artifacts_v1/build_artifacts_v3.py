#!/usr/bin/env python3
"""Create native start/end comparison panels and byte-identical copies of partial native videos."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
DOCS = ROOT / 'docs/2026-10-19/stability_adapter_2'
P = DOCS / 'results/left_hand_off_current_v1'
RUN = P / 'native_back100_static'
MEDIA = RUN / 'media'
ART = P / 'artifacts_v1'
VIDEO = DOCS / 'video/left_hand_off_current_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
SCRIPT = ART / 'build_artifacts_v3.py'
PIN = ART / 'preflight_pin_v3.json'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ffprobe(path: Path) -> dict:
    command = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration', '-of', 'json', str(path)]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    streams = data.get('streams', [])
    if len(streams) != 1:
        raise ValueError(f'expected one video stream in {path}; got {len(streams)}')
    return {'command': command, 'exit_code': result.returncode, 'stream': streams[0]}


def main() -> None:
    pin = json.loads(PIN.read_text(encoding='utf-8'))
    if pin.get('schema') != 'left_hand_off_preflight_pin_v1':
        raise ValueError('unsupported/missing preflight pin schema')
    if pin['producer']['path'] != str(SCRIPT):
        raise ValueError('preflight pin points to a different producer')
    pinned_inputs = pin['inputs']
    for row in pinned_inputs:
        path = Path(row['path'])
        if not path.is_file() or sha(path) != row['sha256_before']:
            raise ValueError(f'input missing or changed since disk pin: {path}')
    if sha(SCRIPT) != pin['producer']['sha256_before']:
        raise ValueError('producer changed since disk pin')

    # Confirm selected native first/last images against the original capture ledger.
    capture_path = MEDIA / 'capture.json'
    capture = json.loads(capture_path.read_text(encoding='utf-8'))
    frames = capture['frames']
    if len(frames) != 29 or frames[0]['physics_step'] != 0 or frames[-1]['physics_step'] != 224:
        raise ValueError('unexpected native capture frame/time extent')
    selected = [('whole_body', 0), ('whole_body', 28), ('hands', 0), ('hands', 28)]
    for view, index in selected:
        frame_path = MEDIA / 'frames' / view / f'{index:05d}.png'
        row = frames[index]
        if row['image_sha256'][str(frame_path)] != sha(frame_path):
            raise ValueError(f'native PNG SHA differs from capture metadata: {frame_path}')
        with Image.open(frame_path) as im:
            if im.size != (1280, 720):
                raise ValueError(f'unexpected native image size {im.size}: {frame_path}')

    font = ImageFont.truetype(str(FONT), 32)
    margin, gap, top, bottom = 24, 18, 108, 24
    out_records = []
    for view, filename, title in [
        ('whole_body', 'whole_body_start_end_v3.png', '전신 native 프레임: 시작과 실제 종료'),
        ('hands', 'hands_start_end_v3.png', '손·기타 근접 native 프레임: 시작과 실제 종료'),
    ]:
        canvas = Image.new('RGB', (margin * 2 + 1280 * 2 + gap, top + 720 + bottom), '#f5f3ef')
        draw = ImageDraw.Draw(canvas)
        draw.text((margin, 12), title, font=font, fill='#202020')
        for idx, label in [(0, '초기 native · 0.000초'), (28, '실제 마지막 native · 0.933초')]:
            x = margin if idx == 0 else margin + 1280 + gap
            draw.text((x + 4, top - 38), label, font=font, fill='#202020')
            frame_path = MEDIA / 'frames' / view / f'{idx:05d}.png'
            with Image.open(frame_path) as im:
                canvas.paste(im.convert('RGB'), (x, top))
        output = ART / filename
        canvas.save(output, format='PNG', optimize=False)
        out_records.append({'path': str(output), 'sha256': sha(output), 'dimensions_px': list(canvas.size), 'source_view': view, 'source_frames': [0, 28], 'source_native_px_each': [1280, 720]})

    # Verify previously made byte-exact native partial copies; do not rewrite them.
    copies = []
    for view in ('whole_body', 'hands'):
        source = MEDIA / f'{view}.mp4'
        dest = VIDEO / f'left_off_back100_static_{view}_v2.mp4'
        if not dest.is_file():
            raise FileNotFoundError(f'pre-existing byte-exact MP4 copy missing: {dest}')
        source_hash, dest_hash = sha(source), sha(dest)
        if source_hash != dest_hash or source.stat().st_size != dest.stat().st_size:
            raise ValueError(f'MP4 copy is not byte-identical: {dest}')
        copies.append({'source_path': str(source), 'source_sha256': source_hash, 'source_bytes': source.stat().st_size, 'copy_path': str(dest), 'copy_sha256': dest_hash, 'copy_bytes': dest.stat().st_size, 'byte_exact': source_hash == dest_hash and source.stat().st_size == dest.stat().st_size, 'ffprobe_source': ffprobe(source), 'ffprobe_copy': ffprobe(dest)})

    # Recheck all pinned inputs and the producer; the original records are immutable.
    after = {row['path']: sha(Path(row['path'])) for row in pinned_inputs}
    changed = [row['path'] for row in pinned_inputs if after[row['path']] != row['sha256_before']]
    producer_after = sha(SCRIPT)
    if changed or producer_after != pin['producer']['sha256_before']:
        raise RuntimeError(f'consumed inputs/producer changed during build: {changed}')
    record = {
        'schema': 'left_hand_off_artifacts_v1',
        'run': str(RUN),
        'scope': 'native run starts with left hand away from guitar at t=0; this is not a continuous release transition or passive-equilibrium test',
        'native_extent': {'physics_steps': 224, 'control_steps': 56, 'physics_seconds': 0.9333333333333333, 'capture_frames': 29, 'first_frame_time_s': 0.0, 'last_frame_time_s': 0.9333333333333333, 'stop_reason': 'guitar safety displacement'},
        'inputs': [{'path': row['path'], 'sha256_before': row['sha256_before'], 'sha256_after': after[row['path']], 'unchanged': after[row['path']] == row['sha256_before']} for row in pinned_inputs],
        'producer': {'path': str(SCRIPT), 'sha256_before': pin['producer']['sha256_before'], 'sha256_after': producer_after, 'unchanged': producer_after == pin['producer']['sha256_before']},
        'images': out_records,
        'videos': copies,
    }
    (ART / 'provenance_v3.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
