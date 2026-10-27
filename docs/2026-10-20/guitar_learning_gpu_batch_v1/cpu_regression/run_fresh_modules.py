"""Serial fresh-process CPU regression driver; never changes project sources."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
ENVIRONMENT = dict(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='',
    MPLCONFIGDIR='/tmp/guitar_gpu_cpu_regression_matplotlib')
ENV = dict(os.environ, **ENVIRONMENT)
FILES = sorted(subprocess.check_output(['rg', '--files', 'guitar_learning/tests', '-g', 'test_*.py'], cwd=str(ROOT), text=True).splitlines())
START = time.monotonic()
REPORT = dict(schema='guitar_learning.fresh_process_cpu_regression.v1',
    started_utc=datetime.now(timezone.utc).isoformat(), cwd=str(ROOT), python=PYTHON,
    environment=ENVIRONMENT, timeout_s=300, discovery_command=['rg', '--files', 'guitar_learning/tests', '-g', 'test_*.py'],
    discovered_modules=len(FILES), modules=[], isolated_replays=[], completed=False)


def save():
    REPORT['elapsed_s'] = time.monotonic()-START
    REPORT['finished_modules'] = len(REPORT['modules'])
    REPORT['summary'] = dict(
        module_passes=sum(r['returncode'] == 0 for r in REPORT['modules']),
        module_failures=sum(r['returncode'] != 0 for r in REPORT['modules']),
        tests_reported=sum(r['tests_reported'] for r in REPORT['modules']),
        test_failures=sum(r['failures'] for r in REPORT['modules']),
        test_errors=sum(r['errors'] for r in REPORT['modules']),
        skipped=sum(r['skipped'] for r in REPORT['modules']))
    temporary=OUT/'status.tmp'
    temporary.write_text(json.dumps(REPORT, indent=2)+'\n')
    temporary.replace(OUT/'report.json')


def execute(name, log_dir):
    command = [PYTHON, '-B', '-m', 'unittest', name, '-v']
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=str(ROOT), env=ENV, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=300)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as failure:
        output = failure.stdout or ''
        if isinstance(output, bytes): output=output.decode('utf-8', 'replace')
        output += '\nCPU regression driver timeout after300s.\n'
        code = 124
    log = OUT/log_dir/(name+'.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output)
    ran = re.findall(r'Ran (\d+) tests? in ([\d.]+)s', output)
    failure = re.findall(r'^FAILED \(([^\n]+)\)', output, re.MULTILINE)
    ending = failure[-1] if failure else ''
    skipped = re.findall(r'(?:skipped=)(\d+)', output)
    row = dict(name=name, command=command, returncode=code,
        elapsed_s=time.monotonic()-started, log=str(log.relative_to(ROOT)),
        tests_reported=int(ran[-1][0]) if ran else 0,
        unittest_elapsed_s=float(ran[-1][1]) if ran else None,
        failures=int(re.search(r'failures=(\d+)',ending).group(1)) if re.search(r'failures=(\d+)',ending) else 0,
        errors=int(re.search(r'errors=(\d+)',ending).group(1)) if re.search(r'errors=(\d+)',ending) else 0,
        skipped=int(skipped[-1]) if skipped else 0)
    if code < 0:
        row['signal'] = -code
        verbose = re.findall(r'^(test_\w+) \(([^)]+)\) \.\.\.',output,re.MULTILINE)
        row['last_verbose_test'] = (verbose[-1][1]+'.'+verbose[-1][0]) if verbose else None
    return row


save()
for filename in FILES:
    module = filename[:-3].replace('/', '.')
    before = hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()
    result = execute(module, 'modules')
    result['test_source_sha256'] = before
    REPORT['modules'].append(result)
    print('%s/%s %s rc=%s reported=%s duration=%.3fs' % (
        len(REPORT['modules']),len(FILES),module,result['returncode'],
        result['tests_reported'],result['elapsed_s']),flush=True)
    save()
    if result['returncode'] == -8:
        # Every method in a SIGFPE module gets its own process, including those
        # preceding the crash; imports and FPU state never leak between methods.
        tree = ast.parse((ROOT/filename).read_text())
        for node in tree.body:
            if isinstance(node,ast.ClassDef):
                methods=[item.name for item in node.body
                         if isinstance(item,ast.FunctionDef) and item.name.startswith('test_')]
                for method in methods:
                    replay = execute(module+'.'+node.name+'.'+method, 'isolated')
                    replay['parent_module'] = module
                    REPORT['isolated_replays'].append(replay)
                    print('  isolated %s rc=%s duration=%.3fs' % (
                        replay['name'],replay['returncode'],replay['elapsed_s']),flush=True)
                    save()
REPORT['completed'] = True
REPORT['finished_utc'] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps(REPORT['summary']),flush=True)
