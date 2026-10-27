"""Measured guitar motion and contact intervals, independent of requested stage names."""
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .left_grip_release_cycle_v2 import TIMES,STAGES


def longest_run(mask):
    best=run=0
    for x in mask:
        run=run+1 if x else 0;best=max(best,run)
    return best/240


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    n=args.native.resolve();out=args.out.resolve();assert not out.exists()
    diagnostic=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/diagnostic_v1/diagnostic.json')
    paths=[Path(__file__).resolve(),Path(__file__).with_name('left_grip_release_cycle_v2.py'),Path(__file__).with_name('initial_pose_noise_v1.py'),diagnostic,
           n/'report.json',n/'initial_values.json',n/'media/physics_endpoint_contacts.json',n/'media/left_cycle_contacts.json',n/'media/left_cycle_efforts.json',n/'media/left_cycle_targets.json',n/'attempt.json']
    inputs={str(p):sha(p) for p in paths};save(out.with_name(out.stem+'_before.json'),inputs)
    initial=read(n/'initial_values.json')['native_initial_state'];ep=read(n/'media/physics_endpoint_contacts.json')['rows'];cr=read(n/'media/left_cycle_contacts.json')['rows'];eff=read(n/'media/left_cycle_efforts.json')['rows'];targets=read(n/'media/left_cycle_targets.json')['rows']
    assert len(ep)==len(cr)==len(eff) and [r['physics_step'] for r in ep]==[r['physics_step'] for r in cr]
    assert [r['physics_step'] for r in ep]==list(range(1,len(ep)+1))
    assert [r['physics_step'] for r in eff]==list(range(len(eff)))
    assert [r['physics_step_before'] for r in targets]==list(range(0,len(ep),4))
    states=[initial['guitar_body_states'][0]]+[r['guitar_body_states']['guitar'] for r in ep]
    root=np.array([pose(s)[0] for s in states]);rot=Rotation.from_quat([pose(s)[1].as_quat() for s in states]);center=np.array(read(diagnostic)['guitar_centre_G_m']);body=root+rot.apply(center)
    dt=np.arange(len(body))/240;positive=[];paired=[];free=[]
    for row in cr:
        contacts=[c for c in row['left_guitar_contacts'] if any(n.startswith('human/LH:') or n in ('human/L_Thorax','human/L_Shoulder','human/L_Elbow','human/L_Wrist') for n in (c['body0_name'],c['body1_name']))];digits=set()
        for c in contacts:
            if c['lambda']<=0:continue
            names=[x for x in (c['body0_name'],c['body1_name']) if x.startswith('human/LH:')]
            digits.update(x.split(':')[1].rstrip('123') for x in names)
        positive.append(bool(digits));paired.append('thumb' in digits and bool(digits & {'index','middle','ring','pinky'}));free.append(not contacts)
    results=[]
    for k,name in enumerate(STAGES):
        start,end=TIMES[k:k+2];idx=np.flatnonzero((dt>start+1e-9)&(dt<=end+1e-9));cidx=idx-1
        if not len(idx):continue
        base=min(int(round(start*240)),len(body)-1)
        movement=np.linalg.norm(body[idx]-body[base],axis=1)*1000;angle=np.rad2deg((rot[base].inv()*rot[idx]).magnitude())
        contact_rows=[cr[i] for i in cidx];support={field:sum(bool(ep[i][field]) for i in cidx) for field in ('right_upper_arm_body_contacts','right_hip_body_contacts','right_thorax_body_contacts','right_forearm_body_contacts')}
        results.append({'stage':name,'start_s':float(start),'end_s':float(dt[idx[-1]]),'samples':len(idx),
            'max_body_change_from_stage_start_mm':float(movement.max()),'final_body_change_from_stage_start_mm':float(movement[-1]),'max_SO3_from_stage_start_deg':float(angle.max()),
            'thumb_plus_other_positive_contact_samples':int(sum(paired[i] for i in cidx)),
            'longest_thumb_plus_other_positive_contact_s':longest_run([paired[i] for i in cidx]),
            'all_left_guitar_contact_free_samples':int(sum(free[i] for i in cidx)),
            'longest_all_left_guitar_contact_free_s':longest_run([free[i] for i in cidx]),
            'contact_bodies':sorted({x for r in contact_rows for c in r['left_guitar_contacts'] for x in (c['body0_name'],c['body1_name']) if x.startswith('human/LH:') or x in ('human/L_Thorax','human/L_Shoulder','human/L_Elbow','human/L_Wrist')}),
            'support_contact_samples':support,'max_wrist_task_error_mm':max(eff[i]['point_error_m'] for i in cidx)*1000})
    wrist=np.array([pose(r['wrist_state'])[0] for r in cr]);wlocal=rot[1:].inv().apply(wrist-root[1:]);prep=min(480,len(body)-1)
    config=read(read(n/'report.json')['config']);props=read(n/'initial_values.json')['PD_properties'];names=read(n/'initial_values.json')['joint_names'];q0=np.array(read(n/'initial_values.json')['q_ref_rad'])
    goals=np.vstack([q0]+[r['final81_rad'] for r in targets]);rates=np.array([config['target_rates_rad_s']['body' if name.startswith(('Torso_','Spine_','Chest_')) else 'head' if name.startswith(('Neck_','Head_')) else 'finger' if ':' in name else 'arm'] for name in names])
    final=np.array([r['actual_submitted_efforts81_Nm'] for r in eff]);caps=np.array(props['effort'])
    for row in results:
        ix=np.flatnonzero((dt[1:]>row['start_s']+1e-9)&(dt[1:]<=row['end_s']+1e-9))
        row['mean_actual_wrist_G_m']=wlocal[ix].mean(axis=0).tolist()
    invariants={'target_rates_within_caps':bool(np.all(abs(np.diff(goals,axis=0))<=rates/60+2e-6)),'target_model_limits':bool(np.all(goals>=np.array(props['lower'])-1e-6) and np.all(goals<=np.array(props['upper'])+1e-6)),'efforts_finite_within_caps':bool(np.isfinite(final).all() and np.all(abs(final)<=caps+1e-6)),'inputs_unchanged':all(sha(p)==h for p,h in inputs.items()),'native_inputs_unchanged':read(n/'report.json')['inputs_unchanged'],
                'forbidden_calls_zero':not read(n/'report.json')['forbidden_calls'],'endpoint_coverage':len(ep)==read(n/'report.json')['physics_steps'],
                'other48_targets_exact':all(r['other48_targets_exact'] for r in targets),'other69_efforts_exact':all(r['other69_efforts_exact'] for r in eff)}
    measured={'completed_execution':read(n/'report.json')['completed'],'duration_s':float(dt[-1]),'body_center_G_m':center.tolist(),
              'maximum_body_from_initial_mm':float(np.linalg.norm(body-body[0],axis=1).max()*1000),'maximum_rotation_from_initial_deg':float(np.rad2deg((rot[0].inv()*rot).magnitude()).max()),
              'maximum_body_from2s_mm':float(np.linalg.norm(body[prep:]-body[prep],axis=1).max()*1000),'maximum_rotation_from2s_deg':float(np.rad2deg((rot[prep].inv()*rot[prep:]).magnitude()).max()),
              'stages':results,'wrist_neck_axis_extent_mm':float(np.ptp(wlocal[:,1])*1000),'body_initial_W_m':body[0].tolist(),'body_final_W_m':body[-1].tolist(),
              'left_contact_scope':'precise left arm/hand body names; fixed L_Hip excluded; original query rows preserved',
              'scope':'BB body centre, not actor root; raw lambda positive thumb+other is contact concurrence, not certified force closure; contact-free counts include all left arm/hand native query contacts, even zero lambda'}
    save(out,{'input_sha256':inputs,'invariants':invariants,'measured':measured});assert all(invariants.values());print(measured,flush=True)


if __name__=='__main__':main()
