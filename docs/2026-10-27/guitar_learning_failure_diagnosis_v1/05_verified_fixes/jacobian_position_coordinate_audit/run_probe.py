"""One unchanged index-reference job; dry plan by default, root owns GPU execution."""
import argparse
import copy
import json
import os
from pathlib import Path
from common import HERE, ROOT, OLD, reused, sha, write, reject_existing


def jobs():
    job = copy.deepcopy(reused().jobs()[1])
    original = job['out']
    job['out'] = str(HERE/'runs/index_reference')
    command = job['args']; start = command.index('-m')
    command[start:start+2] = [str(HERE/'child.py')]
    job['args'] = [value.replace(original, job['out']) for value in command]
    return [job]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    plan, old = jobs(), reused()
    if not args.execute:
        print(json.dumps(dict(jobs=plan, GPU_executed=False), indent=2)); return
    seal = json.loads((HERE/'preparation_seal.json').read_text())
    if seal['independent_review'] != 'passed_no_findings':
        raise ValueError('Independent review required')
    if any(not Path(p).is_file() or sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation changed')
    base = HERE/'runs'; reject_existing(base)
    base.mkdir(); (base/'logs').mkdir()
    baseline = old.original()
    env = os.environ.copy()
    env['PATH'] = str(old.PYTHON.parent)+os.pathsep+env.get('PATH', '')
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT), LD_LIBRARY_PATH=str(old.PYTHON.parent.parent/'lib'))
    identity = dict(script_sha256=sha(old.DIAG/'03_short_learning/support/run_short_comparison.py'), active_source_pins=seal['input_pins'])
    baseline.run_child(plan[0], base, env, identity)
    checked = old.validate(plan[0])
    report = json.loads((base/'index_reference/coordinate_audit_report.json').read_text())
    if not report['completed']:
        raise ValueError('Coordinate observation incomplete')
    import numpy as np
    actual_eval = json.loads((base/'index_reference/evaluation.json').read_text())
    source_eval = json.loads((OLD/'runs/index_reference/evaluation.json').read_text())
    actual = np.load(base/'index_reference/trace_env0_episode0.npz')
    source = np.load(OLD/'runs/index_reference/trace_env0_episode0.npz')
    comparison = {}
    for key in sorted(set(source.files) | set(actual.files)):
        same_shape = key in source.files and key in actual.files and source[key].shape == actual[key].shape
        comparison[key] = dict(same_shape=same_shape, exact=bool(same_shape and np.array_equal(source[key], actual[key])),
            max_abs_difference=float(abs(source[key].astype(float)-actual[key].astype(float)).max()) if same_shape else None)
    write(base/'report.json', dict(completed=True, launcher_returncode=0, original_validation=checked,
        observation_checks=report['checks'], original_reference_comparison=dict(
            evaluation_exact=actual_eval == source_eval, env0_trace_fields=comparison,
            scope='actual reproducibility comparison; disagreement preserved, not hidden or assumed identical'),
        scope='one original initial/reference condition; no control changes'))


if __name__ == '__main__':
    main()
