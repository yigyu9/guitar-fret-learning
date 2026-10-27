#!/usr/bin/env python3
"""Plot saved strap-length comparisons and reuse stored native camera frames."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image
import numpy as np

from plot_palm_side_feedback import overlay


ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASE = RESULTS / 'palm_side_strap_v1'
FACET = RESULTS / 'palm_neck_side_v1/facet_distal_search/search.json'
CONDITIONS = (
    ('current', '현재 길이·0 N law', '#666666'),
    ('taut', '짧은 길이·0 N law', '#1878b8'),
    ('initial_5n', '초기 5 N law', '#e07a24'),
    ('initial_10n', '초기 10 N law', '#25855a'),
)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_curves(out, inputs):
    font = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
    if font.exists():
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    values = {}
    for folder, label, color in CONDITIONS:
        run = PHASE/folder/'short'
        paths = [run/name for name in ('trace.json','normal_tasks.json','contacts.json','report.json')]
        trace, tasks, contacts, report = [read(p) for p in paths]
        if len(trace) != 25 or len(tasks) != 25 or len(contacts) != 24 or not all(report['checks'].values()):
            raise ValueError(f'{folder}: saved run structure/check mismatch')
        time = np.asarray([r['time_s'] for r in trace], dtype=float)
        task = np.asarray(tasks, dtype=float)
        pos = np.asarray([r['position_error_m'] for r in trace], dtype=float)*1000
        rot = np.asarray([r['rotation_error_deg'] for r in trace], dtype=float)
        tension = np.asarray([r['last_applied_tension_n'] for r in trace], dtype=float)
        point = np.linalg.norm(task[:, :3], axis=1)*1000
        if task.shape != (25, 6) or not all(np.isfinite(x).all() for x in (time, task, pos, rot, tension, point)):
            raise ValueError(f'{folder}: nonfinite or malformed saved values')
        if time[0] != 0 or abs(time[-1]-.1)>1e-12 or np.any(np.diff(time)<=0):
            raise ValueError(f'{folder}: unexpected time coverage')
        values[folder] = (time, pos, rot, tension, point, label, color)
        for p in paths:
            inputs[str(p.resolve())] = sha(p)
    panel = (
        ('기타 위치 오차 크기 (mm)', 1),
        ('기타 회전 오차 (°)', 2),
        ('trace PRESTEP applied strap tension field (N)', 3),
        ('손 추적점 오차 크기 (mm)', 4),
    )
    for ax, (title, column) in zip(axes.flat, panel):
        for folder, _, _ in CONDITIONS:
            time, pos, rot, tension, point, label, color = values[folder]
            series = (None, pos, rot, tension, point)[column]
            ax.plot(time, series, color=color, marker='o', ms=2.5, lw=1.6, label=label)
        ax.set_title(title)
        ax.set_xlabel('저장 시각 (s)')
        ax.set_xlim(0, .1)
        ax.grid(True, alpha=.25)
        ax.legend(fontsize=8)
    fig.suptitle('절대 strap rest length 및 초기 tension-law 조건의 저장 비교', y=1.01)
    fig.tight_layout()
    image = out/'palm_side_strap_curves.png'
    fig.savefig(image, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return image


def make_camera(out, inputs):
    directory = PHASE/'native_initial_10n'
    report_path, states_path = directory/'report.json', directory/'states.json'
    report, states = read(report_path), read(states_path)
    if len(states) != 25 or not all(report['checks'].values()):
        raise ValueError('camera capture report/states mismatch')
    local_facet = np.asarray(read(FACET)['palmar_facet_point_local_m'], dtype=float)
    rows = []
    for step, caption in ((0, 'Initial 10 N · t=0'), (24, 'Initial 10 N · t=0.1 s')):
        pair = []
        for view, camera_key in (('front','blue_front'), ('side','blue_side')):
            key = next(k for k, meta in report['images'].items()
                       if f'blue_{view}_' in k and meta['physics_step'] == step)
            meta = report['images'][key]
            image_path = ROOT/key
            if sha(image_path) != meta['sha256']:
                raise ValueError(f'{key}: camera image SHA mismatch')
            pair.append(overlay(image_path, meta, report['camera_specs'][camera_key],
                                states[step], local_facet, f'{caption} · {view}'))
            inputs[str(image_path.resolve())] = sha(image_path)
        rows.append(pair)
    inputs[str(report_path.resolve())] = sha(report_path)
    inputs[str(states_path.resolve())] = sha(states_path)
    inputs[str(FACET.resolve())] = sha(FACET)
    width, height = rows[0][0].size
    if any(image.size != (width,height) for row in rows for image in row):
        raise ValueError('camera images differ in dimensions')
    canvas = Image.new('RGB',(width*2,height*2),(24,24,24))
    for y,row in enumerate(rows):
        for x,image in enumerate(row): canvas.paste(image,(x*width,y*height))
    image=out/'palm_side_strap_camera.png'
    canvas.save(image)
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args()
    out=args.out_dir.resolve()
    if out.exists(): raise FileExistsError(f'output directory already exists: {out}')
    analysis_path=PHASE/'analysis.json'
    analysis=read(analysis_path)
    if len(analysis['checks'])!=10 or not all(analysis['checks'].values()):
        raise ValueError('analysis.json must contain ten passing checks')
    if analysis['counts']!={'native_initializations':9,'physics_steps':124}:
        raise ValueError('unexpected run counts')
    out.mkdir(parents=True)
    inputs={str(analysis_path.resolve()):sha(analysis_path),str(Path(__file__).resolve()):sha(__file__)}
    curves=make_curves(out,inputs)
    camera=make_camera(out,inputs)
    manifest={'producer':str(Path(__file__).resolve()),'producer_sha256':sha(__file__),
              'inputs_sha256':inputs,'outputs_sha256':{curves.name:sha(curves),camera.name:sha(camera)},
              'scope':'Saved trace and existing native camera capture only; no native run or physics step.'}
    (out/'plot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'outputs':manifest['outputs_sha256'],'manifest':str(out/'plot_manifest.json')}))


if __name__=='__main__': main()
