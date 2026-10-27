"""Post-hoc different-target contact query; never relabel the training task."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
from guitar_learning.fretting_v1 import measure_sample, FretTarget, FretContract

PHASE = Path(__file__).resolve().parent


def main():
    rows = []
    for worker in range(4):
        folder = PHASE/'left_run_v1'/('worker_%03d'%worker)/'audit_episode_000000'
        initial = json.loads((folder/'initial_values.json').read_text())
        path = folder/'transition_00000000.json.gz'
        with gzip.open(path, 'rt') as stream:
            data = json.load(stream)
        sample = data['info']['native_control']['physics_samples240'][-1]
        kwargs = (sample['native'], initial['human_body_names'], initial['guitar_body_names'], sample['native_contacts'])
        contract = FretContract(minimum_dwell_s=.05)
        original = measure_sample(*kwargs, FretTarget(2, 7, 'ring'), contract)
        alternate = measure_sample(*kwargs, FretTarget(1, 5, 'index'), contract)
        recorded = next(iter(data['info']['physics_measurements'][-1]['music']['targets'].values()))['candidate']
        if original['fretting_contact_candidate'] != recorded:
            raise AssertionError('original target replay mismatch')
        rows.append(dict(worker_id=worker, source=str(path), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            physics_step=sample['native']['physics_step'], original_target=original['target'],
            original_candidate=original['fretting_contact_candidate'],
            alternate_target=alternate['target'], alternate_candidate=alternate['fretting_contact_candidate'],
            alternate_marker_approach=alternate['marker_approach'],
            alternate_distal_origin_distance_m=alternate['marker_approach_distance_m'],
            alternate_valid_evidence_ids=alternate['valid_evidence_ids'],
            alternate_valid_bodies=alternate['valid_contact_finger_bodies']))
    result = dict(original_target_replay_matches=True, alternative_positive_sample_count=sum(row['alternate_candidate'] for row in rows),
        rows=rows, scope='same native state queried with another target offline; single-sample positive control only, not original-target success,50ms dwell,pressure or full sensor calibration')
    with (PHASE/'contact_positive_control_v1.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(alternative_positive_sample_count=result['alternative_positive_sample_count'], samples=len(rows))))


if __name__ == '__main__':
    main()
