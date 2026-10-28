"""CPU-only audit of saved regression logs; no training or native imports."""
import argparse
from collections import Counter
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
UPDATES=(50,100,150,200)


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def flatten(value,prefix=''):
    result={}
    for k,v in value.items():
        key=prefix+k
        if isinstance(v,dict):result.update(flatten(v,key+'.'))
        elif isinstance(v,(float,int)) or v is None:result[key]=v
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:print('Readiness only; no actual data read.');return
    sys.path.insert(0,str(Path.cwd()))
    original=load_module('frozen_learning_analysis',BASE/'learning_analysis/analyze.py');grid=original.grid
    out=HERE/'results_v1';original.probe.cap.reject_existing(out);inputs,verified={},{}
    def track(p):p=Path(p);inputs[str(p.resolve())]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(mapping):
        for p,h in mapping.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    review=read(BASE/'learning_analysis/results_v1/review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    verification=read(BASE/'learning_analysis/results_v1/verification.json')
    for k in ('input_sha256','verified_input_sha256'):pins(verification[k])
    basic=read(BASE/'learning_analysis/results_v1/comparison.json')
    metrics=[json.loads(v) for v in track(BASE/'train/metrics.jsonl').read_text().splitlines()]
    episodes=[json.loads(v) for v in track(BASE/'train/episodes.jsonl').read_text().splitlines()]
    assert [m['update'] for m in metrics]==list(range(1,301)) and len(episodes)==5504
    assert all(m['mean_failure_cost']==0 and m['cost_weight']==1 for m in metrics)
    assert all(e['cost']==0 and not e['termination']['physical_failure'] and not e['termination']['wrist_failure'] for e in episodes)
    import numpy as np
    import torch
    from guitar_learning.gpu.wrong_press import pad_contact_cells
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    helper=load_module('frozen_index_precheck',BASE/'precheck_analysis/analyze.py')
    trace_helper=load_module('frozen_prelearning_trace',helper.HELPER)
    for p in (Path(original.__file__),Path(helper.__file__),Path(trace_helper.__file__),Path(__file__),HERE/'PLAN.md',
              grid.ROOT/'guitar_learning/gpu/control.py',grid.ROOT/'guitar_learning/gpu/environment.py',
              grid.ROOT/'guitar_learning/gpu/simplified_finger_environment.py',grid.ROOT/'guitar_learning/gpu/wrong_press.py',
              grid.ROOT/'guitar_learning/training/decision_ppo.py',grid.ROOT/'guitar_learning/training/ppo.py'):track(p)
    class AuditEnvironment(ShortEnvironment):
        def _left_wrong_contacts(self,*args):
            result=super()._left_wrong_contacts(*args)
            self.audit_cells=pad_contact_cells(args[-2],args[-1],self.pad_valid,self.loaded[:,self.pad_indices],self.starts,self.ends,self.frets,self.press_plane)
            return result
    metadata,_=fixture(1);config=read(BASE/'cpu_inputs/settings.json');short=config['song']['short_learning'];source=short['view']['source_target']
    names=short['learned_action_names'];qids=[metadata['joint_names'].index(n) for n in names];aids=short['learned_action_indices']
    rows=[];cases={}
    for u in UPDATES:
        folder=BASE/('evaluation_%06d'%u);t=dict(np.load(track(folder/'trace_env0_episode0.npz')))
        controller=read(folder/'training_contract.json')['action']['target_contract'];meta=read(folder/'trace_metadata.json')
        ai=[controller['action_order'].index(n) for n in names]
        assert ai==aids and controller['action_codec']['mode']=='incremental'
        lo=np.asarray(controller['action_lower_rad'],np.float32)[ai];hi=np.asarray(controller['action_upper_rad'],np.float32)[ai]
        target=t['target'][:,qids];actual=t['q'][:,qids];action=t['executed_action'][:,aids]
        old=np.r_[np.asarray(controller['reference105_rad'],np.float32)[None,qids],target[:-1]]
        predicted=np.clip(old+action*np.float32(4/60),lo,hi)
        residual=float(abs(predicted-target).max());assert residual<1e-6
        assert np.array_equal(action,t['policy_action'][:,aids]) and np.max(abs(target-old))<=4/60+1e-6
        masks=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s']);audible=masks[1]
        trace=trace_helper.trace_audit(t,metadata,config,basic['cases'][str(u)]['episodes'],'policy',controller)
        assert not trace['candidate_wrong_mismatches']
        env=AuditEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
        def snap(k):return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
        env.reset([0],snap(0));flags=[];mins=[];maxs=[];cells=Counter()
        for k,time in enumerate(t['time_s']):
            env.clock[0]=round(time*240);env._snapshot(snap(k));j=env.selected_index
            assert [bool(env.candidate[0,j]),bool(env.wrong[0,j])]==[bool(t['candidate'][k]),bool(t['wrong'][k])]
            flags.append(env.wrong_source_flags[0,j].tolist());mins.append(env.wrong_source_fret_min[0,j].tolist());maxs.append(env.wrong_source_fret_max[0,j].tolist())
            if audible[k] and bool(env.wrong[0,j]) and not bool(env.contact_loaded_target[0,j]):
                valid,pf,ps=env.audit_cells;f=int(env.finger[j])-1
                wrong=valid[0,f] & ~((pf[0,f]==env.fret[j]) & (ps[0,f]==env.string[j]))
                cells.update(set((int(s)+1,int(fret)) for s,fret in zip(ps[0,f][wrong].tolist(),pf[0,f][wrong].tolist())))
            for i,n in enumerate(names):rows.append(dict(update=u,endpoint=k,time_s=float(time),source_time_s=float(t['source_time_s'][k]),phase='audible' if audible[k] else ('before' if masks[0][k] else 'after'),joint=n,action=float(action[k,i]),actual_deg=float(np.rad2deg(actual[k,i])),target_deg=float(np.rad2deg(target[k,i])),target_minus_actual_deg=float(np.rad2deg(target[k,i]-actual[k,i])),at_upper=bool(target[k,i]>=hi[i]-1e-6)))
        joint=[]
        for i,n in enumerate(names):
            at=target[:,i]>=hi[i]-1e-6;indices=np.flatnonzero(at);err=np.rad2deg(target[audible,i].astype(np.float64)-actual[audible,i])
            joint.append(dict(name=n,lower_deg=float(np.rad2deg(lo[i])),upper_deg=float(np.rad2deg(hi[i])),first_upper_endpoint=int(indices[0]) if len(indices) else None,
                first_upper_local_s=float(t['time_s'][indices[0]]) if len(indices) else None,first_upper_source_s=float(t['source_time_s'][indices[0]]) if len(indices) else None,
                upper_endpoints=int(at.sum()),positive_action_at_previous_upper=int(((old[:,i]>=hi[i]-1e-6)&(action[:,i]>0)).sum()),audible_upper=int(at[audible].sum()),
                audible_actual_at_upper=int((actual[audible,i]>=hi[i]-1e-6).sum()),audible_actual_mean_deg=float(np.rad2deg(actual[audible,i].astype(np.float64)).mean()),audible_target_mean_deg=float(np.rad2deg(target[audible,i].astype(np.float64)).mean()),audible_signed_gap_mean_deg=float(err.mean()),audible_abs_gap_max_deg=float(abs(err).max())))
        flags=np.asarray(flags)[audible];mins=np.asarray(mins)[audible];maxs=np.asarray(maxs)[audible]
        cases[str(u)]=dict(summary=basic['cases'][str(u)]['summary'],joints=joint,codec_max_residual_rad=residual,trace=trace,arm=helper.arm_audit(t,meta,config,controller),
            wrong_sources=dict(body_order=['thumb2','thumb3','index2','index3','middle2','middle3','ring2','ring3','pinky2','pinky3'],cause_order=['other_higher','own_wrong_fret','own_wrong_string'],audible_counts=flags.sum(0).tolist(),
                fret_min=[int(mins[:,b][flags[:,b].any(-1)].min()) if flags[:,b].any() else None for b in range(10)],fret_max=[int(maxs[:,b][flags[:,b].any(-1)].max()) if flags[:,b].any() else None for b in range(10)],
                own_wrong_distinct_cells_per_endpoint=[dict(physical_string_1based=s,fret=f,endpoints=n) for (s,f),n in sorted(cells.items())],target_physical_string_1based=int(env.string[env.selected_index])+1,target_fret=int(env.fret[env.selected_index])))
    metric_rows=[]
    for m in metrics:
        d=m['diagnostics'];row={k:m[k] for k in ('update','mean_reward','mean_failure_cost','cost_value_loss','actor_lr','analytic_kl','max_attempted_kl','kl_retries','cost_weight')}
        row.update(flatten(d['advantages'],'adv.'));row.update(flatten(d['post_update'],'post.'));metric_rows.append(row)
    episode_rows=[]
    for u in sorted({e['update'] for e in episodes}):
        es=[e for e in episodes if e['update']==u];episode_rows.append(dict(update=u,count=len(es),achieved=sum(e['achieved'] for e in es),mean_clean=float(np.mean([e['clean_fraction'] for e in es])),mean_wrong=float(np.mean([e['audible_wrong_fraction'] for e in es])),cost_sum=sum(e['cost'] for e in es)))
    summary=dict(raw_cost_nonzero_updates=[m['update'] for m in metrics if m['mean_failure_cost']],cost_GAE_nonzero_updates=[m['update'] for m in metrics if any(m['diagnostics']['advantages']['cost_raw'][k] for k in ('mean','std','min','max'))],
        cost_loss_nonzero_updates=[m['update'] for m in metrics if m['cost_value_loss']],KL_retry_updates=[m['update'] for m in metrics if m['kl_retries']],LR_changes=[dict(update=m['update'],actor_lr=m['actor_lr']) for i,m in enumerate(metrics) if i==0 or m['actor_lr']!=metrics[i-1]['actor_lr']],
        combined_mean_residual_max=max(abs(m['diagnostics']['advantages']['combined_raw']['mean']-(m['diagnostics']['advantages']['reward_raw']['mean']-m['diagnostics']['advantages']['cost_raw']['mean'])) for m in metrics),
        metric_samples={str(u):metric_rows[u-1] for u in (50,100,140,150,160,170,180,190,200,216,250,300)})
    out.mkdir();grid.write(out/'comparison.json',dict(cases=cases,training=summary,episode_batches=episode_rows))
    for name,table in (('metrics300.csv',metric_rows),('episode_batches.csv',episode_rows),('selected4_endpoints.csv',rows)):
        with (out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(10,6))
    for i,ax in enumerate(axes.flat):
        for u in UPDATES:
            rs=[r for r in rows if r['update']==u and r['joint']==names[i]];ax.plot([r['time_s'] for r in rs],[r['target_deg'] for r in rs],label=str(u))
        ax.axhline(cases['50']['joints'][i]['upper_deg'],color='gray',ls=':');ax.axvspan(3,source['end_s']-source['onset_s']+3,color='gray',alpha=.12);ax.set(title=names[i],xlabel='local seconds',ylabel='submitted target deg')
    axes[0,0].legend();fig.tight_layout();fig.savefig(out/'selected4_targets.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True)
    for key in ('reward_raw','cost_raw','combined_raw'):axes[0].plot(range(1,301),[m['diagnostics']['advantages'][key]['std'] for m in metrics],label=key)
    axes[0].set(ylabel='GAE/combined std');axes[0].legend()
    for key in ('reward','cost'):axes[1].plot(range(1,301),[m['diagnostics']['post_update']['critics'][key]['mse'] for m in metrics],label=key)
    axes[1].set(ylabel='critic MSE',yscale='log');axes[1].legend()
    axes[2].plot([r['update'] for r in episode_rows],[r['achieved']/r['count'] for r in episode_rows],label='stochastic completed train batch')
    axes[2].plot(UPDATES,[cases[str(u)]['summary']['achieved_fraction'] for u in UPDATES],'o-',label='fixed128 evaluation');axes[2].set(xlabel='update',ylabel='achieved fraction');axes[2].legend()
    for ax in axes:ax.axvspan(150,200,color='gray',alpha=.15)
    fig.tight_layout();fig.savefig(out/'training_diagnostics.png',dpi=150);plt.close(fig)
    write_report(out,cases,summary)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,env0_endpoints=884,selected4_rows=len(rows),metrics=300,completed_train_episodes=len(episodes),
        codec_scope='poststep submitted target equals bounded memory; previous saved target plus action*4/60; first previous=controller reset reference;1e-6rad reporting check only',
        geometry_scope='env0float32 saved snapshots with original CPU helpers; candidate/wrong all884 exact; nearest scalar not anysample witness; no240Hzintegration replay',
        source_functions=['gpu/control.py:BatchedController.targets','training/decision_ppo.py:compute_decision_gae/DecisionPPOTrainer._update','training/ppo.py:policy_advantages','gpu/simplified_finger_environment.py:_left_wrong_contacts','gpu/wrong_press.py:pad_contact_cells/wrong_press_sources']))
    print(out)


