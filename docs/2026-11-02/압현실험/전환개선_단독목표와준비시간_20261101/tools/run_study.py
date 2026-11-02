"""A초기 B단독→긴휴지 AB→시간단축을 조건별 fresh 모델로 직렬 실행한다."""
import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import statistics
import sys
from datetime import datetime, timedelta, timezone

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE=Path(__file__).resolve().parents[1]
HELPER=ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/tools/study.py'
spec=importlib.util.spec_from_file_location('single_gap_process_helpers',HELPER)
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
BUDGETS=(622592,1245184,2097152)
CONDITIONS=('b_only','gap150','gap100','gap075')

def seal():
    """현행 소스와 이번 입력만 봉인한다. 실행이 읽는 원본 pin도 그대로 유지한다."""
    paths={HELPER}
    for folder in (ROOT/'guitar_learning',BASE/'tools',BASE/'geometry'):
        for current,dirs,names in os.walk(folder,followlinks=False):
            dirs[:]=[d for d in dirs if d not in ('archive','__pycache__') and not (Path(current)/d).is_symlink()]
            paths.update(Path(current)/n for n in names if n.endswith(('.py','.json','.xml','.obj','.stl')))
    for name in ('virtual_middle_s3_f8_only_v2','virtual_middle_s3_f6_f8_gap150_v2','virtual_middle_s3_f6_f8_gap100_v2','virtual_middle_s3_f6_f8_gap075_v2'):
        paths.update(p for p in (ROOT/'data/song_bundles'/name).rglob('*') if p.is_file())
    paths.update(ROOT/n for n in json.loads((BASE/'geometry/initial_provenance.json').read_text())['active_physical_inputs'])
    return {str(p.resolve().relative_to(ROOT)):study.sha(p) for p in sorted(paths)}


def passed(m):
    """실용 달성과90%시간유지 gate. 정시·전구간완전성공은 별도 보고한다."""
    return (m['joint_achievement']/m['episodes']>=.9 and min(m['clean_s'])>=1.35
            and (m['physical']+m['wrist'])/m['episodes']<=.01)


def analyze(folder,count):
    """M=1/2 원장을 같은 기준으로 계산하고 실제240Hz 거절 원인을 분리한다."""
    folder=Path(folder);report=json.loads((folder/'report.json').read_text())
    if not all(report.get(k) is True for k in ('completed','lifecycle_verified','failed_episodes_in_denominator','first_episode_per_env_per_batch')) or report['episodes']!=count:
        raise ValueError('최초episode·실패포함분모·실행정리 검증 실패')
    config=report['settings']['transition'];goals=config['schedule'];roles=config['goal_roles'];M=len(goals)
    rows=study.first_episodes(folder,count)
    result=dict(episodes=count,goal_roles=roles,condition=config['condition'],achievement=[0]*M,clean_s=[0.]*M,wrong_s=[0.]*M,
                joint_achievement=0,entire_hold=0,on_time=0,previous_tail_and_on_time=0,physical=0,wrist=0,reward_terms={},
                rejection=[dict(position=0,facing=0,load=0,wrong=0,clean=0) for _ in goals])
    ids=[r['finger_control_diagnostics']['episode_id'] for r in rows];eligible=[]
    for r in rows:
        ledger=r['left_note_ledger']['values'];ok=r['valid'] and not r['termination']['physical_failure'] and not r['termination']['wrist_failure'];eligible.append(ok)
        if len(ledger['left'])!=M:raise ValueError('조건 목표수와 원장 불일치')
        result['physical']+=bool(r['termination']['physical_failure']);result['wrist']+=bool(r['termination']['wrist_failure'])
        result['joint_achievement']+=ok and all(ledger['left'])
        result['entire_hold']+=ok and all(v>=g['end_s']-g['onset_s']-1e-8 for v,g in zip(ledger['clean'],goals))
        first=r['transition_diagnostics']['first_contact_s']
        result['on_time']+=ok and all(t is not None and t<=g['onset_s']+1/240+1e-8 for t,g in zip(first,goals))
        for i in range(M):
            result['achievement'][i]+=bool(ledger['left'][i]);result['clean_s'][i]+=ledger['clean'][i]/count;result['wrong_s'][i]+=ledger['wrong'][i]/count
        for k,v in r['reward_components'].items():result['reward_terms'][k]=result['reward_terms'].get(k,0.)+v/count
        if abs(sum(r['reward_components'].values())-r['reward'])>1e-4:raise ValueError('보상 합계 불일치')
    tail=[[] for _ in rows];onset=[None for _ in rows];distances=[]
    with gzip.open(folder/'finger_control_trace.jsonl.gz','rt') as stream:
        for line in stream:
            tr=json.loads(line)['natural_preparation']['transition']
            if tr['schema']!=config['schema'] or tr['sequence_sha256']!=config['sequence_sha256']:raise ValueError('trace 조건 계약 불일치')
            for env in range(count):
                if tr['all_env_episode_ids'][env]!=ids[env]:continue
                t=tr['all_env_episode_time_s'][env];clean=[c and not w for c,w in zip(tr['all_env_candidate'][env],tr['all_env_wrong'][env])]
                for i,g in enumerate(goals):
                    if not g['onset_s']<=t<g['end_s']:continue
                    if not tr['all_env_position_geometry'][env][i]:key='position'
                    elif not tr['all_env_facing_geometry'][env][i]:key='facing'
                    elif not tr['all_env_assigned_loaded'][env][i]:key='load'
                    elif tr['all_env_wrong'][env][i]:key='wrong'
                    else:key='clean'
                    result['rejection'][i][key]+=1
                if goals[-1]['onset_s']<=t<goals[-1]['end_s']:distances.append(tr['all_env_distance_m'][env][-1])
                if M==2:
                    if goals[0]['end_s']-.05-1e-8<=t<goals[0]['end_s']-1e-8:tail[env].append(clean[0])
                    if onset[env] is None and t>=goals[1]['onset_s']-1e-8:onset[env]=t<=goals[1]['onset_s']+1/240+1e-8 and clean[1]
    result['previous_tail_and_on_time']=(sum(ok and len(a)>=11 and all(a) and bool(b) for ok,a,b in zip(eligible,tail,onset)) if M==2 else None)
    result['B_pad_distance_median_m']=statistics.median(distances) if distances else None
    result['B_pad_distance_min_m']=min(distances) if distances else None
    result['evaluation']=str(folder);study.write(folder/'analysis.json',result)
    return result


