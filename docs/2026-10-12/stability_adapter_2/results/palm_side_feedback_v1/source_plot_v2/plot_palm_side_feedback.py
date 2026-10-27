#!/usr/bin/env python3
"""Plot saved palm-side feedback measurements and saved Gym camera frames."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1'
NECK = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1'
MODES = ('off', 'bias', 'tracking')
COLORS = {'off': '#666666', 'bias': '#e07a24', 'tracking': '#1878b8'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def vec3(obj):
    return np.array([obj['x'], obj['y'], obj['z']], dtype=float)


def quat_rotate(q, point):
    x, y, z, w = q
    v = np.asarray(point, dtype=float)
    qv = np.array([x, y, z], dtype=float)
    return v + 2.0 * np.cross(qv, np.cross(qv, v) + w * v)


def body_pose(state, body_index):
    pose = state['human_body_states'][body_index]['pose']
    p = vec3(pose['p'])
    r = pose['r']
    q = np.array([r['x'], r['y'], r['z'], r['w']], dtype=float)
    return p, q


def local_to_world(state, body_index, local_point):
    p, q = body_pose(state, body_index)
    return p + quat_rotate(q, local_point)


def camera_project(point, camera):
    eye = np.asarray(camera['eye'], dtype=float)
    target = np.asarray(camera['target'], dtype=float)
    forward = target - eye
    forward /= np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rel = np.asarray(point, dtype=float) - eye
    depth = float(np.dot(rel, forward))
    if depth <= 0:
        return None
    width, height = int(camera['width']), int(camera['height'])
    focal = width / (2.0 * math.tan(math.radians(camera['horizontal_fov_deg']) / 2.0))
    px = width / 2.0 + focal * float(np.dot(rel, right)) / depth
    py = height / 2.0 - focal * float(np.dot(rel, up)) / depth
    return px, py


def overlay(image_path, image_meta, camera, state, local_facet, title):
    image = Image.open(image_path).convert('RGBA')
    width, height = image.size
    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, 'RGBA')
    polygon = [camera_project(p, camera) for p in image_meta['target_polygon_W_m']]
    if all(p is not None for p in polygon):
        draw.polygon(polygon, fill=(0, 220, 235, 55), outline=(0, 235, 255, 245), width=4)
    facet_world = local_to_world(state, 18, local_facet)
    facet_xy = camera_project(facet_world, camera)
    if facet_xy:
        x, y = facet_xy
        radius = 11
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(255, 106, 36, 235), outline=(255,255,255,255), width=3)
        draw.text((x+14, y-20), 'source facet · saved pose', fill=(255,255,255,255), stroke_width=2, stroke_fill=(0,0,0,220))
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle((0, 0, width, 38), fill=(0,0,0,180))
    draw.text((12, 7), title, font=font, fill=(255,255,255,255))
    return Image.alpha_composite(image, layer).convert('RGB')


def make_metrics(phase, out):
    analysis = read(phase / 'analysis.json')
    if not all(analysis['checks'].values()) or len(analysis['checks']) != 14:
        raise ValueError('analysis.json must carry 14 passing checks')
    traces, tasks = {}, {}
    for mode in MODES:
        traces[mode] = read(phase / ('native_tracking/trace.json' if mode == 'tracking' else f'short/{mode}/trace.json'))
        tasks[mode] = read(phase / ('native_tracking/tasks.json' if mode == 'tracking' else f'short/{mode}/tasks.json'))
        if len(traces[mode]) != 25 or len(tasks[mode]) != 25:
            raise ValueError(f'{mode}: expected 25 saved states/queries')
        report_path = phase / ('native_tracking/report.json' if mode == 'tracking' else f'short/{mode}/report.json')
        report = read(report_path)
        if not all(report['checks'].values()):
            raise ValueError(f'{mode}: report check is false')
    t = np.array([x['time_s'] for x in traces['tracking']], dtype=float)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    for mode in MODES:
        times = np.array([x['time_s'] for x in traces[mode]], dtype=float)
        point_mm = np.linalg.norm(np.asarray(tasks[mode], dtype=float)[:, :3], axis=1) * 1000.0
        guitar_mm = np.array([x['position_error_m'] for x in traces[mode]]) * 1000.0
        guitar_deg = np.array([x['rotation_error_deg'] for x in traces[mode]])
        axes[0].plot(times, point_mm, color=COLORS[mode], label=mode)
        axes[1].plot(times, guitar_mm, color=COLORS[mode], label=mode)
        axes[2].plot(times, guitar_deg, color=COLORS[mode], label=mode)
    axes[0].set_title('LH palm task-point error')
    axes[0].set_ylabel('distance to live target (mm)')
    axes[1].set_title('Guitar position error')
    axes[1].set_ylabel('position error (mm)')
    axes[2].set_title('Guitar orientation error')
    axes[2].set_ylabel('orientation error (deg)')
    for ax in axes:
        ax.set_xlabel('saved time (s)')
        ax.grid(True, alpha=.25)
        ax.legend(title='condition')
    fig.suptitle('Saved PhysX measurements; guitar curves overlap where raw values match', y=1.02)
    fig.tight_layout()
    path = out / 'palm_side_feedback_metrics.png'
    fig.savefig(path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return path


def make_camera(phase, out):
    native = phase / 'native_tracking'
    report = read(native / 'report.json')
    states = read(native / 'states.json')
    facet_data = read(NECK / 'facet_distal_search/search.json')
    local_facet = np.asarray(facet_data['palmar_facet_point_local_m'], dtype=float)
    short = NECK / 'facet_native_short'
    short_probe = read(short / 'probe.json')
    panels = []
    specifications = [
        ('prior fixed-target · 0.1 s', short, short_probe, 24),
        ('tracking initial · 0 s', native, report, 0),
        ('tracking · 0.1 s', native, report, 24),
    ]
    for label, directory, probe, step in specifications:
        state = probe['states'][step] if directory != native else states[step]
        row = []
        for cam_name, cam_key in [('front', 'blue_front'), ('side', 'blue_side')]:
            camera = probe['camera_specs'][cam_key]
            key = next(k for k, v in probe['images'].items() if f'blue_{cam_name}_' in k and v['physics_step'] == step)
            image_meta = probe['images'][key]
            image_path = ROOT / key
            panel = overlay(image_path, image_meta, camera, state, local_facet,
                            f'{label} · {cam_name} camera')
            row.append(panel)
        panels.append(row)
    w, h = panels[0][0].size
    canvas = Image.new('RGB', (2*w, len(panels)*h), (24,24,24))
    for i, row in enumerate(panels):
        for j, panel in enumerate(row):
            canvas.paste(panel, (j*w, i*h))
    path = out / 'palm_side_feedback_camera_comparison.png'
    canvas.save(path)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=Path, default=PHASE)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    phase = args.phase.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    outputs = [make_metrics(phase, out), make_camera(phase, out)]
    inputs = [phase/'analysis.json', phase/'calibration_provenance.json', phase/'controller_checks.json',
              phase/'native_tracking/report.json', phase/'native_tracking/states.json', phase/'native_tracking/trace.json',
              phase/'native_tracking/tasks.json', phase/'native_tracking/contacts.json', phase/'native_tracking/controls.json',
              NECK/'facet_distal_search/search.json', NECK/'facet_native_short/probe.json']
    for mode in ('off','bias'):
        inputs += [phase/f'short/{mode}/{name}.json' for name in ('report','states','trace','tasks','controls','contacts')]
    for directory in (phase/'native_tracking', NECK/'facet_native_short'):
        inputs += sorted(directory.glob('*.png'))
    manifest = {'producer':str(Path(__file__).resolve()), 'producer_sha256':sha(__file__),
                'inputs':{str(p):sha(p) for p in inputs},
                'outputs':{p.name:sha(p) for p in outputs},
                'source_scope':'Read-only plotting of saved JSON and native Gym camera PNGs; no simulation or camera capture.'}
    (out/'plot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'outputs':[str(p) for p in outputs], 'manifest':str(out/'plot_manifest.json')}))


if __name__ == '__main__':
    main()
