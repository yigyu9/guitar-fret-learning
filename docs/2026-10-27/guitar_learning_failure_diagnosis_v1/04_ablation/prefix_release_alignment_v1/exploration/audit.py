"""Read-only CPU goal-noise units; one prescribed sigma formula, no tuning."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
DIAG=HERE.parents[2]
ROOT=HERE.parents[5]
GOAL=DIAG/'05_verified_fixes/index_prefix_goal_codec_v1'
SAMPLES=100000
SEED=7


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value


def report(v):
    names=['MCP x','MCP z','PIP','DIP'];lookup={(r['case'],r['axis'],r['distribution']):r for r in v['rows']};axes=[r['axis'] for r in v['rows'][:4]]
    lines=['# 목표각 탐색 단위 CPU 검사','','원saved log_std의 동일clamp[-5,2]/float32exp를 확인했다. effective std=%.17g, config와차이=%.3g이다. 이후 고정μ/σ와기존decode를float64로 평가했다. 원CUDA/float32정책잡음 bitexact 재현은 아니다.'%(v['original_effective_std'],v['config_minus_effective_std']),
        '공통 seed7/float64 표준정규100000×4를 N/Ref 및 사전지정env0 phase중간6행의 두sigma에 동일하게 사용했다. 원genuineGoalPolicy의6개μ만읽었고 후보sigma로정책을생성하거나원log_std/설정에쓰지않았다.','',
        'nominal=(4/60)·원effective std=%.12g rad=%.6f°. 이는 기존incremental neutral의 **1차 기준**이며 정확한 유한잡음RMS가 아니다.'%(v['nominal_rad'],v['nominal_deg']),'',
        '| 축 | L(rad/raw) | 공식후보 sigma |','|---|---:|---:|']
    for i,n in enumerate(names):lines.append('| %s | %.9f | %.11f |'%(n,v['L_rad_per_raw4'][i],v['candidate_sigma4'][i]))
    lines+=['','Δθ는 noisy goal−동일μ의 deterministic goal이다. 아래의초과비율은 |Δθ|>4/60의 **rateclip 전 목표노이즈** 비율이며 실제controller clip발생률이나관절변위가아니다. 전체64행의bias/1·5·50·95·99분위수/상한은 distribution.csv·comparison.json에 있다.','',
        '| 고정평균 | 축 | RMS 원→후보(도) | 평균편향 원→후보(도) | 초과비율 원→후보(%) |','|---|---|---:|---:|---:|']
    for case in ('N','Ref'):
        for i,axis in enumerate(axes):
            a,b=lookup[case,axis,'original'],lookup[case,axis,'candidate'];lines.append('| %s | %s | %.6f → %.6f | %.6f → %.6f | %.5f → %.5f |'%(case,names[i],a['RMS_deg'],b['RMS_deg'],a['bias_deg'],b['bias_deg'],100*a['rate_preclip_exceed_fraction'],100*b['rate_preclip_exceed_fraction']))
    lines+=['','decode의기울기는035기준양/음span이며 L은양쪽최댓값이다. 따라서 g(z)=decode(tanh z)에 대해 |g(μ+σε)−g(μ)|≤Lσ|ε|다. Gaussian모집단 E[ε²]=1일때 RMS≤Lσ=nominal(후보)이고, 유한표본의검산상한은 **Lσ·sqrt(mean(ε²))**다. 모집단nominal에모든표본RMS를무조건assert하지않았다. 표본 ε_RMS4=%s이며각행finite상한을별도로저장했다. 점별부등식의최대수치잔차 %.3g rad는float64반올림범위다.'%(v['epsilon_RMS4'],v['maximum_pointwise_bound_excess_rad']),
        'N의양/음span비대칭과tanh때문에 평균편향과실제RMS는μ/축마다달라진다. 후보는8case에서관측초과0건이지만 Gaussian의모집단꼬리확률0·모든목표증분rate이내를보장하지않는다. 원native가동범위/4rad/s/PD/cap/guard는수정하지않았고물리계산은하지않았다.',
        '사전phase중간행(짝수면뒤쪽중앙)의 start_clock: '+', '.join('%s=%s'%(c['case'],c['start_clock']) for c in v['cases'][2:])+'. 저장phase라벨/행순서로선정했으며성공사례사후선별이나시간확장은없다.',
        '원70e/73tensor·관측불변과원rawgoal CPU잔차 %.3g(선행허용 %.3g)을검증했다. 본검사는목표각확률산술/전역L후보공식검사이며실제움직임·힘·PPO효과/적절한탐색표준편차의최적성을증명하지않는다. 매개변수탐색/후보적용/새fit/GPU/native/모델저장0,직접입력SHA만확인했다.'%(v['raw_CPU_max_abs_residual'],v['reused_CPU_tolerance']),'','![목표노이즈 RMS 비교](exploration_units.png)']
    return '\n'.join(lines)+'\n'


def main():
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink();inputs={}
    def track(p):p=Path(p).resolve();inputs[str(p)]=sha(p);return p
    def read(p):return json.loads(track(p).read_text())
    review=read(GOAL/'analysis/results_recovery_v1/review.json');assert review['verdict']=='PASS' and not review['findings']
    comparison=read(GOAL/'analysis/results_recovery_v1/comparison.json');assert inputs[str(GOAL/'analysis/results_recovery_v1/comparison.json')]==review['reviewed_sha256'][str(GOAL/'analysis/results_recovery_v1/comparison.json')]
    folder=GOAL/'recovery_v1/runs/evaluate';contract=read(folder/'training_contract.json');short=contract['task']['short_learning']
    for p in (Path(__file__),HERE/'PLAN.md',HERE.parent/'PLAN.md',GOAL/'probe.py',GOAL/'codec.py',ROOT/'guitar_learning/skills/finger_skill_policy.py',ROOT/'guitar_learning/training/policy.py',ROOT/'guitar_learning/training/gpu_pool.py'):
        track(p)
    sys.path.insert(0,str(ROOT))
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import FIELDS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    data=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));frozen={k:data[k].copy() for k in FIELDS}
    selected=[];selection=[]
    for phase in range(6):
        indices=np.flatnonzero((data['env_id']==0)&(data['phase']==phase));assert len(indices)>0
        k=int(indices[len(indices)//2]);selected.append(k);selection.append(dict(case='phase'+str(phase),phase=phase,env_id=0,source_row=k,phase_samples=len(indices),start_clock=int(data['start_clock'][k]),clock=int(data['clock'][k])))
    probe=module('goal_exploration_producer',GOAL/'probe.py');codec=probe.support();track(probe.parent.__file__);track(probe.parent.support().__file__)
    checkpoint=track(GOAL/'runs/fit/initial.pt');assert inputs[str(checkpoint)]=='70e40d1cb80a90a2636fd7d1babb4870bd82333d900c667fa136bac233ef9327'
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False);policy=codec.policy_type(probe)(contract=contract,size='large',fresh=False)
    assert policy.architecture==payload['identity']['architecture'];policy.load_state_dict(payload['model'],strict=True);policy.eval();state={k:v.clone() for k,v in policy.state_dict().items()};assert len(state)==73
    with torch.no_grad():pred=policy(*(torch.from_numpy(data[k][selected].copy()) for k in FIELDS))
    action_ids=short['learned_action_indices'];mean=pred['mean'][:,action_ids].double();raw_residual=float((mean.tanh()-torch.from_numpy(data['raw_goal_normalized'][selected]).double()).abs().max())
    assert raw_residual<=comparison['raw_goal_model_CPU_max_abs_residual']
    action=contract['action']['target_contract'];active=[action['joint_names'].index(n) for n in action['action_order']]
    reference=torch.tensor(action['reference105_rad'],dtype=torch.float64)[active][action_ids];low=torch.tensor(action['action_lower_rad'],dtype=torch.float64)[action_ids];high=torch.tensor(action['action_upper_rad'],dtype=torch.float64)[action_ids]
    assert ((low<=reference)&(reference<=high)).all();L=torch.maximum(high-reference,reference-low);assert (L>0).all()
    config_std=float(short['initial_std']);assert config_std==0.1711710544767014
    saved_log_std=payload['model']['finger_log_std'][:4].clone();effective_log_std=saved_log_std.clamp(-5,2)
    assert torch.equal(pred['log_std'][:,action_ids],effective_log_std.expand(6,-1))
    saved_std=pred['log_std'][:,action_ids].exp().double();original_std=float(saved_std[0,0])
    assert torch.equal(saved_std,torch.full_like(saved_std,original_std)) and abs(original_std-config_std)<1e-8
    step=4/60;nominal=step*original_std;sigma=torch.full_like(L,nominal)/L;assert torch.isfinite(sigma).all() and (sigma>0).all() and torch.allclose(L*sigma,torch.full_like(L,nominal),atol=1e-17,rtol=0)
    schedule=short['reference_release_schedule'];goals=torch.tensor([schedule['negative_selected_rad'],schedule['reference_selected_rad']],dtype=torch.float64)
    raw=codec.encode(goals,reference,low,high);assert (raw.abs()<1).all();anchors=raw.atanh();assert torch.allclose(codec.decode(anchors.tanh(),reference,low,high),goals,atol=1e-15,rtol=0)
    means=torch.cat((anchors,mean));cases=[dict(case='N',source='original negative schedule'),dict(case='Ref',source='original reference schedule'),*selection]
    generator=torch.Generator(device='cpu').manual_seed(SEED);epsilon=torch.randn(SAMPLES,4,dtype=torch.float64,generator=generator);epsilon_rms=epsilon.square().mean(0).sqrt()
    rows=[];bound_excess=[]
    for case,mu in zip(cases,means):
        center=codec.decode(mu.tanh(),reference,low,high);assert torch.equal(codec.decode((mu+epsilon*0).tanh(),reference,low,high),center.expand(SAMPLES,-1))
        case.update(mean_latent4=mu.tolist(),deterministic_goal_deg4=torch.rad2deg(center).tolist())
        for label,std in (('original',torch.full_like(L,original_std)),('candidate',sigma)):
            delta=codec.decode((mu+std*epsilon).tanh(),reference,low,high)-center
            point_bound=L*std*epsilon.abs();excess=float((delta.abs()-point_bound).max());assert excess<1e-12;bound_excess.append(excess)
            rms=delta.square().mean(0).sqrt();finite_bound=L*std*epsilon_rms;assert (rms<=finite_bound+1e-12).all()
            quantile=torch.quantile(delta,torch.tensor([.01,.05,.5,.95,.99],dtype=torch.float64),dim=0)
            for i,name in enumerate(short['learned_action_names']):rows.append(dict(case=case['case'],axis=name,distribution=label,sigma_latent=float(std[i]),RMS_rad=float(rms[i]),RMS_deg=float(torch.rad2deg(rms[i])),bias_rad=float(delta[:,i].mean()),bias_deg=float(torch.rad2deg(delta[:,i].mean())),quantiles_rad=quantile[:,i].tolist(),quantiles_deg=torch.rad2deg(quantile[:,i]).tolist(),rate_preclip_exceed_fraction=float((delta[:,i].abs()>step).double().mean()),population_Lipschitz_RMS_bound_rad=float(L[i]*std[i]),finite_sample_RMS_bound_rad=float(finite_bound[i])))
    assert all(torch.equal(v,state[k]) for k,v in policy.state_dict().items()) and all(np.array_equal(data[k],frozen[k]) for k in FIELDS)
    checks=dict(saved_log_std_effective_clamp_verified=True,model73_unchanged=True,observations_unchanged=True,raw_CPU_reproduced=True,zero_noise_exact=True,anchors_encode_decode_roundtrip=True,candidate_finite_positive=True,candidate_formula_only=True,pointwise_Lipschitz=True,finite_sample_bound=True)
    result=dict(seed=SEED,samples=SAMPLES,epsilon_dtype='float64',epsilon_sha256=hashlib.sha256(epsilon.numpy().tobytes()).hexdigest(),epsilon_RMS4=epsilon_rms.tolist(),nominal_rad=nominal,nominal_deg=float(np.rad2deg(nominal)),rate_step_rad=step,original_config_std=config_std,original_effective_std=original_std,saved_log_std4=saved_log_std.tolist(),effective_log_std4=effective_log_std.tolist(),saved_float32_std4=saved_std[0].tolist(),config_minus_effective_std=config_std-original_std,negative_slope_rad_per_raw4=(reference-low).tolist(),positive_slope_rad_per_raw4=(high-reference).tolist(),L_rad_per_raw4=L.tolist(),candidate_sigma4=sigma.tolist(),raw_CPU_max_abs_residual=raw_residual,reused_CPU_tolerance=comparison['raw_goal_model_CPU_max_abs_residual'],maximum_pointwise_bound_excess_rad=max(bound_excess),cases=cases,rows=rows,checks=checks,
        scope='Fixed means and Gaussian goal-noise arithmetic before rateclip; float64 evaluation of original decode with frozen float32 model means, not CUDA/float32 sampling bitexact or physical motion/PPO effect; nominal is first-order incremental reference, not exact finite incremental RMS')
    assert all(sha(p)==h for p,h in inputs.items());out.mkdir();write=lambda name,v:(out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    write('comparison.json',result);write('verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,fit_executed=False,checkpoint_sha256=inputs[str(checkpoint)],input_sha256=inputs,direct_input_count=len(inputs),checks=checks))
    with (out/'distribution.csv').open('w',newline='') as f:
        columns=[k for k in rows[0] if k not in ('quantiles_rad','quantiles_deg')]+['q01_deg','q05_deg','q50_deg','q95_deg','q99_deg'];writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for r in rows:writer.writerow({**{k:r[k] for k in columns[:-5]},**dict(zip(columns[-5:],r['quantiles_deg']))})
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(10,6),sharex=True);x=np.arange(len(cases))
    for i,ax in enumerate(axes.flat):
        for offset,label,color in ((-.19,'original','#377eb8'),(.19,'candidate','#ff7f00')):
            ax.bar(x+offset,[r['RMS_deg'] for r in rows if r['axis']==short['learned_action_names'][i] and r['distribution']==label],width=.38,label=label,color=color)
        ax.axhline(np.rad2deg(nominal),ls='--',color='gray',label='nominal / candidate population bound');ax.axhline(np.rad2deg(step),ls=':',color='black',label='4/60 rad reference');ax.set_title(short['learned_action_names'][i]);ax.set_ylabel('Goal-noise RMS (deg)');ax.set_xticks(x);ax.set_xticklabels([c['case'].replace('phase','p') for c in cases]);ax.grid(axis='y',alpha=.2)
    axes.flat[0].legend(fontsize=7);fig.suptitle('Common seed7 Gaussian; goal variation before rateclip');fig.tight_layout(rect=(0,0,1,.95));fig.savefig(out/'exploration_units.png',dpi=140);plt.close(fig)
    (out/'RESULTS.md').write_text(report(result))
    print(json.dumps({k:result[k] for k in ('samples','nominal_rad','L_rad_per_raw4','candidate_sigma4','raw_CPU_max_abs_residual','maximum_pointwise_bound_excess_rad')},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if a.execute:main()
    else:print('CPU arithmetic only; pass --execute; no original files changed')