def progress(state,out):
    state['updated_at']=study.now();job=state.get('current_job') or {};p=Path(job.get('out','/nonexistent'))/'J/learning_metrics.jsonl'
    partial=0
    if job.get('operation')=='train' and p.exists():
        rows=[]
        for line in p.read_text().splitlines():
            try:rows.append(json.loads(line))
            except json.JSONDecodeError:pass
        partial=len(rows)
        if rows:state['seconds_per_update']=statistics.mean(r['collection_s']+r['update_s'] for r in rows[-8:])
    state['current_partial_updates']=partial
    study.write(out/'progress.json',state)
    lines=['# 8프렛 이동·전환 개선 실험','',f"- 상태: {state['status']}",f"- 갱신: {state['updated_at']}",f"- 현재: {job.get('label','없음')}",f'- 현재 블록 완료: {partial}',
           '- 예상: 단독+gap1.5 01:30~02:30 / 시간단축 포함02:30~04:30 KST(11월2일). 실제 조건 통과·검증에 따라 달라짐.',
           '', '|조건|seed|경험|평가|목표별달성|공동달성|평균clean초|완전유지|정시|물리/손목|','|---|---:|---:|---|---|---:|---|---:|---:|---|']
    for r in state['results'].values():
        m=r['metrics'];lines.append(f"|{r['condition']}|{r['seed']}|{r['budget']}|{r['tag']}|{m['achievement']} / {m['episodes']}|{m['joint_achievement']}|{[round(x,3) for x in m['clean_s']]}|{m['entire_hold']}|{m['on_time']}|{m['physical']}/{m['wrist']}|")
    lines+=['','## 판단']+['- '+v for v in state.get('interpretations',[])]
    if state.get('error'):lines+=['','실행 오류: '+state['error']]
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')


