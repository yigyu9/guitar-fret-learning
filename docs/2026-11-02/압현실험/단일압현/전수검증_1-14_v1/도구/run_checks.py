"""한 조합 한 GPU 프로세스를 순차 실행하고 중단 후 미완료 조합부터 이어간다.

과제 실패는 재시도하지 않는다. 실행 오류는 최대 두 번 기록한 뒤 다음 조합으로
넘긴다. 시작할 때 전체 CPU 자료를 동결하며 실행마다 입력 SHA를 확인한다.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def stop_group(process):
    """리더 종료 후에도 남은 GPU 자식 프로세스를 정리한다."""
    for sig,seconds in ((signal.SIGTERM,5.),(signal.SIGKILL,1.)):
        try:os.killpg(process.pid,sig)
        except ProcessLookupError:return
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            try:os.killpg(process.pid,0)
            except ProcessLookupError:return
            time.sleep(.1)
    process.wait()


def valid_result(path,expected_case):
    try:report=json.loads(path.read_text())
    except (FileNotFoundError,ValueError):return False
    if (report.get('schema')!='guitar_learning.range336.native_single_press.v1' or report.get('case')!=expected_case or
            not report.get('completed') or not report.get('execution_completed') or report.get('failure') is not None or
            not report.get('source_sha256_match_after') or not report.get('scene_closed') or not report.get('pool_closed') or
            report.get('environments')!=1 or report.get('start_denominator')!=1 or report.get('optimizer_updates')!=0 or
            report.get('outcome') not in ('preparation_failed','finger_ik_unresolved','native_press_failed','press_success')):return False
    pins=json.loads((path.parent/'inputs_before.json').read_text())
    # 재개도 원시 입력을 다시 대조한다. 완료 표지만 보고 이전 자료를 신뢰하지 않는다.
    return bool(pins) and all(Path(filename).is_file() and sha(filename)==value for filename,value in pins.items())


def balanced_cases(cases):
    """손가락을 교대로 검사하고 초기에는 경계와 넓은 줄 범위를 먼저 본다."""
    by_key={(c['finger'],c['string_standard_1based'],c['fret']):c['case_id'] for c in cases}
    frets=(12,1,14,6,3,9,2,4,5,7,8,10,11,13)
    return [by_key[(finger,string,fret)] for fret in frets for string in (1,3,6,2,4,5)
        for finger in ('index','middle','ring','pinky')]


def coordinate(args):
    out=Path(args.out).resolve();source=Path(args.geometry).resolve();cases_path=Path(args.cases).resolve()
    new=not out.exists();out.mkdir(parents=True,exist_ok=True)
    manifest_path=out/'manifest.json';state_path=out/'state.json'
    fixed=out/'geometry_frozen.json'
    if new:
        geometry=json.loads(source.read_text());cases=json.loads(cases_path.read_text())['cases']
        if not geometry.get('completed'):raise ValueError('336 CPU 탐색 완료 후 실행해야 함')
        identifiers=balanced_cases(cases)
        if len(set(identifiers))!=len(identifiers):raise ValueError('중복 case')
        if set(identifiers)!={r['case_id'] for r in geometry['rows']}:raise ValueError('geometry/case 전수 목록 불일치')
        fixed.write_bytes(source.read_bytes())
        manifest=dict(schema='guitar_learning.range336.queue.v1',cases=identifiers,seed=args.seed,
            ordering='Each fret/string cell alternates index, middle, ring, pinky; early coverage frets12,1,14 and strings1,3,6',
            source_geometry=str(source),source_geometry_sha256=sha(fixed),timeout_s=args.timeout,
            pins={str(p):sha(p) for p in (fixed,cases_path,HERE/'native_check.py',HERE/'geometry.py',HERE/'copy_origin.json',HERE/'summarize.py',Path(__file__).resolve())})
        write(manifest_path,manifest)
        state=dict(schema='guitar_learning.range336.state.v1',completed=False,status='ready',
            total=len(identifiers),results={},started_epoch=time.time(),manifest_sha256=sha(manifest_path))
        write(state_path,state)
    manifest=json.loads(manifest_path.read_text());state=json.loads(state_path.read_text())
    if state['manifest_sha256']!=sha(manifest_path):raise ValueError('실행 명세 변경')
    def check_inputs():
        for filename,expected in manifest['pins'].items():
            if sha(filename)!=expected:raise ValueError('실행 소스/입력 변경: '+filename)
    check_inputs();active=None;interrupted=False
    def update():
        finished=[r for r in state['results'].values() if r['status'] in ('done','inspection_error')]
        durations=[r['elapsed_s'] for r in finished if r.get('elapsed_s') is not None]
        state.update(finished=len(finished),remaining=state['total']-len(finished),updated_epoch=time.time(),
            estimated_remaining_s=(sum(durations)/len(durations)*(state['total']-len(finished))) if durations else None)
        write(state_path,state)
    def refresh_summary(plot=False):
        environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MPLCONFIGDIR=str(out/'.matplotlib'))
        command=[sys.executable,str(HERE/'summarize.py'),'--run',str(out)]
        if not plot:command.append('--no-plot')
        with (out/'summary.stdout.log').open('ab') as stream:
            try:
                result=subprocess.run(command,env=environment,cwd=str(ROOT),stdout=stream,stderr=subprocess.STDOUT,timeout=120)
                if result.returncode:state['summary_warning']='집계 오류: summary.stdout.log 확인'
                else:state.pop('summary_warning',None)
            except subprocess.TimeoutExpired:state['summary_warning']='집계 시간 초과'
        update()
    def interrupt(*_):raise KeyboardInterrupt('중단 신호')
    signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
    try:
        for case in manifest['cases']:
            check_inputs();existing=state['results'].get(case)
            if existing and existing['status']=='done':
                if not valid_result(Path(existing['report']),case):raise ValueError('완료 결과의 SHA/정리 검증 실패: '+case)
                continue
            if existing and existing['status']=='inspection_error':continue
            case_out=out/case;case_out.mkdir(exist_ok=True)
            attempts=sorted(p for p in case_out.glob('attempt*') if p.is_dir())
            # 직전 중단 직후 완성된 report는 재개 때 검증하여 회수한다.
            if attempts and valid_result(attempts[-1]/'report.json',case):
                report=json.loads((attempts[-1]/'report.json').read_text())
                state['results'][case]=dict(status='done',report=str(attempts[-1]/'report.json'),outcome=report['outcome'],elapsed_s=report['elapsed_s']);update();refresh_summary(plot=state['finished']%12==0);continue
            for attempt in range(len(attempts)+1,3):
                check_inputs();attempt_out=case_out/('attempt%02d'%attempt)
                state['status']='running';state['current']=dict(case=case,attempt=attempt,out=str(attempt_out));update()
                command=[args.python,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),'run',str(HERE/'native_check.py'),
                    '--geometry',str(fixed),'--case',case,'--seed',str(manifest['seed']),'--out',str(attempt_out)]
                environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
                started=time.monotonic()
                with (case_out/('attempt%02d.stdout.log'%attempt)).open('wb') as stream:
                    active=subprocess.Popen(command,cwd=str(ROOT),env=environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                    try:code=active.wait(timeout=manifest['timeout_s'])
                    except subprocess.TimeoutExpired:code=None
                    finally:stop_group(active);active=None
                elapsed=time.monotonic()-started;check_inputs()
                path=attempt_out/'report.json'
                if code==0 and valid_result(path,case):
                    report=json.loads(path.read_text())
                    state['results'][case]=dict(status='done',report=str(path),outcome=report['outcome'],elapsed_s=elapsed);update();refresh_summary(plot=state['finished']%12==0);break
                write(case_out/('attempt%02d.execution.json'%attempt),dict(returncode=code,timeout=code is None,elapsed_s=elapsed,report=str(path)))
            else:
                latest=sorted(case_out.glob('attempt[0-9][0-9]'))
                state['results'][case]=dict(status='inspection_error',report=str(latest[-1]/'report.json') if latest else None,elapsed_s=None);update();refresh_summary(plot=state['finished']%12==0)
        state['status']='complete';state['completed']=True;state.pop('current',None);update();refresh_summary(plot=True)
    except KeyboardInterrupt:
        interrupted=True;state['status']='interrupted';update()
    except Exception as exc:
        state['status']='blocked_input_or_integrity_error';state['failure']=repr(exc);update();raise
    finally:
        if active is not None:stop_group(active)
    return 130 if interrupted else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry',required=True);parser.add_argument('--cases',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--python',default='/home/ajou/miniconda3/envs/rl38/bin/python');parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--timeout',type=float,default=180.)
    args=parser.parse_args()
    if args.timeout<=0:parser.error('양수 timeout 필요')
    return coordinate(args)


if __name__=='__main__':raise SystemExit(main())
