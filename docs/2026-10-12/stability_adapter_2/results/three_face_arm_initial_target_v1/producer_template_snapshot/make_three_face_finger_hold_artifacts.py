"""Build two saved-data plots for the approved three-face finger-hold trials."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1'
LABELS = ('saved_finger_targets', 'initial_finger_targets')
DISPLAY = {'saved_finger_targets': 'Saved finger targets', 'initial_finger_targets': 'Initial finger targets'}
COLORS = {'saved_finger_targets': '#2878b5', 'initial_finger_targets': '#d17c18'}
BODIES = ('thumb3', 'index3', 'middle3', 'palm')
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [Path(__file__).resolve(), FONT_PATH, PHASE / 'artifact_brief.json', PHASE / 'analysis.json']
    for label in LABELS:
        run = PHASE / 'native' / label
        paths.extend((run / 'report.json', run / 'capture.json', run / 'initial_values.json'))
        paths.extend(run / 'frames' / 'hands' / f'{idx:05d}.png' for idx in (0, 150))
    paths = [p.resolve() for p in paths]
    if len(paths) != len(set(paths)) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('approved brief, analysis, font, or selected native inputs are missing')
    return paths


def validate(analysis, input_hashes):
    if set(analysis.get('curves', {})) != set(LABELS):
        raise ValueError('analysis curve labels do not match the approved two trials')
    summary = analysis.get('summary', [])
    if isinstance(summary, list):
        summary = {row['label']: row for row in summary}
    if set(summary) != set(LABELS):
        raise ValueError('analysis summary labels do not match the approved two trials')
    for label in LABELS:
        curve = analysis['curves'][label]
        times = curve.get('time_s', [])
        if len(times) != 1201 or any(abs(float(t) - i / 240) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{label}: expected saved 0..5 s samples at 240 Hz')
        for field in ('guitar_position_error_mm', 'guitar_rotation_error_deg'):
            values = curve.get(field, [])
            if len(values) != 1201 or not all(math.isfinite(float(v)) for v in values):
                raise ValueError(f'{label}: invalid {field} samples')
        groups = summary[label].get('contacts_by_any_other_body', {})
        for body in BODIES:
            steps = groups.get('human/LH:' + body, {}).get('positive_steps', [])
            if any(not isinstance(step, int) or step < 1 or step > 1200 for step in steps):
                raise ValueError(f'{label}: invalid positive raw contact step for LH:{body}')
        report_path = PHASE / 'native' / label / 'report.json'
        report = json.loads(report_path.read_text())
        if report.get('completed') is not True or report.get('physics_steps') != 1200:
            raise ValueError(f'{label}: native run is not a completed 5 s trial')
        capture_path = PHASE / 'native' / label / 'capture.json'
        capture = json.loads(capture_path.read_text())
        if capture.get('renderer') != 'Isaac Gym native camera' or capture.get('fps') != 30:
            raise ValueError(f'{label}: unexpected native camera metadata')
        frames = capture.get('frames', [])
        for idx in (0, 150):
            image = (PHASE / 'native' / label / 'frames' / 'hands' / f'{idx:05d}.png').resolve()
            if len(frames) <= idx or abs(float(frames[idx].get('time_s', -1)) - idx / 30) > 1e-9:
                raise ValueError(f'{label}: missing native hands frame at {idx / 30:g} s')
            if input_hashes[str(image)] != frames[idx].get('image_sha256', {}).get(str(image)):
                raise ValueError(f'{label}: frame {idx} hash does not match capture record')
    return summary


def draw_curves(path, analysis, summary, brief):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), gridspec_kw={'height_ratios': (1, 1, 1.15)})
    for ax, field, title in (
        (axes[0], 'guitar_position_error_mm', 'Guitar position error (mm)'),
        (axes[1], 'guitar_rotation_error_deg', 'Guitar rotation error (deg)'),
    ):
        for label in LABELS:
            curve = analysis['curves'][label]
            ax.plot(curve['time_s'], curve[field], color=COLORS[label], lw=1.5, label=DISPLAY[label])
        ax.set_ylabel(title)
        ax.set_xlim(0, 5)
        ax.grid(True, alpha=.25)
        ax.legend(loc='best')

    ax = axes[2]
    offsets = (-0.10, 0.10)
    for body_idx, body in enumerate(BODIES):
        for trial_idx, label in enumerate(LABELS):
            groups = summary[label]['contacts_by_any_other_body']
            group = groups.get('human/LH:' + body, {'positive_steps': []})
            times = [step / 240 for step in group['positive_steps']]
            ax.scatter(times, [body_idx + offsets[trial_idx]] * len(times), s=8,
                       color=COLORS[label], marker='|', linewidths=1.0)
    ax.set_yticks(range(len(BODIES)), ['LH:' + body for body in BODIES])
    ax.set_ylim(-.5, len(BODIES) - .5)
    ax.set_xlim(0, 5)
    ax.set_xlabel('Simulation time (s), saved samples at 240 Hz')
    ax.set_ylabel('Body positive-lambda samples')
    ax.grid(axis='x', alpha=.25)
    ax.legend(handles=[plt.Line2D([0], [0], color=COLORS[label], marker='|', linestyle='None', label=DISPLAY[label])
                       for label in LABELS], loc='upper right')
    fig.suptitle(brief.get('plot_title', 'Three-face finger target hold'))
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)


def draw_hands_montage(path):
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(str(FONT_PATH), 22)
    cell_w, cell_h, label_h, margin, gap = 640, 360, 42, 18, 14
    sheet = Image.new('RGB', (margin * 2 + cell_w * 2 + gap,
                              margin * 2 + (cell_h + label_h) * 2 + gap), '#f2f2f2')
    draw = ImageDraw.Draw(sheet)
    for row, frame_idx in enumerate((0, 150)):
        for col, label in enumerate(LABELS):
            source = PHASE / 'native' / label / 'frames' / 'hands' / f'{frame_idx:05d}.png'
            image = Image.open(source).convert('RGB')
            if image.size != (1280, 720):
                raise ValueError(f'{source}: unexpected image dimensions')
            image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            x, y = margin + col * (cell_w + gap), margin + label_h + row * (cell_h + label_h + gap)
            sheet.paste(image, (x, y))
            stamp = 't=0.0 s · step 0' if frame_idx == 0 else 't=5.0 s · step 1200'
            draw.text((x + 3, y - label_h + 7), f'{DISPLAY[label]} · hands · {stamp}',
                      fill='#111111', font=font)
    sheet.save(path, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    outputs = (out_dir / 'three_face_finger_hold_curves.png',
               out_dir / 'three_face_finger_hold_hands.png')
    manifest = out_dir / 'artifact_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory must be fresh and empty')
    declared = explicit_inputs()
    before = {str(path): sha256(path) for path in declared}
    brief = json.loads((PHASE / 'artifact_brief.json').read_text())
    analysis = json.loads((PHASE / 'analysis.json').read_text())
    summary = validate(analysis, before)
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_curves(outputs[0], analysis, summary, brief)
    draw_hands_montage(outputs[1])
    after = {str(path): sha256(path) for path in declared}
    if before != after:
        raise RuntimeError('an input changed during artifact generation')
    manifest.write_text(json.dumps({
        'producer_sha256': sha256(__file__),
        'inputs_sha256_before': before,
        'inputs_sha256_after': after,
        'outputs_sha256': {str(path.resolve()): sha256(path) for path in outputs},
        'native_calls': 0,
    }, indent=2, allow_nan=False) + '\n')
    print('\n'.join(map(str, (*outputs, manifest))))


if __name__ == '__main__':
    main()
