#!/usr/bin/env python3
"""Plot saved half-second strap traces and re-encode saved native camera frames."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from PIL import Image

from plot_palm_side_feedback import overlay

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASE = RESULTS / 'palm_side_strap_long_v1'
FACET = RESULTS / 'palm_neck_side_v1/facet_distal_search/search.json'
CONDITIONS = (
    ('current', '현재 길이·0 N law', '#666666'),
    ('taut', '짧은 길이·0 N law', '#1878b8'),
    ('initial_5n', '초기 5 N law', '#e07a24'),
    ('initial_10n', '초기 10 N law', '#25855a'),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def make_curves(out, inputs):
    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    values = {}
    for folder, label, color in CONDITIONS:
        run = PHASE / folder
        paths = [run / name for name in ('trace.json', 'normal_tasks.json', 'contacts.json', 'report.json')]
        trace, tasks, contacts, report = [read(path) for path in paths]
        if len(trace) != 121 or len(tasks) != 121 or len(contacts) != 120 or not all(report['checks'].values()):
            raise ValueError(f'{folder}: run structure/check mismatch')
        time = np.asarray([row['time_s'] for row in trace], dtype=float)
        position = np.asarray([row['position_error_m'] for row in trace], dtype=float) * 1000
        rotation = np.asarray([row['rotation_error_deg'] for row in trace], dtype=float)
        tension = np.asarray([row['last_applied_tension_n'] for row in trace], dtype=float)
        task = np.asarray(tasks, dtype=float)
        point = np.linalg.norm(task[:, :3], axis=1) * 1000
        if task.shape != (121, 6) or not all(np.isfinite(a).all() for a in (time, position, rotation, tension, task, point)):
            raise ValueError(f'{folder}: malformed or nonfinite data')
        if time[0] != 0 or abs(time[-1] - .5) > 1e-12 or np.any(np.diff(time) <= 0):
            raise ValueError(f'{folder}: unexpected time coverage')
        values[folder] = (time, position, rotation, tension, point, label, color)
        for path in paths:
            inputs[str(path.resolve())] = sha(path)

    panels = (
        ('기타 위치 오차 크기 (mm)', 1),
        ('기타 회전 오차 (°)', 2),
        ('trace PRESTEP applied strap tension field (N)', 3),
        ('손 추적점 오차 크기 (mm)', 4),
    )
    for ax, (title, field) in zip(axes.flat, panels):
        for folder, _, _ in CONDITIONS:
            time, pos, rot, tension, point, label, color = values[folder]
            data = (None, pos, rot, tension, point)[field]
            ax.plot(time, data, color=color, lw=1.5, label=label)
        ax.set_title(title)
        ax.set_xlabel('저장 시각 (s)')
        ax.set_xlim(0, .5)
        ax.grid(True, alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('네 절대 strap rest length·초기 tension-law 조건의 0.5초 저장 비교')
    fig.tight_layout()
    path = out / 'palm_side_strap_long_curves.png'
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return path


def make_camera_and_video(out, inputs):
    directory = PHASE / 'native_current'
    report_path, states_path = directory / 'report.json', directory / 'states.json'
    report, states = read(report_path), read(states_path)
    if len(states) != 121 or len(report['images']) != 62 or not all(report['checks'].values()):
        raise ValueError('camera report/state coverage mismatch')
    local_facet = np.asarray(read(FACET)['palmar_facet_point_local_m'], dtype=float)
    inputs[str(report_path.resolve())] = sha(report_path)
    inputs[str(states_path.resolve())] = sha(states_path)
    inputs[str(FACET.resolve())] = sha(FACET)
    camera_rows = []
    for step in range(0, 121, 4):
        pair = []
        for view, camera_key in (('front', 'blue_front'), ('side', 'blue_side')):
            key, meta = next((k, v) for k, v in report['images'].items()
                             if f'blue_{view}_' in k and v['physics_step'] == step)
            image_path = Path(key)
            if sha(image_path) != meta['sha256']:
                raise ValueError(f'camera image hash mismatch: {image_path}')
            inputs[str(image_path.resolve())] = sha(image_path)
            image = overlay(image_path, meta, report['camera_specs'][camera_key], states[step], local_facet,
                            f'current · step {step} · t={step/240:.3f}s · {view}')
            pair.append(image)
        camera_rows.append(pair)

    w, h = camera_rows[0][0].size
    camera = Image.new('RGB', (2*w, 2*h), (24, 24, 24))
    camera.paste(camera_rows[0][0], (0, 0)); camera.paste(camera_rows[0][1], (w, 0))
    camera.paste(camera_rows[-1][0], (0, h)); camera.paste(camera_rows[-1][1], (w, h))
    camera_path = out / 'palm_side_strap_long_camera.png'
    camera.save(camera_path)

    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise FileNotFoundError('ffmpeg is required to encode saved-frame video')
    commands = []
    outputs = []
    with tempfile.TemporaryDirectory(prefix='palm_side_strap_long_frames_') as tmp:
        frame_dir = Path(tmp)
        for i, pair in enumerate(camera_rows):
            canvas = Image.new('RGB', (w, h*2), (24, 24, 24))
            canvas.paste(pair[0], (0, 0)); canvas.paste(pair[1], (0, h))
            canvas.save(frame_dir / f'frame_{i:03d}.png')
        for name, fps in (('palm_side_strap_long_realtime.mp4', 60), ('palm_side_strap_long_slow.mp4', 6)):
            target = out / name
            cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-framerate', str(fps),
                   '-i', str(frame_dir / 'frame_%03d.png'), '-frames:v', '31', '-c:v', 'libx264',
                   '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            commands.append({'command': cmd, 'returncode': result.returncode, 'stderr': result.stderr})
            if result.returncode:
                raise RuntimeError(result.stderr)
            outputs.append(target)
    return camera_path, outputs, commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        raise FileExistsError(f'output directory already exists: {out}')
    analysis_path = PHASE / 'analysis.json'
    analysis = read(analysis_path)
    if len(analysis['checks']) != 12 or not all(analysis['checks'].values()):
        raise ValueError('analysis checks are incomplete')
    if analysis['counts'] != {'native_initializations': 5, 'physics_steps': 600}:
        raise ValueError('unexpected phase counts')
    out.mkdir(parents=True)
    producer = Path(__file__).resolve()
    helper = Path(overlay.__code__.co_filename).resolve()
    inputs = {str(analysis_path.resolve()): sha(analysis_path), str(producer): sha(producer), str(helper): sha(helper)}
    curves = make_curves(out, inputs)
    camera, videos, ffmpeg_commands = make_camera_and_video(out, inputs)
    before = dict(inputs)
    changed = [path for path, digest in before.items() if sha(path) != digest]
    if changed:
        raise RuntimeError(f'inputs changed during plot: {changed}')
    outputs = [curves, camera, *videos]
    manifest = {'producer': str(producer), 'producer_sha256': sha(producer), 'inputs_sha256': inputs,
                'outputs_sha256': {path.name: sha(path) for path in outputs},
                'scope': 'Saved traces, existing current camera frames, and source overlay only; no native run or physics step.'}
    (out / 'plot_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'ffmpeg_commands.json').write_text(json.dumps(ffmpeg_commands, indent=2) + '\n')
    print(json.dumps({'outputs': manifest['outputs_sha256'], 'inputs': len(inputs),
                      'manifest': str(out / 'plot_manifest.json'), 'ffmpeg_commands': ffmpeg_commands}))


if __name__ == '__main__':
    main()
