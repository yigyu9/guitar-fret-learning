#!/usr/bin/env python3
"""Plot saved native target readbacks; never queries or runs the simulator."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

JOINT = 'L_Shoulder_x'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_hashes(mapping, expected_count, label):
    if not isinstance(mapping, dict) or len(mapping) != expected_count:
        raise ValueError(f'{label}: expected {expected_count} SHA records')
    for path, digest in mapping.items():
        p = Path(path)
        if not p.is_file() or sha(p) != digest:
            raise ValueError(f'{label}: input SHA mismatch: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='native_target_readback_v1 result directory')
    parser.add_argument('--out', type=Path, required=True, help='new PNG output path')
    args = parser.parse_args()
    run = args.run.resolve()
    out = args.out.resolve()
    report_path = run / 'report.json'
    readbacks_path = run / 'readbacks.json'
    native_report_path = run / 'native' / 'report.json'
    manifest_path = out.with_name('plot_manifest.json')
    if not all(p.is_file() for p in (report_path, readbacks_path, native_report_path)):
        raise FileNotFoundError('report.json, readbacks.json, and native/report.json are required')
    if out.exists() or manifest_path.exists():
        raise FileExistsError('preserve existing plot output and manifest')

    report = json.loads(report_path.read_text())
    readbacks = json.loads(readbacks_path.read_text())
    native_report = json.loads(native_report_path.read_text())
    expected_checks = {'original_native_contracts_pass', 'seven_prefix_arrays_exact',
                       '48_aligned_reads', 'reads_preserve_states_targets_PD', 'sources_current'}
    if set(report.get('checks', {})) != expected_checks or not all(report['checks'].values()):
        raise ValueError('readback report checks are missing or failed')
    if len(report.get('input_sha256', {})) != 180:
        raise ValueError('expected 180 report input SHA records')
    verify_hashes(report['input_sha256'], 180, 'readback report')
    if len(readbacks) != 48:
        raise ValueError('expected 48 native getter records')
    if len(native_report.get('checks', {})) != 13 or not all(native_report['checks'].values()):
        raise ValueError('native report contract checks are missing or failed')
    if native_report.get('native_physics_steps') != 24:
        raise ValueError('expected the saved 24-step run')
    if len(report.get('human_joint_names', [])) != 105 or report['human_joint_names'].count(JOINT) != 1:
        raise ValueError('105 named native axes including selected shoulder are required')
    joint_index = report['human_joint_names'].index(JOINT)

    times, phases, submitted, stored, maxdiff = [], [], [], [], []
    for i, row in enumerate(readbacks):
        step = i // 2
        expected_phase = 'before_step' if i % 2 == 0 else 'after_step'
        expected_physics_step = step if expected_phase == 'before_step' else step + 1
        if row.get('physics_step') != expected_physics_step or row.get('phase') != expected_phase:
            raise ValueError('getter row order/phase differs')
        q = np.asarray(row.get('submitted_targets_rad'), dtype=float)
        native = np.asarray(row.get('native_stored_targets_rad'), dtype=float)
        if q.shape != (105,) or native.shape != (105,) or not np.isfinite(q).all() or not np.isfinite(native).all():
            raise ValueError('each saved getter row must contain 105 finite float values')
        diff = np.abs(native - q)
        # This is an observation consistency check, not a zero-difference gate.
        times.append(expected_physics_step / 240.0)
        phases.append(expected_phase)
        submitted.append(q[joint_index])
        stored.append(native[joint_index])
        maxdiff.append(float(diff.max()))

    derived_max = max(maxdiff)
    recorded_max = float(report['max_stored_submitted_difference_rad'])
    if not np.isfinite(recorded_max) or not np.isclose(derived_max, recorded_max, atol=1e-12, rtol=0):
        raise ValueError('raw-derived max difference does not match the report observation')

    times = np.asarray(times)
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.8), sharex=True)
    axes[0].plot(times, submitted, color='#4c78a8', lw=1.8, marker='o', ms=3,
                 label='Submitted target (solid circles)')
    axes[0].plot(times, stored, color='#f58518', lw=1.5, ls='--', marker='s', ms=3,
                 mfc='none', label='Native stored target (dashed open squares)')
    axes[0].set_title(JOINT + ': submitted and native-stored target')
    axes[0].set_ylabel('Target coordinate (rad)')
    axes[0].text(.02, .03, '48 actual getter reads; overlapping curves indicate observed equality.',
                 transform=axes[0].transAxes, fontsize=9, color='#444444')

    axes[1].plot(times, maxdiff, color='#54a24b', lw=1.8, marker='o', ms=3)
    axes[1].set_title('Maximum difference across 105 native axes')
    axes[1].set_ylabel('Max absolute submitted–stored difference (rad)')
    axes[1].set_ylim(-0.005, 0.05)
    axes[1].text(.02, .03, f'Observed max: {derived_max:.1f} rad; no synthetic t=0 values.',
                 transform=axes[1].transAxes, fontsize=9, color='#444444')
    for ax in axes:
        ax.set_xlabel('Getter sample time (s); before/after reads retained in sequence')
        ax.set_xlim(-.005, .105)
        ax.grid(True, alpha=.25)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle('Saved native target readback, 24-step observation', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .94))

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches='tight')
    plt.close(fig)
    manifest = {
        'purpose': 'saved readback plotting only; no getter calls or simulator execution',
        'report': {'path': str(report_path), 'sha256': sha(report_path), 'input_sha256_count': len(report['input_sha256'])},
        'readbacks': {'path': str(readbacks_path), 'sha256': sha(readbacks_path), 'rows': len(readbacks), 'axes_per_row': 105},
        'native_report': {'path': str(native_report_path), 'sha256': sha(native_report_path), 'checks': native_report['checks']},
        'report_checks': report['checks'],
        'input_sha256': report['input_sha256'],
        'plotter': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
        'selected_joint': JOINT,
        'getter_observation': {'reads': 48, 'per_read_axes': 105, 'derived_max_abs_difference_rad': derived_max,
                               'report_max_abs_difference_rad': recorded_max, 'exact_equality_is_observation_not_gate': True},
        'outputs': {'image': {'path': str(out), 'sha256': sha(out)}},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'image': str(out), 'sha256': sha(out), 'readback_rows': len(readbacks),
                      'input_sha256_count': len(report['input_sha256']), 'observed_max_difference_rad': derived_max}))


if __name__ == '__main__':
    main()
