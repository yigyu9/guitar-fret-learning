#!/usr/bin/env python3
"""원격 checkout만 검증한다. 기존 GPU 연구 종료와 CPU 증거 통과를 먼저 기다린다."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT = ROOT / '.runtime/pushed_verification_20261101/project'
PIPELINE = ROOT / 'docs/2026-11-02/압현실험/중지6에서8프렛_환경수비교_20261101/pipeline_v2.json'
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
COMMIT = 'cdca74d921d25142af73caed326a6f19ae1fc27b'


def inside(path, parent):
    try:
        Path(path).relative_to(parent)
        return True
    except ValueError:
        return False


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def command(args, cwd=PROJECT):
    return subprocess.check_output(args, cwd=str(cwd), text=True, stderr=subprocess.STDOUT).strip()


def cpu_gate(audit, project=PROJECT, directory=HERE):
    """수정되지 않은 CPU 감사 증거와 원격 checkout 파일 실체를 확인한다."""
    required = {'completed': True, 'success': True, 'remote_sha': COMMIT,
                'project': str(project), 'clean_tracked': True, 'lfs_verified': True}
    for key, value in required.items():
        if audit.get(key) != value:
            raise ValueError('CPU audit gate failed: ' + key)
    for key in ('checkout_manifest', 'input_audit', 'lfs_report'):
        path = directory / audit[key]
        if path.resolve().parent != directory.resolve():
            raise ValueError('audit evidence outside audit directory')
        if digest(path) != audit[key + '_sha256']:
            raise ValueError('audit evidence changed: ' + key)
    manifest = load(directory / audit['checkout_manifest'])
    if manifest['commit'] != COMMIT or manifest['project'] != str(project) or not manifest['files']:
        raise ValueError('checkout manifest identity mismatch')
    for item in manifest['files']:
        path = project / item['path']
        if not inside(path.resolve(), project.resolve()):
            raise ValueError('checkout file outside project: ' + item['path'])
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('checkout file changed: ' + item['path'])


def ready(pipeline, gpu_pids):
    return pipeline.get('status') in ('complete', 'completed', 'failed', 'interrupted') and not gpu_pids


def gpu_processes():
    output = command(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader,nounits'])
    # 알 수 없는 출력/드라이버 오류는 유휴로 간주하지 않는다.
    if any(not line.strip().isdigit() for line in output.splitlines()):
        raise ValueError('unrecognized GPU process output: ' + output)
    return [int(line) for line in output.splitlines()]


def tracked_identity():
    if command(['git', 'rev-parse', 'HEAD']) != COMMIT:
        raise ValueError('remote commit changed')
    if command(['git', 'rev-parse', 'origin/main']) != COMMIT:
        raise ValueError('remote main identity changed')
    if command(['git', 'status', '--porcelain', '--untracked-files=no']):
        raise ValueError('tracked checkout files changed')


def environment_roots():
    payload = command([PYTHON, '-B', '-c',
        'import json,site,sys; print(json.dumps([sys.prefix,sys.base_prefix]+site.getsitepackages()))'])
    return [Path(value).resolve() for value in json.loads(payload)]


def cleanup_group(child):
    """직접 자식 종료 여부와 별개로 자신의 프로세스 그룹 잔여 자손을 종료한다."""
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass
    # 이미 종료한 strace의 wait()는 자손 생존 여부를 알려주지 않는다.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=15)


def trace_access(path, project=PROJECT, original=ROOT, installed_roots=()):
    """성공한 open의 해석된 경로와 exec/readlink만 데이터 접근 증거로 검사한다."""
    outside, unknown, metadata, unresolved = [], [], 0, []
    accesses = {}
    allowed_roots = [Path(value).resolve() for value in
                     ('/usr', '/bin', '/sbin', '/lib', '/lib64', '/etc', '/dev', '/proc', '/sys', '/run')]
    allowed_roots.extend(Path(value).resolve() for value in installed_roots)
    tool_configs = {Path.home() / '.gitconfig', Path.home() / '.config/git/config'}
    records = 0
    pending = {}
    with Path(path).open(errors='replace') as stream:
        for line in stream:
            pid = line.split(None, 1)[0]
            if '<unfinished ...>' in line:
                pending[pid] = line.split('<unfinished ...>')[0]
                continue
            if 'resumed>' in line:
                if pid not in pending:
                    unresolved.append(line.strip())
                    continue
                line = pending.pop(pid) + line.split('resumed>', 1)[1]
            if re.search(r'\b(stat|lstat|newfstatat|statx|access|faccessat|readlinkat)\(', line):
                metadata += 1
            if not re.search(r'\b(open|openat|openat2|execve|readlink)\(', line):
                continue
            if re.search(r'= -1\b', line) or '<unfinished ...>' in line:
                continue
            candidates = []
            match = re.search(r'= \d+<(/[^>]*)>', line)
            if match:
                candidates.append(match.group(1).split(' (deleted)')[0])
            elif re.search(r'\b(execve|readlink)\(', line) and re.search(r'= (0|[1-9]\d*)\s*$', line):
                found = re.search(r'\b(?:execve|readlink)\("([^"]+)"', line)
                if found and found.group(1).startswith('/'):
                    candidates.append(found.group(1))
                elif found:
                    unresolved.append(line.strip())
            elif re.search(r'\b(open|openat|openat2)\(', line) and re.search(r'= \d+\s*$', line):
                unresolved.append(line.strip())
            for name in candidates:
                if 'O_DIRECTORY' in line:
                    metadata += 1
                    continue
                records += 1
                target = Path(name).resolve()
                if inside(target, project.resolve()):
                    category = 'fresh_checkout'
                elif any(inside(target, parent) for parent in allowed_roots) or target in tool_configs:
                    category = 'installed_environment'
                elif inside(target, original.resolve()) or name.startswith('/media/') or name.startswith('/home/ajou/yigyu/'):
                    category = 'external_project'
                    outside.append({'path': name, 'trace': line.strip()})
                else:
                    category = 'unknown_external'
                    unknown.append({'path': name, 'trace': line.strip()})
                record = accesses.setdefault(name, {'path': name, 'resolved': str(target),
                                                    'category': category, 'count': 0})
                record['count'] += 1
    unresolved.extend(pending.values())
    return {'successful_accesses': records, 'file_accesses': list(accesses.values()),
            'external_project_reads': outside, 'unknown_external_accesses': unknown,
            'metadata_probes': metadata, 'unresolved_successful_accesses': unresolved,
            'passed': records > 0 and not outside and not unknown and not unresolved}


def main():
    report_path = HERE / 'GPU_REPORT.json'
    if report_path.exists():
        raise RuntimeError('GPU_REPORT.json already exists; preserve the earlier attempt')
    report = {'status': 'waiting', 'stage': 'CPU audit', 'driver_pid': os.getpid(),
              'remote_sha': COMMIT, 'project': str(PROJECT), 'actual_gpu_verification': False}
    child = None

    def save():
        report['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        temporary = report_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(report_path)
        (HERE / 'GPU_REPORT.md').write_text(
            '# push된 checkout GPU 검증\n\n상태: ' + report['status'] + '\n\n단계: ' + report['stage'] +
            '\n\n실제 실행·오류·파일 접근 증거는 GPU_REPORT.json에 기록한다. 미실행은 통과가 아니다.\n')

    def stop(signum, _frame):
        raise InterruptedError('received signal %d' % signum)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        save()
        while True:
            audit_path = HERE / 'CPU_AUDIT.json'
            if audit_path.exists():
                audit = load(audit_path)
                if audit.get('completed') is True:
                    cpu_gate(audit)
                    break
                if audit.get('success') is False:
                    raise ValueError('CPU audit failed; GPU verification forbidden')
            time.sleep(15)
        report.update(stage='waiting for original research and GPU release', cpu_audit_sha256=digest(audit_path))
        save()
        while True:
            pipeline = load(PIPELINE)
            pids = gpu_processes()
            report.update(pipeline_status=pipeline.get('status'), existing_gpu_pids=pids)
            save()
            if ready(pipeline, pids):
                break
            time.sleep(15)
        cpu_gate(audit)
        tracked_identity()
        if gpu_processes():
            raise ValueError('GPU acquired by another process before launch')
        out = PROJECT / 'runs/pushed_only_smoke'
        trace = PROJECT / '.runtime/gpu_file_access.log'
        trace.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() or trace.exists():
            raise ValueError('GPU output already exists; preserve earlier attempt')
        args = ['strace', '-f', '-yy', '-e', 'trace=%file', '-o', str(trace), PYTHON, '-B',
                str(PROJECT / 'scripts/smoke_portability.py'), '--out', str(out),
                '--cache-root', str(PROJECT / '.runtime/cache')]
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        for key, name in (('XDG_CACHE_HOME', 'xdg_cache'), ('TMPDIR', 'tmp'), ('CUDA_CACHE_PATH', 'cuda_cache')):
            directory = PROJECT / '.runtime' / name
            directory.mkdir(parents=True, exist_ok=True)
            env[key] = str(directory)
        installed_roots = environment_roots()
        report.update(status='running', stage='native train/resume/evaluation', command=args,
                      script_sha256=digest(__file__), installed_environment_roots=[str(p) for p in installed_roots],
                      relocated_cache_environment={key: env[key] for key in ('XDG_CACHE_HOME', 'TMPDIR', 'CUDA_CACHE_PATH')})
        save()
        with (HERE / 'GPU_DRIVER.log').open('x') as log:
            child = subprocess.Popen(args, cwd=str(PROJECT), env=env, stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            report['child_pid'] = child.pid
            save()
            code = child.wait(timeout=3600)
        report['returncode'] = code
        report['trace'] = trace_access(trace, installed_roots=installed_roots)
        smoke = load(out / 'report.json') if (out / 'report.json').exists() else {}
        report['smoke_report'] = smoke
        stages = {item['name']: item.get('passed') is True and item.get('skipped') is not True
                  for item in smoke.get('stages', [])}
        report['actual_stages'] = {key: stages.get(key, False) for key in ('train', 'resume', 'evaluation')}
        cpu_gate(audit)
        tracked_identity()
        if code != 0 or smoke.get('completed') is not True or not all(report['actual_stages'].values()) or not report['trace']['passed']:
            raise ValueError('GPU smoke or project isolation verification failed')
        report.update(status='completed', stage='verified', actual_gpu_verification=True)
    except BaseException as error:
        report.update(status='interrupted' if isinstance(error, (InterruptedError, KeyboardInterrupt)) else 'failed',
                      failure={'type': type(error).__name__, 'message': str(error)})
    finally:
        if child is not None:
            cleanup_group(child)
        save()
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