def write_report(out,cases,s):
    fmt=lambda xs:', '.join('%.3f'%x for x in xs)
    lines=['# 검지 학습 후퇴: 누적 목표와 비용 추정의 분리 감사','',
        '50/100/150회는 각각128/128이지만200회는0/128·wrong97.8104%다. 큰 목표−실제 차이와 마지막 관절 굴곡은 성공한150회에도 이미 존재한다. 비용 추정 영향과 이 추종 현상을 별도로 확인했으며 단일 원인은 확정하지 않는다.','',
        '## 선택4의 bounded 목표와 추종','',
        '아래는 env0 첫시도 60Hz 끝점이다. 순서는 MCPx/MCPz/PIP/DIP이며 상한은 약90/30/90/90°다. 시각은 local초(음중 [3.0,3.1703)초); 전체128의 상세 추종 원인이 아니다.','',
        '| update | 상한 최초 도달 local초 | 음중 target평균° | 음중 actual평균° | 음중 target−actual평균° |',
        '|---:|---|---|---|---|']
    for u in UPDATES:
        js=cases[str(u)]['joints'];first=', '.join('미도달' if j['first_upper_local_s'] is None else '%.4f'%j['first_upper_local_s'] for j in js)
        lines.append('| %d | %s | %s | %s | %s |'%(u,first,fmt([j['audible_target_mean_deg'] for j in js]),fmt([j['audible_actual_mean_deg'] for j in js]),fmt([j['audible_signed_gap_mean_deg'] for j in js])))
    lines+=['',
        '50회의 MCPz 상한은3.5167초로 음후다. 100회부터 MCPx/PIP 목표가 음전 상한에 도달한다. 150회 PIP actual17.7079°/target90.0002°(차72.2923°), DIP actual83.7254°/target88.3738°가 이미 관측된다. 200회는4축 모두 음전 상한이며 PIP차69.9366°는150회보다 작다. 따라서 큰 PIP차 하나만으로150→200의 성공/실패 차이를 설명할 수 없다.','',
        '원 `BatchedController.targets`의 `clamp(old_target + action*4/60, native_bounds)`를 저장된 action/이전target으로 재계산한884끝점 잔차는0rad다. LH21은alpha1/누적codec이며 손목의alpha0.2와 구분한다. 1e-6rad는 이 감사의 상한분류·재귀검사 수치허용이며 음악판정을 바꾸지 않는다. 선택4의 실제각은 음중 상한에 도달하지 않았다.','',
        '| update | 직전target이상한인데양의명령인끝점수(MCPx/z/PIP/DIP) |','|---:|---|']
    for u in UPDATES:lines.append('| %d | %s |'%(u,str([j['positive_action_at_previous_upper'] for j in cases[str(u)]['joints']])))
    lines+=['',
        '상한으로 향하는 명령과 실제 추종 지연은 확인되지만 저장되는 목표는 clamp된 유한값이다. 범위 밖 숨은 목표의 무제한 누적은 아니다. 정방향 명령은 상한에서 유지되고 반대 명령은 다음 제어틱부터 목표를 되돌릴 수 있다는 원codec 계약은 유지된다. 실제 원인에 접촉 차단·모터/자세 한계 중 무엇이 기여했는지는 이 로그만으로 분리할 수 없다.','',
        '## 실제 오압현 분리','',
        '| update | loaded/position/facing/positive/candidate/wrong (음중11끝점) | 몸체1/2/3합력평균N | 손목오차평균mm/° |',
        '|---:|---|---|---|']
    for u in UPDATES:
        p=cases[str(u)]['trace']['phases']['audible'];m=p['metric_mean'];lines.append('| %d | %s | %s | %s |'%(u,str(p['CPU_gate_counts']),fmt(m[12:15]),fmt(m[15:17])))
    lines+=['',
        'cp200 env0 원helper 재생은 검지 distal(index3)의 own_wrong_string을11/11에서 반환했다. 목표는physical3현4프렛이며 qualifying any-sample은physical2현3프렛11끝점,2현4프렛1끝점이다(중복가능). 다른손가락 other_higher와 own_wrong_fret는0이다. 150회는positive/candidate11이며 wrong0이다. cp200에서distal합력은 남아도 목표 위치·positive는0이다. 이는 원판정의 현/프렛 기하를 좁힌 관찰이며 접촉 상대쌍·실제압력·음향의 증거는 아니다.','',
        'candidate/wrong은884끝점 모두 원저장값과exact다. nearest 거리/높이 잔차>1µm는 없지만 nearest scalar는 qualifying any-sample witness와 다르며 실제native sample index는 저장되지 않았다. 위 현/프렛·원인표는 저장snapshot에 현재와SHA일치한 원helper를 적용한 CPU 재구성이다. 다른127의 몸체pose/force/cause endpoint는 없으므로 전체128 실패를 같은 원인으로 확정하지 않는다.','',
        '## 비용 추정과 PPO 로그','',
        '300회 모두 즉시실패비용평균0, 종료5504원장 cost0·물리/손목실패0이다. cost GAE와cost loss는각300회nonzero다. 원 `compute_decision_gae`는 cost+discount*next_cost_value−cost_value에서 시작하고 반환target=GAE+value이므로 실제비용0과 추정GAE0은 동치가 아니다. cost_weight1에서 combined=reward_GAE−cost_GAE이며 평균식 최대잔차는%.3g다. 추정된 비용이 실제 actor 목적에 들어간 경로는 확인되지만 이를 유일한 후퇴원인으로 확정하지 않는다.'%s['combined_mean_residual_max'],'',
        '| update | reward/cost/combined GAE std | cost value/target평균 | cost MSE / EV |',
        '|---:|---|---|---|']
    for u in (150,180,190,200):
        m=s['metric_samples'][str(u)];lines.append('| %d | %s | %s | %.6g / %.6g |'%(u,fmt([m['adv.'+k+'.std'] for k in ('reward_raw','cost_raw','combined_raw')]),fmt([m['post.critics.cost.'+k+'.mean'] for k in ('value','target')]),m['post.critics.cost.mse'],m['post.critics.cost.explained_variance']))
    lines+=['',
        '190회의cost GAE std.02417은reward.02855에비해작지않고 combined std는.00669다. 200회cost value평균.05864/target.00772·MSE.00844·EV−36.26으로불일치가보인다. 음의EV는상수평균예측보다못한분산설명이며 target분산에도영향받으므로 단독정책원인척도가아니다. 실제old value/nextvalue/transition별GAE tape는저장되지않아동일표본counterfactual advantage/gradient를재계산할수없다.','',
        '학습률은1~215회3e−5이고유일한KL재시도/7.5e−6변경은216회다. 200회붕괴보다뒤라최초후퇴의선행사건으로둘수없다. latentGaussian entropy는150/200회각−1.386003/−1.385548이며이는연속Gaussian의미분entropy다. 음수나작은변동만으로탐색붕괴를확정하지않는다. ratio/KL/entropy/value/target/MSE/EV의전체300행은metrics300.csv에보존했다.','',
        'stochastic학습종료batch와deterministic고정평가는다른표본이다. 학습은H32연속시계/221tick episode를이어가므로인접update가서로다른음전·음중노출을포함한다. 150회고정128/128을그주변stochastic종료batch와같은모집단으로비교하지않는다. 그래프에두분모를구분했다.','',
        '## 다음 단일 대조 후보와 한계','',
        '비용초기화B는별도worker설계범위다. 추종측의다음후보는동일저장action tape에서원누적대비유한target−actual오차완화의matched진단이다. 원4rad/s와native범위교집합안에서만target memory/반환native제출/관측target_error를동시에맞추고다른축·엄지035·팔teacher·보상/실패는유지해야한다. 큰기존오차를한번에actual로치환하면원속도제약을벗어나므로그런동작을부드러운보정으로부르지않는다. 진단게이트/완화수치는여기서채택하지않았다.','',
        '원적positioncodec 대조도가능하지만0명령이reset기준을요청하는등행동의미와엄지/비선택축영향까지달라질수있어분리설계가필요하다. 기존incremental checkpoint의strict계약을우회해position모델로로드할수없으며새계약·명시적action tape대조또는fresh학습이어야한다. 이번에는어느대조도구현/실행하지않았다. 두가설의인과입증이나새gain/범위/힘/성공문턱변경을확대하지않는다.','',
        '고정기타/검지단음/seed7의전체128음원장과env0 60Hz관찰이다. 몸체합력은모터torque·접촉쌍·압력·240Hz최대가아니고학습성과의자연스러움·해제/다음음·자유기타/J33로확대하지않는다. 원자료·source·기존분석·봉인/GPU변경0.','',
        '재현: 이폴더 analyze.py --root-completed (rl38,CUDA_VISIBLE_DEVICES빈값). verification.json에모든원입력/SHA와원함수경로,comparison.json에첫상한시각·source시각·원인/phase통계,CSV에전체행을보존했다.','',
        '![선택4목표](selected4_targets.png)','![전체학습진단](training_diagnostics.png)']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
