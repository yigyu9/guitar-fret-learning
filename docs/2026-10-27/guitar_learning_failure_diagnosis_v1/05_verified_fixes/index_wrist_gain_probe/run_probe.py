"""Reuse the original index four jobs, child launcher and validator."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'


def reused():
    path = OLD/'run_prechecks.py'
    spec = importlib.util.spec_from_file_location('index_gain_reused', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jobs():
    result = copy.deepcopy(reused().jobs()[:4])
    for job in result:
        job['out'] = job['out'].replace(str(OLD/'runs'), str(HERE/'runs'))
        args = job['args']
        start = args.index('-m')
        args[start:start+2] = [str(HERE/'child.py')]
        job['args'] = [value.replace(str(OLD/'runs'), str(HERE/'runs')) for value in args]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    plan, old = jobs(), reused()
    baseline = old.original()
    if not args.execute:
        print(json.dumps(dict(jobs=plan, GPU_executed=False), indent=2))
        return
    seal = baseline.read(HERE/'preparation_seal.json')
    if seal['independent_review'] != 'passed_no_findings':
        raise ValueError('Independent reviewed preparation required')
    if any(baseline.sha(path) != value for path, value in seal['input_sha256'].items()):
        raise ValueError('Preparation input changed')
    (HERE/'runs').mkdir(exist_ok=False)
    (HERE/'runs/logs').mkdir()
    env = os.environ.copy()
    env['PATH'] = str(old.PYTHON.parent)+os.pathsep+env.get('PATH', '')
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT),
        LD_LIBRARY_PATH=str(old.PYTHON.parent.parent/'lib'))
    identity = dict(script_sha256=baseline.sha(DIAG/'03_short_learning/support/run_short_comparison.py'),
        active_source_pins=seal['input_sha256'])
    stages, started = [], time.time()
    for job in plan:
        baseline.run_child(job, HERE/'runs', env, identity)
        checked = old.validate(job)
        from child import control
        from guitar_learning.tool.experiments.short_finger_learning.wrist import WRIST_CONTROL
        settings = baseline.read(Path(job['out'])/'settings.json')
        if settings['song']['short_learning']['wrist_control'] != control(WRIST_CONTROL):
            raise ValueError('Actual control contract differs')
        if job['name'] == 'index_initial':
            import torch
            original = torch.load(OLD/'runs/index_initial/initial.pt', map_location='cpu', weights_only=False)
            actual = torch.load(Path(job['out'])/'initial.pt', map_location='cpu', weights_only=False)
            same = [k for k, v in original['model'].items() if torch.equal(v, actual['model'][k])]
            if original['updates'] != 0 or actual['updates'] != 0 or len(same) != 73:
                raise ValueError('Require all73 actual initial tensors identical')
            baseline.write(HERE/'runs/actual_initial_verification.json', dict(updates=0, same_tensors=73,
                original_sha256=baseline.sha(OLD/'runs/index_initial/initial.pt'),
                actual_sha256=baseline.sha(Path(job['out'])/'initial.pt'), control=settings['song']['short_learning']['wrist_control']))
        stages.append(dict(name=job['name'], validation=checked))
        print('COMPLETE '+job['name'], flush=True)
    if any(baseline.sha(path) != value for path, value in seal['input_sha256'].items()):
        raise ValueError('Preparation input changed')
    baseline.write(HERE/'runs/report.json', dict(completed=True, stages=stages, wall_s=time.time()-started,
        scope='single predeclared0.1deg/tick diagnostic; initial.pt reference/zero/random only; no added gain search'))


if __name__ == '__main__':
    main()
