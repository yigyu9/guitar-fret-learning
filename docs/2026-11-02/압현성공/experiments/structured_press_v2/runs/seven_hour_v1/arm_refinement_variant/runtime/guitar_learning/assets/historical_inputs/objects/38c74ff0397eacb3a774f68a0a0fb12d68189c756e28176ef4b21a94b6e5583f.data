"""Audit actual applied steps, including incomplete control ticks and constructor failures."""
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--cases',type=Path,nargs='+',required=True);args=parser.parse_args()
    a=ROOT/'stability_adapter_2';p=ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1';geometry=read(a/'assets/om_body_geometry_v3/manifest.json')
    paths=[Path(__file__).resolve(),p/'diagnostic_v1/diagnostic.json',a/'assets/om_body_geometry_v3/manifest.json']+list(a.glob('*.py'))+[f for n in args.cases for f in n.rglob('*') if f.is_file()]
    inputs={str(f):sha(f) for f in paths};save(args.out.with_name(args.out.stem+'_before.json'),inputs)
    centre=np.array(read(p/'diagnostic_v1/diagnostic.json')['guitar_centre_G_m']);result={}
    for n in args.cases:
        report=read(n/'report.json');initial=read(n/'initial_values.json');state=initial['native_initial_state'];steps=report['physics_steps'];controls=report['control_steps']
        assert report['inputs_unchanged'] and not report['forbidden_calls'] and not report['strap_enabled'] and not report['checkpoints_connected'] and report['training_updates']==0
        check=read(n/'initial_verification.json');assert all(check['invariants'].values()) and check['FK_ok'] and check['source_audit']['source_clear']
        assert abs(report['physics_seconds']-steps/240)<1e-12 and controls*4<=steps<=controls*4+3
        rows=read(n/'media/physics_endpoint_contacts.json')['rows'] if steps else [];assert len(rows)==steps
        gs=[state['guitar_body_states'][0]]+[row['guitar_body_states']['guitar'] for row in rows];poses=[pose(s) for s in gs];rot=Rotation.from_quat([r.as_quat() for _,r in poses]);pos=np.array([g for g,_ in poses]);body=pos+rot.apply(centre)
        displacement=np.linalg.norm(body-body[0],axis=1)*1000;angles=np.rad2deg((rot[0].inv()*rot).magnitude());angular=np.array([np.linalg.norm([s['vel']['angular'][k] for k in 'xyz']) for s in gs])
        contacts={field:sum(bool(row[field]) for row in rows) for field in ('left_arm_hand_guitar_contacts','right_upper_arm_body_contacts','right_thorax_body_contacts','right_forearm_body_contacts','right_distal_guitar_contacts','right_hip_body_contacts','chest_guitar_contacts','trunk_guitar_contacts')}
        if steps:
            tracking=read(n/'media/left_wrist_tracking_rows.json')['rows'];body_commands=read(n/'media/body_effort_rows.json')['rows'];actuator=read(n/'media/effort_control_rows.json')
            assert actuator['right_effort_calls']==steps and len(body_commands)>=steps and len(tracking)>=steps
            for k in range(steps):
                t=tracking[k];command=body_commands[k];assert t['physics_step']==command['physics_step']==k and rows[k]['physics_step']==k+1
                assert not t['enabled'] and np.array_equal(t['virtual_force_request_W_N'],np.zeros(3)) and np.array_equal(t['task_left_Nm'],np.zeros(12))
                assert np.array_equal(command['final_efforts_Nm'],t['actual_combined_submitted_efforts_Nm']) and np.isfinite(command['final_efforts_Nm']).all()
        complete=bool(report['completed'] and steps==1200);late=rows[1080:] if complete else None
        result[n.name]={'completed_5s':complete,'physics_steps':steps,'completed_control_steps':controls,'incomplete_control_physics_steps':steps-controls*4,'physics_seconds':steps/240,'failure':report['failure'],
            'source_native_initial_verification_passed':True,'left_task_zero_on_applied_steps':True,'actual_left_contact_steps':contacts['left_arm_hand_guitar_contacts'],
            'left_free_5s':bool(complete and contacts['left_arm_hand_guitar_contacts']==0),'contacts':contacts,
            'maximum_BBcentre_displacement_mm_240Hz':float(displacement.max()),'final_BBcentre_displacement_mm':float(displacement[-1]),
            'maximum_SO3_delta_deg_240Hz':float(angles.max()),'final_SO3_delta_deg':float(angles[-1]),'final_native_angular_speed_rad_s':float(angular[-1]),
            'late4_to5_BBcentre_change_mm':float(np.linalg.norm(body[1200]-body[960])*1000) if complete else None,
            'late4_to5_SO3_change_deg':float(np.rad2deg((rot[960].inv()*rot[1200]).magnitude())) if complete else None,
            'last120_contacts':{field:sum(bool(row[field]) for row in late) for field in contacts} if complete else None,
            'initial_BBcentre_W_m':body[0].tolist(),'initial_q_deg':dict(zip(initial['joint_names'],np.rad2deg(initial['q_ref_rad']).tolist())),
            'videos':{key:{'path':value['path'],'duration':value['stream']['duration'],'frames':value['stream']['nb_read_frames']} for key,value in report['videos'].items()},
            'scope':'actual applied commands only; pending requests beyond step count are excluded; source/local-BB centre transformed to world, not COM/world-axis AABB; no passive equilibrium or fret/strike success claim'}
    assert all(sha(f)==h for f,h in inputs.items());save(args.out,{'passed':True,'input_sha256':inputs,'cases':result,'scope':'evidence audit; left_free_5s is independent of physical guitar naturalness and drift acceptance'})
    for key,row in result.items():print(key,row['physics_seconds'],'left_free_5s',row['left_free_5s'],'BBmm',row['final_BBcentre_displacement_mm'],'SO3deg',row['final_SO3_delta_deg'])

if __name__=='__main__':main()
