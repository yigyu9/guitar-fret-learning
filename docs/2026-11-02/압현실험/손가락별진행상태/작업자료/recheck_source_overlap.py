"""기존336검사가 끝나면 신규소스작성과 겹친 검사오류 한 건을 다시 검사한다.

기존 물리 과제 실패는 재시도하지 않는다. 원래 두 시도는 그대로 보존하고,
별도 명시적 복구 시도03의 원시 검증이 통과한 경우에만 결과 원장을 보완한다.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').exists())
STUDY=ROOT/'docs/2026-11-02/압현실험/단일압현/전수검증_1-14_v1'
RUN=STUDY/'로그/sweep_v1'
OUT=Path(__file__).resolve().parent/'소스간섭_재검사'
CASE='ring_s3_f4'
PYTHON='/home/ajou/miniconda3/envs/rl38/bin/python'


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p,d):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    paths=[ROOT/p for p in ('guitar_learning/gpu/finger_progress.py',
        'guitar_learning/tool/experiments/song_finger_progress.py',
        'guitar_learning/tests/test_finger_progress.py','guitar_learning/tests/test_song_finger_progress.py')]
    paths.extend([STUDY/'도구/native_check.py',STUDY/'도구/geometry.py',RUN/'geometry_frozen.json',Path(__file__).resolve()])
    pins={str(p):digest(p) for p in paths};write(OUT/'inputs_before.json',pins)
    status=dict(stage='waiting_for_original_sweep',case=CASE,started_epoch=time.time(),completed=False)
    def save(**values):status.update(values,updated_epoch=time.time());write(OUT/'state.json',status)
    process=None
    try:
        signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
        deadline=time.monotonic()+12*3600
        while True:
            state=json.loads((RUN/'state.json').read_text())
            if state.get('completed') and state.get('status')=='complete':break
            if state.get('status') in ('blocked_input_or_integrity_error','interrupted'):
                raise RuntimeError('기존 검사가 멈춰 있어 자동 GPU 재검사를 시작하지 않음')
            if time.monotonic()>deadline:raise TimeoutError('기존 검사 완료 대기12시간 초과')
            save(original_finished=state.get('finished'),original_total=state.get('total'));time.sleep(30)
        original=state['results'][CASE]
        if original.get('status')!='inspection_error':raise ValueError('소스 간섭 검사오류 한 건만 복구 가능')
        for attempt in ('attempt01','attempt02'):
            report=json.loads((RUN/CASE/attempt/'report.json').read_text())
            if report.get('completed') or 'SHA 불일치' not in (report.get('failure') or ''):
                raise ValueError('보존된 두 오류가 소스 검증 실패인지 확인 필요')
        for p,sha in pins.items():
            if digest(p)!=sha:raise ValueError('동결한 작업 소스가 바뀌어 재검사를 시작하지 않음: '+p)
        while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
            if time.monotonic()>deadline:raise TimeoutError('GPU 유휴 대기 초과')
            save(stage='waiting_for_idle_gpu');time.sleep(15)
        target=RUN/CASE/'attempt03'
        if target.exists():raise FileExistsError('복구 시도 원문 덮어쓰기 금지')
        command=[PYTHON,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),'run',str(STUDY/'도구/native_check.py'),
            '--geometry',str(RUN/'geometry_frozen.json'),'--case',CASE,'--seed','7','--out',str(target)]
        save(stage='rechecking',out=str(target))
        env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        with (OUT/'native.stdout.log').open('wb') as stream:
            process=subprocess.Popen(command,cwd=str(ROOT),env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=180)
            finally:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait();process=None
        report=json.loads((target/'report.json').read_text())
        if (report.get('schema')!='guitar_learning.range336.native_single_press.v1' or report.get('case')!=CASE or
                report.get('environments')!=1 or report.get('start_denominator')!=1 or report.get('optimizer_updates')!=0 or
                report.get('outcome') not in ('preparation_failed','finger_ik_unresolved','native_press_failed','press_success')):
            raise ValueError('복구 보고서 identity/분모/실행 범위 불일치')
        if report['outcome']=='press_success':
            episode=json.loads((target/'episode.json').read_text())
            if not report.get('task_success') or not report.get('preparation_ready') or episode.get('song',{}).get('stage_success') is not True:
                raise ValueError('압현 성공 원장과 보고서 불일치')
        if code or not all(report.get(k) for k in ('completed','execution_completed','source_sha256_match_after','scene_closed','pool_closed')) or report.get('failure'):
            raise RuntimeError('별도 복구 검사 미완료; 원문 보존')
        native_pins=json.loads((target/'inputs_before.json').read_text())
        for p,sha in native_pins.items():
            if digest(p)!=sha:raise ValueError('복구 입력 SHA 불일치: '+p)
        for p,sha in pins.items():
            if digest(p)!=sha:raise ValueError('복구 중 작업 소스 변경: '+p)
        state=json.loads((RUN/'state.json').read_text())
        if not state.get('completed') or state['results'][CASE]!=original:raise ValueError('기존 원장 상태 변경')
        state.setdefault('integrity_recovery',[]).append(dict(case=CASE,previous=original,
            new_report=str(target/'report.json'),reason='new source files were edited during original attempts; both invalid originals retained',
            recovery_manifest=str(OUT/'inputs_before.json'),updated_epoch=time.time()))
        state['results'][CASE]=dict(status='done',report=str(target/'report.json'),outcome=report['outcome'],elapsed_s=report['elapsed_s'])
        state['updated_epoch']=time.time();write(RUN/'state.json',state)
        subprocess.run([PYTHON,str(STUDY/'도구/summarize.py'),'--run',str(RUN)],cwd=str(ROOT),env=env,check=True,timeout=120)
        save(stage='complete',completed=True,outcome=report['outcome'],report=str(target/'report.json'))
    except BaseException as exc:
        save(stage='failed',failure=repr(exc));raise
    finally:
        if process is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()


if __name__=='__main__':main()
