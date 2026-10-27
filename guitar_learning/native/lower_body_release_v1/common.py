"""Local runtime inputs and explicit provenance for the native105 controller."""
import json
import hashlib
from pathlib import Path
import numpy as np
from ..paths import ROOT, A, NATIVE, ASSETS, PROVENANCE, provenance_records, resolve_input_path, original_input_path, rebase_paths

BASE = ROOT / 'paper/initial_pose/lower_body_release_v1'
HUMAN = ASSETS / 'tab2body/assets/smpl_mpl_hands_body.xml'
H0 = ROOT / 'docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125'
MANIFEST = A / 'working_initial_pose_v1/manifest.json'
LOWER = tuple(s+'_'+p+'_' for s in ('L','R') for p in ('Hip','Knee','Ankle','Toe'))


def read(path):
    return rebase_paths(json.loads(resolve_input_path(path).read_text()))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def sha(path):
    return hashlib.sha256(resolve_input_path(path).read_bytes()).hexdigest()


def pin(config=None, extra=()):
    """Pin current runtime inputs and preserve historical gate path identities."""
    import os
    from guitar_learning.historical_inputs import fingerprint_paths
    from ..paths import verify_provenance
    verify_provenance()
    paths = set(NATIVE.rglob('*.py')) | {PROVENANCE}
    if config:
        paths.add(resolve_input_path(config))
        candidate = read(config).get('candidate')
        if candidate:
            paths.add(resolve_input_path(candidate))
    historical = []
    for path in extra:
        lexical = Path(os.path.abspath(os.fspath(path)))
        if any((ROOT / name) in lexical.parents for name in ('tab2body', 'stability_adapter_2')):
            historical.append(str(lexical))
        else:
            paths.add(resolve_input_path(path))
    pins = {str(path.resolve()): sha(path) for path in sorted(paths)}
    pins.update(fingerprint_paths(historical))
    return pins


def verify(pins):
    """Verify original historical bytes and the current migrated implementation."""
    from guitar_learning.historical_inputs import fingerprint_paths
    from ..paths import verify_provenance
    actual = fingerprint_paths(pins)
    verify_provenance()
    return actual == {str(path): expected for path, expected in pins.items()}


def restore():
    manifest = read(MANIFEST)
    upper = dict(zip(manifest['joint_names'], manifest['target81_rad']))
    report, state = read(H0/'report.json'), read(H0/'states.json')[0]
    names = report['human_joint_names']
    assert len(names) == 105 and len(set(names)) == 105
    lower = {name: float(state['pos']) for name, state in zip(names, state['human_dof_states']) if name.startswith(LOWER)}
    assert len(lower) == 24
    q = np.array([upper[name] if name in upper else lower[name] for name in names], dtype=np.float32).astype(float)
    return {'schema': 'sa2_native105_initial_v1', 'joint_names': names, 'q_ref_rad': q.tolist(),
            'upper81_source': str(MANIFEST), 'lower24_source': str(H0), 'lower24_q_rad': lower, 'lower_deltas_rad': {},
            'guitar_position_W_m': manifest['guitar_actor_root_W_m'], 'guitar_quaternion_xyzw': manifest['guitar_quaternion_xyzw'],
            'expected_initial_state': read(manifest['native_initial'])['native_initial_state'],
            'support_candidate': manifest['candidate'],
            'scope': 'H0 lower24 restored by name with original upper81; actual native FK/property validation remains required.'}
