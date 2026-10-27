"""Run every discovered test module in a fresh CPU Python process.

No floating-point masks or test code are changed. A prior single-process crash
is separate evidence and is never treated as a passed run by this script.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
out = PHASE/'cpu_isolated'
out.mkdir(exist_ok=False)
modules = ['.'.join(p.relative_to(ROOT).with_suffix('').parts)
           for p in sorted((ROOT/'guitar_learning/tests').rglob('test*.py'))]
started, results = time.perf_counter(), []
for module in modules:
    log = out/(module.rsplit('.', 1)[-1]+'.log')
    begin = time.perf_counter()
    with log.open('x') as stream:
        run = subprocess.run([sys.executable, '-B', '-X', 'faulthandler', '-m', 'unittest', module, '-v'],
                             cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT)
    match = re.search(r'Ran (\d+) tests? in ([\d.]+)s', log.read_text())
    results.append(dict(module=module, exit_code=run.returncode,
        tests=int(match.group(1)) if match else None, wall_s=time.perf_counter()-begin,
        log=str(log.relative_to(PHASE))))
    value = dict(completed=len(results)==len(modules), passed=all(r['exit_code']==0 and r['tests'] is not None for r in results),
        modules_completed=len(results), modules_total=len(modules),
        tests=sum(r['tests'] or 0 for r in results), wall_s=time.perf_counter()-started,
        failures=[r for r in results if r['exit_code']!=0 or r['tests'] is None], results=results,
        scope='Fresh CPU process for each module; not a passing single-process suite and not a floating-point root-cause fix')
    temp = out/'status.json.tmp';temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(out/'status.json')
    print(json.dumps(dict(module=module, exit_code=run.returncode, tests=results[-1]['tests'],
        modules_completed=len(results), modules_total=len(modules))),flush=True)
(out/'report.json').write_text(json.dumps(value,indent=2)+'\n')
sys.exit(0 if value['passed'] else 1)
