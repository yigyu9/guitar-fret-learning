"""Fresh current index bootstrap, then own initial reference/zero/random; dry by default."""
import argparse
import copy
import json
import os
from pathlib import Path
from common import HERE, ROOT, OLD, OLD_INITIAL, reused, sha, write, reject_existing


def jobs():
    result = copy.deepcopy(reused().jobs()[:4])
    for job in result:
        job['out'] = job['out'].replace(str(OLD/'runs'), str(HERE/'runs'))
        command = job['args']; index = command.index('-m')
        command[index:index+2] = [str(HERE/'child.py')]
        job['args'] = [value.replace(str(OLD/'runs'), str(HERE/'runs')) for value in command]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    plan, old = jobs(), reused()
    if not args.execute:
        print(json.dumps(dict(jobs=plan, GPU_executed=False), indent=2)); return
    seal = json.loads((HERE/'preparation_seal.json').read_text())
    if seal['independent_review'] != 'passed_no_findings':
        raise ValueError('Independent reviewed current preparation required')
    if any(not Path(p).is_file() or sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation changed')
    base = HERE/'runs'; reject_existing(base); base.mkdir(); (base/'logs').mkdir()
    original = old.original()
    env = os.environ.copy()
    env['PATH'] = str(old.PYTHON.parent)+os.pathsep+env.get('PATH','')
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT), LD_LIBRARY_PATH=str(old.PYTHON.parent.parent/'lib'))
    identity = dict(script_sha256=sha(old.DIAG/'03_short_learning/support/run_short_comparison.py'), active_source_pins=seal['input_pins'])
    stages = []
    for job in plan:
        original.run_child(job, base, env, identity)
        # Only current new jobs are validated; old historical runs are never revalidated under new source.
        checked = old.validate(job)
        audit = json.loads((Path(job['out'])/'precheck_audit.json').read_text())
        if not audit['completed']:
            raise ValueError('Incomplete current precheck sidecar')
        if job['name'] == 'index_initial':
            import torch
            prior = torch.load(OLD_INITIAL, map_location='cpu', weights_only=False)
            fresh = torch.load(Path(job['out'])/'initial.pt', map_location='cpu', weights_only=False)
            same = {k: bool(k in fresh['model'] and torch.equal(v, fresh['model'][k])) for k, v in prior['model'].items()}
            identical = set(prior['model']) == set(fresh['model']) and len(same) == 73 and all(same.values())
            write(base/'initial_model_comparison.json', dict(old_sha256=sha(OLD_INITIAL), fresh_sha256=sha(Path(job['out'])/'initial.pt'),
                same_model_tensors=same, key_sets_equal=set(prior['model']) == set(fresh['model']), all73_equal=identical,
                scope='model values only; no old full strict load or inherited performance'))
            if not identical:
                raise ValueError('Fresh initial must match all73 original model tensors; comparison preserved')
        stages.append(dict(name=job['name'], launcher_returncode=0, validation=checked, sidecar_checks=audit['checks']))
    if any(sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation changed')
    write(base/'report.json', dict(completed=True, stages=stages,
        scope='current geometry and wrist qpos-J v2; fresh initial only;4first attempts each including failures; not learned policy performance'))


if __name__ == '__main__':
    main()
