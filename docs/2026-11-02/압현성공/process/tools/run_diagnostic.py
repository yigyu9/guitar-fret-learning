"""v9에서16목표를 새로 검사하고 반복 성공 영상만 최종 video에 저장한다.

다른 연구의 프로세스·상태·캐시는 읽거나 제어하지 않는다. --resume은 같은
소스와 이 실행이 완료·봉인한 단계만 재사용한다. 실패한 부분 출력은 자동 삭제하지 않는다.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

TOOLS = Path(__file__).resolve().parent
PROCESS = TOOLS.parent
BASE = PROCESS.parent
REPO = next(p for p in TOOLS.parents if (p/'guitar_learning').is_dir())
MODES = (('free_open', 'none'), ('free_feedback', 'joint_error_integral'), ('free_live', 'live_wrist'))


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_pins():
    # 실행/후처리 및 실제 학습 모듈 변경을 단계 사이마다 감지한다.
    paths = list(TOOLS.glob('*.py'))+list((REPO/'guitar_learning').rglob('*.py'))
    return {str(p.resolve()): sha(p) for p in sorted(paths)}


def successes(report):
    return [r for r in report['goals'] if r['diagnostic_hold_100ms'] and r['failure'] is None]


def verify_report(path):
    report = read(path)
    if not report['source_unchanged'] or report['initial_reset_calls'] != 1:
        raise ValueError('입력/초기화 무결성 실패: '+str(path))
    if len(report['goals']) != 16 or list(report['settings']['representative_rows']) != list(range(16)):
        raise ValueError('16개 목표 전체 기록 필요: '+str(path))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--adopt-geometry', action='store_true', help='같은 v9 소스에서 먼저 완료한 이번 process/geometry 등록')
    parser.add_argument('--cpu-python', default='/home/ajou/miniconda3/envs/rl38/bin/python')
    parser.add_argument('--gpu-python', default='/home/ajou/miniconda3/envs/rl38/bin/python')
    parser.add_argument('--bundle', type=Path, default=REPO/'data/song_bundles/05_BN2-131-B_solo')
    parser.add_argument('--max-nfev', type=int, default=240)
    parser.add_argument('--gpu', default='0')
    args = parser.parse_args()
    PROCESS.mkdir(parents=True, exist_ok=True)
    with (PROCESS/'runner.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(args)


def run(args):
    (BASE/'video').mkdir(parents=True, exist_ok=True)
    pins = source_pins()
    manifest_path = PROCESS/'run_manifest.json'
    settings = dict(bundle=str(args.bundle.resolve()), max_nfev=args.max_nfev, ramp_s=6., hold_s=6.,
                    modes=MODES, cpu_python=args.cpu_python, gpu_python=args.gpu_python, gpu=args.gpu)
    # JSON 문서로 읽힌 tuple/list 차이를 제거한다.
    settings = json.loads(json.dumps(settings))
    if manifest_path.exists():
        if not args.resume:
            raise FileExistsError('기존 실행 발견: 검증 후 이어가려면 --resume 사용')
        manifest = read(manifest_path)
        if manifest['source_pins'] != pins or manifest['settings'] != settings:
            raise RuntimeError('소스 또는 설정이 달라 기존 완료 단계 재사용 불가')
    else:
        manifest = dict(source_pins=pins, settings=settings, completed={})
        write(manifest_path, manifest)
    state = dict(phase='preparing', pid=os.getpid(), completed=list(manifest['completed']))
    def progress(**changes):
        state.update(changes, updated_at=datetime.now(timezone.utc).isoformat())
        write(PROCESS/'status.json', state)
        (PROCESS/'progress.md').write_text('# 압현 진단 진행\n\n단계: '+state['phase']+
            '\n\n최근 확인(UTC): '+state['updated_at']+'\n\n'+state.get('detail', '')+'\n', encoding='utf-8')
    env = os.environ.copy()
    env.update(PYTHONPATH=str(REPO/'isaacgym/python')+':'+str(REPO),
        PATH=str(Path(args.gpu_python).parent)+':/usr/local/cuda/bin:/usr/bin:/bin',
        LD_LIBRARY_PATH=str(Path(args.gpu_python).parent.parent/'lib'),
        PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', LANG='C.UTF-8', LC_ALL='C.UTF-8',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
        MUJOCO_GL='osmesa', TORCH_EXTENSIONS_DIR=str(PROCESS/'cache/torch'),
        CUDA_CACHE_PATH=str(PROCESS/'cache/cuda'), PYTORCH_KERNEL_CACHE_PATH=str(PROCESS/'cache/kernels'),
        MPLCONFIGDIR=str(PROCESS/'cache/mpl'))
    for folder in ('logs', 'cache/torch', 'cache/cuda', 'cache/kernels', 'cache/mpl'):
        (PROCESS/folder).mkdir(parents=True, exist_ok=True)
    def complete(name, proofs):
        manifest['completed'][name] = {str(p.resolve()): sha(p) for p in proofs}
        write(manifest_path, manifest)
        progress(completed=list(manifest['completed']))
    def execute(name, command, proofs, gpu=False, output=None):
        if source_pins() != pins:
            raise RuntimeError('실행 소스가 변경됨')
        if name in manifest['completed']:
            if any(not Path(p).is_file() or sha(Path(p)) != digest for p, digest in manifest['completed'][name].items()):
                raise RuntimeError('완료 단계의 증거가 변경됨: '+name)
            progress(phase='reuse_'+name)
            return
        if output is not None and output.exists():
            raise FileExistsError('미완료 출력은 자동 재사용/삭제하지 않음: '+str(output))
        progress(phase=name, device='gpu' if gpu else 'cpu')
        child = env.copy()
        child['CUDA_VISIBLE_DEVICES'] = args.gpu if gpu else ''
        log_path = PROCESS/'logs'/(name+'.log')
        with log_path.open('a', encoding='utf-8') as stream:
            stream.write('\nSTART '+datetime.now(timezone.utc).isoformat()+'\n')
            stream.flush()
            process = subprocess.Popen([args.gpu_python if gpu else args.cpu_python, '-B']+command,
                cwd=REPO, env=child, stdout=stream, stderr=subprocess.STDOUT)
            progress(child_pid=process.pid, log=str(log_path.resolve()))
            started = time.monotonic()
            try:
                while process.poll() is None:
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        progress(elapsed_s=round(time.monotonic()-started, 1))
            except BaseException:
                # 이 단계에서 직접 만든 자식만 정리한다. 다른 연구에는 신호를 보내지 않는다.
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise
            progress(returncode=process.returncode, child_pid=None)
            if process.returncode:
                raise RuntimeError(name+' 실패: '+str(log_path))
        if source_pins() != pins:
            raise RuntimeError('단계 실행 중 소스가 변경됨')
        complete(name, proofs() if callable(proofs) else proofs)
    try:
        geometry = PROCESS/'geometry'
        if args.adopt_geometry and 'geometry' not in manifest['completed']:
            candidates = read(geometry/'candidates.json')
            if not candidates.get('initial_pose') or len(candidates['goals']) != 16:
                raise ValueError('새 초기자세 출처가 있는16목표 geometry만 등록 가능')
            geometry_pins = read(geometry/'inputs_before.json')
            if any(not Path(path).is_file() or sha(Path(path)) != digest for path, digest in geometry_pins.items()):
                raise RuntimeError('선행 geometry 원본 입력 SHA 불일치')
            if candidates['search']['max_nfev'] != args.max_nfev or Path(candidates['bundle']) != args.bundle.resolve():
                raise RuntimeError('선행 geometry 설정 불일치')
            complete('geometry', sorted(p for p in geometry.rglob('*') if p.is_file()))
        execute('geometry', [str(TOOLS/'runtime.py'), 'geometry', '--bundle', str(args.bundle.resolve()),
                '--out', str(geometry), '--max-nfev', str(args.max_nfev)],
                lambda: sorted(p for p in geometry.rglob('*') if p.is_file()), output=geometry)
        outcomes = {}
        for mode, feedback in MODES:
            for repetition in range(2):
                name = mode+('_repeat' if repetition else '')
                out = PROCESS/'replay'/name
                if feedback == 'live_wrist':
                    command = [str(TOOLS/'live_wrist.py'), '--geometry', str(geometry)]
                else:
                    command = [str(TOOLS/'runtime.py'), 'replay', '--geometry', str(geometry),
                               '--mode', 'free', '--feedback', feedback]
                command += ['--out', str(out), '--ramp-s', '6', '--hold-s', '6']
                execute(name, command, lambda out=out: sorted(p for p in out.rglob('*') if p.is_file()), gpu=True, output=out)
                outcomes[name] = verify_report(out/'report.json')
                if not successes(outcomes[name]):
                    break
        selected = {}
        for mode, _ in MODES:
            if mode+'_repeat' not in outcomes:
                continue
            repeated = {r['row']: r for r in outcomes[mode+'_repeat']['goals']}
            for goal in successes(outcomes[mode]):
                other = repeated[goal['row']]
                quality = min(goal['best_contact_streak_s'], other['best_contact_streak_s'])
                if quality+1e-12 >= .1 and other['failure'] is None:
                    if goal['row'] not in selected or selected[goal['row']]['verified_streak_s'] < quality:
                        selected[goal['row']] = dict(mode=mode, row=goal['row'], verified_streak_s=quality)
        write(PROCESS/'verified_successes.json', dict(successes=list(selected.values()),
            selection='Two independent free-guitar replays from v9, >=100ms continuous diagnostic contact and no safety failure in both; not song achievement'))
        cached = str(TOOLS/'cached_npz_runtime.py')
        analysis = BASE/'analysis'
        execute('analyze', [cached, str(TOOLS/'analyze.py'), '--root', str(PROCESS)],
            [analysis/'analysis.json', analysis/'analysis.csv', analysis/'RESULTS.md'])
        execute('plot', [cached, str(TOOLS/'plot_analysis.py'), '--root', str(PROCESS)],
            [analysis/'summary.png', analysis/'contact_matrix.png', analysis/'plot_data.json'])
        for mode, _ in MODES:
            rows = sorted(row for row, item in selected.items() if item['mode'] == mode)
            if not rows:
                continue
            out = PROCESS/'rendering'/mode
            videos = BASE/'video'/mode
            execute('render_'+mode, [cached, str(TOOLS/'render_summary.py'), '--source', str(PROCESS/'replay'/mode),
                '--out', str(out), '--video-out', str(videos), '--rows']+list(map(str, rows)),
                lambda out=out, videos=videos: sorted(p for folder in (out, videos) for p in folder.rglob('*') if p.is_file()), output=out)
        bad = [p for p in (BASE/'video').rglob('*') if p.is_file() and p.suffix.lower() != '.mp4']
        if bad:
            raise RuntimeError('video에는 MP4만 허용: '+str(bad))
        summarize(outcomes, selected, geometry)
        progress(phase='complete', verified_successes=len(selected), detail='새16목표 검사·조건비교·반복재현·성공영상·분석 완료')
    except BaseException as error:
        progress(phase='failed', failure=repr(error), detail='실패한 단계의 부분 출력도 보존. 로그를 확인한다.')
        raise


def summarize(outcomes, selected, geometry):
    lines = ['# v9 초기자세 압현 진단', '',
        'v9 초기자세에서 손가락별4개, 총16개 목표를 검사했다. 학습된 정책 평가가 아닌 소스 FK 후보의 실제 물리 재생이다.', '',
        '| 조건 | 100ms·안전실패 없음 | 전체 |', '|---|---:|---:|']
    for name, report in outcomes.items():
        lines.append('| %s | %d | 16 |'%(name, len(successes(report))))
    lines += ['', '두 독립 실행에서 모두100ms 이상 연속 진단 접촉을 유지하고 안전실패가 없었던 목표: **%d / 16**.'%len(selected), '',
        '실패도 process/replay에 전부 보존한다. 탐색·추종 실패가 곧 도달 불가능을 뜻하지 않으며,100ms 진단 접촉은 음향 성공이나 곡 시간창 내 달성과 다르다.', '',
        '- `video/`: 반복 검증된 성공 목표의 MP4만 저장.',
        '- `analysis/`: 결과표·CSV·JSON·그림.', '- `process/`: 실행 도구·기하 탐색·실제 기록·로그·렌더 증거·캐시·진행 상태.',
        '- [initial_pose/](initial_pose/README.md): 초기자세 제작 이력과 적용 기록.', '',
        '[상세 분석](analysis/RESULTS.md) · [전체 결과표](analysis/analysis.csv) · [진행 상태](process/status.json)', '']
    (BASE/'README.md').write_text('\n'.join(lines), encoding='utf-8')
    (BASE/'SUMMARY.md').write_text('\n'.join(lines[:len(outcomes)+5])+ '\n\n자세한 결과는 [분석](analysis/RESULTS.md)을 확인한다.\n', encoding='utf-8')
    goals = read(geometry/'candidates.json')['goals']
    rows = ['# 이번 진단 목표', '', '| 번호 | 손가락 | 물리 줄 | 프렛 | 원곡 음 인덱스 |', '|---:|---|---:|---:|---:|']
    names = {1:'검지',2:'중지',3:'약지',4:'소지'}
    rows += ['| %d | %s | %d | %d | %d |'%(g['row'], names[g['finger']], g['physical_string'], g['fret'], g['source_note_index']) for g in goals]
    (BASE/'TARGETS.md').write_text('\n'.join(rows)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
