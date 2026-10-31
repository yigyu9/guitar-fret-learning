"""Compare native self-collision OFF/ON at the last initial support pose."""
import argparse
import json
import sys
from pathlib import Path
from itertools import combinations
import xml.etree.ElementTree as ET

from .self_collision_environment import SelfCollisionEnvironment
from .self_collision_probe import PHASE, SUPPORT_PHASE
from .thigh_palm_support import SupportEnvironment
from .build_fixed_lower_asset import ASSET, LOWER_BODIES, read, sha
from . import run_joint_hold as runner


def audit(env):
    filters=env.collision_filters
    active=[n for n in env.human_bodies if filters[n] and n!='LH:thumb_pad']
    pairs=[{'body0':a,'body1':b,'allowed':all(x&y==0 for x in filters[a] for y in filters[b])}
        for a,b in combinations(active,2)]
    def side(n):return 'L' if n=='L_Wrist' or n.startswith('LH:') else 'R' if n=='R_Wrist' or n.startswith('RH:') else None
    changed=[];matrix_ok=True
    spans=env.gym.get_actor_rigid_body_shape_indices(env.env,env.human)
    original={n:env.importer_filters[s.start:s.start+s.count] for n,s in zip(env.human_bodies,spans)}
    for p in pairs:
        a,b=p['body0'],p['body1']
        old=all(x&y==0 for x in original[a] for y in original[b])
        intended=(side(a) and side(b) and side(a)!=side(b)) or (side(a)=='L' and b=='R_Elbow') or (side(b)=='L' and a=='R_Elbow') or (side(a)=='R' and b=='L_Elbow') or (side(b)=='R' and a=='L_Elbow')
        matrix_ok &= p['allowed']==bool(old or intended)
        if old!=p['allowed']:changed.append(p)
    excludes=[(e.get('body1'),e.get('body2')) for e in ET.parse(ASSET).findall('./contact/exclude')]
    guitar=[n for n in env.guitar_bodies if filters[n] and n not in ('G:thumb_support_proxy','G:pluck_range')]
    checks={'pair_matrix_exact_to_intended_policy':matrix_ok,
        'both_hands_can_collide':all(p['allowed'] for p in pairs if side(p['body0']) and side(p['body1']) and side(p['body0'])!=side(p['body1'])),
        'explicit_28_exclusions_retained':len(excludes)==28 and all(all(x&y!=0 for x in filters[a] for y in filters[b]) for a,b in excludes),
        'all_active_human_guitar_pairs_allowed':all(x&y==0 for a in active for b in guitar for x in filters[a] for y in filters[b]),
        'proxy_human_guitar_exclusions_retained':all(x&y!=0 for a in ('LH:thumb_pad','G:thumb_support_proxy','G:pluck_range') for b in active+guitar for x in filters[a] for y in filters[b]),
        'guitar_self_collision_remains_excluded':all(x&y!=0 for a,b in combinations(guitar,2) for x in filters[a] for y in filters[b])}
    if not all(checks.values()):raise AssertionError(checks)
    return {'checks':checks,'native_filters':filters,'active_human_pair_matrix':pairs,
        'newly_allowed_pairs':changed,'policy':env.self_collision_policy,'explicit_exclusions':excludes}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('off','on'),default='on')
    parser.add_argument('--physics-steps',type=int,choices=(24,120),default=24)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    search_path=SUPPORT_PHASE/'search_near_touch.json';search=read(search_path)
    settings=Path(search['rows'][0]['settings_path']);shift=search['guitar_initial_translation_m']
    previous=SUPPORT_PHASE/'short/clear_2um'
    files=[Path(__file__).resolve(),Path(__file__).with_name('self_collision_environment.py'),
        Path(__file__).with_name('self_collision_probe.py'),Path(__file__).with_name('thigh_palm_support.py'),
        Path(__file__).with_name('fixed_lower_environment.py'),ASSET,settings,search_path]
    files += [previous/(n+'.json') for n in ('report','states','trace','contacts','controls','leg_torques')]
    hashes={str(p):sha(p) for p in files}
    scenes=[];mask_audit={}
    def factory(initial):
        env=(SelfCollisionEnvironment if args.mode=='on' else SupportEnvironment)(initial,shift)
        scenes.append(env)
        if len(scenes)==2 and args.mode=='on':
            try:mask_audit.update(audit(env))
            except Exception:
                env.close();raise
        return env
    old_factory,old_argv=runner.InitialEnvironment,sys.argv
    runner.InitialEnvironment=factory
    sys.argv=[runner.__file__,'--mode','on','--settings',str(settings),'--out',str(args.out),'--physics-steps',str(args.physics_steps)]
    try:runner.main()
    finally:runner.InitialEnvironment,sys.argv=old_factory,old_argv
    report,states,contacts=(read(args.out/(n+'.json')) for n in ('report','states','contacts'))
    baseline=read(previous/'report.json')
    checks={k:v for k,v in scenes[-1].lock_checks.items() if k!='initial_body_poses_match'}
    checks.update(initial_state_exact_to_previous=states[0]==read(previous/'states.json')[0],
        lower_all_states_exact=all(s['human_body_states'][report['human_body_names'].index(n)]==states[0]['human_body_states'][report['human_body_names'].index(n)] for s in states for n in LOWER_BODIES),
        pd_and_targets_unchanged=all(report[k]==baseline[k] for k in ('initial_joint_targets_rad','native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm')),
        extra_inputs_unchanged=all(sha(Path(p))==h for p,h in hashes.items()))
    if args.mode=='off' and args.physics_steps==24:
        checks['off_raw_prefix_exact']=all(read(args.out/(n+'.json'))==read(previous/(n+'.json')) for n in ('states','trace','contacts','controls','leg_torques'))
    self_rows=[dict(physics_step=f['physics_step'],contact=c) for f in contacts for c in f['contacts']
        if c['body0_name'].startswith('human/') and c['body1_name'].startswith('human/')]
    report.update(self_collision_mode=args.mode,self_collision_checks=checks,collision_mask_audit=mask_audit,
        native_self_contact_rows=len(self_rows),native_positive_self_contact_lambda_rows=sum(c['contact']['lambda']>0 for c in self_rows),
        native_self_contact_pairs=sorted({tuple(sorted((c['contact']['body0_name'],c['contact']['body1_name']))) for c in self_rows}),
        source_sha256={**report['source_sha256'],**hashes})
    for name,value in (('report',report),('self_contacts',self_rows)):
        (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'self_contact_rows':len(self_rows),'positive_lambda_rows':report['native_positive_self_contact_lambda_rows'],
        'pairs':report['native_self_contact_pairs'],'p_mm':1000*report['max_position_error_m'],'q_deg':report['max_rotation_error_deg']},indent=2))
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
