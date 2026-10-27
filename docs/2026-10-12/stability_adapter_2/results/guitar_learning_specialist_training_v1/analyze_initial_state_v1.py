"""Describe recorded initial geometry without claiming reachability or pressure."""
import gzip
import hashlib
import json
import math
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    roles = {}
    for hand in ('left', 'right'):
        run = PHASE/(hand+'_run_v1')
        contract = json.loads((run/'training_contract.json').read_text())
        rows = []
        for worker in range(4):
            path = run/('worker_%03d'%worker)/'audit_episode_000000/transition_00000000.json.gz'
            with gzip.open(path, 'rt') as stream:
                data = json.load(stream)
            measured = data['info']['physics_measurements'][-1]['music']
            identity, target = next(iter(measured['targets'].items()))
            evidence = target['evidence']
            geometry = measured['geometry'][identity]
            positive = [row for row in evidence['contact_evidence']
                        if row['positive_lambda'] and row['human_body'].startswith('human/LH:')]
            guide = data['info'].get('pick_guide')
            rows.append(dict(worker_id=worker, source=str(path), source_sha256=digest(path),
                physics_step=measured['physics_step'], task_time_s=measured['task_time_s'],
                target=evidence['target'], target_contact_candidate=target['candidate'],
                left_distal_origin_delta_G_m=geometry['delta'],
                left_distal_origin_target_distance_m=evidence['marker_approach_distance_m'],
                pick_delta_to_string_G_m=geometry['pick_delta'],
                positive_LH_contacts=[dict(human_body=e['human_body'], guitar_body=e['guitar_body'],
                    nearest_physical_string=e['nearest_physical_string'], reason_flags=e['reason_flags']) for e in positive],
                right_guide=guide))
        half = contract['action']['offset_half_range_rad']
        selected = half[:33] if hand == 'left' else half[33:]
        roles[hand] = dict(rows=rows, sigma_normalized_pre_tanh=math.exp(-3),
            one_sigma_unfiltered_target_offsets_rad=[v*math.tanh(math.exp(-3)) for v in selected],
            smoothing_alpha=contract['action']['smoothing_alpha'],
            scope='first post-control sample at task time1/60 s, before press window; observations are not a reachability test')
    target = PHASE/'initial_state_diagnostic_v1.json'
    with target.open('x') as stream:
        json.dump(dict(roles=roles,
            interpretation='Distal origin and pick marker distances are geometric proxies. Positive other-finger contacts establish observation only, not the target skill. No reachable successful trajectory has been established by this analysis.'),
            stream, indent=2)
        stream.write('\n')
    print('Recorded initial geometry and measured other-finger contact evidence for8 worker starts.')


if __name__ == '__main__':
    main()
