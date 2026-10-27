"""Validate the separate body-root guitar, with no simulation steps."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import isaacgym  # noqa: F401 - import before numpy
from isaacgym import gymapi
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'tab2body/assets/guitar_asset.xml'
NEW = ROOT/'stability_adapter_2/assets/guitar_asset_body_root_v2.xml'
OUT = ROOT/'docs/2026-10-12/stability_adapter_2/results/guitar_body_root_v2_side_native_v3'


def vec(value):
    return np.array([value[a] for a in 'xyz'], dtype=float)


def rotate(q, p):
    return p+2*q[3]*np.cross(q[:3], p)+2*np.cross(q[:3], np.cross(q[:3], p))


def inertia(prop):
    return np.array([[getattr(getattr(prop.inertia, a), b) for b in 'xyz'] for a in 'xyz'])


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    inputs = [OLD, NEW, NEW.with_suffix('.json'), Path(__file__).resolve(),
              Path(__file__).with_name('build_guitar_body_root_v2.py'),
              Path(__file__).with_name('GUITAR_BODY_ROOT_V2_PLAN.md')]
    inputs += list((OLD.parent/'mesh').glob('guitar_neck*.obj'))
    hashes = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs}
    old_root = ET.parse(OLD).getroot().find('worldbody/body')
    new_root = ET.parse(NEW).getroot().find('worldbody/body')
    c = np.array([0., -.4, -.0217])
    checks = {'root_body_unchanged': old_root.attrib == new_root.attrib,
              'body_center_at_zero': new_root.find("body[@name='G:body']").get('pos') == '0 0 0',
              'child_count_equal': len(old_root) == len(new_root)}
    checks['all_only_expected_child_offsets_changed'] = all(
        a.tag == b.tag and {k:v for k,v in a.attrib.items() if k!='pos'} ==
        {k:v for k,v in b.attrib.items() if k!='pos'} and
        np.allclose(np.fromstring(a.get('pos','0 0 0'), sep=' ')-c,
                    np.fromstring(b.get('pos','0 0 0'), sep=' '), atol=1e-12, rtol=0) and
        [ET.tostring(e) for e in a] == [ET.tostring(e) for e in b]
        for a,b in zip(old_root,new_root))
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams(); params.gravity = gymapi.Vec3(0,0,0)
    params.physx.use_gpu = False; params.use_gpu_pipeline = False
    sim = gym.create_sim(0,-1,gymapi.SIM_PHYSX,params)
    if sim is None: raise RuntimeError('CPU PhysX scene creation failed')
    try:
        options = gymapi.AssetOptions(); options.fix_base_link = True
        options.override_com = True; options.override_inertia = True
        assets = [gym.load_asset(sim,str(f.parent),f.name,options) for f in (OLD,NEW)]
        if any(asset is None for asset in assets): raise RuntimeError('asset load failed')
        env = gym.create_env(sim,gymapi.Vec3(-2,-2,0),gymapi.Vec3(2,2,2),1)
        q = np.array([.2,-.3,.4,.5]); q /= np.linalg.norm(q)
        positions = [np.array([.1,-.2,.8])]
        positions.append(positions[0]+rotate(q,c))
        actors = []
        for i,(asset,p) in enumerate(zip(assets,positions)):
            pose = gymapi.Transform(); pose.p = gymapi.Vec3(*p); pose.r = gymapi.Quat(*q)
            actors.append(gym.create_actor(env,asset,pose,'guitar_v'+str(i+1),i,0))
        assert gym.prepare_sim(sim)
        names = [gym.get_actor_rigid_body_names(env,a) for a in actors]
        states = [gym.get_actor_rigid_body_states(env,a,gymapi.STATE_POS) for a in actors]
        props = [gym.get_actor_rigid_body_properties(env,a) for a in actors]
        checks['native_body_names_equal'] = names[0] == names[1]
        position_error = max(np.linalg.norm(vec(a['pose']['p'])-vec(b['pose']['p']))
                             for a,b in zip(states[0][1:],states[1][1:]))
        checks['native_child_world_positions_equal'] = bool(position_error < 1e-6)
        rotations = [[[s['pose']['r'][axis] for axis in 'xyzw'] for s in group] for group in states]
        checks['native_body_quaternions_equal'] = bool(np.allclose(rotations[0],rotations[1],atol=1e-6))
        body = names[1].index('G:body')
        checks['native_root_at_body_center'] = bool(np.linalg.norm(vec(states[1][0]['pose']['p'])-
                                                                  vec(states[1][body]['pose']['p'])) < 1e-6)
        checks['native_masses_equal'] = bool(np.allclose([p.mass for p in props[0]], [p.mass for p in props[1]],rtol=1e-5,atol=1e-7))
        checks['native_root_com_correctly_translated'] = bool(np.allclose(np.array([getattr(props[0][0].com,k) for k in 'xyz'])-c,np.array([getattr(props[1][0].com,k) for k in 'xyz']),atol=1e-5))
        checks['native_inertias_equal'] = all(np.allclose(inertia(a),inertia(b),rtol=1e-4,atol=1e-6) for a,b in zip(*props))
    finally:
        gym.destroy_sim(sim)
    checks['inputs_preserved'] = all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
    result = {'checks':checks,'native_max_child_world_position_error_m':float(position_error),
              'native_body_count':len(names[0]),'native_root_com_m':[[getattr(group[0].com,k) for k in 'xyz'] for group in props],'old_root_to_new_root_m':c.tolist(),
              'input_sha256':hashes,'physics_steps':0,
              'scope':'isolated fixed-base asset/frame audit; free-guitar dynamics not tested'}
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    assert all(checks.values()), checks
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
