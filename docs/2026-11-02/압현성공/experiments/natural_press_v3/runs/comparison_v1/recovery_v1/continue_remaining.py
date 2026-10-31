"""원본 실패 블록을 보존하고 고정된 나머지700회만 순차 실행한다."""
import argparse
import copy
from datetime import datetime,timedelta
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parent
TASKS=(('E2',7,200),)+tuple((condition,17,total) for condition in ('E0','E1','E2') for total in (100,200))


def load_study():
    sys.path.insert(0,str(ORIGINAL))
    spec=importlib.util.spec_from_file_location('natural_original_study',ORIGINAL/'run_study.py')
    study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
    if study.HERE!=ORIGINAL:raise ValueError('원본 HERE 불일치')
    return study


def label(condition,seed,total):return 'seed{}_{}_u{}'.format(seed,condition,total)


def save_before(study):
    manifest=HERE/'before_sha256.json'
    if manifest.exists():
        for name,sha in json.loads(manifest.read_text()).items():
            if study.digest(HERE/name)!=sha:raise RuntimeError('보존한 before 자료 변경')
        return
    hashes={}
    for name in ('progress.json','진행상황.md','RESULTS.md'):
        source=ORIGINAL/name;target=HERE/('before_'+name)
        if target.exists():raise FileExistsError(str(target))
        shutil.copyfile(source,target);hashes[target.name]=study.digest(source)
        if study.digest(target)!=hashes[target.name]:raise ValueError('before 복사 SHA 불일치')
    study.write(manifest,hashes)


def seal_state(study,state):
    original=json.loads((ORIGINAL/'source_seal.json').read_text())
    if any(state['source_seal'].get(k)!=v for k,v in original.items()):raise ValueError('원본 state/source 봉인 불일치')
    study.verify_sources(original)
    files=(Path(__file__).resolve(),HERE/'test_continue_remaining.py',HERE/'PLAN.md')
    added={str(p.relative_to(study.ROOT)):study.digest(p) for p in files}
    record=dict(original_source_seal_sha256=study.digest(ORIGINAL/'source_seal.json'),additional_sources=added)
    path=HERE/'continuation_source_seal.json'
    if path.exists() and json.loads(path.read_text())!=record:raise RuntimeError('계속 실행 코드/원본 봉인 변경')
    if not path.exists():study.write(path,record)
    state['source_seal']=dict(original,**added)
    state['recovery']=state.get('recovery',dict(schema='natural_press.continuation.v1',failed_blocks=[],skipped_blocks=[],artifact_errors=[]))
    state['recovery'].update(original_target_updates=1400,remaining_authorized_updates=700,original_failed_block='seed7_E1_u200')
    state['recovery'].setdefault('original_error',state.get('error'))
    state['recovery'].setdefault('original_failure_job',copy.deepcopy(state.get('current_job')))
    failed=ORIGINAL/'blocks/seed7_E1_u200/train/J/report.json'
    if failed.exists():
        raw=json.loads(failed.read_text())
        state['recovery']['preserved_failed_block']=dict(label='seed7_E1_u200',model_success=False,
            report=str(failed),sha256=study.digest(failed),optimizer_updates=raw.get('optimizer_updates'),updates_in_run=raw.get('updates_in_run'),
            committed=raw.get('journal',{}).get('committed'))
    state['recovery']['source_record']=record
    return record


def verify(study,state):
    study.verify_sources(state['source_seal'])
    if study.digest(ORIGINAL/'source_seal.json')!=state['recovery']['source_record']['original_source_seal_sha256']:
        raise RuntimeError('원본 source_seal 변경')
    preserved=state['recovery'].get('preserved_failed_block')
    if preserved and study.digest(preserved['report'])!=preserved['sha256']:
        raise RuntimeError('보존한 원래 실패 보고서 변경')


def finish_child(study):
    child=study.CHILD
    if child is not None:
        for sig,wait in ((signal.SIGINT,30),(signal.SIGTERM,10),(signal.SIGKILL,5)):
            if child.poll() is not None:break
            try:os.killpg(child.pid,sig)
            except ProcessLookupError:pass
            try:child.wait(timeout=wait)
            except subprocess.TimeoutExpired:continue
        if child.poll() is None:raise RuntimeError('GPU child 종료 실패')
        child.wait();study.CHILD=None
    occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if occupied:raise RuntimeError('GPU 프로세스가 남아 독립 조건으로 전환 불가: '+occupied)


