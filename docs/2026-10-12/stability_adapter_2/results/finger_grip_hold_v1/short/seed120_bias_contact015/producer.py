"""Native free-guitar finger target experiment; root/lower fixed and self collision ON."""
import argparse
import json
from pathlib import Path

from .self_collision_environment import SelfCollisionEnvironment
from .finger_grip_probe import PHASE, REFERENCE, SUPPORT_PHASE
from .finger_grip_control import FingerGripControl, DIGITS
from .build_fixed_lower_asset import read, sha, LOWER_BODIES
from .environment import ROOT, np, gymapi
from .run_joint_hold import native_state, snapshot
from .joint_hold_residual import JointHoldResidual
from .native_contacts import body_names, read_contacts
from .run_self_collision import audit


def validated_seed(settings):
    manifest=read(PHASE/'probe_settings_manifest.json')
    entry=manifest['settings'][str(settings.resolve())]
    if sha(settings)!=entry['settings_sha256'] or sha(Path(entry['probe_path']))!=entry['probe_sha256']:
        raise ValueError('seed settings or source probe changed')
    row=next(r for r in read(Path(entry['probe_path']))['rows'] if r['name']==entry['row_name'])
    if not entry['settings_q_exact_to_saved_probe'] or not row['source_clear'] or not all(row['checks'].values()):
        raise ValueError('seed failed initial geometry or native checks')
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('off','ramp','contact'),required=True)
    parser.add_argument('--cap',type=float,default=.6)
    parser.add_argument('--bias',type=Path)
    parser.add_argument('--settings',type=Path,default=ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/curl_0.json')
    parser.add_argument('--physics-steps',type=int,choices=(24,120,240),default=24)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    grip=FingerGripControl(args.mode,args.cap)
    args.out.mkdir(parents=True,exist_ok=False)
    reference=read(REFERENCE/'report.json')
    search_path=SUPPORT_PHASE/'search_near_touch.json';search=read(search_path)
    files=[Path(p) for p in reference['source_sha256']]
    files += [REFERENCE/(n+'.json') for n in ('report','states','trace','contacts','controls','leg_torques')]
    files += [Path(__file__).resolve(),Path(__file__).with_name('finger_grip_control.py'),Path(__file__).with_name('finger_grip_probe.py'),args.settings.resolve(),search_path]
    files += [PHASE/'probe_settings_manifest.json']+[PHASE/n for n in ('probe.json','probe_deep.json','probe_mixed.json')]
    if args.bias:files.append(args.bias.resolve())
    hashes={str(p):sha(p) for p in files}
    env=None
    states,trace,contacts,controls,torques=[],[],[],[],[]
    try:
        seed=validated_seed(args.settings)
        env=SelfCollisionEnvironment(read(args.settings),search['guitar_initial_translation_m'])
        mask=audit(env)
        arm=np.array([i for i in env.main_indices if not env.names[i].startswith(('LH:','RH:'))])
        fingers=np.array([env.names.index('LH:'+digit+suffix) for digit in DIGITS for suffix in ('1_x','2','3')])
        other=np.array([i for i in range(len(env.names)) if i not in arm and i not in fingers])
        low,high=np.array(reference['diagnostic_lower_rad']),np.array(reference['diagnostic_upper_rad'])
        bias=np.zeros(24)
        if args.bias:
            bias_settings=read(args.bias)
            if bias_settings['settings_sha256']!=sha(args.settings):raise ValueError('bias belongs to another initial pose')
            bias=np.array([bias_settings['arm_target_bias_rad'][env.names[i]] for i in arm])
            q0=env.initial_q[arm].astype(float)
            controller=JointHoldResidual(q0,np.maximum(low,q0-.15)-bias,np.minimum(high,q0+.15)-bias)
        else:controller=JointHoldResidual(env.initial_q[arm],low,high)
        names=body_names(env.gym,env.env);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        states,trace,contacts,controls,torques=[native_state(env)],[snapshot(env)],[],[],[env.last_leg_torques.tolist()]
        interval=env.config['physics_hz']//env.config['control_hz']
        if interval*env.config['control_hz']!=env.config['physics_hz']:raise ValueError('control rate must divide physics rate')
        checks={'commands_preserve_states':True,'noncontrolled_targets_held':True,'arm_target_bounds':True,
                'finger_target_bounds':True,'finger_target_rate':True,'contact_reads_preserve_states':True}
        previous_finger=env.initial_q[fingers].copy();last_contacts=[]
        arm_record={};finger_record={}
        for step in range(args.physics_steps):
            updated=step%interval==0
            if updated:
                before=native_state(env);dofs=env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)
                target,arm_record=controller.update(dofs['pos'][arm],1/env.config['control_hz'])
                target=target+bias
                finger_offsets,finger_record=grip.update(last_contacts,1/env.config['control_hz'])
                offsets=np.zeros(66,dtype=np.float32)
                for i,value in zip(arm,target-env.initial_q[arm]):offsets[list(env.main_indices).index(i)]=value
                for n,value in finger_offsets.items():offsets[list(env.main_indices).index(env.names.index(n))]=value
                env.set_main_offsets(offsets)
                checks['commands_preserve_states'] &= native_state(env)==before
                checks['finger_target_rate'] &= bool((np.abs(env.target[fingers]-previous_finger)<=6/env.config['control_hz']+2e-7).all())
                previous_finger=env.target[fingers].copy()
            checks['noncontrolled_targets_held'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            checks['arm_target_bounds'] &= bool(((env.target[arm]>=low-2e-7)&(env.target[arm]<=high+2e-7)).all() and (np.abs(env.target[arm]-env.initial_q[arm])<=.15+2e-7).all())
            checks['finger_target_bounds'] &= bool(((env.target[fingers]>=env.lower[fingers])&(env.target[fingers]<=env.upper[fingers])).all() and (np.abs(env.target[fingers]-env.initial_q[fingers])<=args.cap+2e-7).all())
            controls.append(dict(arm_record,physics_step=step+1,updated_before_step=updated,
                final_arm_targets_rad=env.target[arm].astype(float).tolist(),arm_static_bias_rad=bias.tolist(),finger_control=finger_record,
                finger_targets_rad=env.target[fingers].astype(float).tolist()))
            env.step_physics();before=native_state(env)
            last_contacts=read_contacts(env.gym,env.env,names)
            contacts.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'contacts':last_contacts})
            checks['contact_reads_preserve_states'] &= native_state(env)==before
            states.append(before);trace.append(snapshot(env));torques.append(env.last_leg_torques.tolist())
        checks.update(initial_state_exact_to_validated_probe=states[0]==seed['initial_state'],
            root_all_states_exact=all(s['human_body_states'][0]==states[0]['human_body_states'][0] for s in states),
            initial_guitar_goal_match=trace[0]['position_error_m']<1e-6 and trace[0]['rotation_error_deg']<.001,
            all_lower_states_exact=all(s['human_body_states'][env.human_bodies.index(n)]==states[0]['human_body_states'][env.human_bodies.index(n)] for s in states for n in LOWER_BODIES),
            native_pd_unchanged=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
            pd_exact_to_reference=all(props[k].astype(float).tolist()==reference[r] for k,r in (('stiffness','native_pd_kp'),('damping','native_pd_kd'),('effort','native_effort_caps_nm'),('driveMode','native_drive_modes'))),
            fixed_absolute_length=all(t['strap_rest_length_m']==reference['absolute_rest_length_m'] for t in trace),
            snapshots_finite=all(t['finite'] for t in trace),inputs_unchanged=all(sha(Path(p))==h for p,h in hashes.items()))
        if args.mode=='off' and args.physics_steps==24 and args.settings.name=='curl_0.json':
            checks['baseline_raw_exact']=all(value==read(REFERENCE/(name+'.json')) for name,value in (('states',states),('trace',trace),('contacts',contacts),('leg_torques',torques)))
        flat=[dict(physics_step=f['physics_step'],contact=c) for f in contacts for c in f['contacts']]
        def pair(c,a,b):return (c['body0_name'].startswith(a) and c['body1_name'].startswith(b)) or (c['body1_name'].startswith(a) and c['body0_name'].startswith(b))
        lh=[r for r in flat if pair(r['contact'],'human/LH:','guitar/')]
        self_rows=[r for r in flat if pair(r['contact'],'human/','human/')]
        thigh=[r for r in flat if pair(r['contact'],'human/R_Hip','guitar/')]
        report=dict(reference,scope='bounded finger closure plus existing arm PI; no guitar-error feedback',mode=args.mode,
            checks=checks,physics_steps=env.steps,initial_settings=env.initial_settings,settings_path=str(args.settings.resolve()),
            initial_joint_targets_rad=env.initial_q.astype(float).tolist(),finger_joint_names=[env.names[i] for i in fingers],
            finger_indices=fingers.tolist(),finger_cap_rad=args.cap,arm_static_bias_rad=bias.tolist(),
            target_bias_settings_path=str(args.bias) if args.bias else None,collision_mask_audit=mask,
            max_position_error_m=max(t['position_error_m'] for t in trace),max_rotation_error_deg=max(t['rotation_error_deg'] for t in trace),
            max_applied_strap_tension_n=max(t['last_applied_tension_n'] for t in trace),
            native_lh_guitar_rows=len(lh),native_positive_lh_guitar_rows=sum(r['contact']['lambda']>0 for r in lh),
            native_lh_guitar_steps=sorted({r['physics_step'] for r in lh}),native_lh_guitar_pairs=sorted({tuple(sorted((r['contact']['body0_name'],r['contact']['body1_name']))) for r in lh}),
            native_thigh_guitar_steps=sorted({r['physics_step'] for r in thigh}),native_self_rows=len(self_rows),
            source_sha256=hashes,source_sha256_after={p:sha(Path(p)) for p in hashes},stability_success=False)
        # Old diagnostic self-collision fields are not results of this new run.
        for key in ('self_collision_checks','native_self_contact_rows','native_positive_self_contact_lambda_rows','native_self_contact_pairs'):
            report.pop(key,None)
        for name,value in (('report',report),('states',states),('trace',trace),('contacts',contacts),('controls',controls),('leg_torques',torques),('lh_contacts',lh)):
            (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'checks':checks,'p_mm':1000*report['max_position_error_m'],'q_deg':report['max_rotation_error_deg'],
            'lh_contact_rows':len(lh),'lh_pairs':report['native_lh_guitar_pairs'],'thigh_steps':len(report['native_thigh_guitar_steps'])},indent=2))
        if not all(checks.values()):raise AssertionError(checks)
    except Exception as error:
        for name,value in (('states',states),('trace',trace),('contacts',contacts),('controls',controls),('leg_torques',torques)):
            safe=json.loads(json.dumps(value),parse_constant=lambda v:{'nonfinite_value':v})
            (args.out/(name+'.json')).write_text(json.dumps(safe,indent=2,allow_nan=False)+'\n')
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),
            'physics_steps':env.steps if env is not None else 0,'run_complete':False,
            'source_sha256':hashes,'nonfinite_failure_values':'encoded as named objects in partial raw'},indent=2)+'\n')
        raise
    finally:
        if env is not None:env.close()


if __name__=='__main__':main()
