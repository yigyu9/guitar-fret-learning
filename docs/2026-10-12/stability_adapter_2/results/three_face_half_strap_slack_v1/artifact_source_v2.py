"""Build saved-data plots for the approved three-face strap-slack trials."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1'
EXPECTED_ANALYSIS_SHA256 = '35e2054f93c863d299437842a79addcadafa40b6ec24f9dfceeaa232c87746e8'
LABELS = ('half_slack', 'zero_slack')
DISPLAY = {'half_slack': 'Half slack · LA 1.09434009 m',
           'zero_slack': 'Zero slack · LA 1.08683321 m'}
COLORS = {'half_slack': '#2878b5', 'zero_slack': '#d17c18'}
MONTAGE_LABELS = {'half_slack': 'Half slack', 'zero_slack': 'Zero slack'}
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
    if sha256(PHASE / 'analysis.json') != EXPECTED_ANALYSIS_SHA256:
        raise ValueError('analysis.json SHA256 does not match the approved brief')
    if set(analysis.get('curves', {})) != set(LABELS):
        raise ValueError('analysis curve labels do not match the approved two trials')
    summaries = {row['label']: row for row in analysis.get('summary', [])}
    if set(summaries) != set(LABELS):
        raise ValueError('analysis summary labels do not match the approved two trials')
    reference = analysis.get('stored_reference_curves', {})
    reference_times = reference.get('time_s', [])
    if len(reference_times) != 1201 or any(abs(float(t) - i / 240) > 1e-9 for i, t in enumerate(reference_times)):
        raise ValueError('stored reference must use saved 0..5 s samples at 240 Hz')
    for field in ('guitar_position_error_mm', 'guitar_rotation_error_deg'):
        values = reference.get(field, [])
        if len(values) != 1201 or not all(math.isfinite(float(v)) for v in values):
            raise ValueError(f'stored reference: invalid {field} samples')
    for label in LABELS:
        curve = analysis['curves'][label]
        times = curve.get('time_s', [])
        if len(times) != 1201 or any(abs(float(t) - i / 240) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{label}: expected saved 0..5 s samples at 240 Hz')
        for field in ('guitar_position_error_mm', 'guitar_rotation_error_deg'):
            values = curve.get(field, [])
            if len(values) != 1201 or not all(math.isfinite(float(v)) for v in values):
                raise ValueError(f'{label}: invalid {field} samples')
        strap_times = curve.get('strap_submitted_time_s', [])
        strap_values = curve.get('strap_submitted_tension_n', [])
        if len(strap_times) != 1200 or len(strap_values) != 1200:
            raise ValueError(f'{label}: expected 1200 submitted strap-law interval-start samples')
        if any(abs(float(t) - i / 240) > 1e-9 for i, t in enumerate(strap_times)):
            raise ValueError(f'{label}: strap-law time must use 0..1199 interval starts at 240 Hz')
        if not all(math.isfinite(float(v)) and 0 <= float(v) <= 300 for v in strap_values):
            raise ValueError(f'{label}: strap-law output must be finite and within [0, 300] N')
        for body in BODIES:
            steps = summaries[label].get('contacts_by_any_other_body', {}).get('human/LH:' + body, {}).get('positive_steps', [])
            if any(not isinstance(step, int) or step < 1 or step > 1200 for step in steps):
                raise ValueError(f'{label}: invalid positive raw contact step for LH:{body}')
        run = PHASE / 'native' / label
        report = json.loads((run / 'report.json').read_text())
        if report.get('completed') is not True or report.get('physics_steps') != 1200:
            raise ValueError(f'{label}: native run is not a completed 5 s trial')
        capture = json.loads((run / 'capture.json').read_text())
        if capture.get('renderer') != 'Isaac Gym native camera' or capture.get('fps') != 30:
            raise ValueError(f'{label}: unexpected native camera metadata')
        frames = capture.get('frames', [])
        for idx in (0, 150):
            image = (run / 'frames' / 'hands' / f'{idx:05d}.png').resolve()
            if len(frames) <= idx or abs(float(frames[idx].get('time_s', -1)) - idx / 30) > 1e-9:
                raise ValueError(f'{label}: missing native hands frame at {idx / 30:g} s')
            if input_hashes[str(image)] != frames[idx].get('image_sha256', {}).get(str(image)):
                raise ValueError(f'{label}: frame hash does not match native capture record')
    return summaries


def draw_curves(path, analysis, brief):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    ref = analysis['stored_reference_curves']
    for ax, field, title, unit in (
        (axes[0, 0], 'guitar_position_error_mm', 'Guitar position error', 'mm'),
        (axes[0, 1], 'guitar_rotation_error_deg', 'Guitar rotation error', 'degrees'),
    ):
        for label in LABELS:
            curve = analysis['curves'][label]
            ax.plot(curve['time_s'], curve[field], color=COLORS[label], lw=1.5, label=DISPLAY[label])
        ax.plot(ref['time_s'], ref[field], color='#555555', lw=1.4, ls='--',
                label='Stored support-loss reference · not a new run')
        ax.set(title=title, ylabel=unit, xlim=(0, 5))
        ax.set_xlabel('Simulation time (s)')
        ax.grid(True, alpha=.25)
        ax.legend(loc='best', fontsize=8)

    ax = axes[1, 0]
    for label in LABELS:
        curve = analysis['curves'][label]
        ax.plot(curve['strap_submitted_time_s'], curve['strap_submitted_tension_n'],
                color=COLORS[label], lw=1.2, label=DISPLAY[label])
    ax.set(title='Passive strap law output (submitted)', xlabel='Interval start time (s)',
           ylabel='Submitted strap law (N)', xlim=(0, 5))
    ax.grid(True, alpha=.25)
    ax.legend(loc='best', fontsize=8)

    ax = axes[1, 1]
    offsets = (-0.10, 0.10)
    summaries = {row['label']: row for row in analysis['summary']}
    for body_idx, body in enumerate(BODIES):
        for trial_idx, label in enumerate(LABELS):
            group = summaries[label].get('contacts_by_any_other_body', {}).get('human/LH:' + body, {})
            times = [step / 240 for step in group.get('positive_steps', [])]
            ax.scatter(times, [body_idx + offsets[trial_idx]] * len(times), s=8,
                       color=COLORS[label], marker='|', linewidths=1.0)
    ax.set_yticks(range(len(BODIES)), ['LH:' + body for body in BODIES])
    ax.set_ylim(-.5, len(BODIES) - .5)
    ax.set_xlim(0, 5)
    ax.set(title='Body positive raw-lambda records', xlabel='Post-step time (s), step / 240',
           ylabel='Body category')
    ax.grid(axis='x', alpha=.25)
    ax.legend(handles=[plt.Line2D([0], [0], color=COLORS[label], marker='|', linestyle='None', label=DISPLAY[label])
                       for label in LABELS], loc='lower right', fontsize=8)
    fig.suptitle(brief.get('plot_title', 'Three-face half strap slack'))
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
            draw.text((x + 3, y - label_h + 7), f'{MONTAGE_LABELS[label]} · hands · {stamp}', fill='#111111', font=font)
    sheet.save(path, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts_v2')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    outputs = (out_dir / 'three_face_half_strap_slack_curves.png',
               out_dir / 'three_face_half_strap_slack_hands.png')
    manifest = out_dir / 'artifact_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory must be fresh and empty')
    declared = explicit_inputs()
    before = {str(path): sha256(path) for path in declared}
    brief = json.loads((PHASE / 'artifact_brief.json').read_text())
    analysis = json.loads((PHASE / 'analysis.json').read_text())
    validate(analysis, before)
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_curves(outputs[0], analysis, brief)
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
