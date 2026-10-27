"""Sequential post-run verification/evaluation; never share an active GPU scene."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path('/home/ajou/yigyu/3')
PHASE=Path(__file__).resolve().parent
BASE=Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long')
RUN=BASE/'train2000'
PYTHON='/home/ajou/miniconda3/envs/rl38/bin/python'
TRACE=ROOT/'docs/2026-10-22/guitar_learning_long_training_v6/native_trace.gdb'
from monitor_training_v2 import process_info


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
    temporary.replace(path)


def step(name,arguments,native=False,render=False):
    command=[PYTHON,'-B']+[str(v) for v in arguments]
    if native:command=['gdb','-q','-batch','-x',str(TRACE),'--args']+command
    env=dict(os.environ,PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0' if native else '',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',OMP_NUM_THREADS='1')
    if render:env.update(MUJOCO_GL='osmesa',LIBGL_ALWAYS_SOFTWARE='1')
    write(BASE/'postprocessing_status.json',dict(stage=name,command=command,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed=False))
    started=time.monotonic()
    with (BASE/(name+'.log')).open('x') as log:
        result=subprocess.run(command,cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        log.flush();os.fsync(log.fileno())
    history.append(dict(stage=name,returncode=result.returncode,wall_s=time.monotonic()-started))
    write(BASE/'postprocessing_steps.json',history)
    if result.returncode:raise RuntimeError(name+' failed; see its preserved log')


def main():
    # Launcher completion means its wait() returned: no training GPU scene remains.
    original=json.loads((PHASE/'launch.json').read_text())
    launcher=process_info(original['launcher_pid'])
    expected=[PYTHON,'-B',str(PHASE/'run_training.py')]
    if not launcher or launcher['command']!=expected:
        if not (PHASE/'launch_result.json').exists():
            raise RuntimeError('Expected training launcher is not running and has no completion marker')
    while True:
        try:
            launch=json.loads((PHASE/'launch_result.json').read_text())
            break
        except (FileNotFoundError,json.JSONDecodeError):
            current=process_info(original['launcher_pid'])
            if not current or not launcher or current['starttime']!=launcher['starttime'] or current['command']!=expected:
                try:
                    launch=json.loads((PHASE/'launch_result.json').read_text())
                    break  # Final reread covers completion between a partial read and launcher exit.
                except (FileNotFoundError,json.JSONDecodeError):
                    raise RuntimeError('Training launcher ended without a valid completion marker; preserve output for inspection')
            if time.time()-datetime.datetime.fromisoformat(original['started_utc']).timestamp()>24*3600:
                raise RuntimeError('Training completion marker absent after24hours; no new GPU process started')
            time.sleep(30)
    if any(launch.get(k)!=original.get(k) for k in ('out','child_pid','started_utc')):
        raise RuntimeError('Completion marker belongs to a different launch')
    if launch['returncode']!=0:raise RuntimeError('Training failed; preserve output for inspection')
    report=json.loads((RUN/'report.json').read_text())
    if not report['completed'] or not report['lifecycle_verified'] or report['failure'] is not None:
        raise RuntimeError('Training did not finish and close its GPU scene normally')
    frozen=json.loads((PHASE/'training_source_manifest.json').read_text())['source']
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in frozen.items()):
        raise RuntimeError('Frozen training source changed')
    step('verify_training',[PHASE/'verify_training.py','--run',RUN,'--updates','2000','--out',BASE/'training_verification.json'])
    step('strict_resume1',['-m','guitar_learning.train','--hand','left','--song','05_BN2-131-B_solo',
        '--device','cuda:0','--physics','gpu','--size','large','--num-envs','1024','--horizon','32',
        '--updates','1','--checkpoint-every','100','--seed','7','--resume',RUN/'final.pt','--out',BASE/'train_resume1'],native=True)
    step('verify_resume',[PHASE/'verify_training.py','--run',BASE/'train_resume1','--updates','1',
        '--parent-checkpoint',RUN/'final.pt','--out',BASE/'resume_verification.json'])
    step('analyze_training',[PHASE/'analysis.py','--run',RUN,'--updates','2000',
        '--verification',BASE/'training_verification.json','--plots','--out',BASE/'analysis_final'])
    step('fixed_evaluation',[PHASE/'evaluate_checkpoints.py','--run',RUN,'--out',BASE/'evaluations',
        '--tag','fixed','--checkpoints','2000','0','500','1000','1500'],native=True)
    evaluations=BASE/'evaluations/fixed_checkpoint_evaluation.json'
    for view in ('fullbody','hand'):
        step('render_best_'+view,[PHASE/'render_video.py','--evaluations',evaluations,
            '--selection','best','--view',view,'--out',BASE/('best_'+view+'_video')],render=True)
    combined=json.loads(evaluations.read_text())
    if not combined['completed']:raise RuntimeError('Fixed evaluation set incomplete')
    rows=sorted(combined['selection']['scores'],key=lambda r:r['updates'])
    text=['# v8 장기 학습 자동 집계','',
        'fresh2000회/65,536,000전이 및 별도 strict resume1회 검산을 완료했다. 아래는 동일1024 첫 에피소드 평가이며 각 저장본의 학습된 curriculum을 그대로 복원했다.','',
        '| 업데이트 | 평균 달성음 /67 | 안전 완료 /1024 |','| --- | --- | --- |']
    text += ['| %d | %.8f | %d |'%(r['updates'],r['mean_achieved'],r['safe_count']) for r in rows]
    best=combined['selection']['best'];text+=['', '평가한 학습 저장본 중 대표 모델: %d회. 평균 달성음→안전 완료수→최근순으로 선정했으며 초기 모델은 후보에서 제외했다.'%best['updates'],
        '', '전신/손 영상은 best_fullbody_video, best_hand_video에 저장했다. analysis_final에는 수집 로그·PPO·메모리·손가락 움직임 그래프가 있다.',
        '', '자동 실행·수치 집계 결과다. 영상의 시각 검토와 최종 독립 결과 검수는 별도로 수행해야 하며, 전체67음 성공·자연스러움·일반화·음압/음향을 평균 달성음만으로 주장하지 않는다.']
    (BASE/'report.md').write_text('\n'.join(text)+'\n')
    write(BASE/'postprocessing_status.json',dict(completed=True,stage='completed',steps=history,report=str(BASE/'report.md'),evaluation=str(evaluations),independent_result_review_pending=True))


history=[]
try:
    main()
except BaseException as error:
    failure=dict(completed=False,stage='failed',steps=history,error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),source_outputs_preserved=True)
    try:
        write(BASE/'postprocessing_status.json',failure)
    except OSError as storage_error:
        failure['external_status_write_error']=str(storage_error)
        write(PHASE/'postprocessing_emergency.json',failure)
    raise
