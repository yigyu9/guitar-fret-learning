"""압현 진단 원값을 보존하고 접촉·음길이·손목 오차를 CPU 그림으로 비교한다."""
import argparse
import hashlib
import json
import os
from pathlib import Path


FINGERS = {1: 'Index', 2: 'Middle', 3: 'Ring', 4: 'Pinky'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(root):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    source = root.parent/'analysis/analysis.json'
    data = json.loads(source.read_text(encoding='utf-8'))
    records = data['records']
    if not records:
        raise ValueError('No physical replay records available')
    verified_path = root/'verified_successes.json'
    verified = json.loads(verified_path.read_text(encoding='utf-8')) if verified_path.exists() else None
    verified_keys = {(item['mode'], item['row']) for item in verified['successes']} if verified else set()
    settings = {item['name']: item['settings'] for item in data['conditions']}
    conditions = sorted({r['condition'] for r in records},
        key=lambda name: (settings[name]['guitar_mode'] != 'free', name[:-7] if name.endswith('_repeat') else name, name.endswith('_repeat')))
    goals = sorted({r['row'] for r in records})
    cells = {(r['condition'], r['row']): r for r in records}
    if len(cells) != len(records):
        raise ValueError('Duplicate condition/goal records')
    if any((mode, row) not in cells for mode in conditions for row in goals):
        raise ValueError('Incomplete goal matrix; do not silently fill missing physical trials')
    labels = [('%s | %s | %s'%('FREE' if settings[name]['guitar_mode'] == 'free' else 'FIXED',
        name[:-7] if name.endswith('_repeat') else name, 'repeat' if name.endswith('_repeat') else 'first')) for name in conditions]
    rows = {goal: next(r for r in records if r['row'] == goal) for goal in goals}
    target_labels = ['%s S%d/F%d'%(FINGERS[rows[g]['finger']][0], rows[g]['physical_string'], rows[g]['fret']) for g in goals]
    stars = np.array([[(mode, row) in verified_keys or (mode.endswith('_repeat') and (mode[:-7], row) in verified_keys)
        for row in goals] for mode in conditions])

    def matrix(key):
        return np.array([[key(cells[(mode, row)]) for row in goals] for mode in conditions], dtype=float)

    contact = matrix(lambda r: r['best_contact_streak_s'])
    ratio = matrix(lambda r: r['best_contact_streak_s']/r['required_clean_s'])
    wrist = matrix(lambda r: r['wrist']['late_hold']['final_goal_live_guitar_position_m']['mean']
                   *1000 if r['wrist']['late_hold']['final_goal_live_guitar_position_m']['mean'] is not None else np.nan)
    if not np.isfinite(contact).all() or not np.isfinite(ratio).all():
        raise ValueError('Invalid contact data')
    out = root.parent/'analysis'
    out.mkdir(parents=True, exist_ok=True)

    def heatmap(axis, values, columns, title, vmax, units, show_verified=False, low_warning=False):
        cmap = plt.get_cmap('viridis').copy()
        cmap.set_bad('#dddddd')
        image = axis.imshow(values, aspect='auto', vmin=0, vmax=max(float(vmax), 1e-9), cmap=cmap)
        axis.set_title(title, fontsize=11)
        axis.set_xticks(range(len(columns)))
        axis.set_xticklabels(columns, rotation=50, ha='right', fontsize=8)
        axis.set_yticks(range(len(conditions)))
        axis.set_yticklabels(labels, fontsize=8)
        for y in range(len(conditions)):
            for x in range(len(columns)):
                value = values[y, x]
                text = 'NA' if not np.isfinite(value) else (('%.3f' if units == 'seconds' else '%.2f')%value)
                if show_verified and stars[y, goals.index(columns[x])]:
                    text += '*'
                warning = low_warning and np.isfinite(value) and value+1e-12 < .1
                axis.text(x, y, text, ha='center', va='center', fontsize=7,
                    color='red' if warning else ('black' if np.isfinite(value) and value > vmax*.6 else 'white'),
                    bbox=dict(facecolor='white', alpha=.85, edgecolor='red', pad=1) if warning else None)
        axis.figure.colorbar(image, ax=axis, label=units, fraction=.035, pad=.02)

    figure, axes = plt.subplots(2, 2, figsize=(15, max(9, len(conditions)*.68)), constrained_layout=True)
    for finger, axis in zip(range(1, 5), axes.flat):
        selected = [g for g in goals if rows[g]['finger'] == finger]
        indices = [goals.index(g) for g in selected]
        heatmap(axis, contact[:, indices], selected, FINGERS[finger]+' continuous diagnostic contact',
            max(float(contact.max()), .1), 'seconds', show_verified=True, low_warning=True)
        axis.set_xticklabels(['S%d / F%d'%(rows[g]['physical_string'], rows[g]['fret']) for g in selected],
                             rotation=0, fontsize=9)
    figure.suptitle('Physical replay contact | red: <100ms | *: two-run verified selection\nStatic diagnostic contact is not timed song achievement', fontsize=13)
    figure.savefig(out/'contact_matrix.png', dpi=150)
    plt.close(figure)

    figure, axes = plt.subplots(3, 1, figsize=(max(14, len(goals)*.85), max(11, len(conditions)*1.25)), constrained_layout=True)
    success = np.array([[sum(cells[(mode, row)]['best_contact_streak_s']+1e-12 >= .1 for row in goals),
                         sum(cells[(mode, row)]['static_streak_meets_note_duration_threshold'] for row in goals)] for mode in conditions])
    y = np.arange(len(conditions))
    axes[0].barh(y-.18, success[:, 0], height=.34, label='>=100ms diagnostic contact')
    axes[0].barh(y+.18, success[:, 1], height=.34, label='Static streak >= source note threshold')
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels, fontsize=8)
    axes[0].set_xlim(0, len(goals))
    axes[0].invert_yaxis()
    axes[0].legend(loc='lower right', fontsize=8)
    axes[0].set_title('Goal counts (static diagnostics; not song achievement)')
    heatmap(axes[1], np.clip(ratio, 0, 1), goals, 'Static contact streak / source note requirement (display capped at1)', 1, 'ratio (capped)')
    heatmap(axes[2], wrist, goals, 'Late hold: mean distance to final wrist goal in live guitar frame | NA: no safe late-hold samples',
        max(float(np.nanmax(wrist)), 1.) if np.isfinite(wrist).any() else 1., 'mm')
    for axis in axes[1:]:
        axis.set_xticklabels(target_labels, rotation=50, ha='right', fontsize=8)
    figure.suptitle('Finger press diagnostic summary | FREE and FIXED results are distinct', fontsize=14)
    figure.savefig(out/'summary.png', dpi=150)
    plt.close(figure)
    # 그림에서는 비율만 잘라 표시하며 아래 JSON에는 모든 원본 값을 보존한다.
    artifact = dict(source=str(source.resolve()), source_sha256=digest(source),
        tool_sha256=digest(Path(__file__)), verified_source_sha256=digest(verified_path) if verified else None,
        condition_order=conditions, goal_order=goals, original_analysis=data, verified_successes=verified,
        rendered_matrices=dict(contact_streak_s=contact.tolist(), original_note_threshold_ratio=ratio.tolist(),
            wrist_late_mean_goal_distance_mm=[[float(v) if np.isfinite(v) else None for v in row] for row in wrist]),
        figures=['contact_matrix.png', 'summary.png'])
    (out/'plot_data.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    plot(args.root.resolve())


if __name__ == '__main__':
    main()