def run(state,out,label,operation,args,updates=0):
    folder=study.run(state,out,label,operation,args,updates=updates)
    reports=[folder/'report.json']+([folder/'J/report.json'] if operation=='train' else [])
    for path in reports:
        d=json.loads(path.read_text())
        if (path.parent.name=='J' or operation!='train') and d.get('lifecycle_verified') is not True:raise ValueError('lifecycle 미검증')
        if any(d.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors')):raise ValueError('입력·물리실행 검증 오류')
    return folder


def evaluate(state,out,condition,seed,budget,checkpoint,tag,count=32,mode='mean'):
    label=f'{condition}_s{seed}_t{budget}_{tag}'
    folder=run(state,out,label,'evaluate',['--condition',condition,'--checkpoint',checkpoint,'--num-envs',count,'--action-mode',mode])
    metrics=analyze(folder,count)
    state['results'][label]=dict(condition=condition,seed=seed,budget=budget,tag=tag,checkpoint=str(checkpoint),metrics=metrics)
    progress(state,out);return metrics


def training_summary(folder):
    """완료episode와PPO수치를요약한다.미완료꼬리는실패0으로채우지않는다."""
    phase=folder/'J';metrics=[json.loads(line) for line in (phase/'learning_metrics.jsonl').open()]
    completed=0;success=None;contact=None;clean=None
    for line in (phase/'episodes.jsonl').open():
        r=json.loads(line)['episode'];ledger=r['left_note_ledger']['values'];M=len(ledger['left'])
        if success is None:success=[0]*M;contact=[0]*M;clean=[0.]*M
        completed+=1
        for i in range(M):
            success[i]+=bool(ledger['left'][i]);contact[i]+=bool(ledger['contact_done'][i]);clean[i]=max(clean[i],ledger['clean'][i])
    return dict(completed_episodes=completed,achievement=success,first_contact_done=contact,max_clean_s=clean,
                rollout_updates=len(metrics),actor_lr_first=metrics[0]['actor_lr'],actor_lr_last=metrics[-1]['actor_lr'],
                actor_lr_min=min(m['actor_lr'] for m in metrics),kl_retries=sum(m['kl_retries'] for m in metrics),
                actor_minibatch_steps=sum(m['diagnostics']['minibatches']['actor_accepted']['steps'] for m in metrics),
                mean_collection_and_update_s=statistics.mean(m['collection_s']+m['update_s'] for m in metrics))


def plot(state,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for name in CONDITIONS:
        for seed in (7,17):
            rows=[r for r in state['results'].values() if r['condition']==name and r['seed']==seed and r['tag']=='development_mean32']
            if not rows:continue
            rows.sort(key=lambda r:r['budget']);xs=[r['budget'] for r in rows]
            axes[0].plot(xs,[100*r['metrics']['achievement'][-1]/r['metrics']['episodes'] for r in rows],marker='o',label=f'{name} s{seed}')
            axes[1].plot(xs,[r['metrics']['clean_s'][-1] for r in rows],marker='o',label=f'{name} s{seed}')
    axes[0].set_ylabel('B achievement (%)');axes[1].set_ylabel('B valid hold (s)')
    for ax in axes:ax.set_xlabel('Collected transitions');ax.grid(alpha=.2)
    if state['results']:axes[0].legend(fontsize=7)
    fig.savefig(out/'learning_performance.png',dpi=150);plt.close(fig)


def condition(state,out,name):
    checkpoints={};final=[]
    for budget in BUDGETS:
        previous_budget=0 if budget==BUDGETS[0] else BUDGETS[BUDGETS.index(budget)-1]
        for seed in (7,17):
            updates=(budget-previous_budget)//32768
            args=['--condition',name,'--seed',seed,'--size','large','--num-envs',1024,'--horizon',32,'--updates',updates]
            if seed in checkpoints:args+=['--resume',checkpoints[seed]]
            folder=run(state,out,f'{name}_s{seed}_t{budget}_train','train',args,updates)
            state.setdefault('training',{})[f'{name}_s{seed}_t{budget}']=training_summary(folder)
            checkpoints[seed]=folder/'J/final.pt'
            evaluate(state,out,name,seed,budget,checkpoints[seed],'development_mean32')
    for seed,checkpoint in checkpoints.items():
        for tag in ('final_mean128','repeat_mean128'):
            final.append(evaluate(state,out,name,seed,BUDGETS[-1],checkpoint,tag,count=128))
        evaluate(state,out,name,seed,BUDGETS[-1],checkpoint,'exploration_sampled32',mode='sampled')
    # 공개영상은조건별대표모델손·전신한쌍만. 실패도성공으로부르지않는다.
    scores={seed:[] for seed in checkpoints}
    for r in state['results'].values():
        if r['condition']==name and r['tag'] in ('final_mean128','repeat_mean128'):
            m=r['metrics'];scores[r['seed']].append((m['joint_achievement']/m['episodes'],min(m['clean_s'])))
    chosen=max(checkpoints,key=lambda s:tuple(statistics.mean(v[i] for v in scores[s]) for i in (0,1)))
    rendered=run(state,out,f'{name}_s{chosen}_representative_render','render',['--condition',name,'--checkpoint',checkpoints[chosen],'--num-envs',4])
    video=BASE/'동영상'/name;video.mkdir(parents=True,exist_ok=True)
    episode=json.loads((rendered/'episode_env0000.json').read_text())
    record=dict(condition=name,seed=chosen,episode_success=episode['left_note_ledger']['values']['left'],files=[])
    for src,dst in [('hand.mp4','손확대.mp4'),('fullbody.mp4','전신.mp4')]:
        target=video/dst
        if target.exists():raise FileExistsError(str(target))
        os.link(rendered/src,target);record['files'].append(dict(path=str(target),sha256=study.sha(target)))
    state.setdefault('videos',[]).append(record)
    ok=all(passed(m) for m in final);state['conditions'][name]=dict(passed=ok,final_metrics=final,representative_seed=chosen)
    state['interpretations'].append(f'{name}: '+('두seed·반복mean128 모두 단계기준 통과' if ok else '단계기준 미통과; 다음 시간단축 조건은 진행하지 않음'))
    plot(state,out);progress(state,out);return ok


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--preflight',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve()
    if out.exists():raise FileExistsError('기존 출력 보존: '+str(out))
    proof=json.loads(args.preflight.read_text())
    if proof.get('completed') is not True or proof.get('passed') is not True or proof.get('original_native_inputs_unchanged') is not True or proof.get('identical_training_native_controller_contract') is not True:raise ValueError('행동범위 검증통과 필요')
    # 증거에 연결된 원본·학습·제어 소스를 재검사한다.
    for name,value in proof['inputs'].items():
        p=Path(name) if Path(name).is_absolute() else ROOT/name
        if study.sha(p)!=value:raise ValueError('행동범위 검증 입력변경: '+name)
    out.mkdir(parents=True);(out/'logs').mkdir()
    def stop(signum,frame):raise KeyboardInterrupt('종료신호 '+str(signum))
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    state=dict(schema='middle_single_and_gap_study.v1',status='running',started_at=study.now(),driver_pid=os.getpid(),jobs={},results={},conditions={},interpretations=[],source_seal=seal(),preflight=str(args.preflight.resolve()))
    state['source_seal'][str(args.preflight.resolve().relative_to(ROOT))]=study.sha(args.preflight)
    study.BASE=BASE;study.progress=progress
    with (ROOT/'.runtime/guitar_gpu_study.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            progress(state,out)
            # 실제 학습·저장·strict재개·M1평가·native렌더를 본 실험 전에 통과시킨다.
            smoke=run(state,out,'smoke_train2','train',['--condition','b_only','--seed',7,'--size','large','--num-envs',1024,'--horizon',32,'--updates',2],2)
            resumed=run(state,out,'smoke_resume1','train',['--condition','b_only','--seed',7,'--num-envs',1024,'--updates',1,'--resume',smoke/'J/final.pt'],1)
            evaluate(state,out,'b_only',7,98304,resumed/'J/final.pt','smoke_mean32')
            run(state,out,'smoke_render','render',['--condition','b_only','--checkpoint',resumed/'J/final.pt','--num-envs',4])
            for name in CONDITIONS:
                if not condition(state,out,name):
                    state['stopped_after_condition']=name
                    state['skipped_conditions']=list(CONDITIONS[CONDITIONS.index(name)+1:])
                    break
            state.update(status='complete',finished_at=study.now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',error=repr(error),finished_at=study.now())
        finally:
            try:study.check_sources(state);source_ok=True
            except BaseException as error:source_ok=False;state.update(status='failed',source_error=repr(error))
            study.write(out/'SOURCE_VERIFICATION.json',dict(unchanged=source_ok,checked_at=study.now(),source_seal=state['source_seal']))
            progress(state,out)
            (out/'RESULTS.md').write_text((out/'진행상황.md').read_text()+'\n\n실행 종료와 학습 성공은 다르다. conditions의passed=false 또는 skipped_conditions를 확인한다.\n')
    return 0 if state['status']=='complete' else 1

if __name__=='__main__':raise SystemExit(main())
