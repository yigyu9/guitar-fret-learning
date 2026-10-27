"""Plot saved five-second palm-stiffness trials and compose recorded camera frames."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1'
LABELS = ('kp_1', 'kp_1p5', 'kp_2')
DISPLAY = {'kp_1': 'kp 1×, kd 1×', 'kp_1p5': 'kp 1.5×, kd 1×', 'kp_2': 'kp 2×, kd 1×'}
COLORS = {'kp_1': '#444444', 'kp_1p5': '#2878b5', 'kp_2': '#d17c18'}
ANALYSIS = PHASE / 'analysis.json'


def sha256(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [
        Path(__file__).resolve(), ANALYSIS,
        ROOT / 'stability_adapter_2/analyze_palm_stiffness_only.py',
        ROOT / 'stability_adapter_2/run_recorded_trial.py',
        ROOT / 'stability_adapter_2/gym_trial_recording.py',
        ROOT / 'stability_adapter_2/capture_isaac_gym_initial.py',
        ROOT / 'stability_adapter_2/FIVE_SECOND_RECORDING_PLAN.md',
        ROOT / 'stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md',
    ]
    for label in LABELS:
        run = PHASE / label
        paths.append(run / 'capture.json')
        paths.append(run / 'controls.jsonl')
        paths.extend(run / 'frames' / camera / f'{frame:05d}.png'
                      for camera in ('whole_body', 'hands') for frame in (0, 150))
    paths = [p.resolve() for p in paths]
    if len(paths) != len(set(paths)) or any(not p.is_file() for p in paths):
        raise FileNotFoundError('declared analysis/source/capture/frame input missing or duplicated')
    return paths


def read_saved_inputs(input_hashes):
    analysis = json.loads(ANALYSIS.read_text())
    checks = analysis.get('checks', {})
    if not checks or not all(checks.values()):
        raise ValueError('analysis.json contains a failed check')
    if analysis.get('counts') != {'native_initializations': 3, 'physics_steps': 3600}:
        raise ValueError('unexpected analysis run counts')
    if set(analysis.get('curves', {})) != set(LABELS):
        raise ValueError('unexpected analysis labels')
    if {row.get('label') for row in analysis.get('summary', [])} != set(LABELS):
        raise ValueError('unexpected summary labels')

    camera_data = {}
    reference_targets = None
    for label in LABELS:
        cap_path = PHASE / label / 'capture.json'
        capture = json.loads(cap_path.read_text())
        controls_path = PHASE / label / 'controls.jsonl'
        controls = [json.loads(line) for line in controls_path.read_text().splitlines()]
        if len(controls) != 1200 or any(row.get('physics_step') != i
                                        for i, row in enumerate(controls, 1)):
            raise ValueError(f'{label}: expected ordered 1200-step controls')
        targets = [row['final_target_rad'] for row in controls]
        if any(target != targets[0] for target in targets[1:]):
            raise ValueError(f'{label}: submitted target is not constant')
        if reference_targets is None:
            reference_targets = targets[0]
        if any(target != reference_targets for target in targets):
            raise ValueError(f'{label}: submitted targets differ across conditions')
        if capture.get('renderer') != 'Isaac Gym native camera' or capture.get('graphics_device_id') != 0:
            raise ValueError(f'{label}: capture is not the expected Gym camera record')
        frames = capture.get('frames', [])
        if len(frames) != 151:
            raise ValueError(f'{label}: expected 151 actual camera frames')
        for idx in (0, 150):
            record = frames[idx]
            if (record.get('physics_step') != idx * 8
                    or abs(float(record.get('time_s', -1)) - idx / 30) > 1e-9
                    or record.get('render_preserves_states') is not True):
                raise ValueError(f'{label}: selected frame timing/state audit mismatch')
            for camera in ('whole_body', 'hands'):
                image = (PHASE / label / 'frames' / camera / f'{idx:05d}.png').resolve()
                expected = record.get('image_sha256', {}).get(str(image))
                if expected is None or expected != input_hashes[str(image)]:
                    raise ValueError(f'{label}/{camera}/{idx}: image SHA differs from capture record')
        camera_data[label] = capture

    curves = analysis['curves']
    for label in LABELS:
        curve = curves[label]
        times = [float(t) for t in curve.get('time_s', [])]
        if len(times) != 1201 or any(abs(t - i / 240) > 1e-9 for i, t in enumerate(times)):
            raise ValueError(f'{label}: expected continuous 0..5s state curve at 240Hz')
        for key in ('guitar_position_error_mm', 'guitar_rotation_error_deg', 'source_normal_gap_mm'):
            values = [float(v) for v in curve.get(key, [])]
            if len(values) != 1201 or not all(math.isfinite(v) for v in values):
                raise ValueError(f'{label}: invalid {key} curve')
    return analysis, camera_data


def draw_curves(path, analysis):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    panels = (
        ('guitar_position_error_mm', '기타 위치 오차 (mm)'),
        ('guitar_rotation_error_deg', '기타 회전 오차 (°)'),
        ('source_normal_gap_mm', 'source 법선 간격 (mm)'),
    )
    for ax, (key, title) in zip(axes, panels):
        for label in LABELS:
            curve = analysis['curves'][label]
            ax.plot(curve['time_s'], curve[key], color=COLORS[label], lw=1.5,
                    label=DISPLAY[label])
        ax.set_ylabel(title)
        ax.set_xlim(0, 5)
        ax.grid(True, alpha=.25)
        ax.legend(loc='best')
    axes[-1].set_xlabel('시뮬레이션 시간 (s) · 저장 native trace')
    fig.suptitle('왼팔 stiffness만 변경한 5초 저장 기록', y=.995)
    fig.tight_layout(rect=(0, 0, 1, .98))
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
    for row, camera in enumerate(('whole_body', 'hands')):
        for col, label in enumerate(LABELS):
            frame_idx = 0 if row == 0 else 150
            source = PHASE / label / 'frames' / camera / f'{frame_idx:05d}.png'
            image = Image.open(source).convert('RGB')
            if image.size != (1280, 720):
                raise ValueError(f'{source}: unexpected camera dimensions')
            image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            x = margin + col * (cell_w + gap)
            y = margin + label_h + row * (cell_h + label_h + gap)
            sheet.paste(image, (x, y))
            view = '전신' if camera == 'whole_body' else '손 근접'
            time = 't=0.0 s · step 0' if frame_idx == 0 else 't=5.0 s · step 1200'
            draw.text((x + 3, y - label_h + 7), f'{label} · {view} · {time}', fill='#111111', font=font)
    sheet.save(path, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=PHASE / 'artifacts')
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    curves_path = out_dir / 'palm_stiffness_only_curves.png'
    camera_path = out_dir / 'palm_stiffness_only_camera.png'
    manifest_path = out_dir / 'artifact_manifest.json'
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('output directory must be fresh and empty')
    declared = explicit_inputs()
    before = {str(p): sha256(p) for p in declared}
    analysis, _ = read_saved_inputs(before)
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_curves(curves_path, analysis)
    draw_camera_sheet(camera_path)
    after = {str(p): sha256(p) for p in declared}
    if before != after:
        raise RuntimeError('an input changed during artifact generation')
    manifest_path.write_text(json.dumps({
        'input_sha256': before,
        'producer_sha256': sha256(__file__),
        'output_sha256': {str(p): sha256(p) for p in (curves_path, camera_path)},
        'selected_camera_frames': [
            {'label': label, 'camera': camera, 'time_s': t, 'physics_step': int(t * 240)}
            for label in LABELS for camera in ('whole_body', 'hands') for t in (0.0, 5.0)
        ],
    }, indent=2) + '\n')
    print(curves_path)
    print(camera_path)
    print(manifest_path)


if __name__ == '__main__':
    main()
