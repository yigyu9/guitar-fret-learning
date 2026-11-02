"""초기bias 한축 변경만 동일예산으로 비교하고 단일압현 범위표에 기록한다."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE=Path(__file__).resolve().parents[1]
PARENT=BASE.parent/'전환개선_단독목표와준비시간_20261101'
SPEC=importlib.util.spec_from_file_location('single_bias_process_helpers',PARENT/'tools/run_study.py')
common=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(common)
study=common.study
BUDGET=622592


def baseline():
    path=PARENT/'research_v1/progress.json';state=json.loads(path.read_text())
    result={}
    for seed in (7,17):
        key=f'b_only_s{seed}_t{BUDGET}_development_mean32';r=state['results'][key]
        if r['budget']!=BUDGET or r['metrics']['episodes']!=32:raise ValueError('동일예산 기준자료 필요')
        result[str(seed)]=r
    return result,path


def progress(state,out):
    job=state.get('current_job') or {};path=Path(job.get('out','/nonexistent'))/'J/learning_metrics.jsonl';partial=0
    if job.get('operation')=='train' and path.exists():
        for line in path.read_text().splitlines():
            try:json.loads(line);partial+=1
            except json.JSONDecodeError:pass
    state.update(updated_at=study.now(),current_partial_updates=partial)
    study.write(out/'progress.json',state)
    lines=['# 초기정책 포화 개선: 단일압현 비교','',f"- 상태: {state['status']}",f"- 갱신: {state['updated_at']}",f"- 현재: {job.get('label','없음')}",f'- 현재 블록 완료: {partial}',
           '- 변경: 초기팔bias 한축만. 실제A6reset·B8목표·보상·std·LR·제어 동일.',
           '- 각seed19updates=622,592경험 후 비교. 곡/전환/전체528조합을 자동 시작하지 않음.',
           '', '|seed|평가|달성|clean초|B거리중앙mm|위치통과표본|물리/손목|','|---:|---|---:|---:|---:|---:|---|']
    for seed,r in state['baseline'].items():
        m=r['metrics'];reject=m['rejection'][0];lines.append(f"|{seed}|기존 mean32|{m['achievement'][0]}/{m['episodes']}|{m['clean_s'][0]:.3f}|{m['B_pad_distance_median_m']*1000:.2f}|{sum(reject.values())-reject['position']}|{m['physical']}/{m['wrist']}|")
    for r in state['results'].values():
        m=r['metrics'];reject=m['rejection'][0];distance=m['B_pad_distance_median_m'];text='없음' if distance is None else f'{distance*1000:.2f}'
        lines.append(f"|{r['seed']}|{r['tag']}|{m['achievement'][0]}/{m['episodes']}|{m['clean_s'][0]:.3f}|{text}|{sum(reject.values())-reject['position']}|{m['physical']}/{m['wrist']}|")
    lines+=['','## 판단']+['- '+v for v in state.get('interpretations',[])]
    if state.get('error'):lines+=['','오류/중단: '+state['error']]
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')


def run(state,out,label,operation,args,updates=0):
    return common.run(state,out,label,operation,['--condition','b_only',*map(str,args)],updates=updates)


def evaluate(state,out,seed,checkpoint,tag,count=32,mode='mean'):
    folder=run(state,out,f's{seed}_{tag}','evaluate',['--checkpoint',checkpoint,'--num-envs',count,'--action-mode',mode])
    metrics=common.analyze(folder,count)
    state['results'][f's{seed}_{tag}']=dict(seed=seed,tag=tag,metrics=metrics,checkpoint=str(checkpoint))
    progress(state,out);return metrics


def interpret(state,out):
    for seed in (7,17):
        old=state['baseline'][str(seed)]['metrics'];new=state['results'][f's{seed}_mean32']['metrics']
        state['interpretations'].append(f"seed{seed}: 같은예산 mean32 달성 {old['achievement'][0]}→{new['achievement'][0]}, clean {old['clean_s'][0]:.3f}→{new['clean_s'][0]:.3f}초, 거리중앙 {old['B_pad_distance_median_m']*1000:.2f}→{new['B_pad_distance_median_m']*1000:.2f}mm")
    passed=all(common.passed(state['results'][f's{s}_mean128']['metrics']) for s in (7,17))
    state['single_target_passed']=passed
    state['interpretations'].append('두seed mean128의 B단독 달성≥90%·평균clean≥1.35초·물리/손목실패≤1% 통과' if passed else '단일압현 단계기준 미통과. 거리개선만으로 압현성공을 선언하지 않으며 장시간 자동연장하지 않음.')
    path=BASE/'단일압현_검증목록.json';registry=json.loads(path.read_text())
    for case in registry['cases']:
        if (case['finger'],case['string_1based'],case['fret'])==('middle',3,8):
            case.update(status='policy_passed' if passed else 'policy_tested_not_passed',evaluation=str(out/'progress.json'),
                scope='same A6 reset, init_bias_cap.9, two seeds mean128; not all initial poses or acoustic success')
    study.write(path,registry)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out.resolve()
    if out.exists():raise FileExistsError('기존 결과 보존: '+str(out))
    old,path=baseline();out.mkdir(parents=True);(out/'logs').mkdir()
    pins=common.seal()
    for p in (list((BASE/'tools').glob('*.py'))+[path,BASE/'PLAN.md']):pins[str(p.relative_to(ROOT))]=study.sha(p)
    # PLAN은실험입력계약이아닌운영문서이므로진행체크리스트갱신을허용한다.
    pins.pop(str((BASE/'PLAN.md').relative_to(ROOT)))
    state=dict(schema='single_press_initial_bias_study.v1',status='running',started_at=study.now(),driver_pid=os.getpid(),jobs={},results={},baseline=old,source_seal=pins,interpretations=[])
    study.BASE=BASE;study.progress=progress
    def stop(signum,frame):raise KeyboardInterrupt('종료신호 '+str(signum))
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    with (ROOT/'.runtime/guitar_gpu_study.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            progress(state,out)
            a=run(state,out,'smoke_train2','train',['--seed',7,'--size','large','--num-envs',1024,'--horizon',32,'--updates',2],2)
            b=run(state,out,'smoke_resume1','train',['--seed',7,'--num-envs',1024,'--resume',a/'J/final.pt','--updates',1],1)
            evaluate(state,out,7,b/'J/final.pt','smoke_mean32')
            run(state,out,'smoke_render','render',['--checkpoint',b/'J/final.pt','--num-envs',4])
            checkpoints={}
            for seed in (7,17):
                folder=run(state,out,f's{seed}_train19','train',['--seed',seed,'--size','large','--num-envs',1024,'--horizon',32,'--updates',19],19)
                state.setdefault('training',{})[str(seed)]=common.training_summary(folder);checkpoints[seed]=folder/'J/final.pt'
                evaluate(state,out,seed,checkpoints[seed],'mean32')
                evaluate(state,out,seed,checkpoints[seed],'mean128',128)
                evaluate(state,out,seed,checkpoints[seed],'sampled32',mode='sampled')
            chosen=max(checkpoints,key=lambda s:(state['results'][f's{s}_mean128']['metrics']['joint_achievement'],state['results'][f's{s}_mean128']['metrics']['clean_s'][0]))
            folder=run(state,out,f's{chosen}_representative_render','render',['--checkpoint',checkpoints[chosen],'--num-envs',4])
            video=BASE/'동영상';video.mkdir(exist_ok=True)
            for source,target in [('hand.mp4','대표_손확대.mp4'),('fullbody.mp4','대표_전신.mp4')]:
                destination=video/target
                if destination.exists():raise FileExistsError(str(destination))
                os.link(folder/source,destination)
            episode=json.loads((folder/'episode_env0000.json').read_text())
            state['representative_video']=dict(seed=chosen,episode_success=episode['left_note_ledger']['values']['left'],source=str(folder))
            interpret(state,out);state.update(status='complete',finished_at=study.now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error,(KeyboardInterrupt,SystemExit)) else 'failed',error=repr(error),finished_at=study.now())
        finally:
            try:study.check_sources(state);unchanged=True
            except BaseException as error:unchanged=False;state.update(status='failed',source_error=repr(error))
            study.write(out/'SOURCE_VERIFICATION.json',dict(unchanged=unchanged,source_seal=pins,checked_at=study.now()))
            progress(state,out);(out/'RESULTS.md').write_text((out/'진행상황.md').read_text()+'\n\n기술완료와압현성공은다르다. single_target_passed와평가지표를확인한다.\n')
    return 0 if state['status']=='complete' else 1

if __name__=='__main__':raise SystemExit(main())
