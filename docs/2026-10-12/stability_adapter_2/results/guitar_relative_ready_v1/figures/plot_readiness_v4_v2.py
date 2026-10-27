#!/usr/bin/env python3
"""Plot the saved v4 preparation distances and sampled readiness conditions."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parents[1]
SUMMARY = PHASE / 'analysis' / 'summary.json'
CONTROLS = PHASE / 'native_v4' / 'data' / 'controls.json'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)

    inputs = [Path(__file__).resolve(), SUMMARY.resolve(), CONTROLS.resolve()]
    before = {str(path): sha256(path) for path in inputs}
    summary = json.loads(SUMMARY.read_text())
    rows = json.loads(CONTROLS.read_text())
    v4 = summary['native_v4']
    if len(rows) != 300 or v4['control_samples'] != len(rows):
        raise ValueError('v4 control coverage mismatch')
    times = [float(row['time_s']) for row in rows]
    distances = [float(row['readiness']['pick_to_ready_m']) * 1000 for row in rows]
    conditions = [row['readiness']['conditions'] for row in rows]
    ready = [bool(row['readiness']['ready_now']) for row in rows]
    fields = [
        ('left_palm_under_neck_contact', 'LH palm / underside'),
        ('left_finger_neck_contact', 'LH finger / neck'),
        ('right_near_strike', 'RH within external 50 mm'),
        ('ready_now', 'Full preparation predicate'),
    ]
    for t, d, row_conditions, full_ready in zip(times, distances, conditions, ready):
        values = [t, d, *[float(bool(row_conditions[key])) for key, _ in fields[:3]], float(full_ready)]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('non-finite saved readiness sample')
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('control times must be strictly increasing')
    if times[0] != 0.0 or times[-1] >= 5.0:
        raise ValueError('unexpected v4 control time coverage')

    fig, (ax_dist, ax_cond) = plt.subplots(
        2, 1, figsize=(12.5, 7.8), sharex=True,
        gridspec_kw={'height_ratios': [1.5, 1.15]}, constrained_layout=True)
    ax_dist.plot(times, distances, color='#2468b4', linewidth=2.1,
                 label='RH pick → current-G ready point')
    ax_dist.axhline(50, color='#b33b30', linestyle='--', linewidth=1.6,
                    label='External proximity gate: 50 mm')
    ax_dist.axhline(10, color='#555555', linestyle=':', linewidth=1.5,
                    label='Original READY distance context: 10 mm')
    ax_dist.set_ylabel('Distance (mm)')
    ax_dist.set_title('v4 native preparation samples (300 control frames)')
    ax_dist.grid(True, alpha=.24)
    ax_dist.legend(loc='center left', bbox_to_anchor=(1.01, .5), ncol=1, framealpha=.92)
    ax_dist.text(.99, .96, f"range {min(distances):.3f}–{max(distances):.3f} mm; last {distances[-1]:.3f} mm",
                 transform=ax_dist.transAxes, ha='right', va='top', fontsize=9,
                 bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})

    y_positions = list(range(len(fields)))
    colors = ['#1c9b68', '#d58218', '#7054a4', '#b33b30']
    for y, ((key, label), color) in enumerate(zip(fields, colors)):
        truth = ready if key == 'ready_now' else [bool(c[key]) for c in conditions]
        selected = [t for t, ok in zip(times, truth) if ok]
        if selected:
            ax_cond.scatter(selected, [y] * len(selected), s=17, color=color,
                            marker='|', linewidths=1.2, label=f'{label}: {len(selected)}/300')
        else:
            ax_cond.plot([], [], color=color, marker='|', linestyle='None',
                         label=f'{label}: 0/300')
    ax_cond.set_yticks(y_positions, [label for _, label in fields])
    ax_cond.set_ylim(-.55, len(fields)-.45)
    ax_cond.invert_yaxis()
    ax_cond.set_xlim(0, 5)
    ax_cond.set_xlabel('Native control time (s)')
    ax_cond.set_title('Conditions sampled per control frame; readiness requires all conditions for 6 consecutive frames')
    ax_cond.grid(axis='x', alpha=.24)
    ax_cond.legend(loc='lower center', bbox_to_anchor=(.5, -0.53), ncol=2,
                   frameon=False, fontsize=9)
    fig.suptitle('Current-guitar strike preparation: geometry proximity and contact/readiness evidence', y=1.02)
    output = out / 'readiness_v4.png'
    fig.savefig(output, dpi=180, bbox_inches='tight')
    plt.close(fig)

    after = {str(path): sha256(path) for path in inputs}
    if after != before:
        raise RuntimeError('plot inputs changed while producing figure')
    manifest = {
        'producer': str(Path(__file__).resolve()),
        'producer_sha256': before[str(Path(__file__).resolve())],
        'inputs_sha256': before,
        'outputs_sha256': {str(output): sha256(output)},
        'input_closure_unchanged': after == before,
        'plot_data': 'native_v4/data/controls.json readiness.pick_to_ready_m and readiness.conditions/ready_now; time_s at control samples',
        'sample_count': len(rows),
        'native_initializations_by_plotter': 0,
        'physics_steps_by_plotter': 0,
        'thresholds_mm': {'external_proximity_gate': 50, 'original_ready_context': 10},
        'note': 'Distances and conditions are separately labeled; the external 50 mm gate is not the original 10 mm READY acquisition. The figure is a plot of saved controls, not a native render.'
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(output), 'sha256': sha256(output), 'samples': len(rows)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
