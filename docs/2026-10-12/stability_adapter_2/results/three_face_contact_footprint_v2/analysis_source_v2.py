"""Summarize four rejected source candidates and their selected facet directions."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASE = BASE / 'three_face_contact_footprint_v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = PHASE / 'analysis_v2.json'
    if output.exists():
        raise FileExistsError('preserve consumed analysis')
    folders = [BASE / 'three_face_contact_footprint_v1', PHASE]
    # Only explicit source inputs; an active stdout log is an output, not input.
    inputs = [f / name for f in folders for name in
              ('proposal.json', 'search_execution.json', 'search_source.py', 'search.log', 'sensitivity.json')]
    inputs += [folders[0] / 'review.md', PHASE / 'review_v2.md']
    hashes = {str(p): sha(p) for p in inputs}
    hashes[str(Path(__file__).resolve())] = sha(__file__)
    hashes[str(ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md')] = sha(ROOT / 'stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md')
    proposals = [json.loads((f / 'proposal.json').read_text()) for f in folders]
    for proposal in proposals:
        if not all(proposal['checks'].values()) or any(sha(p) != h for p, h in proposal['input_sha256'].items()):
            raise AssertionError('source preparation input closure')
        hashes.update(proposal['input_sha256'])
    import numpy as np
    from scipy.spatial.transform import Rotation
    initial = json.loads((BASE / 'three_face_support_loss_v1/native/saved_finger_targets/initial_values.json').read_text())
    names = initial['human_body_names']
    summary = []
    for folder, proposal in zip(folders, proposals):
        execution = json.loads((folder / 'search_execution.json').read_text())
        if execution['exit_code'] != 0 or proposal['rows'] or len(proposal['rejected']) != 2:
            raise AssertionError('two rejected source candidates; no native execution')
        for row in proposal['rejected']:
            state = row['source_state']
            gq = state['guitar_body_states'][0]['pose']['r']
            gr = Rotation.from_quat([gq[k] for k in 'xyzw'])
            directions = {}
            for body, anchor in proposal['anchors'].items():
                q = state['human_body_states'][names.index(body)]['pose']['r']
                rotation = Rotation.from_quat([q[k] for k in 'xyzw'])
                directions[body] = gr.inv().apply(rotation.apply(anchor['source_normal_local'])).tolist()
            summary.append({'phase': folder.name, 'label': row['label'], 'reasons': row['reasons'],
                'anchor_G_m': row['anchor_G_m'], 'anchor_goal_G_m': row['anchor_goal_G_m'],
                'anchor_goal_error_mm': row['anchor_goal_error_mm'], 'source_facet_outward_G': directions,
                'source_intersections': row['source_intersections'],
                'source_footprint': row.get('source_footprint'),
                'source_hull_to_finite_patch': row.get('source_hull_to_finite_patch')})
    checks = {'four_rejected_source_candidates_no_native': True,
              'facet_direction_transformed_from_source_pose': True,
              'sealed_inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()):
        raise AssertionError(checks)
    output.write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'summary': summary,
        'counts': {'source_candidates': 4, 'native_initializations': 0, 'physics_steps': 0},
        'scope': 'source FK geometry and candidate exclusion, not actual Gym frames or cooked contact; source triangle outward is not an anatomical pad; no stability success'}, indent=2) + '\n')
    print(json.dumps({'checks': checks, 'candidates': len(summary)}, indent=2))


if __name__ == '__main__':
    main()
