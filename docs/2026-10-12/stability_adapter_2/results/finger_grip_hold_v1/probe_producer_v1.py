"""Initial-only native finger FK and source hull distances; no physics steps."""
import json
from pathlib import Path

from .self_collision_environment import SelfCollisionEnvironment
from .self_collision_probe import SUPPORT_PHASE
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha
from .run_joint_hold import native_state
from .initial_overlap import build_probe
from .search_hand_support import palm_neck_gap
from .plot_neck_palm import geometry
from .thigh_palm_support import intersection

PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1'
REFERENCE = PHASE.parent/'self_collision_v1/short/on'
DIGITS = ('index','middle','ring','pinky')


def finger_deltas(amount):
    return {'LH:'+digit+suffix: amount*weight for digit in DIGITS
            for suffix,weight in (('1_x',.7),('2',1.),('3',.6))}


def main():
    output = PHASE/'probe.json'
    trials = ROOT/'stability_adapter_2/trials/finger_grip_hold_v1'
    if output.exists() or trials.exists():
        raise FileExistsError('preserve finger probe and trials')
    search_path = SUPPORT_PHASE/'search_near_touch.json'
    search, reference = read(search_path), read(REFERENCE/'report.json')
    initial = read(REFERENCE/'states.json')[0]
    settings_path = Path(search['rows'][0]['settings_path'])
    base = read(settings_path)
    q0 = dict(zip(reference['human_joint_names'],reference['initial_joint_targets_rad']))
    files = [Path(__file__).resolve(),settings_path,search_path,REFERENCE/'report.json',REFERENCE/'states.json',
             ROOT/'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json',ROOT/'docs/2026-08-19/정리.txt']
    files += [Path(p) for p in reference['source_sha256']]
    hashes = {str(p):sha(p) for p in files}
    trials.mkdir(parents=True)
    PHASE.mkdir(parents=True,exist_ok=True)
    rows = []
    for amount in (0.,.15,.3,.6):
        name = 'curl_'+str(round(amount*100))
        settings = dict(base,joint_angles_rad=dict(base['joint_angles_rad']))
        settings['joint_angles_rad'].update({n:q0[n]+d for n,d in finger_deltas(amount).items()})
        path = trials/(name+'.json')
        path.write_text(json.dumps(settings,indent=2)+'\n')
        env = SelfCollisionEnvironment(settings,search['guitar_initial_translation_m'])
        try:
            state = native_state(env)
            probe = build_probe(env)
            model,data,shapes = probe
            fingers = [s for s in shapes if s['body'] in ('LH:'+d+str(j) for d in DIGITS for j in (1,2,3))]
            guitar = [s for s in shapes if s['actor']=='guitar' and s['body'] not in ('G:thumb_support_proxy','G:pluck_range')]
            hands = [s for s in shapes if s['body'].startswith('LH:') and s['body']!='LH:thumb_pad']
            right = [s for s in shapes if s['body'].startswith('RH:')]
            meshes = {s['geom_id']:geometry(model,data,s) for s in hands+right+guitar}
            crossings = [{'human':a['body'],'guitar':b['body'],'common_radius_m':radius}
                for a in hands for b in guitar
                for radius in [intersection(meshes[a['geom_id']],meshes[b['geom_id']])] if radius>1e-7]
            cross_hands = [[a['body'],b['body']] for a in hands for b in right
                if intersection(meshes[a['geom_id']],meshes[b['geom_id']])>1e-7]
            distances = {s['body']:palm_neck_gap(probe,s['body']) for s in fingers}
            unchanged = all(state['human_body_states'][i]==initial['human_body_states'][i]
                for i,n in enumerate(env.human_bodies) if not n.startswith('LH:') or n=='LH:palm')
            checks = {'zero_physics_steps':env.steps==0,'nonfinger_bodies_exact':unchanged,
                      'guitar_state_exact':state['guitar_body_states']==initial['guitar_body_states'],
                      'inside_native_limits':bool(((env.initial_q>=env.lower)&(env.initial_q<=env.upper)).all()),
                      'rest_length_exact':env.rest_length==reference['absolute_rest_length_m']}
            if not all(checks.values()):raise AssertionError(checks)
            rows.append({'name':name,'amount_rad':amount,'settings_path':str(path),
                'checks':checks,'finger_neck_source':distances,'hand_guitar_source_intersections':crossings,
                'cross_hand_source_intersections':cross_hands,'initial_state':state,
                'source_clear':not crossings and not cross_hands})
            print(json.dumps({'name':name,'min_tip_neck_mm':1000*min(v['source_hull_distance_m'] for n,v in distances.items() if n.endswith('3')),
                'source_crossings':crossings,'cross_hands':cross_hands}),flush=True)
        finally:
            env.close()
    after = {p:sha(Path(p)) for p in hashes}
    if hashes!=after:raise AssertionError('probe inputs changed')
    output.write_text(json.dumps({'rows':rows,'input_sha256':hashes,'input_sha256_after':after,
        'native_initializations':4,'physics_steps':0,'scope':'native initialization FK; source hull metrics, not cooked contacts'},indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    main()
