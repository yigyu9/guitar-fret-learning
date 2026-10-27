"""Check post-preparation states so reset-relative costs cannot hide drift."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.safety import contact_flags

OUT=Path(__file__).resolve().parent
RUN=OUT/'run_v1'


def read(p):return json.loads(p.read_text())


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def pose(row):
    return np.array([row['pose']['p'][k] for k in 'xyz']),Rotation.from_quat([row['pose']['r'][k] for k in 'xyzw'])


def main():
    assert read(RUN/'report.json')['completed']
    paths=sorted(RUN.glob('worker_*/audit_episode_*/initial_values.json'))
    pins={str(p):sha(p) for p in paths+[Path(__file__).resolve(),RUN/'report.json']}
    with (OUT/'preparation_inputs_before.json').open('x') as f:json.dump(pins,f,indent=2)
    refs={};rows=[]
    for path in paths:
        worker=path.parent.parent.name;v=read(path);native=v['native']['native']
        assert len(v['joint_names'])==105 and len(v['zero_range_indices'])==8
        assert v['human_root_fixed'] and not v['guitar_root_fixed'] and not v['guitar_gravity_disabled']
        guitar=pose(native['guitar_body_states'][v['guitar_body_names'].index('guitar')])
        feet=np.array([pose(native['human_body_states'][v['human_body_names'].index(s+'_Ankle')])[0] for s in ('L','R')])
        q=np.array([r['pos'] for r in native['human_dof_states']])
        refs.setdefault(worker,(guitar,feet,q));ref,foot0,q0=refs[worker];flags=contact_flags(v['native'])
        rows.append(dict(worker=worker,path=str(path),guitar_position_change_m=float(np.linalg.norm(guitar[0]-ref[0])),
            guitar_rotation_change_rad=float((ref[1].inv()*guitar[1]).magnitude()),
            foot_position_change_max_m=float(np.linalg.norm(feet-foot0,axis=1).max()),
            q_change_max_rad=float(np.max(np.abs(q-q0))),any_support=bool(flags[:3].any()),
            triple_support=bool(flags[:3].all()),both_feet=bool(flags[-2:].all())))
    result=dict(preparation_count=len(rows),reference='First prepared state of each same worker; not a hidden solver cache equality claim',
        maxima={k:max(r[k] for r in rows) for k in ('guitar_position_change_m','guitar_rotation_change_rad','foot_position_change_max_m','q_change_max_rad')},
        counts={k:sum(r[k] for r in rows) for k in ('any_support','triple_support','both_feet')},rows=rows)
    with (OUT/'preparation_analysis.json').open('x') as f:json.dump(result,f,indent=2)
    changed=[p for p,h in pins.items() if sha(Path(p))!=h]
    with (OUT/'preparation_verification.json').open('x') as f:json.dump(dict(completed=not changed,changed_inputs=changed),f,indent=2)
    assert not changed


if __name__=='__main__':main()
