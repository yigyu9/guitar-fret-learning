"""Compare requested EFFORT damping pulses and retained original activation data."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    phase=args.phase.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    names=('d0_off','d0_on','d1_off','d1_on')
    old=phase.parent/'human_effort_activation_probe_v2'
    files=[Path(__file__).resolve()]
    for n in names:
        files += [phase/n/'data'/f for f in ('report.json','states.json','commands.json','initial_values.json')]
        files += [phase/n/f for f in ('inputs_before.json','inputs_after.json')]
    files += [old/n/'data/states.json' for n in ('off','on')]
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    hashes={str(p):digest(p) for p in files};read=lambda p:json.loads(p.read_text())
    write=lambda n,d:(out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    write('inputs_before.json',{'sha256':hashes})
    initial={n:read(phase/n/'data/initial_values.json') for n in names}
    assert all(v['native_initial_state']==initial['d0_off']['native_initial_state'] for v in initial.values())
    joints=initial['d0_off']['joint_names'];indices=[joints.index('R_Shoulder_'+a) for a in 'xyz']
    states={n:{r['physics_step']:r['native_state'] for r in read(phase/n/'data/states.json')} for n in names}
    reports={};reproduction={};rows=[]
    for n in names:
        report=read(phase/n/'data/report.json');closure=read(phase/n/'inputs_after.json')
        assert report['completed_5s'] and report['physics_steps']==1200 and report['frame_count']==151 and all(report['checks'].values())
        assert closure['inputs_unchanged'] and closure['task_error'] is None
        assert all(digest(Path(v['path']))==v['sha256'] for v in report['videos'].values())
        commands=read(phase/n/'data/commands.json');assert len(commands)==300
        for row in commands:
            torque=np.array(row['requested_human_joint_torque_Nm']);assert torque.shape==(81,) and np.isfinite(torque).all()
            if row['before_physics_step'] or n.endswith('_off'):assert np.count_nonzero(torque)==0
        reports[n]={'report':report,'closure':closure}
    for setting in ('off','on'):
        saved=read(old/setting/'data/states.json');n='d0_'+setting
        reproduction[n]={'matched_samples':sum(states[n][r['physics_step']]==r['native_state'] for r in saved),'compared_samples':len(saved)}
        assert reproduction[n]['matched_samples']==reproduction[n]['compared_samples']
    vector=lambda s,k:np.array([r[k] for r in s['human_dof_states']])
    for step in range(1,5):
        for label,a,b in (('torque_d0','d0_on','d0_off'),('torque_d1','d1_on','d1_off'),('damping_off','d1_off','d0_off'),('damping_on','d1_on','d0_on')):
            dq=vector(states[a][step],'pos')-vector(states[b][step],'pos')
            dv=vector(states[a][step],'vel')-vector(states[b][step],'vel')
            rows.append({'comparison':label,'physics_step':step,'q_delta_rad':dq.tolist(),'qdot_delta_rad_s':dv.tolist(),
                'shoulder_q_delta_rad':dq[indices].tolist(),'shoulder_qdot_delta_rad_s':dv[indices].tolist()})
    summary={'initial_states_exact':True,'zero_damping_reproduction':reproduction,'reports':reports,
        'step4_responses':[r for r in rows if r['physics_step']==4],
        'scope':'requested EFFORT damping and four-step pulse observations; not isolated measured drive torque or certification of all-joint damping/full-song performance; no learning'}
    write('rows.json',rows);write('summary.json',summary)
    unchanged=all(digest(Path(p))==h for p,h in hashes.items());write('inputs_after.json',{'unchanged':unchanged,'input_count':len(hashes)})
    assert unchanged
    print(json.dumps([{k:r[k] for k in ('comparison','shoulder_q_delta_rad','shoulder_qdot_delta_rad_s')} for r in summary['step4_responses']]))


if __name__=='__main__':main()