def prerequisite(state,condition,seed,total):
    if total==100:return True
    name=label(condition,seed,100)
    return name in state['results'] and all(state['jobs'].get(name+'_'+kind,{}).get('status')=='complete' for kind in ('train','aligned','free_v9'))


def verify_complete(study,state,name):
    for kind in ('train','aligned','free_v9'):
        job=state['jobs'].get(name+'_'+kind,{})
        if job.get('status')!='complete':raise RuntimeError('완료 결과의 작업 누락: '+name)
        if study.digest(job['report'])!=job['report_sha256']:raise RuntimeError('완료 보고서 변경: '+name)
        if any(not Path(p).is_file() or study.digest(p)!=sha for p,sha in job['evidence_sha256'].items()):
            raise RuntimeError('완료 원자료 변경: '+name)


def results(study,state):
    lines=['# 실패 블록 보존 후 남은 고정 비교 결과','',
        '후보 E1/E2는 바꾸지 않았다. 실패/부분/건너뜀은 완료 모델 성능이 아니다. 원본 RESULTS.md는 보존한다.','',
        '| 조건 | seed | 누적 반복 | 정렬 성공 | v9 성공 | v9 clean평균 | 물리/손목 실패 |','|---|---:|---:|---:|---:|---:|---:|']
    for row in state['results'].values():
        m=row['free_v9'];lines.append('| {} | {} | {} | {}/32 | {}/32 | {:.4f} | {}/{} |'.format(row['condition'],row['seed'],row['updates'],row['aligned']['success_count'],m['success_count'],m['mean_clean_s'],m['physical_failure_count'],m['wrist_failure_count']))
    lines+=['','원래 계획1400회 중 seed7 E1 누적200의 실패 블록은 재시도하지 않는다. 완료된 블록만 합산하며 부분 commit은 별도 기록한다.','',
        '상태: '+state['status'],'','실패/건너뜀: `'+json.dumps(state['recovery'],ensure_ascii=False)+'`']
    if state.get('finished_at'):lines+=['','종료: '+state['finished_at']]
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def install_reporting(study,state):
    original_write,original_progress=study.write,study.progress
    def write(path,value):
        path=Path(path)
        return original_write(HERE/'summary.json' if path==ORIGINAL/'summary.json' else path,value)
    def progress(current):
        original_progress(current)
        excluded={r['label'] for r in current['recovery']['failed_blocks']+current['recovery']['skipped_blocks']}
        pending=[label(c,s,t) for c,s,t in TASKS if label(c,s,t) not in excluded]
        remaining=sum(100 for name in pending if current['jobs'].get(name+'_train',{}).get('status')!='complete')
        active=current.get('current_job') or {};completed=current.get('current_block_completed_updates',0)
        if active.get('operation')=='train':remaining=max(0,remaining-completed)
        if current['status']=='running':
            evaluations=sum(current['jobs'].get(name+'_'+kind,{}).get('status')!='complete' for name in pending for kind in ('aligned','free_v9'))
            seconds=remaining*current.get('seconds_per_update_recent',5.04)+evaluations*70
            now=datetime.now(study.KST)
            current['estimated_finish_earliest']=(now+timedelta(seconds=seconds*.85)).isoformat(timespec='minutes')
            current['estimated_finish_latest']=(now+timedelta(seconds=seconds*1.25)).isoformat(timespec='minutes')
        elif current['status']=='finished_with_failed_blocks':
            current['estimated_finish_earliest']=current['estimated_finish_latest']=current['finished_at']
        current['recovery']['remaining_train_updates']=remaining
        original_write(ORIGINAL/'progress.json',current);original_write(HERE/'progress.json',current)
        text=(ORIGINAL/'진행상황.md').read_text().splitlines()
        text=[('- 예상 종료: '+current['estimated_finish_earliest']+' ~ '+current['estimated_finish_latest']) if line.startswith('- 예상 종료:') else line for line in text]
        text+=['','계속 실행 v1: 원래1400회 중 실패 블록을 보존하며 추가700회만 진행한다. 실패/부분 commit을 완료 모델로 세지 않는다.',
            '현재 상태: '+current['status']+'; 남은 추가 학습 '+str(remaining)+'회. 상세 실패/건너뜀은 recovery_v1/RESULTS.md를 확인한다.']
        (ORIGINAL/'진행상황.md').write_text('\n'.join(text)+'\n');(HERE/'진행상황.md').write_text('\n'.join(text)+'\n')
    study.write,study.progress,study.result_table=write,progress,lambda current:results(study,current)


