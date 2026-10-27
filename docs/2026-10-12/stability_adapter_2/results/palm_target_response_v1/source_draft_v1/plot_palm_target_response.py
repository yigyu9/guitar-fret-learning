#!/usr/bin/env python3
"""Plot saved 0.5 s target/response windows; never runs physics."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

MODES = ('PI', 'RATE_PI', 'PALM_RATE')
COLORS = {'PI': '#4c78a8', 'RATE_PI': '#f58518', 'PALM_RATE': '#54a24b'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    response_path = args.results_dir / 'response.json'
    out_dir = args.out_dir
    if not response_path.is_file():
        raise FileNotFoundError(response_path)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError('preserve existing artifact outputs: ' + str(out_dir))

    data = json.loads(response_path.read_text())
    checks = data.get('checks', {})
    expected = {
        'saved_contracts_and_sources_current', 'previous_frozen_copies_preserved',
        'three_aligned_30_window_series', 'four_step_delivered_targets_held',
        'initial_world_source_goal_held', 'PALM_calculated_static_residuals_match',
    }
    if set(checks) != expected or not all(checks.values()):
        raise ValueError('response contract checks are absent or failed')
    if set(data.get('series', {})) != set(MODES):
        raise ValueError('expected PI, RATE_PI, PALM_RATE series')
    source_hashes = data.get('input_sha256', {})
    if len(source_hashes) != 154:
        raise ValueError('expected 154 consumed input SHA records')
    if not all(Path(path).is_file() and sha(path) == digest for path, digest in source_hashes.items()):
        raise ValueError('a consumed input SHA differs')

    fig, axes = plt.subplots(2, 1, figsize=(12.4, 8.0), sharex=True)
    for mode in MODES:
        rows = data['series'][mode]
        if len(rows) != 30:
            raise ValueError(mode + ' must contain 30 saved windows')
        times = np.asarray([r['pre_time_s'] for r in rows], dtype=float)
        expected_steps = list(range(0, 120, 4))
        if [r['pre_step'] for r in rows] != expected_steps or any(r['post_step'] != r['pre_step'] + 4 for r in rows):
            raise ValueError(mode + ' window step alignment differs')
        if not np.allclose(times, np.asarray(expected_steps) / 240.0, atol=1e-12, rtol=0):
            raise ValueError(mode + ' pre-step times differ')
        gap = np.asarray([r['left_max_pre_gap_deg'] for r in rows], dtype=float)
        projection = np.asarray([
            np.nan if r['observed_return_direction_projection_mm'] is None
            else float(r['observed_return_direction_projection_mm']) for r in rows
        ])
        if not np.isfinite(gap).all() or not (np.isfinite(projection) | np.isnan(projection)).all():
            raise ValueError(mode + ' contains invalid plotted values')
        if sum(np.isnan(projection)) != 1 or not np.isnan(projection[0]):
            raise ValueError(mode + ' initial undefined projection must remain null')
        axes[0].plot(times, gap, color=COLORS[mode], lw=2, label=mode)
        axes[1].plot(times, projection, color=COLORS[mode], lw=2, marker='o', ms=3, label=mode)

    axes[0].set_title('Delivered target minus actual left-arm coordinates')
    axes[0].set_ylabel('Maximum absolute scalar gap (°)')
    axes[0].grid(True, alpha=.25)
    axes[0].legend(frameon=False, ncol=3)
    axes[1].axhline(0, color='#555555', lw=1, alpha=.8)
    axes[1].set_title('Measured four-step source-center movement projected toward pre-window goal')
    axes[1].set_ylabel('Observed return-direction projection (mm)')
    axes[1].set_xlabel('Window pre-step time (s)')
    axes[1].grid(True, alpha=.25)
    axes[1].legend(frameon=False, ncol=3)
    axes[1].text(.01, .03, 'First window is undefined (null) and omitted; no sign is imposed.',
                 transform=axes[1].transAxes, fontsize=9, color='#444444')
    fig.suptitle('Saved 0.5 s palm target/response audit', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .96))

    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / 'palm_target_response.png'
    fig.savefig(image, dpi=180, bbox_inches='tight')
    plt.close(fig)
    manifest = {
        'purpose': 'saved-data plotting only; no native execution or physics',
        'response_json': {'path': str(response_path.resolve()), 'sha256': sha(response_path)},
        'comparison_checks': checks,
        'input_sha256_count': len(source_hashes),
        'input_sha256': source_hashes,
        'plotter': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
        'outputs': [{'path': str(image.resolve()), 'sha256': sha(image)}],
        'plot_semantics': {
            'panel_1': 'left_max_pre_gap_deg from saved windows; scalar coordinate gap, not physical rotation angle or torque',
            'panel_2': 'observed_return_direction_projection_mm from measured four-step source-center movement; null omitted, signs unmodified',
        },
    }
    (out_dir / 'plot_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'image': str(image), 'sha256': sha(image), 'input_sha256_count': len(source_hashes)}))


if __name__ == '__main__':
    main()
