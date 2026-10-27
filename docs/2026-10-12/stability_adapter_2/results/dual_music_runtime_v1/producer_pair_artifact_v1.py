"""Create a saved-frame montage for the dual checkpoint pair diagnostic."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1'
PAIR = PHASE / 'pair100_v4'
OUTPUT = PHASE / 'pair_montage_v1.png'
MANIFEST = PHASE / 'pair_artifact_manifest_v1.json'
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
VIEWS = ('whole_body', 'hands')
FRAME_INDICES = (0, 60, 116)
FRAME_EXPECTED = {
    0: (0, 0.0),
    60: (480, 2.0),
    116: (924, 3.85),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_inputs():
    paths = [
        Path(__file__).resolve(), FONT_PATH,
        PHASE / 'execution_summary_v1.json',
        PHASE / 'preload_analysis_v2.json',
        PHASE / 'pair_analysis_v1.json',
        PHASE / 'early_attempts.json',
        PHASE / 'preload_artifact_note_v2.md',
        PHASE / 'preload_comparison_v2.png',
        PHASE / 'preload_curves_v2.png',
        PAIR / 'initial_values.json', PAIR / 'report.json',
        PAIR / 'source_contract.json', PAIR / 'controls.json',
        PAIR / 'trace.json', PAIR / 'music_physics_samples.json',
        PAIR / 'joint_crossings.json', PAIR / 'joint_events.json',
        PAIR / 'media' / 'capture.json', PAIR / 'media' / 'videos.json',
        PAIR / 'media' / 'hands.mp4', PAIR / 'media' / 'whole_body.mp4',
    ]
    for index in FRAME_INDICES:
        for view in VIEWS:
            paths.append(PAIR / 'media' / 'frames' / view / f'{index:05d}.png')
    resolved = [path.resolve() for path in paths]
    if len(resolved) != len(set(resolved)) or any(not path.is_file() for path in resolved):
        raise FileNotFoundError('a declared native, analysis, preload artifact, or font input is missing')
    return resolved


def validate_inputs(hashes):
    execution = json.loads((PHASE / 'execution_summary_v1.json').read_text())
    preload = json.loads((PHASE / 'preload_analysis_v2.json').read_text())
    pair = json.loads((PHASE / 'pair_analysis_v1.json').read_text())
    report = json.loads((PAIR / 'report.json').read_text())
    source = json.loads((PAIR / 'source_contract.json').read_text())
    capture = json.loads((PAIR / 'media' / 'capture.json').read_text())
    videos = json.loads((PAIR / 'media' / 'videos.json').read_text())

    if execution.get('new_native_runs') != 3 or execution.get('total_new_physics_steps') != 3324:
        raise ValueError('execution summary does not match the approved run accounting')
    if preload.get('selected_condition') != 'preload100' or preload.get('selected_factor') != 1.0:
        raise ValueError('preload analysis no longer selects factor 1.0')
    selected = preload['conditions']['preload100']
    if selected['position_box_outside_samples'] != 0 or selected['position_box_max_outside_norm_mm'] != 0.0:
        raise ValueError('selected preload condition does not meet the stated position-box diagnostic')
    if preload.get('stability_success') is not False or preload.get('training_ready') is not False:
        raise ValueError('preload analysis status changed')
    expected_pair = {
        'control_steps': 231,
        'physics_steps': 924,
        'preparation_seconds': 2.0,
        'PLAY_seconds': 1.85,
        'actor_ticks': 111,
        'dimension': 1299,
        'guitar_max_displacement_from_initial_mm': 403.60520447989126,
        'guitar_max_rotation_from_initial_deg': 63.99228587715886,
    }
    for key, value in expected_pair.items():
        if pair.get(key) != value:
            raise ValueError(f'pair analysis field {key} differs from approved result')
    if pair.get('first_terminal') != 'Fret wrist_safety_termination; native G-local wrist X bound; not joint angular limit':
        raise ValueError('pair first terminal reason changed')
    if pair.get('terminal_wrist_position_G_m', [None])[0] != 0.34882652759552:
        raise ValueError('terminal G-local wrist X differs from approved result')
    if pair.get('joint_successes') != 0 or pair.get('joint_crossings') != 1:
        raise ValueError('pair joint-event summary changed')
    if pair.get('source_Strike_per_control_boolean_counts', {}).get('physical_target_hit') != 0:
        raise ValueError('Strike source hit count changed')
    if report.get('completed') is not True or report.get('physics_steps') != 924 or report.get('stop_reason') != 'first_source_terminal':
        raise ValueError('native pair report is not the expected early-terminated diagnostic')
    if source.get('Fret_checkpoint', '').endswith('fret_035000.pt') is False or source.get('Strike_checkpoint', '').endswith('strike_010000.pt') is False:
        raise ValueError('pair source checkpoints differ from the approved pair')
    if source.get('dwell_s') != 0.1 or source.get('detector_rearm_physics_frames') != 8:
        raise ValueError('pair detector settings differ from the approved diagnostic')
    if capture.get('renderer') != 'Isaac Gym native camera' or capture.get('fps') != 30:
        raise ValueError('unexpected native camera metadata')
    frames = capture.get('frames', [])
    for index in FRAME_INDICES:
        expected_step, expected_time = FRAME_EXPECTED[index]
        if index >= len(frames):
            raise ValueError(f'missing native capture frame {index}')
        record = frames[index]
        if record.get('physics_step') != expected_step or abs(float(record.get('time_s', -1)) - expected_time) > 1e-9:
            raise ValueError(f'frame {index} time/step does not match the approved selection')
        for view in VIEWS:
            frame_path = (PAIR / 'media' / 'frames' / view / f'{index:05d}.png').resolve()
            if hashes[str(frame_path)] != record.get('image_sha256', {}).get(str(frame_path)):
                raise ValueError(f'{view} frame {index} hash differs from capture metadata')
    for view in VIEWS:
        video = videos[view]
        if video.get('stream', {}).get('nb_read_frames') != '117' or video.get('stream', {}).get('duration') != '3.900000':
            raise ValueError(f'{view} video metadata differs from the native capture')
    return pair, selected


def build_montage(path):
    from PIL import Image, ImageDraw, ImageFont

    font_path = str(FONT_PATH)
    title_font = ImageFont.truetype(font_path, 24)
    label_font = ImageFont.truetype(font_path, 19)
    cell_w, cell_h = 635, 357
    margin, gap, title_h, column_h, row_h, row_gap = 20, 18, 48, 32, 32, 14
    width = margin * 2 + cell_w * 2 + gap
    height = margin * 2 + title_h + column_h + 3 * (row_h + cell_h + row_gap)
    sheet = Image.new('RGB', (width, height), '#f3f5f8')
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin + 5), '동시 Fret + Strike native pair · 실제 camera frame',
              font=title_font, fill='#172033')
    y = margin + title_h
    for col, view in enumerate(VIEWS):
        x = margin + col * (cell_w + gap)
        label = 'Whole body · 전신' if view == 'whole_body' else 'Hands · 양손'
        draw.text((x + 4, y + 5), label, font=label_font, fill='#26344a')
    y += column_h
    for index in FRAME_INDICES:
        step, time_s = FRAME_EXPECTED[index]
        time_label = f't={time_s:.2f} s · physics step {step}'
        draw.text((margin + 4, y + 4), time_label, font=label_font, fill='#26344a')
        y += row_h
        for col, view in enumerate(VIEWS):
            x = margin + col * (cell_w + gap)
            source = PAIR / 'media' / 'frames' / view / f'{index:05d}.png'
            with Image.open(source) as original:
                image = original.convert('RGB')
                if image.size != (1280, 720):
                    raise ValueError(f'unexpected native frame dimensions: {source} {image.size}')
                resampling = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
                image = image.resize((cell_w, cell_h), resampling)
            sheet.paste(image, (x, y))
            draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline='#c8ced8', width=1)
        y += cell_h + row_gap
    sheet.save(path, format='PNG', optimize=True)


def main():
    if OUTPUT.exists() or MANIFEST.exists():
        raise FileExistsError('pair montage v1 outputs must not overwrite existing files')
    inputs = explicit_inputs()
    before = {str(path): sha256(path) for path in inputs}
    pair, selected = validate_inputs(before)
    build_montage(OUTPUT)
    after = {str(path): sha256(path) for path in inputs}
    if before != after:
        OUTPUT.unlink(missing_ok=True)
        raise RuntimeError('a declared input changed during montage generation')
    manifest_value = {
        'producer_sha256': sha256(__file__),
        'inputs_sha256_before': before,
        'inputs_sha256_after': after,
        'outputs_sha256': {str(OUTPUT.resolve()): sha256(OUTPUT)},
        'native_calls': 0,
        'physics_steps': 0,
        'selected_frame_indices': list(FRAME_INDICES),
        'selected_frame_physics_steps': [FRAME_EXPECTED[i][0] for i in FRAME_INDICES],
        'selected_preload_condition': 'preload100',
        'pair_physics_steps': pair['physics_steps'],
        'preload_position_box_outside_samples': selected['position_box_outside_samples'],
    }
    MANIFEST.write_text(json.dumps(manifest_value, indent=2, allow_nan=False) + '\n')
    print(str(OUTPUT))
    print(str(MANIFEST))


if __name__ == '__main__':
    main()
