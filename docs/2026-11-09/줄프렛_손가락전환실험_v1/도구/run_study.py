"""단일 압현 세 조건과 전환 세 조건을 순차 학습·평가·렌더한다."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').exists())
BASE=Path(__file__).resolve().parents[1]
PYTHON='/home/ajou/miniconda3/envs/rl38/bin/python'
CASES=('single_middle_s3_f6','single_middle_s1_f8','single_ring_s2_f7',
       'transition_middle_s3_f6_to_s3_f8','transition_middle_s3_f6_to_s1_f8','transition_middle_s3_f6_to_ring_s2_f7')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)

def metrics(path):
    rows=[json.loads(line)['episode'] for line in Path(path).read_text().splitlines() if line]
    if not rows:raise ValueError('평가 분모가 비었음')
    m=len(rows[0]['left_note_ledger']['values']['left']);success=[0]*m;raw_success=[0]*m;clean=[0.]*m;wrong=[0.]*m;best=[0.]*m
    all_notes=full=physical=wrist=0
    for row in rows:
        note=row['left_note_ledger']['values']
        if len(note['left'])!=m:raise ValueError('평가 목표 수 불일치')
        safe=bool(row.get('valid') and not row['termination']['physical_failure'] and not row['termination']['wrist_failure'])
        all_notes+=int(safe and row['song'].get('stage_success') and all(note['left']))
        full+=int(safe and all(x>=1.5-1e-6 for x in note['clean']))
        physical+=int(row['termination']['physical_failure']);wrist+=int(row['termination']['wrist_failure'])
        for i in range(m):
            raw_success[i]+=int(note['left'][i]);success[i]+=int(safe and note['left'][i])
            clean[i]+=note['clean'][i];wrong[i]+=note['wrong'][i];best[i]+=note['best_clean_streak'][i]
    n=len(rows)
    keys=set().union(*(row.get('reward_components',{}) for row in rows))
    rewards={key:sum(row.get('reward_components',{}).get(key,0.) for row in rows)/n for key in sorted(keys)}
    return dict(episodes=n,mean_reward_components=rewards,target_success=success,raw_target_latches=raw_success,all_notes_success=all_notes,full_duration_all_notes=full,
        mean_clean_s=[x/n for x in clean],mean_wrong_s=[x/n for x in wrong],mean_best_streak_s=[x/n for x in best],physical=physical,wrist=wrist)


def summarize(state,out):
    lines=['# 줄·프렛 및 손가락 전환 실험 진행','',f"상태: {state['status']}",'',
        '| 조건 | 평가 수 | 목표별 달성 | 전체 달성 | 전체 길이 유지 | 평균 clean 초 | 물리/손목 종료 |',
        '| --- | ---: | --- | ---: | ---: | --- | --- |']
    for case,result in state['results'].items():
        m=result.get('metrics')
        if m:lines.append(f"| {case} | {m['episodes']} | {m['target_success']} | {m['all_notes_success']} | {m['full_duration_all_notes']} | {m['mean_clean_s']} | {m['physical']}/{m['wrist']} |")
        else:lines.append(f"| {case} | — | {result.get('status')} | — | — | — | — |")
    lines+=['','독립 새 정책 large64/H32/100회/seed7, 평균 정책 고정16환경 평가. 한 난수의 짧은 학습으로 최종 수렴이나 일반화를 선언하지 않는다.',
        '진단 IK/패드 보정의 결과와 학습 정책의 결과를 분리한다. 목표별 독립 도달은 전환 가능성의 증명이 아니다.']
    (out/'결과.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--validation-proof',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.relative_to(ROOT)
    out.mkdir(parents=True,exist_ok=True)
    lock=(out/'driver.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    proof=read(args.validation_proof)
    if proof.get('completed') is not True:raise ValueError('GPU 학습/재개/평가/영상 실행 검증 선행 필요')
    for path,expected in proof['source_sha256'].items():
        if sha(path)!=expected:raise ValueError('GPU 검증 소스 변경')
    for item in proof['reports']:
        if sha(item['path'])!=item['sha256'] or not read(item['path']).get('completed'):
            raise ValueError('GPU 검증 원문 변경 또는 미완료')
    inputs=BASE/'입력';manifest=read(inputs/'manifest.json')
    if not manifest.get('completed'):raise ValueError('생성 입력 완료 필요')
    files=list((BASE/'도구').glob('*.py'))+list(inputs.rglob('*'))+list((ROOT/'guitar_learning').rglob('*.py'))
    paths=[p for p in files if p.is_file() and 'archive' not in p.parts]
    pins={str(p.resolve()):sha(p) for p in paths};pin_path=out/'inputs_before.json'
    if pin_path.exists():
        saved=read(pin_path)
        if pins!=saved:raise ValueError('기존 연구 재개 입력/소스 불일치')
    else:write(pin_path,pins)
    for name,expected in manifest['files_sha256'].items():
        if sha(inputs/name)!=expected:raise ValueError('번들 SHA 불일치')
    state_path=out/'state.json'
    state=read(state_path) if state_path.exists() else dict(status='ready',completed=False,results={},jobs={},started_epoch=time.time(),gpu_validation=str(args.validation_proof.resolve()))
    process=None
    def validate_job(saved):
        if not saved.get('completed'):raise ValueError('미완료 실행을 재사용할 수 없음')
        for path,expected in saved['artifacts'].items():
            if not Path(path).is_file() or sha(path)!=expected:raise ValueError('완료 산출물 SHA 불일치: '+path)
        report=read(saved['report'])
        if not report.get('completed') or report.get('failure'):raise ValueError('완료 원장 불일치')
        phase=Path(saved['out'])/'J/report.json'
        if phase.exists() and (not read(phase).get('completed') or not read(phase).get('lifecycle_verified')):
            raise ValueError('학습 정리 원장 불일치')
    def update(**values):
        state.update(values,updated_epoch=time.time());write(state_path,state);summarize(state,out)
    def verify():
        for p,h in pins.items():
            if sha(p)!=h:raise RuntimeError('연구 중 소스/입력 변경: '+p)
    def gpu_idle():
        deadline=time.monotonic()+6*3600
        while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
            update(status='waiting_for_gpu')
            if time.monotonic()>deadline:raise TimeoutError('GPU 유휴 대기6시간 초과')
            time.sleep(15)
    def job(label,operation,options):
        nonlocal process
        previous=state['jobs'].get(label)
        if previous and previous.get('completed'):
            validate_job(previous)
            return Path(previous['out'])
        verify();gpu_idle();verify()
        parent=out/'로그'/label;parent.mkdir(parents=True,exist_ok=True)
        attempt=parent/('attempt%02d'%(len(list(parent.glob('attempt*')))+1))
        command=[PYTHON,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),'run',str(BASE/'도구/learning.py'),operation,*map(str,options),'--out',str(attempt)]
        update(status='running',current=dict(label=label,operation=operation,out=str(attempt),started_epoch=time.time()))
        environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        with (parent/(attempt.name+'.stdout.log')).open('wb') as log:
            process=subprocess.Popen(command,cwd=str(ROOT),env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+(3600 if operation=='train' else 1200)
            try:
                while process.poll() is None:
                    if time.monotonic()>deadline:raise TimeoutError(label+' 실행 시간 초과')
                    update(child_pid=process.pid)
                    try:process.wait(timeout=30)
                    except subprocess.TimeoutExpired:pass
                code=process.returncode
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait();process=None
        verify();report_path=attempt/'report.json';report=read(report_path)
        if code or not report.get('completed') or report.get('failure'):
            state['jobs'][label]=dict(completed=False,out=str(attempt),report=str(report_path),returncode=code)
            update();raise RuntimeError(label+' 미완료; 원문 보고서 확인')
        if operation=='train':
            phase=read(attempt/'J/report.json')
            if not phase.get('completed') or not phase.get('lifecycle_verified'):raise ValueError('GPU 학습 정리/봉인 실패')
        elif not report.get('lifecycle_verified'):raise ValueError('GPU 평가/영상 정리 실패')
        artifacts=[report_path]+list(attempt.glob('*.mp4'))
        if operation=='train':artifacts.extend([attempt/'J/report.json',attempt/'J/final.pt',attempt/'J/inputs_before.json'])
        if operation=='evaluate':artifacts.extend([attempt/'episodes.jsonl',attempt/'episode_metadata.json'])
        state['jobs'][label]=dict(completed=True,out=str(attempt),report=str(report_path),report_sha256=sha(report_path),
            artifacts={str(path):sha(path) for path in artifacts})
        update();return attempt
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    try:
        for case in CASES:
            if state['results'].get(case,{}).get('status')=='complete':
                for operation in ('train','evaluate','render'):validate_job(state['jobs'][case+'_'+operation])
                for path,expected in state['results'][case]['video_sha256'].items():
                    if sha(path)!=expected:raise ValueError('공개 영상 변경')
                continue
            update(current_case=case)
            try:
                training=job(case+'_train','train',['--bundle',inputs/'song_bundles'/case,'--size','large','--num-envs',64,'--horizon',32,'--updates',100,'--seed',7,'--checkpoint-every',50])
                checkpoint=training/'J/final.pt'
                evaluation=job(case+'_evaluate','evaluate',['--checkpoint',checkpoint,'--num-envs',16])
                measure=metrics(evaluation/'episodes.jsonl')
                state['results'][case]=dict(status='evaluated',checkpoint=str(checkpoint),metrics=measure);update()
                render=job(case+'_render','render',['--checkpoint',checkpoint,'--num-envs',1])
                videos=BASE/'동영상';videos.mkdir(exist_ok=True)
                published=[]
                for video in sorted(render.glob('*.mp4')):
                    destination=videos/(case+'_'+video.name)
                    if destination.exists():
                        if sha(destination)!=sha(video):raise ValueError('동영상 원문 덮어쓰기 금지')
                    else:os.link(video,destination)
                    published.append(str(destination))
                if len(published)!=2:raise ValueError('손/전신 영상2개 필요')
                state['results'][case].update(status='complete',videos=published,video_sha256={path:sha(path) for path in published});update()
            except Exception as exc:
                verify()
                state['results'].setdefault(case,{}).update(status='failed',error=repr(exc));update()
        failed=[c for c,r in state['results'].items() if r['status']!='complete']
        update(status='complete' if not failed else 'completed_with_failures',completed=not failed,failed_cases=failed)
    except BaseException as exc:
        update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'blocked',failure=repr(exc));raise
    finally:
        if process is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()

if __name__=='__main__':main()
