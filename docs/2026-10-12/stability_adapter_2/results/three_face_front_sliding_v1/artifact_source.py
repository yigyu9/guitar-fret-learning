"""Visualize six rejected source-only front-finger initial searches."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
BASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASES = [BASE / 'three_face_front_finger_initial_v1', BASE / 'three_face_front_sliding_v1']
OUT = PHASES[1] / 'artifacts'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def main():
    OUT.mkdir(exist_ok=False)
    expected = {str(Path(__file__).resolve()): sha(__file__)}
    data = []
    for phase in PHASES:
        proposal = read(phase / 'proposal.json')
        assert all(proposal['checks'].values()) and len(proposal['rejected']) == 3 and not proposal['rows']
        assert proposal['native_initializations'] == proposal['physics_steps'] == 0
        for p, value in proposal['input_sha256'].items():
            assert p not in expected or expected[p] == value
            expected[p] = value
        for name in ['proposal.json', 'search_execution.json', 'initial_guesses.json', 'interval_data_verification.json', 'root_preflight.json']:
            expected[str(phase / name)] = sha(phase / name)
        data.extend(proposal['rejected'])
    before = {p: sha(p) for p in expected}
    assert before == expected
    colors = ['#347ba6', '#df914d']
    x = np.arange(6)
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    fig.subplots_adjust(left=.08, right=.77, bottom=.17, top=.90, hspace=.28)
    for ax, field, bodies, labels in [(axes[0], 'anchor_goal_error_mm', ['LH:thumb3', 'LH:palm'], ['Thumb point', 'Palm point']),
                                    (axes[1], 'front_goal_error_mm', ['LH:index3', 'LH:middle3'], ['Index point', 'Middle point'])]:
        for k, (body, label, color) in enumerate(zip(bodies, labels, colors)):
            values = np.array([r[field][body] for r in data])
            ax.bar(x + (k - .5) * .35, values, width=.35, color=color, label=label)
            for j, value in enumerate(values):
                ax.text(j + (k - .5) * .35, value + .12, f'{value:.2f}', ha='center', fontsize=8)
        ax.axvline(2.5, color='#777777', linestyle='--', linewidth=1)
        ax.set_ylabel('Source point goal error (mm)')
        ax.grid(axis='y', alpha=.2)
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.set_ylim(0, max(r[field][b] for r in data for b in bodies) * 1.25)
    for j, r in enumerate(data):
        axes[0].text(j, max(r['anchor_goal_error_mm'].values()) + 1., f"crossings: {len(r['source_intersections'])}", ha='center', fontsize=8, color='#812d27')
    axes[0].set_title('Fixed initial front XY (left) / sliding front XY (right): all rejected')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(['half\nfixed', 'near\nfixed', 'linear\nfixed', 'half\nsliding', 'near\nsliding', 'linear\nsliding'])
    fig.suptitle('25-coordinate initial source searches; six rejected candidates', fontsize=14)
    fig.text(.5, .055, 'Seeds differ between batches. Static source measures, not guitar drift or a causal ablation. New Gym trials: 0.', ha='center', fontsize=9)
    comparison = OUT / 'six_source_candidates.png'
    fig.savefig(comparison, dpi=180, bbox_inches='tight'); plt.close(fig)

    chosen = min(data[3:], key=lambda r: max(r['anchor_goal_error_mm'].values()))
    points = dict(chosen['anchor_G_m'], **chosen['front_point_G_m'])
    goals = dict(chosen['anchor_goal_G_m'], **chosen['front_goal_G_m'])
    fig, ax = plt.subplots(figsize=(10, 6.5))
    fig.subplots_adjust(left=.10, right=.74, bottom=.17, top=.88)
    ax.axhline(-8., color='#22658b', linestyle='--', label='Rear neck plane Gz = -8 mm')
    ax.axhline(read(PHASES[1] / 'proposal.json')['front_outer_source_z_G_m'] * 1000,
               color='#61794b', linestyle='--', label='Outer source front plane')
    for body, color in zip(points, ['#684c9a', '#347ba6', '#df914d', '#bd4b4b']):
        point, goal = np.asarray(points[body]) * 1000, np.asarray(goals[body]) * 1000
        label = body.replace('LH:', '')
        ax.plot([point[1], goal[1]], [point[2], goal[2]], color=color, linewidth=1)
        ax.scatter([point[1]], [point[2]], color=color, s=65, label=label + ' source point')
        ax.scatter([goal[1]], [goal[2]], color=color, marker='x', s=70, label=label + ' goal')
    ax.set_xlabel('Gy (mm)'); ax.set_ylabel('Gz (mm)'); ax.grid(alpha=.2)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)
    ax.set_title('Sliding / previous_near: source points and goals in GY-GZ projection')
    fig.text(.5, .04, 'Selected by smallest max(thumb, palm) goal error; still rejected. Points are proxies, not contact features or full hulls.', ha='center', fontsize=8)
    geometry = OUT / 'source_points_Gyz.png'
    fig.savefig(geometry, dpi=180, bbox_inches='tight'); plt.close(fig)
    after = {p: sha(p) for p in expected}
    assert before == after
    manifest = dict(input_sha256_before=before, input_sha256_after=after,
        outputs_sha256={str(p): sha(p) for p in [comparison, geometry]},
        selected_scope='sliding previous_near minimum max(thumb,palm); not admissible',
        source_candidates=6, accepted=0, native_initializations=0, physics_steps=0,
        producer_sha256=sha(__file__), scope='source-only static comparison; independent final review pending tool quota')
    (OUT / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'outputs':list(manifest['outputs_sha256']), 'inputs':len(expected), 'source_candidates':6,'native':0}))

if __name__ == '__main__':
    main()
