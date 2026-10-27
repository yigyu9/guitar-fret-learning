"""Create saved-data curves and a contact sheet for the multi-face grip trials."""
import argparse
import hashlib
import json
import math
import numbers
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3'
LABELS = ('baseline', 'seed_1', 'seed_2')
DISPLAY = {'baseline': 'Baseline', 'seed_1': 'Seed 1', 'seed_2': 'Seed 2'}
COLORS = {'baseline': '#444444', 'seed_1': '#2878b5', 'seed_2': '#d17c18'}
CAMERAS = ('whole_body', 'hands')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [
        Path(__file__).resolve(),
        PHASE / 'analysis.json', PHASE / 'analysis_execution.json',
        PHASE / 'execution.json', PHASE / 'environment.json',
        PHASE / 'search.json', PHASE / 'face_audit.json',
    ]
    for label in LABELS:
        run = PHASE / 'native' / label
        paths.extend(run / f'{name}.json' for name in ('report', 'capture', 'initial_values', 'videos'))
        paths.extend(run / 'frames' / camera / f'{frame:05d}.png'
                     for camera in CAMERAS for frame in (0, 150))
    paths = [p.resolve() for p in paths]
    if len(paths) != len(set(paths)) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('declared phase, report, capture, or selected camera input missing')
    return paths


