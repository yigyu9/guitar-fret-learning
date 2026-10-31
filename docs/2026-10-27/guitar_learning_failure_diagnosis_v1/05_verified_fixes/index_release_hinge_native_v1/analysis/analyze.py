"""Read-only native trace analysis. Does not import physics/runtime or edit inputs."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
MODES = ('baseline', 'candidate')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
files = [p for mode in MODES for p in (ROOT/'runs'/mode).iterdir() if p.is_file()]
files += [ROOT/'cpu_inputs/candidate.json', ROOT/'cpu_verification.json']
reference = ROOT.parent/'index_release_clearance_v1/runs/reference/trace_env0_episode0.npz'
files.append(reference)
before = {str(p):sha(p) for p in files}
config = json.loads((ROOT/'cpu_inputs/candidate.json').read_text())['song']['short_learning']
metadata = json.loads((ROOT/'runs/candidate/trace_metadata.json').read_text())
joints = metadata['joint_names']; bodies = metadata['body_names']
notes = config['view']['source_targets']; offset = config['view']['score_offset_s']
audible = [(n['onset_s']-offset,n['end_s']-offset) for n in notes]
bounds = config['reference_release_schedule']['phase_boundaries_local_s']
result = {'scope':'no-NN deterministic native diagnostic, not policy training/performance', 'denominator':{'attempts_per_condition':128,'notes_per_condition':384,'failed_attempts_retained':True},'audible_local_s':audible,'phase_boundaries_local_s':bounds,'runs':{}}
traces={}; surfaces={}
for mode in MODES:
    folder=ROOT/'runs'/mode
    evaluation=json.loads((folder/'evaluation.json').read_text()); episodes=evaluation['episodes']
    trace=np.load(folder/'trace_env0_episode0.npz'); surface=np.load(folder/'release_clearance4.npz')
    traces[mode]=trace; surfaces[mode]=surface
    rewards={k:{'sum':float(sum(e['reward_components'][k] for e in episodes)), 'mean':float(np.mean([e['reward_components'][k] for e in episodes]))} for k in episodes[0]['reward_components']}
    rs={'attempts':len(episodes),'invalid':sum(not e['valid'] for e in episodes),'achieved_all3':sum(e['achieved'] for e in episodes),'reward':{'sum':sum(e['reward'] for e in episodes),'mean':float(np.mean([e['reward'] for e in episodes]))},'reward_components':rewards,'cost_sum':sum(e['cost'] for e in episodes),'acceptance':evaluation['acceptance'],'report':json.loads((folder/'report.json').read_text()),'per_note':[]}
    assert len(episodes)==128 and all(len(e['notes'])==3 for e in episodes)
    for i,idx in enumerate((4,7,8)):
        ns=[e['notes'][i] for e in episodes]
        rs['per_note'].append({'source_index':idx,'denominator':128,'achieved':sum(n['achieved'] for n in ns),'released':sum(n['released'] for n in ns),'clean_mean':float(np.mean([n['clean_fraction'] for n in ns])),'clean_min':min(n['clean_fraction'] for n in ns),'wrong_mean':float(np.mean([n['audible_wrong_fraction'] for n in ns])),'missing_mean':float(np.mean([n['missing_fraction'] for n in ns])),'achieved_and_released':sum(n['achieved'] and n['released'] for n in ns),'failed_achievement_and_released':sum(not n['achieved'] and n['released'] for n in ns)})
    local=surface['clock']/240
    phase=(local>=bounds[1]) & (local<=bounds[2])
    minimum=surface['point_signed_height'].min(axis=1)*1000
    rs['surface']={'all_rows':len(local),'env_ids':np.unique(surface['env_id']).tolist(),'valid_rows':int(surface['valid_snapshot'].sum()),'post_failure_rows':int(surface['post_failure'].sum()),'phase3_rows':int(phase.sum()),'phase3_min_signed_height_mm':float(minimum[phase].min()),'phase3_rows_ge_5mm':int((minimum[phase]>=5).sum()),'phase3_loaded_rows':int(surface['body_loaded'][phase].sum()),'phase3_candidate_rows':int(surface['candidate'][phase].sum()),'scope':'all original128 distal samples per saved endpoint; 4env only; not 128env trajectory maximum'}
    t=trace['time_s']; onset=np.flatnonzero(t>=audible[1][0])[0]
    rs['B7_first_onset_endpoint']={'local_s':float(t[onset]),'PIP_actual_deg':float(np.rad2deg(trace['q'][onset,joints.index('LH:index2')])),'PIP_target_deg':float(np.rad2deg(trace['target'][onset,joints.index('LH:index2')])),'DIP_actual_deg':float(np.rad2deg(trace['q'][onset,joints.index('LH:index3')])),'DIP_target_deg':float(np.rad2deg(trace['target'][onset,joints.index('LH:index3')]))}
    previous=onset-1
    rs['B7_onset_previous_endpoint']={'local_s':float(t[previous]),'PIP_actual_deg':float(np.rad2deg(trace['q'][previous,joints.index('LH:index2')])),'DIP_actual_deg':float(np.rad2deg(trace['q'][previous,joints.index('LH:index3')]))}
    def intervals(mask):
        starts=np.flatnonzero(mask & ~np.r_[False,mask[:-1]])
        ends=np.flatnonzero(mask & ~np.r_[mask[1:],False])
        return [[float(t[a]),float(t[b])] for a,b in zip(starts,ends)]
    rs['env0_B7_candidate_intervals_saved_endpoints_s']=intervals(trace['candidate'][:,1] & (t>=audible[1][0]) & (t<=audible[1][1]))
    rs['env0_B7_net_distal_force_zero_endpoints_in_audible']=int(((np.linalg.norm(trace['net_body_force_n'][:,bodies.index('human/LH:index3')],axis=1)==0)&(t>=audible[1][0])&(t<=audible[1][1])).sum())
    pins=json.loads((folder/'inputs_after.json').read_text());rs['input_pin_count']=len(pins['input_pins']);rs['input_pin_changed_paths']=pins['changed_paths']
    result['runs'][mode]=rs
ref=np.load(reference); base=traces['baseline']
keys=('q','target','body_state','candidate','wrong','released','release_s')
result['historical_baseline_exact']={k:bool(np.array_equal(base[k],ref[k])) for k in keys}
diff=np.any(traces['candidate']['decoded_goal_rad']!=base['decoded_goal_rad'],axis=1)
first=int(np.flatnonzero(diff)[0]);result['first_changed_action']={'endpoint_local_s':float(base['time_s'][first]),'action_start_local_s':float(base['time_s'][first]-1/60),'A_end_local_s':audible[0][1]}
result['noise']={'stage_ready':False,'native_noisy_runs':0,'note':'noisy mode invocation was blocked by pre-IsaacGym musical gate; invocation log is not a native noisy run'}
result['static_vs_native']={'static_candidate_clearance_mm':7.56,'static_scope':'prepared anchor/qtarget geometry prediction; not a native trajectory clearance guarantee','native_candidate_min_mm':result['runs']['candidate']['surface']['phase3_min_signed_height_mm'],'causal_limit':'actual q tracking, index1 frame/anchor and wrist pose can differ from static conditions; these traces do not isolate their individual causal contributions'}
# Representative env0 traces: targets, actual joints, force and loaded candidate timing.
fig,axes=plt.subplots(5,1,figsize=(13,12),sharex=True)
colors={'baseline':'#386cb0','candidate':'#e17c05'}
for mode in MODES:
    a=traces[mode]; t=a['time_s']; c=colors[mode]
    for ax,j in zip(axes[:2],('LH:index2','LH:index3')):
        ix=joints.index(j); ax.plot(t,np.rad2deg(a['q'][:,ix]),c=c,label=mode+' actual');ax.plot(t,np.rad2deg(a['target'][:,ix]),c=c,ls='--',alpha=.6,label=mode+' target')
    force=np.linalg.norm(a['net_body_force_n'][:,bodies.index('human/LH:index3')],axis=1)
    axes[2].plot(t,force,c=c,label=mode+' index3 net body force')
    for i in range(3): axes[3].step(t,a['candidate'][:,i].astype(float)+i*1.2+(0.12 if mode=='candidate' else 0),where='post',c=c,label=mode+f' note{(4,7,8)[i]}')
    s=surfaces[mode]; keep=s['env_id']==0; st=s['clock'][keep]/240
    axes[4].step(st,s['body_loaded'][keep].astype(float)+(0.12 if mode=='candidate' else 0),where='post',c=c,label=mode+' distal loaded')
for ax,label in zip(axes,['PIP (deg)','DIP (deg)','Net force (N)','Candidate (offset)','Loaded (offset)']):
    ax.set_ylabel(label);ax.grid(alpha=.25)
    for i,(start,end) in enumerate(audible): ax.axvspan(start,end,color='#66c2a5',alpha=.12);ax.text((start+end)/2,.97,f'A4' if i==0 else f'B{(7,8)[i-1]}',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=8)
    for b in bounds: ax.axvline(b,c='grey',lw=.7,ls=':')
axes[0].legend(ncol=2,fontsize=8);axes[2].legend(fontsize=8);axes[3].legend(ncol=3,fontsize=7);axes[4].legend(fontsize=8)
axes[-1].set_xlabel('Local episode seconds');fig.suptitle('Saved env0: actual/target tracking, body force, contact candidates, audible windows');fig.tight_layout();fig.savefig(OUT/'env0_motion_contact.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(3,1,figsize=(12,9),sharex=True)
for mode in MODES:
    s=surfaces[mode]
    for env in range(4):
        k=s['env_id']==env;t=s['clock'][k]/240;label=f'{mode} env{env}'
        axes[0].plot(t,s['point_signed_height'][k].min(axis=1)*1000,c=colors[mode],alpha=.65,label=label)
        axes[1].step(t,s['body_loaded'][k].astype(float)+env*1.3+(0.12 if mode=='candidate' else 0),c=colors[mode],where='post')
        axes[2].step(t,s['candidate'][k].astype(float)+env*1.3+(0.12 if mode=='candidate' else 0),c=colors[mode],where='post')
axes[0].axhline(5,c='black',ls='--',label='5mm design threshold');axes[0].axhline(0,c='grey',lw=.8)
for ax,l in zip(axes,['Minimum signed height (mm)','Distal loaded (env offsets)','A4 candidate (env offsets)']):
    ax.set_ylabel(l);ax.grid(alpha=.25);ax.axvspan(bounds[1],bounds[2],color='grey',alpha=.1)
axes[0].legend(ncol=3,fontsize=8);axes[-1].set_xlabel('Local episode seconds');fig.suptitle('Common original surface window: env0..3, 128 distal samples per endpoint');fig.tight_layout();fig.savefig(OUT/'surface_common_window.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4));x=np.arange(3);w=.36
for j,mode in enumerate(MODES):
    ns=result['runs'][mode]['per_note'];axes[0].bar(x+(j-.5)*w,[n['achieved']/128*100 for n in ns],w,label=mode,color=colors[mode]);axes[1].bar(x+(j-.5)*w,[n['clean_mean']*100 for n in ns],w,label=mode,color=colors[mode])
for ax,title in zip(axes,['Original note achievement / 128','Mean note clean fraction']): ax.set_xticks(x,['A4','B7','B8']);ax.set_ylim(0,105);ax.set_title(title);ax.set_ylabel('%');ax.legend();ax.grid(axis='y',alpha=.2)
axes[1].axhline(90,c='black',ls='--');fig.tight_layout();fig.savefig(OUT/'performance.png',dpi=160);plt.close(fig)
dump('analysis.json',result)
after={str(p):sha(p) for p in files}
checks={'inputs_unchanged':before==after,'all128_denominator':all(result['runs'][m]['attempts']==128 for m in MODES),'note_opportunities384':all(sum(n['denominator'] for n in result['runs'][m]['per_note'])==384 for m in MODES),'nine_reward_components':all(len(result['runs'][m]['reward_components'])==9 for m in MODES),'historical_baseline_exact':all(result['historical_baseline_exact'].values()),'phase3_104_rows':all(result['runs'][m]['surface']['phase3_rows']==104 for m in MODES),'candidate_phase3_no_loaded_or_candidate':result['runs']['candidate']['surface']['phase3_loaded_rows']==result['runs']['candidate']['surface']['phase3_candidate_rows']==0,'candidate_not_all_5mm':result['runs']['candidate']['surface']['phase3_rows_ge_5mm']<104,'gate_not_ready':not result['runs']['candidate']['acceptance']['stage_ready']}
dump('verification.json',{'all_checks_passed':all(checks.values()),'checks':checks,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'NN_constructors':0,'training_steps':0,'angle_grid_or_std_searches':0})
assert all(checks.values()), checks
print(json.dumps({'checks':checks,'runs':{m:{k:v for k,v in result['runs'][m].items() if k in ('achieved_all3','surface','B7_first_onset_endpoint','reward')} for m in MODES}},indent=2))
