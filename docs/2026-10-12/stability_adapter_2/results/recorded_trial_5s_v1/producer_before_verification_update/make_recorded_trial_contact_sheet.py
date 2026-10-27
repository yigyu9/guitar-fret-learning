"""Make a labelled sheet from six already-recorded native Gym camera frames."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1'
RUN = PHASE / 'baseline'
CAPTURE = RUN / 'capture.json'
VERIFICATION = PHASE / 'verification.json'
SAMPLES = ((0, 'whole_body'), (75, 'whole_body'), (150, 'whole_body'),
           (0, 'hands'), (75, 'hands'), (150, 'hands'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    paths = [Path(__file__).resolve(), CAPTURE, VERIFICATION]
    paths += [RUN / 'frames' / camera / f'{frame:05d}.png'
              for frame, camera in SAMPLES]
    paths = [p.resolve() for p in paths]
    if len(set(paths)) != len(paths) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('declared input missing or duplicated')
    return paths


def make_sheet(output, capture, verification, input_hashes):
    from PIL import Image, ImageDraw, ImageFont

    if not all(verification['checks'].values()) or len(verification['checks']) != 8:
        raise ValueError('verification.json must contain eight passing checks')
    if verification['counts']['full_native_initializations'] != 1 or verification['counts']['full_physics_steps'] != 1200:
        raise ValueError('unexpected full-run counts')
    frames = capture.get('frames', [])
    if len(frames) != 151 or capture.get('fps') != 30:
        raise ValueError('expected 151 recorded frames at 30 fps')
    if capture.get('renderer') != 'Isaac Gym native camera' or capture.get('graphics_device_id') != 0:
        raise ValueError('unexpected camera provenance')

    font_path = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    font = ImageFont.truetype(str(font_path), 23) if font_path.exists() else ImageFont.load_default()
    label_font = ImageFont.truetype(str(font_path), 24) if font_path.exists() else ImageFont.load_default()
    cell_w, cell_h, label_h, margin, gap = 640, 360, 42, 18, 14
    sheet = Image.new('RGB', (margin * 2 + cell_w * 3 + gap * 2,
                              margin * 2 + (cell_h + label_h) * 2 + gap), '#f2f2f2')
    draw = ImageDraw.Draw(sheet)
    for row, camera in enumerate(('whole_body', 'hands')):
        for col, frame_index in enumerate((0, 75, 150)):
            path = RUN / 'frames' / camera / f'{frame_index:05d}.png'
            record = frames[frame_index]
            if record.get('physics_step') != frame_index * 8 or abs(record.get('time_s', -1) - frame_index / 30) > 1e-9:
                raise ValueError(f'frame {frame_index} capture timing mismatch')
            if record.get('render_preserves_states') is not True:
                raise ValueError(f'frame {frame_index} does not preserve saved state')
            if record.get('image_sha256', {}).get(str(path.resolve())) != input_hashes[str(path.resolve())]:
                raise ValueError(f'frame {frame_index} SHA differs from capture record')
            image = Image.open(path).convert('RGB')
            if image.size != (1280, 720):
                raise ValueError(f'{path}: expected 1280x720')
            image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            x = margin + col * (cell_w + gap)
            y = margin + label_h + row * (cell_h + label_h + gap)
            sheet.paste(image, (x, y))
            view = '전신' if camera == 'whole_body' else '손 확대'
            title = f'{view}  ·  t = {frame_index / 30:.1f} s  ·  step {frame_index * 8}'
            draw.text((x + 4, y - label_h + 8), title, fill='#111111', font=font)
    sheet.save(output, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    image = out_dir / 'recorded_trial_5s_contact_sheet.png'
    manifest = out_dir / 'contact_sheet_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory is not empty; choose a new path')
    declared = inputs()
    before = {str(p): digest(p) for p in declared}
    capture = json.loads(CAPTURE.read_text())
    verification = json.loads(VERIFICATION.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    make_sheet(image, capture, verification, before)
    after = {str(p): digest(p) for p in declared}
    if before != after:
        raise RuntimeError('an input changed while creating contact sheet')
    manifest.write_text(json.dumps({
        'input_sha256': before,
        'producer_sha256': digest(__file__),
        'output_sha256': {str(image): digest(image)},
        'selected_frames': [
            {'camera': camera, 'frame_index': frame, 'time_s': frame / 30,
             'physics_step': frame * 8}
            for camera in ('whole_body', 'hands') for frame in (0, 75, 150)
        ],
    }, indent=2) + '\n')
    print(image)
    print(manifest)


if __name__ == '__main__':
    main()
