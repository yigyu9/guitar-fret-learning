"""Read frozen native physics-foundation runs; never claim musical success."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation
from .environment_contract_v1 import EnvironmentContract


def rotation(state):
    q = state['pose']['r']
    return Rotation.from_quat([q[k] for k in ('x', 'y', 'z', 'w')])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=Path, required=True)
    args = parser.parse_args()
    output = args.phase/'analysis.json'
    if output.exists(): raise FileExistsError('preserve successful analysis')
    layout = json.loads((args.phase/'reference_layout.json').read_text())
    names = layout['human_body_names']
    chest, pelvis = names.index('Chest'), names.index('Pelvis')
    contract = EnvironmentContract()
    paths = [Path(__file__).resolve(), Path(__file__).with_name('environment_contract_v1.py'),
             args.phase/'reference_layout.json', Path(layout['source'])]
    paths += [Path(f) for f in contract.inputs]
    for condition in ('neutral', 'small_motion'):
        folder = args.phase/('native_'+condition+'_v2')
        paths += [folder/f for f in ('initial_values.json','report.json','trace.json','commands.json',
                                    'states.jsonl','observations.jsonl','media/videos.json')]
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    results = {}
    initial_states = []
    for condition in ('neutral', 'small_motion'):
        folder = args.phase/('native_'+condition+'_v2')
        initial = json.loads((folder/'initial_values.json').read_text())
        report = json.loads((folder/'report.json').read_text())
        rows = json.loads((folder/'trace.json').read_text())
        commands = json.loads((folder/'commands.json').read_text())
        if not report['completed'] or len(rows) != 301 or len(commands) != 300:
            raise ValueError('completed 5s/300-control run required')
        initial_states.append(initial['native_initial_state'])
        p = np.array([v['guitar_position_W_m'] for v in rows])
        q = np.array([v['guitar_quaternion_xyzw'] for v in rows])
        q /= np.linalg.norm(q, axis=1)[:,None]
        angle = np.rad2deg(2*np.arccos(np.clip(np.abs(q@q[0]),0,1)))
        joint = np.array([v['q_rad'] for v in rows])
        target = np.r_[contract.q_ref[None,:], np.array([c['final_rad'] for c in commands])]
        low = np.array([-.5,-.15,.65])
        high = np.array([-.15,.15,initial['z_chest_frozen_m']])
        outside = np.maximum(np.maximum(low-p,p-high),0)
        chest_angles = []
        with (folder/'states.jsonl').open() as handle:
            ref = None
            for line in handle:
                bodies = json.loads(line)['human_body_states']
                r = rotation(bodies[pelvis]).inv()*rotation(bodies[chest])
                if ref is None: ref = r
                chest_angles.append(np.rad2deg((r*ref.inv()).magnitude()))
        groups = {}
        for group in ('body','head','arm','finger'):
            indices = [i for i,g in enumerate(contract.groups) if g==group]
            groups[group] = {'actual_max_q_delta_deg': float(np.rad2deg(abs(joint[:,indices]-joint[0,indices]).max())),
                'target_max_delta_rad': float(abs(target[:,indices]-target[0,indices]).max())}
        results[condition] = {'controls': len(commands),'physics_steps':report['physics_steps'],
            'frames_per_view':report['frame_count'],'native_state_matches_reference':initial['initial_state_exact_reference'],
            'guitar_max_displacement_from_initial_mm':float(np.linalg.norm(p-p[0],axis=1).max()*1000),
            'guitar_final_displacement_from_initial_mm':float(np.linalg.norm(p[-1]-p[0])*1000),
            'guitar_max_rotation_from_initial_deg':float(angle.max()),
            'guitar_final_rotation_from_initial_deg':float(angle[-1]),
            'position_box_outside_samples':int(np.any(outside>0,axis=1).sum()),
            'position_box_max_outside_norm_mm':float(np.linalg.norm(outside,axis=1).max()*1000),
            'guitar_z_min_m':float(p[:,2].min()),
            'body_chest_relative_reset_rotation_max_deg':float(max(chest_angles)),
            'groups':groups,'target_rate_pass':bool(np.all(abs(np.diff(target,axis=0))<=contract.rates/60+1e-7)),
            'left_palm_guitar_contact_samples':sum(any('human/LH:palm' in (c['body0_name'],c['body1_name'])
                and any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name'])) for c in v['contacts']) for v in rows),
            'training_ready':False,'stability_success':False}
    assert initial_states[0] == initial_states[1]
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in before.items())
    result = {'scope':'saved native 60Hz sample analysis, no new physics or musical scoring',
              'same_initial_native_state':True,'native_runs':2,'results':results,
              'input_sha256':before,'inputs_unchanged':True,
              'next_initialization_issue':'initial actual q and load-bearing PD target need separate calibration; neutral q_ref is not stable guitar support',
              'rotation_allowed_SO3_membership':'not implemented; initial-relative angle is diagnostic only'}
    with output.open('x') as handle:json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps(results,ensure_ascii=False))


if __name__ == '__main__': main()
