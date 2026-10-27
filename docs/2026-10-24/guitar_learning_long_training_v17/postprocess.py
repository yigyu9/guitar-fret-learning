"""Wait for the authorized run, then verify, evaluate, analyze and render it."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
RUN = PHASE/'train2000'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_status(value):
    temporary = PHASE/'pipeline_status.tmp'
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
    temporary.replace(PHASE/'pipeline_status.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--detach', action='store_true')
    args = parser.parse_args()
    if args.detach:
        with (PHASE/'postprocess_supervisor.log').open('x') as log:
            child = subprocess.Popen([PYTHON, '-B', str(Path(__file__).resolve())],
                cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
        record = dict(pid=child.pid, started_utc=now())
        (PHASE/'postprocess_detached.json').write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps(record))
        return
    status = dict(completed=False, stage='waiting_for_training', started_utc=now(),
                  training_run=str(RUN), pid=os.getpid(), steps=[])
    environment = dict(os.environ)
    environment.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', OMP_NUM_THREADS='1')
    pins = json.loads((PHASE/'postprocess_tool_manifest.json').read_text())

    def check_tools():
        for name, digest in pins.items():
            assert hashlib.sha256((PHASE/name).read_bytes()).hexdigest() == digest, name

    def execute(stage, command):
        check_tools()
        status.update(stage=stage, stage_started_utc=now())
        write_status(status)
        with (PHASE/('postprocess_'+stage+'.log')).open('x') as log:
            result = subprocess.run(command, cwd=str(ROOT), env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        status['steps'].append(dict(stage=stage, command=command, returncode=result.returncode,
                                    ended_utc=now()))
        write_status(status)
        if result.returncode:
            raise RuntimeError(stage+' failed; see its preserved console log')

    try:
        check_tools()
        deadline = time.monotonic()+18*3600
        result = None
        while result is None:
            assert time.monotonic() < deadline, 'Training did not finish within18h'
            status.update(last_checked_utc=now(), completed_update_files=len(list(RUN.glob('update_*.json'))))
            write_status(status)
            try:
                result = json.loads((PHASE/'train2000_launch_result.json').read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(30)
        assert result['returncode'] == 0, 'Training launcher failed'
        report = json.loads((RUN/'report.json').read_text())
        assert report['completed'] and report['optimizer_updates'] == 2000
        assert report['transitions'] == 65536000 and not report['failure']
        assert not report['changed_inputs'] and not report['missing_import_pins'] and not report['cleanup_errors']
        execute('verification', [PYTHON, '-B', str(PHASE/'verify_training.py'),
            '--phase', str(PHASE), '--run', str(RUN), '--updates', '2000',
            '--out', str(PHASE/'training_verification.json')])
        execute('evaluation', ['gdb', '-q', '-batch', '-x',
            str(ROOT/'docs/2026-10-22/guitar_learning_long_training_v6/native_trace.gdb'),
            '--args', PYTHON, '-B', str(PHASE/'evaluate_checkpoints.py'),
            '--run', str(RUN), '--out', str(PHASE), '--checkpoints', '0', '500', '1000', '1500', '2000'])
        execute('analysis', [PYTHON, '-B', str(PHASE/'analyze_training.py'),
            '--phase', str(PHASE), '--run', str(RUN), '--updates', '2000',
            '--verification', str(PHASE/'training_verification.json'),
            '--out', str(PHASE/'analysis_final'), '--plots'])
        selection = json.loads((PHASE/'checkpoint_evaluation.json').read_text())['selection']
        movies = []
        choices = ['latest']
        if selection['best']['updates'] != selection['latest']['updates']:
            choices.append('best')
        for choice in choices:
            for view in ('fullbody', 'hand'):
                output = PHASE/(choice+'_'+view+'_video')
                execute('render_'+choice+'_'+view, [PYTHON, '-B', str(PHASE/'render_video.py'),
                    '--selection', choice, '--view', view, '--out', str(output)])
                video = output/(choice+'_'+('fullbody' if view == 'fullbody' else 'left_hand')+'_60fps.mp4')
                assert video.is_file() and video.stat().st_size > 0, str(video)
                movies.append(str(video))
        status.update(completed=True, stage='complete', ended_utc=now(),
                      selection=selection, videos=movies)
        links = '\n'.join('- ['+Path(p).name+']('+p+')' for p in movies)
        table = '\n'.join('| %s | %.4f/67 | %d/1024 |' % (
            '초기' if row['updates'] == 0 else str(row['updates'])+'업데이트',
            row['mean_achieved'], row['safe_count']) for row in selection['scores'])
        comparison = ('평가한 학습 모델 중 최고는 %d업데이트(평균 %.4f/67음), '
            '최종은 %.4f/67음이다. 최고 대비 최종 변화는 %+.4f음이다.\n\n') % (
            selection['best']['updates'], selection['best']['mean_achieved'],
            selection['latest']['mean_achieved'],
            selection['latest']['mean_achieved']-selection['best']['mean_achieved'])
        (PHASE/'RESULTS.md').write_text('# v17 장기 학습 결과\n\n'
            'large/1024환경/H32/seed7의 새 2,000업데이트·65,536,000전이와 '
            '로그검증·5개 체크포인트 평가·분석·영상 렌더를 완료했다.\n\n'
            '| 모델 | 평균 달성음 | 안전 시간축 완주 |\n| --- | ---: | ---: |\n'+table+'\n\n'+comparison+
            '고정 1024환경 첫 종료곡의 평균이며 물리 실패도 분모에 포함한다. '
            '달성음은 연속 clean 문턱의 학습 지표이며 음 끝까지 완전한 유지나 실제 음향 성공률이 아니다. '
            '한 곡·한 seed의 결과로 보상 항의 인과 효과나 일반화를 확정하지 않는다.\n\n'
            '- [학습 로그 분석](analysis_final/analysis.md)\n'
            '- [고정1024환경 평가](checkpoint_evaluation.json)\n'
            '- [로그·저장 검증](training_verification.json)\n\n'+links+'\n')
        write_status(status)
    except BaseException as error:
        status.update(completed=False, stage='error', ended_utc=now(), error_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
        write_status(status)
        raise


if __name__ == '__main__':
    main()
