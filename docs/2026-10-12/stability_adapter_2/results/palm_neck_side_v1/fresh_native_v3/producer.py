"""Fresh native FK and optional one-step collider diagnostic of side-palm proposals."""
import argparse
import json
from pathlib import Path

from .audit_palm_side_target import PHASE,side_target,closest_polygon
from .finger_grip_probe import SUPPORT_PHASE
from .self_collision_environment import SelfCollisionEnvironment
from .environment import np
from .build_fixed_lower_asset import read,sha,pose,LOWER_BODIES
from .run_joint_hold import native_state,snapshot
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .native_contacts import body_names,read_contacts
from .search_palm_neck_side import REFERENCE
from scipy.spatial.transform import Rotation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--steps',type=int,choices=(0,1),default=0)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    face_path=PHASE/'face_audit/audit.json';search_path=PHASE/'fk_search/search.json'
    initial_path=PHASE/'initial_audit_v2/audit.json';shift_path=SUPPORT_PHASE/'search_near_touch.json'
    face,search,initial=read(face_path),read(search_path),read(initial_path)
    fixed_path=PHASE/'fixed_length_settings_manifest.json';fixed=read(fixed_path)
    if sha(face_path)!=fixed['face_audit_sha256']:raise ValueError('face audit changed')
    reference=read(REFERENCE/'report.json')
    selected=[r for r in face['rows'] if r['face_used_clear']]
    inputs=[Path(__file__).resolve(),face_path,search_path,initial_path,shift_path,fixed_path]
    inputs += [Path(p) for p in face['input_sha256']]
    inputs += [Path(r['settings_path']) for r in fixed['rows']]
    inputs += [Path(__file__).with_name(n) for n in ('face_referenced_geometry.py','native_contacts.py','self_collision_environment.py')]
    hashes={str(p):sha(p) for p in inputs}
    rows=[]
    for candidate in selected:
        fixed_row=next(r for r in fixed['rows'] if r['name']==candidate['name'])
        old=Path(candidate['settings_path']);settings=Path(fixed_row['settings_path'])
        if sha(old)!=candidate['settings_sha256'] or sha(settings)!=fixed_row['settings_sha256']:raise ValueError('candidate settings changed')
        original,updated=read(old),read(settings)
        if dict(original,strap_rest_length_m=initial['absolute_rest_length_m'])!=updated:raise ValueError('fixed length variant changed other settings')
        predicted=next(r['source_state'] for r in search['rows'] if r['name']==candidate['name'])
        env=SelfCollisionEnvironment(read(settings),read(shift_path)['guitar_initial_translation_m'])
        state=None;checks={}
        try:
            state=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human)
            arm=set(reference['arm_indices'][:12]);base=initial['initial_state']
            before,norms=[],[]
            for n in env.human_bodies:
                a,b=pose(state['human_body_states'][env.human_bodies.index(n)]),pose(predicted['human_body_states'][env.human_bodies.index(n)])
                before.append(np.linalg.norm(a[0]-b[0]));norms.append(np.linalg.norm((Rotation.from_quat(a[1])*Rotation.from_quat(b[1]).inv()).as_rotvec()))
            probe=build_probe(env)
            palm=face_geometry(*probe[:2],next(s for s in probe[2] if s['body']=='LH:palm'))
            _,polygon,_=side_target(env)
            gap=closest_polygon(palm,polygon)
            checks={'fresh_fk_positions_match':bool(max(before)<1e-6),'fresh_fk_orientations_match':bool(max(norms)<1e-5),
                'nonleftarm_q_exact':all(d==base['human_dof_states'][i] for i,d in enumerate(state['human_dof_states']) if i not in arm),
                'guitar_initial_all_states_exact':state['guitar_body_states']==base['guitar_body_states'],
                'native_pd_exact':all(props[k].astype(float).tolist()==reference[r] for k,r in (('stiffness','native_pd_kp'),('damping','native_pd_kd'),('effort','native_effort_caps_nm'),('driveMode','native_drive_modes'))),
                'absolute_length_exact':env.rest_length==initial['absolute_rest_length_m'],
                'initial_queries_preserve_states':state==native_state(env)}
            if not all(checks.values()):raise AssertionError(checks)
            states=[state];trace=[snapshot(env)];contacts=[]
            names=body_names(env.gym,env.env)
            for _ in range(args.steps):
                env.step_physics();states.append(native_state(env));trace.append(snapshot(env))
                contacts.append({'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
            checks['root_lower_exact']=all(s['human_body_states'][env.human_bodies.index(n)]==state['human_body_states'][env.human_bodies.index(n)] for s in states for n in ('Pelvis',)+LOWER_BODIES)
            row={'name':candidate['name'],'settings_path':str(settings),'settings_sha256':sha(settings),
                'checks':checks,'source_max_fk_position_error_m':float(max(before)),
                'source_max_fk_rotation_error_rad':float(max(norms)),
                'face_used_source_hull_to_blue_polygon':gap,'initial_settings':env.initial_settings,
                'initial_route_length_m':env.initial_route_length,'absolute_rest_length_m':env.rest_length,
                'states':states,'trace':trace,'contacts':contacts,
                'scope':'one-step diagnostic only' if args.steps else 'fresh initialization-only FK; no cooked-clear certification'}
            rows.append(row)
            (args.out/'probe.json').write_text(json.dumps({'rows':rows,'input_sha256':hashes,
                'native_initializations':len(rows),'physics_steps':len(rows)*args.steps},indent=2,allow_nan=False)+'\n')
            print(json.dumps({'name':row['name'],'checks':checks,'source_gap_mm':gap['distance_m']*1000,
                'initial_route_length_m':env.initial_route_length,'p_mm':trace[-1]['position_error_m']*1000,
                'q_deg':trace[-1]['rotation_error_deg'],'contacts':contacts},indent=2),flush=True)
            if not all(checks.values()):raise AssertionError(checks)
        except Exception as error:
            (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),
                'candidate':candidate['name'],'checks':checks,'initial_state':state,
                'physics_steps':len(rows)*args.steps+env.steps,'native_initializations_attempted':len(rows)+1,
                'input_sha256':hashes},indent=2,allow_nan=False)+'\n')
            raise
        finally:env.close()
    if not all(sha(Path(p))==h for p,h in hashes.items()):raise AssertionError('probe inputs changed')


if __name__=='__main__':main()
