"""The prescribed six release controls, four observed envs, no new physics."""
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('goal_release_actual_guard',HERE/'analyze_recovery.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
audit.complete(audit.read(audit.BASE/'02_launcher.json'),audit.read(audit.RECOVERY/'01_launcher.json'),audit.read(audit.BASE/'cpu_inputs/commands.json')['fit'],audit.read(audit.RECOVERY/'cpu_inputs/commands.json')['evaluate'])
assert (HERE/'results_recovery_v1/comparison.json').is_file()
recovery=audit.module('goal_release_recovery',audit.RECOVERY/'probe.py');probe=recovery.source;sys.path.insert(0,str(probe.grid.ROOT));codec=probe.support()
import numpy as np
import torch
from types import SimpleNamespace
from guitar_learning.tool.experiments.short_finger_learning import runner
torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
inputs={}
def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
folder=recovery.output('evaluate');d=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));g=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False));t=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False))
rows=audit.read(track(folder/'evaluation.json'))['episodes'];contract=audit.read(track(folder/'training_contract.json'))['action']['target_contract'];short=probe.parent.settings()['song']['short_learning'];ids=short['learned_action_indices']
active=torch.tensor([contract['joint_names'].index(n) for n in contract['action_order']]);ref=torch.tensor(contract['reference105_rad'],dtype=torch.float32);N=torch.tensor(short['reference_release_schedule']['negative_selected_rad'],dtype=torch.float32)
old=ref[None].repeat(len(d['clock']),1);old[:,active[ids]]=torch.from_numpy(d['old_target_rad']);incremental=torch.zeros(39,dtype=torch.bool);incremental[17:33]=True
fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=incremental,controller=SimpleNamespace(reference=ref,target=old,active=active,action_low=torch.tensor(contract['action_lower_rad']),action_high=torch.tensor(contract['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
reference=runner.read_reference(track(probe.parent.base.pre.INPUTS['index'][1]),short);desired=codec.desired_reference(probe,fake,reference)[:,ids].numpy();normalized_N=codec.encode(N,*codec.bounds(fake)).numpy()
N_direction=np.sign(N.numpy()-np.asarray(short['reference_release_schedule']['reference_selected_rad']))
selected=[]
for k in np.flatnonzero(d['phase']==2):
    i=int(d['env_id'][k]);clock=int(d['clock'][k]);start=int(d['start_clock'][k]);control=start//4
    value=dict(env_id=i,start_clock=start,clock=clock,current_goal=int(d['current_goal'][k]),
        raw_goal4=d['raw_goal_normalized'][k].tolist(),raw_goal_minus_full_N4=(d['raw_goal_normalized'][k]-normalized_N).tolist(),
        decoded_minus_full_N_deg=np.rad2deg(d['decoded_goal_rad'][k]-N.numpy()).tolist(),decoded_minus_scheduled_desired_deg=np.rad2deg(d['decoded_goal_rad'][k]-desired[k]).tolist(),
        physical_requested4=d['requested_NN_action'][k].tolist(),request_toward_N_sign4=(d['requested_NN_action'][k]*N_direction>0).tolist(),
        oldtarget_minus_full_N_deg=np.rad2deg(d['old_target_rad'][k]-N.numpy()).tolist(),finaltarget_minus_full_N_deg=np.rad2deg(d['final_target_rad'][k]-N.numpy()).tolist(),
        actual_target_increment_deg=np.rad2deg(d['final_target_rad'][k]-d['old_target_rad'][k]).tolist(),raw_DIP_target_rad=float(d['raw_DIP_target_rad'][k]),final_DIP_target_rad=float(d['final_DIP_target_rad'][k]),
        current_goal_candidate=bool(g['candidate'][control,i]),current_goal_wrong=bool(g['wrong'][control,i]),eligible=bool(g['eligible'][control,i]),blocked=bool(g['blocked'][control,i]))
    if i==0:
        endpoint=clock//4-1;value.update(env0_postcontrol_candidate3=t['candidate'][endpoint].tolist(),env0_postcontrol_wrong3=t['wrong'][endpoint].tolist())
    selected.append(value)
release=[r['notes'][0] for r in rows];cross={str(a):{str(rel):sum(bool(n['achieved'])==a and bool(n['released'])==rel for n in release) for rel in (False,True)} for a in (False,True)}
released_delays=np.asarray([n['release_s'] for n in release if n['released']],dtype=float)
track(Path(__file__));result=dict(rows=selected,observed_envs=[0,1,2,3],rows_expected_if_all_complete=24,actual_rows=len(selected),normalized_full_N4=normalized_N.tolist(),N_direction_sign4=N_direction.tolist(),A_achieved_release_cross=cross,
    native_A_release_s_for_released_summary=dict(count=len(released_delays),minimum=float(released_delays.min()) if len(released_delays) else None,median=float(np.median(released_delays)) if len(released_delays) else None,maximum=float(released_delays.max()) if len(released_delays) else None),
    input_sha256=inputs,scope='phase2 is original request-endpoint six-control window; full N and instantaneous scheduled desired are distinct; candidate here is postcontrol60Hz only env0, currentgoal guard candidate may be B not A; native release_s is its original ledger quantity, no inferred240Hz event or full skin separation')
out=HERE/'results_recovery_v1/release_window.json';assert not out.exists();probe.grid.write(out,result)
print('해제창 관측 행',len(selected),'A 달성/해제 교차',cross)
