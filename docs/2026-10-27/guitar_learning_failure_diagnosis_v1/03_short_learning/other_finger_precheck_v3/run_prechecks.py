"""Dry-run by default; twelve original-CLI stages, no long RL or source edits."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
PYTHON = Path('/home/ajou/miniconda3/envs/rl38/bin/python')
MODULE = 'guitar_learning.tool.experiments.short_finger_learning'
ROWS = (('index', 1), ('ring', 16), ('pinky', 23))


def original():
    path = DIAG/'03_short_learning/support/run_short_comparison.py'
    spec = importlib.util.spec_from_file_location('other_finger_original_precheck', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jobs():
    prefix = ['taskset', '-c', '0-13', 'env', 'KMP_AFFINITY=disabled', 'OMP_PROC_BIND=false',
              'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', str(PYTHON), '-m', MODULE]
    result = []
    for finger, row in ROWS:
        teacher = HERE/('teacher_%s_row%d.json' % (finger, row))
        reference = HERE/('reference_%s_row%d.json' % (finger, row))
        train = HERE/'runs'/(finger+'_initial')
        result.append(dict(name=finger+'_initial', out=str(train), finger=finger, teacher=str(teacher),
            args=prefix+['train', '--teacher', str(teacher), '--mode', 'incremental', '--initial-std',
                '.1711710544767014', '--size', 'large', '--num-envs', '4', '--horizon', '32',
                '--updates', '1', '--save-every', '50', '--seed', '7', '--out', str(train)]))
        for control in ('reference', 'zero', 'random'):
            output = HERE/'runs'/(finger+'_'+control)
            args = prefix+['evaluate', '--checkpoint', str(train/'initial.pt'), '--control', control,
                          '--episodes', '4', '--out', str(output)]
            if control == 'reference':
                args += ['--reference', str(reference)]
            result.append(dict(name=finger+'_'+control, out=str(output), finger=finger,
                teacher=str(teacher), control=control, args=args))
    return result


def validate(job):
    baseline = original()
    output = Path(job['out'])
    report, after = baseline.read(output/'report.json'), baseline.read(output/'inputs_after.json')
    before = baseline.read(output/'inputs_before.json')
    settings, scene = baseline.read(output/'settings.json'), baseline.read(output/'gpu_scene_final.json')
    if (not report['completed'] or not report['closed'] or report['failure'] or not after['verified']
            or not scene['closed'] or before != after['input_pins']):
        raise ValueError('Incomplete precheck: '+job['name'])
    expected = dict(seed=7, size='large', num_envs=4, horizon=32, updates=1)
    if any(settings[key] != value for key, value in expected.items()):
        raise ValueError('Precheck settings differ')
    teacher = settings['song']['short_learning']['teacher']
    if teacher['input_path'] != job['teacher'] or teacher['input_sha256'] != baseline.sha(job['teacher']):
        raise ValueError('Precheck teacher differs')
    spec = settings['song']['short_learning']
    if (spec['mode'] != 'incremental' or spec['initial_std'] != .1711710544767014
            or settings['initial_std'] != spec['initial_std']):
        raise ValueError('Precheck action/exploration contract differs')
    if any(baseline.sha(path) != value for path, value in after['input_pins'].items()):
        raise ValueError('Precheck source changed')
    if 'control' not in job:
        if not (output/'initial.pt').is_file():
            raise ValueError('Missing own initial checkpoint')
        metrics = [json.loads(line) for line in (output/'metrics.jsonl').read_text().splitlines()]
        if len(metrics) != 1 or metrics[0]['update'] != 1 or metrics[0]['total_transitions'] != 128:
            raise ValueError('Expected only one bootstrap update')
        return dict(initial_checkpoint=str(output/'initial.pt'), initial_sha256=baseline.sha(output/'initial.pt'),
                    scope='one-update bootstrap only; trained final checkpoint unused')
    evaluation = baseline.read(output/'evaluation.json')
    episodes = evaluation['episodes']
    if (evaluation['condition'] != job['control'] or evaluation['assigned_quotas'] != [1]*4
            or len(episodes) != 4 or sorted(e['env_id'] for e in episodes) != list(range(4))):
        raise ValueError('Require all four assigned first attempts, failures included')
    return dict(summary=evaluation['summary'], scope='scripted/zero/initial-random control; not trained policy')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    plan, baseline = jobs(), original()
    if not args.execute:
        print(json.dumps(dict(jobs=plan, GPU_executed=False, learned_final_checkpoint_used=False), ensure_ascii=False, indent=2))
        return
    seal = baseline.read(HERE/'preparation_seal.json')
    if seal.get('independent_review') != 'passed_no_findings':
        raise ValueError('Reviewed CPU preparation required before root GPU handoff')
    if any(baseline.sha(path) != value for path, value in seal['input_sha256'].items()):
        raise ValueError('Precheck preparation changed')
    (HERE/'runs').mkdir(exist_ok=False)
    (HERE/'runs/logs').mkdir()
    reused = DIAG/'03_short_learning/support/run_short_comparison.py'
    identity = dict(script_sha256=baseline.sha(reused), active_source_pins=seal['input_sha256'])
    env = os.environ.copy()
    env['PATH'] = str(PYTHON.parent)+os.pathsep+env.get('PATH', '')
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT),
               LD_LIBRARY_PATH=str(PYTHON.parent.parent/'lib'))
    completed, started = [], time.time()
    for job in plan:
        baseline.run_child(job, HERE/'runs', env, identity)
        completed.append(dict(name=job['name'], validation=validate(job)))
        print('COMPLETE '+job['name'], flush=True)
    if any(baseline.sha(path) != value for path, value in seal['input_sha256'].items()):
        raise ValueError('Precheck preparation source changed')
    baseline.write(HERE/'runs/report.json', dict(completed=True, stages=completed, wall_s=time.time()-started,
        scope='three unverified source candidates tested under finite arm-only wrist teacher; no long RL/free-guitar/full-song claim'))


if __name__ == '__main__':
    main()
