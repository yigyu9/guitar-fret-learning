"""Bake recorded native lower-body link transforms into a private fixed MJCF."""
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from .strap import rotate

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125'
ASSET = Path(__file__).with_name('assets')/'humanoid_fixed_lower.xml'
MANIFEST = ASSET.with_suffix('.json')
LOWER_BODIES = tuple(side+'_'+part for side in ('L','R') for part in ('Hip','Knee','Ankle','Toe'))


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose(state):
    p, q = state['pose']['p'], state['pose']['r']
    return np.array([p[a] for a in 'xyz']), np.array([q[a] for a in ('x','y','z','w')])


def multiply(a, b):
    return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]), a[3]*b[3]-a[:3]@b[:3]]


def build():
    if ASSET.exists() or MANIFEST.exists():
        raise FileExistsError('preserve existing derived model')
    source = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'
    report, state = read(REFERENCE/'report.json'), read(REFERENCE/'states.json')[0]
    states = dict(zip(report['human_body_names'],state['human_body_states']))
    tree = ET.parse(source)
    model = tree.getroot()
    # Resolve unchanged original meshes without copying or modifying them.
    # Gym's MJCF importer concatenates asset-root + meshdir even for an
    # absolute meshdir. A relative path works in both Gym and MuJoCo.
    model.find('compiler').set('meshdir',os.path.relpath(source.parent/'mesh',ASSET.parent))
    parents = {child:parent for parent in model.iter() for child in parent}
    removed, transforms = [], {}
    for body in model.iter('body'):
        name = body.get('name')
        if name not in LOWER_BODIES:
            continue
        parent_name = parents[body].get('name')
        pp, pq = pose(states[parent_name]); bp, bq = pose(states[name])
        pq /= np.linalg.norm(pq); bq /= np.linalg.norm(bq)
        inverse = pq*np.array([-1,-1,-1,1])
        local_p, local_q = rotate(inverse,bp-pp), multiply(inverse,bq)
        local_q /= np.linalg.norm(local_q)
        body.set('pos',' '.join(format(v,'.17g') for v in local_p))
        body.set('quat',' '.join(format(v,'.17g') for v in local_q[[3,0,1,2]]))
        for joint in list(body.findall('joint')):
            removed.append(joint.get('name')); body.remove(joint)
        transforms[name] = {'parent':parent_name,'position_m':local_p.tolist(), 'quaternion_xyzw':local_q.tolist()}
    for parent in model.iter():
        for child in list(parent):
            if child.get('joint') in removed:
                parent.remove(child)
    original = ET.parse(source).getroot()
    checks = {'eight_lower_bodies_baked':set(transforms)==set(LOWER_BODIES),
        '24_lower_joints_removed':len(removed)==24,
        '81_remaining_joints':len(model.findall('.//worldbody//joint'))==81,
        'all_geoms_unchanged':[ET.tostring(g) for g in model.iter('geom')]==[ET.tostring(g) for g in original.iter('geom')],
        'upper_joint_definitions_unchanged':[ET.tostring(j) for j in model.findall('.//worldbody//joint')]==
            [ET.tostring(j) for j in original.findall('.//worldbody//joint') if j.get('name') not in removed]}
    if not all(checks.values()):
        raise AssertionError(checks)
    ASSET.parent.mkdir(parents=True,exist_ok=True)
    tree.write(ASSET,encoding='unicode')
    inputs = [source,REFERENCE/'report.json',REFERENCE/'states.json',Path(__file__).resolve(),Path(__file__).with_name('strap.py')]
    MANIFEST.write_text(json.dumps({'checks':checks,'removed_joint_names':removed,'fixed_transforms':transforms,
        'input_sha256':{str(p):sha(p) for p in inputs},'asset_sha256':sha(ASSET)},indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':
    build()