def require_finite(value, label):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, numbers.Real):
        if not math.isfinite(float(value)):
            raise ValueError(f'{label}: non-finite numeric metadata')
        return
    if isinstance(value, dict):
        for key, child in value.items():
            require_finite(child, f'{label}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            require_finite(child, f'{label}[{index}]')


def load_and_validate(input_hashes):
    analysis = json.loads((PHASE / 'analysis.json').read_text())
    require_finite(analysis, 'analysis.json')
    checks = analysis.get('checks', {})
    if len(checks) != 7 or not all(checks.values()):
        raise ValueError('expected all seven analysis checks to pass')
    if analysis.get('counts') != {'native_initializations': 3, 'physics_steps': 3600}:
        raise ValueError('unexpected analysis run counts')
    if set(analysis.get('curves', {})) != set(LABELS):
        raise ValueError('unexpected analysis condition labels')
    summaries = {row['label']: row for row in analysis.get('summary', [])}
    if set(summaries) != set(LABELS):
        raise ValueError('unexpected summary condition labels')

    for label in LABELS:
        summary = summaries[label]
        if summary.get('stability_success') is not False:
            raise ValueError(f'{label}: unexpected stability_success value')
        report = json.loads((PHASE / 'native' / label / 'report.json').read_text())
        require_finite(report, f'{label}/report.json')
        if (report.get('completed') is not True or report.get('physics_steps') != 1200
                or report.get('native_initializations') != 1
                or not report.get('checks') or not all(report.get('checks', {}).values())):
            raise ValueError(f'{label}: native run contract mismatch')
        capture = json.loads((PHASE / 'native' / label / 'capture.json').read_text())
        require_finite(capture, f'{label}/capture.json')
        if (capture.get('renderer') != 'Isaac Gym native camera'
                or capture.get('graphics_device_id') != 0 or capture.get('fps') != 30):
            raise ValueError(f'{label}: unexpected camera metadata')
        frames = capture.get('frames', [])
        if len(frames) != 151:
            raise ValueError(f'{label}: expected 151 actual camera frames')
        for idx, frame in enumerate(frames):
            if (frame.get('physics_step') != idx * 8
                    or abs(float(frame.get('time_s', -1)) - idx / 30) > 1e-9
                    or frame.get('render_preserves_states') is not True):
                raise ValueError(f'{label}: invalid frame sequence/timing')
            # Both views must exist at each saved frame, not only at chosen display times.
            expected_paths = {str((PHASE / 'native' / label / 'frames' / cam / f'{idx:05d}.png').resolve())
                              for cam in CAMERAS}
            image_hashes = frame.get('image_sha256', {})
            if set(image_hashes) != expected_paths:
                raise ValueError(f'{label}: incomplete paired camera views at frame {idx}')
            for image_path in expected_paths:
                if not Path(image_path).is_file() or sha256(image_path) != image_hashes[image_path]:
                    raise ValueError(f'{label}: camera frame hash mismatch at frame {idx}')
        for idx in (0, 150):
            for camera in CAMERAS:
                image = (PHASE / 'native' / label / 'frames' / camera / f'{idx:05d}.png').resolve()
                if input_hashes[str(image)] != frames[idx]['image_sha256'][str(image)]:
                    raise ValueError(f'{label}: sealed camera frame hash mismatch')

        curve = analysis['curves'][label]
        times = [float(x) for x in curve.get('time_s', [])]
        if len(times) != 1201 or any(abs(t - i / 240) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{label}: expected 0..5 s state samples at 240 Hz')
        for field in ('guitar_position_error_mm', 'guitar_rotation_error_deg'):
            values = curve.get(field, [])
            if len(values) != 1201 or not all(math.isfinite(float(v)) for v in values):
                raise ValueError(f'{label}: invalid {field} samples')
    return analysis


def draw_curves(path, analysis):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    panels = (
        ('guitar_position_error_mm', 'Guitar position error (mm)'),
        ('guitar_rotation_error_deg', 'Guitar rotation error (°)'),
    )
    for ax, (field, title) in zip(axes, panels):
        for label in LABELS:
            curve = analysis['curves'][label]
            ax.plot(curve['time_s'], curve[field], color=COLORS[label], lw=1.5,
                    label=DISPLAY[label])
        ax.set_ylabel(title)
        ax.set_xlim(0, 5)
        ax.grid(True, alpha=.25)
        ax.legend(loc='best')
    axes[-1].set_xlabel('Simulation time (s), saved native trace')
    fig.suptitle('Multi-face grip trial: 5 s saved guitar errors')
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def draw_camera_sheet(path):
    from PIL import Image, ImageDraw, ImageFont

    font_path = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    font = ImageFont.truetype(str(font_path), 23) if font_path.exists() else ImageFont.load_default()
    cell_w, cell_h, label_h, margin, gap = 640, 360, 42, 18, 14
    sheet = Image.new('RGB', (margin * 2 + cell_w * 3 + gap * 2,
                              margin * 2 + (cell_h + label_h) * 2 + gap), '#f2f2f2')
    draw = ImageDraw.Draw(sheet)
    for row, frame_idx in enumerate((0, 150)):
        for col, label in enumerate(LABELS):
            source = PHASE / 'native' / label / 'frames' / 'hands' / f'{frame_idx:05d}.png'
            image = Image.open(source).convert('RGB')
            if image.size != (1280, 720):
                raise ValueError(f'{source}: unexpected camera dimensions')
            image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            x = margin + col * (cell_w + gap)
            y = margin + label_h + row * (cell_h + label_h + gap)
            sheet.paste(image, (x, y))
            time = 't=0.0 s · step 0' if frame_idx == 0 else 't=5.0 s · step 1200'
            draw.text((x + 3, y - label_h + 7), f'{DISPLAY[label]} · hands · {time}',
                      fill='#111111', font=font)
    sheet.save(path, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    curve_path = out_dir / 'multi_face_grip_curves.png'
    camera_path = out_dir / 'multi_face_grip_hands_camera.png'
    manifest_path = out_dir / 'artifact_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory must be fresh and empty')
    declared = explicit_inputs()
    before = {str(p): sha256(p) for p in declared}
    analysis = load_and_validate(before)
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_curves(curve_path, analysis)
    draw_camera_sheet(camera_path)
    after = {str(p): sha256(p) for p in declared}
    if before != after:
        raise RuntimeError('an input changed during artifact generation')
    manifest_path.write_text(json.dumps({
        'input_sha256': before,
        'producer_sha256': sha256(__file__),
        'output_sha256': {str(p): sha256(p) for p in (curve_path, camera_path)},
        'displayed_camera_frames': [
            {'label': label, 'camera': 'hands', 'time_s': t, 'physics_step': int(t * 240)}
            for label in LABELS for t in (0.0, 5.0)
        ],
    }, indent=2, allow_nan=False) + '\n')
    print(curve_path)
    print(camera_path)
    print(manifest_path)


if __name__ == '__main__':
    main()