def run_remaining(study,state):
    known={r['label'] for r in state['recovery']['failed_blocks']+state['recovery']['skipped_blocks']}
    for condition,seed,total in TASKS:
        name=label(condition,seed,total)
        if name in known:continue
        verify(study,state)
        if name in state['results']:
            verify_complete(study,state,name)
            continue
        if not prerequisite(state,condition,seed,total):
            state['recovery']['skipped_blocks'].append(dict(label=name,reason='같은 조건100회 학습/평가 미완료',model_success=False))
            study.progress(state);results(study,state);continue
        try:study.block(state,condition,seed,total)
        except Exception as error:
            finish_child(study);verify(study,state)
            if isinstance(error,FileExistsError):raise
            job=state.get('current_job')
            if job and job.get('status') in ('running','failed'):
                job.update(status='failed',finished_at=study.timestamp(),error=str(error));operation=job['operation']
            else:
                registered=[v for k,v in state['jobs'].items() if k.startswith(name+'_')]
                if not registered:raise  # 디스크/실행 전 충돌 등 전역 준비 실패는 계속하지 않는다.
                operation='analysis' if all(v['status']=='complete' for v in registered) else registered[-1]['operation']
            failure=dict(label=name,operation=operation,message=str(error),traceback=traceback.format_exc(),model_success=False)
            phase=ORIGINAL/'blocks'/name/'train/J/report.json'
            if phase.exists():
                raw=json.loads(phase.read_text());failure['partial_training']=dict(optimizer_updates=raw.get('optimizer_updates'),updates_in_run=raw.get('updates_in_run'),committed=raw.get('journal',{}).get('committed'))
            state['recovery']['failed_blocks'].append(failure);state['current_job']=None
        verify(study,state);study.progress(state);results(study,state)


def render_selected(study,state):
    for condition in ('E1','E2'):
        for total in (100,200):
            name=label(condition,7,total)
            if name not in state['results']:continue
            out=HERE/'renders'/name
            try:
                checkpoint=ORIGINAL/'blocks'/name/'free_v9_eval/model_only/J/final.pt'
                study.run_job(state,'recovery_'+name+'_render','render',['--checkpoint',checkpoint,'--num-envs',4],out,render=True)
                publication=out/'published_video.json'
                if publication.exists():
                    if any(study.digest(row['path'])!=row['sha256'] for row in json.loads(publication.read_text())):
                        raise ValueError('공개 영상 변경')
                else:study.publish_video(out,'recovery_v1_'+name)
            except Exception as error:
                finish_child(study);verify(study,state)
                state['recovery']['artifact_errors'].append(dict(label=name,message=str(error)))
                job=state.get('current_job')
                if job and job['status']=='running':job.update(status='failed',finished_at=study.timestamp(),error=str(error))
                state['current_job']=None


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true');args=parser.parse_args()
    study=load_study()
    with (ORIGINAL/'gpu.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save_before(study);state=json.loads((ORIGINAL/'progress.json').read_text())
        if state.get('selected_conditions')!=['E1','E2']:raise ValueError('원래 고정 후보 E1/E2 불일치')
        seal_state(study,state)
        for name in state['results']:verify_complete(study,state,name)
        finish_child(study)
        state['status']='running';state['driver_pid']=os.getpid();state['current_job']=None;state.pop('error',None)
        install_reporting(study,state)
        def stop(signum,frame):
            finish_child(study);raise KeyboardInterrupt('계속 실행 종료 신호')
        signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
        try:
            study.progress(state);run_remaining(study,state)
            if args.render:render_selected(study,state)
            verify(study,state);state.update(status='finished_with_failed_blocks',finished_at=study.timestamp(),current_job=None)
        except BaseException as error:
            try:finish_child(study)
            finally:
                job=state.get('current_job')
                if job and job.get('status')=='running':job.update(status='failed',finished_at=study.timestamp(),error=str(error))
                state.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',current_job=None,
                    error=dict(type=type(error).__name__,message=str(error)),stopped_at=study.timestamp())
                study.progress(state);results(study,state)
            raise
        study.progress(state);results(study,state)


if __name__=='__main__':main()
