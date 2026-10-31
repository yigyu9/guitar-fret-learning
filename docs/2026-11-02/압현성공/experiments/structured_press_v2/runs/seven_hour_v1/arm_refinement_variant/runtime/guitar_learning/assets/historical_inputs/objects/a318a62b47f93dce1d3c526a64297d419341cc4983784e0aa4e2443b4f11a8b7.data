"""Fresh native direct-geometry admission for the five-finger initial candidate."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from . import near_contact_initial_audit as admission
from . import run_small_wrist_recorded_diagnostic as runner
from .environment import np, ROOT
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection
from .run_joint_hold import native_state
from .build_fixed_lower_asset import LOWER_BODIES, pose
from scipy.spatial.transform import Rotation

B = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
POLICY = B / 'torso_hold_native_collision_v1/initial_collision/shape_properties.json'
BASELINE = B / 'initial_middle3_alignment_v1/native/initial_values.json'
PROXY = B / 'palm_neck_side_v1/initial_audit_v2/audit.json'


def audit_initial(env, search, row):
    before = native_state(env)
    base = json.loads(BASELINE.read_text())
    properties = env.gym.get_actor_rigid_shape_properties(env.env, env.human)
    spans = env.gym.get_actor_rigid_body_shape_indices(env.env, env.human)
    filters = {n:[int(properties[k].filter) for k in range(s.start, s.start+s.count)] for n,s in zip(env.human_bodies,spans)}
    guitar_properties = env.gym.get_actor_rigid_shape_properties(env.env, env.guitar)
    guitar_spans = env.gym.get_actor_rigid_body_shape_indices(env.env, env.guitar)
    guitar_filters = {n:[int(guitar_properties[k].filter) for k in range(s.start, s.start+s.count)] for n,s in zip(env.guitar_bodies,guitar_spans)}
    expected = json.loads(POLICY.read_text())['mask_audit']['native_filters']
    probe = build_probe(env)
    meshes, hg, cross = source_checks(probe)
    xml = ET.parse(ROOT / env.config['humanoid_asset']).getroot()
    parents = {c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain = []; current = a
        while current in parents: chain.append(current); current = parents[current]
        chain.append(current); steps = 0; current = b
        while current not in chain and current in parents: steps += 1; current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    humans = [s for s in probe[2] if s['actor'] == 'human']
    overlaps = []; count = 0
    for i,a in enumerate(humans):
        for b in humans[i+1:]:
            if distance(a['body'],b['body']) <= 2: continue
            sameleft = all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow') for s in (a,b))
            allowed = all(x & y == 0 for x in filters[a['body']] for y in filters[b['body']])
            if not (sameleft or allowed): continue
            count += 1
            radius = intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius > 1e-7: overlaps.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
    proxy = np.array(json.loads(PROXY.read_text())['palmar_normal_proxy_local'])
    up = float(Rotation.from_quat(pose(before['human_body_states'][env.human_bodies.index('LH:palm')])[1]).apply(proxy)[2])
    fixed = [env.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
    props = env.gym.get_actor_dof_properties(env.env,env.human)
    actual_pd = {n:props[n].astype(int if n=='driveMode' else float).tolist() for n in props.dtype.names}
    checks = dict(fresh_native_human_filters_equal_reference=all(filters[n] == expected[n] for n in env.human_bodies),
        fresh_native_guitar_filters_equal_reference=all(guitar_filters[n] == expected[n] for n in env.guitar_bodies),
        source_human_guitar_clear=not hg, source_cross_hands_clear=not cross,
        complete_source_self1188_clear=count == 1188 and not overlaps, palm_up_proxy=up > 0,
        root_lower_initial_exact=all(before['human_body_states'][i] == base['native_initial_state']['human_body_states'][i] for i in fixed),
        guitar_initial_fullstate_exact=before['guitar_body_states'] == base['native_initial_state']['guitar_body_states'],
        all_PD_properties_exact=actual_pd == base['PD_properties'],
        main66_and_body9_exact=env.names == base['human_joint_names'] and [env.names[i] for i in env.main_indices] == base['main_control_joint_names'],
        no_proposed_FK_state='source_state' not in row,
        zero_steps_and_readonly=env.steps == 0 and native_state(env) == before)
    return dict(checks=checks, source_intersections=hg, cross_hand_intersections=cross,
        complete_source_self_screen=dict(pair_count=count,intersections=overlaps,native_filters=filters,guitar_native_filters=guitar_filters),
        palm_up_proxy_z=up,
        scope='Fresh actual native pose direct source LP screen, no FK prediction/certificate; graph<=2 excluded; source shapes are not PhysX cooked clearance certification')


def main():
    original_audit, original_save = admission.audit_initial, runner.save
    def save_direct(path, value):
        if Path(path).name in ('attempt.json','initial_values.json','report.json'):
            value = dict(value)
            value['inherited_scope'] = value.get('scope')
            value['scope'] = 'Five source-range initial/held hinges changed; fresh actual native direct source geometry gate without FK; same passive strap/PD/root/lower/G initialization; no pose replay or post-start state writes'
            if 'checks' in value:
                value['checks'] = dict(value['checks'])
                old = value['checks'].pop('initial_grip_source_and_FK_gate', None)
                if old is not None: value['checks']['direct_native_source_gate'] = old
            if value.get('failure',{}):
                value['inherited_failure'] = value['failure']
                if value['failure']['message'].startswith('initial grip source/FK gate rejected'):
                    value['failure'] = dict(type=value['failure']['type'],message='fresh direct native source gate rejected; t0 partial video saved')
        original_save(path,value)
    admission.audit_initial, runner.save = audit_initial, save_direct
    try: runner.main()
    finally: admission.audit_initial, runner.save = original_audit, original_save


if __name__ == '__main__': main()
