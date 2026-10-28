"""CPU fixed-state priority-token sensitivity; no physics or fitting."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent/'index_prefix_goal_codec_v1'
ROOT=HERE.parents[4]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v

def main():
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    inputs={}
    def track(p):p=Path(p).resolve();inputs[str(p)]=sha(p);return p
    def read(p):return json.loads(track(p).read_text())
    review=read(GOAL/'analysis/results_recovery_v1/review.json');assert review['verdict']=='PASS' and not review['findings']
    checked=review['reviewed_sha256']
    def reviewed(p):
        p=track(p);assert inputs[str(p)]==checked[str(p)];return json.loads(p.read_text())
    window=reviewed(GOAL/'analysis/results_recovery_v1/release_window.json')
    tokens=reviewed(GOAL/'analysis/results_recovery_v1/release_tokens.json')
    comparison=reviewed(GOAL/'analysis/results_recovery_v1/comparison.json')
    folder=GOAL/'recovery_v1/runs/evaluate';contract=read(folder/'training_contract.json')
    checkpoint=track(GOAL/'runs/fit/initial.pt');assert inputs[str(checkpoint)]=='70e40d1cb80a90a2636fd7d1babb4870bd82333d900c667fa136bac233ef9327'
    for p in (Path(__file__),HERE/'PLAN.md',GOAL/'probe.py',GOAL/'codec.py',ROOT/'guitar_learning/gpu/environment.py',ROOT/'guitar_learning/gpu/finger_reward.py',ROOT/'guitar_learning/skills/finger_skill_policy.py',ROOT/'guitar_learning/training/policy.py',ROOT/'guitar_learning/training/gpu_pool.py'):
        track(p)
    sys.path.insert(0,str(ROOT))
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import FIELDS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    d=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));selected=np.flatnonzero(d['phase']==2)
    assert len(selected)==window['actual_rows']==24
    observations={k:torch.from_numpy(d[k][selected].copy()) for k in FIELDS};original={k:v.clone() for k,v in observations.items()}
    assert observations['state'].shape==(24,561) and observations['priority_events'].shape==(24,8,24)
    record={(v['env_id'],v['start_clock']):v for v in tokens['records']};release={(v['env_id'],v['start_clock']):v for v in window['rows']}
    assert len(release)==24 and len(record)==len(tokens['records'])
    slots=contract['observation']['finger_targets']['slots'];ids=[slots.index('index_tracking'),slots.index('index_next')];assert ids==[0,1]
    cf={k:v.clone() for k,v in observations.items()};mapping=[];scales=np.asarray(contract['observation']['event_scales'],dtype=np.float32)
    columns={'onset_delta_s':0,'end_delta_s':1,'press_delta_s':2,'current':7,'preparing':8,'surface_candidate_now':9,'surface_wrong_now':10,'released':14}
    for j,k in enumerate(selected):
        key=(int(d['env_id'][k]),int(d['start_clock'][k]));r=record[key];w=release[key]
        assert np.array_equal(d['raw_goal_normalized'][k],np.asarray(w['raw_goal4'],dtype=np.float32))
        chosen=[]
        for source_index in (4,7):
            candidates=[v for v in r['events'] if v['source_index']==source_index];assert len(candidates)==1
            token=candidates[0];slot=token['slot'];assert observations['mask'][j,slot]
            for name,col in columns.items():assert float(observations['events'][j,slot,col]*scales[col])==token['features'][name]
            chosen.append(slot)
        assert observations['priority_mask'][j,ids].all()
        for a,b in zip(ids,chosen):cf['priority_events'][j,a]=observations['events'][j,b]
        mapping.append(dict(env_id=key[0],start_clock=key[1],clock=int(d['clock'][k]),main_slots=chosen,original_priority_sources=[v['source_index'] for v in r['index_priority']],counterfactual_priority_sources=[4,7]))
    assert all(torch.equal(cf[k],original[k]) for k in FIELDS if k!='priority_events')
    assert torch.equal(cf['priority_events'][:,2:],original['priority_events'][:,2:])
    unchanged=(cf['priority_events']==original['priority_events']).all(-1).all(-1);assert int(unchanged.sum())==4 and unchanged[:4].all() and not unchanged[4:].any()
    probe=module('priority_release_goal_producer',GOAL/'probe.py');codec=probe.support()
    track(probe.parent.__file__);track(probe.parent.support().__file__)
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    policy=codec.policy_type(probe)(contract=contract,size='large',fresh=False);assert policy.architecture==payload['identity']['architecture']
    policy.load_state_dict(payload['model'],strict=True);policy.eval();weights={n:v.clone() for n,v in policy.state_dict().items()};assert len(weights)==73
    def predict(obs):return policy(*(obs[k] for k in FIELDS))['mean'][:,17:21].tanh()
    with torch.no_grad():
        baseline=predict(observations);noop=predict({k:v.clone() for k,v in observations.items()});changed=predict(cf)
    assert torch.equal(baseline,noop) and torch.equal(baseline[unchanged],changed[unchanged])
    residual=float((baseline-torch.from_numpy(d['raw_goal_normalized'][selected])).abs().max())
    tolerance=comparison['raw_goal_model_CPU_max_abs_residual'];assert residual<=tolerance,(residual,tolerance)
    assert all(torch.equal(v,weights[n]) for n,v in policy.state_dict().items()) and all(torch.equal(observations[k],original[k]) for k in FIELDS)
    action=contract['action']['target_contract'];active=[action['joint_names'].index(n) for n in action['action_order']];ai=contract['task']['short_learning']['learned_action_indices']
    ref=torch.tensor(action['reference105_rad'])[active][ai];low=torch.tensor(action['action_lower_rad'])[ai];high=torch.tensor(action['action_upper_rad'])[ai]
    base_deg=torch.rad2deg(codec.decode(baseline,ref,low,high)).numpy();cf_deg=torch.rad2deg(codec.decode(changed,ref,low,high)).numpy()
    rows=[];baseN=[];cfN=[];baseDesired=[];cfDesired=[]
    for j,k in enumerate(selected):
        m=mapping[j];w=release[m['env_id'],m['start_clock']];native_deg=np.rad2deg(d['decoded_goal_rad'][k]);bn=np.asarray(w['decoded_minus_full_N_deg'])+base_deg[j]-native_deg;cn=np.asarray(w['decoded_minus_full_N_deg'])+cf_deg[j]-native_deg
        bd=np.asarray(w['decoded_minus_scheduled_desired_deg'])+base_deg[j]-native_deg;cd=np.asarray(w['decoded_minus_scheduled_desired_deg'])+cf_deg[j]-native_deg
        baseN.append(bn);cfN.append(cn);baseDesired.append(bd);cfDesired.append(cd)
        rows.append(dict(m,noop=bool(unchanged[j]),original_saved_raw4=w['raw_goal4'],CPU_raw4=baseline[j].tolist(),counterfactual_raw4=changed[j].tolist(),original_saved_decoded_deg4=native_deg.tolist(),CPU_decoded_deg4=base_deg[j].tolist(),counterfactual_decoded_deg4=cf_deg[j].tolist(),counterfactual_minus_CPU_deg4=(cf_deg[j]-base_deg[j]).tolist(),CPU_minus_N_deg4=bn.tolist(),counterfactual_minus_N_deg4=cn.tolist(),CPU_minus_scheduled_desired_deg4=bd.tolist(),counterfactual_minus_scheduled_desired_deg4=cd.tolist()))
    rms=lambda x:np.sqrt(np.mean(np.asarray(x)**2,axis=0)).tolist()
    summary=dict(rows=24,observed_envs=[0,1,2,3],noop_rows=4,replaced_rows=20,raw_CPU_max_abs_residual=residual,reused_CPU_tolerance=tolerance,
        reference_anchor_source='Reviewed release_window saved decoded-minus-N and decoded-minus-scheduled-desired plus change from original saved decoded angle; no clock reconstruction',
        maximum_abs_goal_change_deg4=np.max(abs(cf_deg-base_deg),axis=0).tolist(),RMS_to_full_N_deg4=dict(original=rms(baseN),counterfactual=rms(cfN)),RMS_to_scheduled_desired_deg4=dict(original=rms(baseDesired),counterfactual=rms(cfDesired)),
        checks=dict(state_other_observations_unchanged=True,other_six_priority_slots_unchanged=True,model73_exact_unchanged=True,noop_input_and_first_four_outputs_exact=True,main_copy_no_rescaling=True,no_clock_reconstruction=True,no_physical_rollout=True),
        scope='Fixed24 saved states only; both shared finger encoder and index head see priority replacement; not training causality/information absence/release success/128generalization')
    # Direct inputs only; no inherited native seal traversal.
    assert all(sha(p)==h for p,h in inputs.items())
    out.mkdir();(out/'comparison.json').write_text(json.dumps(dict(summary=summary,rows=rows),ensure_ascii=False,indent=2)+'\n')
    with (out/'rows.csv').open('w',newline='') as f:
        fields=['env_id','start_clock','clock','noop']+[name+'_'+str(i) for name in ('original_saved_raw','CPU_raw','counterfactual_raw','original_saved_decoded_deg','CPU_decoded_deg','counterfactual_decoded_deg','counterfactual_minus_CPU_deg','CPU_minus_N_deg','counterfactual_minus_N_deg','CPU_minus_scheduled_desired_deg','counterfactual_minus_scheduled_desired_deg') for i in range(4)]
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in rows:
            flat={k:r[k] for k in fields[:4]}
            for name in fields[4:]:base,i=name.rsplit('_',1);flat[name]=r[base+'4'][int(i)]
            writer.writerow(flat)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(9,5),sharex=True)
    for axis,col,title in zip(axes.flat,range(4),('MCP x','MCP z','PIP','DIP')):
        axis.plot(np.asarray(baseDesired)[:,col],label='Original CPU');axis.plot(np.asarray(cfDesired)[:,col],label='A4/B7 priority');axis.axhline(0,color='gray',lw=.7);axis.set_title(title);axis.set_ylabel('Goal error (deg)');axis.set_xlabel('Saved row (4 envs per control)');axis.grid(alpha=.2)
    axes.flat[0].legend();fig.suptitle('Goal minus original scheduled desired; fixed 24 saved states');fig.tight_layout(rect=(0,0,1,.94));fig.savefig(out/'priority_sensitivity.png',dpi=140);plt.close(fig)
    (out/'verification.json').write_text(json.dumps(dict(completed=True,CPU_only=True,GPU_executed=False,fit_executed=False,input_sha256=inputs,checks=summary['checks'],checkpoint_sha256=inputs[str(checkpoint)],direct_input_count=len(inputs)),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.execute:main()
    else:print('CPU fixed-state audit only; pass --execute; original inputs unchanged')
