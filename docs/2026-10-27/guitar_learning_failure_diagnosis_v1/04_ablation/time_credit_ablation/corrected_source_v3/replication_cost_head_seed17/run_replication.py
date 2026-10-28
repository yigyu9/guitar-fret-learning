"""Dry-run by default; fresh B seed17 using the sealed original child wrapper."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SUPPORT = BASE/'support'
sys.path.insert(0, str(SUPPORT))
from run_variant import validate_freeze, watched_sources
from variants import validate_settings

VARIANT = 'B_zero_cost_head'
SEED = 17
OUTPUT = HERE/'B_zero_cost_head_seed17'
REUSED = BASE.parents[2]/'03_short_learning/support/run_short_comparison.py'


def original():
    spec = importlib.util.spec_from_file_location('seed17_original_short_comparison', REUSED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extra_sources():
    return [Path(__file__).resolve(), HERE/'PLAN.md', HERE/'cpu_self_test.py']


def jobs():
    plan = original().jobs(OUTPUT, 'incremental', SEED)
    for job in plan:
        at = job['args'].index('-m')
        job['args'] = job['args'][:at]+[str(Path(__file__).resolve()), 'child', '--variant', VARIANT]+job['args'][at+2:]
    return plan


def validate(job):
    baseline = original()
    checked = baseline.validate(job, 'incremental', SEED)
    validate_settings(baseline.read(Path(job['out'])/'settings.json'), VARIANT)
    for path in extra_sources():
        pins = baseline.read(Path(job['out'])/'inputs_before.json')
        if pins.get(str(path)) != baseline.sha(path):
            raise ValueError('Seed17 adapter input pin mismatch: '+str(path))
    return checked


def child():
    # Keep the existing settings/policy/strict-load path; extend input evidence only.
    import run_variant
    before = run_variant.watched_sources
    run_variant.watched_sources = lambda: [*before(), *extra_sources()]
    try:
        sys.argv.pop(1)
        run_variant.main()
    finally:
        run_variant.watched_sources = before


def analyze():
    baseline = original()
    baseline.analyze(OUTPUT)
    rows = []
    for update in (50, 100, 150, 200, 250, 300):
        summary = baseline.read(OUTPUT/('evaluation_%06d' % update)/'evaluation.json')['summary']
        passed = (summary['achieved_fraction'] >= .8 and summary['mean_clean_fraction'] >= .7
                  and summary['mean_audible_wrong_fraction'] <= .1 and summary['physical_failure_fraction'] <= .05)
        rows.append(dict(update=update, passed=passed, summary=summary))
    pairs = [[a['update'], b['update']] for a, b in zip(rows, rows[1:]) if a['passed'] and b['passed']]
    baseline.write(OUTPUT/'analysis/acceptance.json', dict(variant=VARIANT, seed=SEED,
        criteria=dict(achieved_fraction_min=.8, mean_clean_fraction_min=.7,
            mean_audible_wrong_fraction_max=.1, physical_failure_fraction_max=.05,
            consecutive_policy_evaluations=2), evaluations=rows, passing_pairs=pairs, passed=bool(pairs),
        scope='B seed17 replication without same-seed baseline; not causal comparison against seed7, adoption, free-guitar or full-song success',
        wrist_and_any_failures='reported in each summary; all assigned128 attempts retained'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--continue-evaluations', action='store_true')
    args = parser.parse_args()
    baseline = original()
    plan = jobs()
    if not args.execute:
        print(json.dumps(dict(seed=SEED, variant=VARIANT, output=str(OUTPUT), jobs=plan,
            GPU_executed=False, reuse=str(REUSED)), ensure_ascii=False, indent=2))
        return
    validate_freeze()
    seal = baseline.read(HERE/'preparation_seal.json')
    if seal.get('independent_review') != 'passed_no_findings':
        raise ValueError('Reviewed seed17 CPU preparation required')
    for path, value in seal['input_sha256'].items():
        if baseline.sha(path) != value:
            raise ValueError('Seed17 preparation source changed: '+path)
    OUTPUT.mkdir(exist_ok=args.continue_evaluations)
    (OUTPUT/'logs').mkdir(exist_ok=args.continue_evaluations)
    active = [p for p in (baseline.ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts]
    identity = dict(seed=SEED, variant=VARIANT, jobs=plan, script_path=str(REUSED),
        script_sha256=baseline.sha(REUSED), active_source_pins={str(p.resolve()):baseline.sha(p)
            for p in [*active, *watched_sources(), *extra_sources(), HERE/'preparation_seal.json']},
        teacher_sha256=baseline.sha(baseline.TEACHER), reference_sha256=baseline.sha(baseline.REFERENCE),
        scope='fresh B only; seed17 replication; large128/H32/300 plus10 first-attempt evaluations')
    path = OUTPUT/'comparison_plan.json'
    if path.exists():
        if baseline.read(path) != identity:
            raise ValueError('Existing seed17 job/input identity differs')
    else:
        baseline.write(path, identity)
    env = os.environ.copy()
    env.update(KMP_AFFINITY='disabled', OMP_PROC_BIND='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    env['PATH'] = str(baseline.PYTHON.parent)+os.pathsep+env.get('PATH', '')
    env['PYTHONPATH'] = str(baseline.ROOT/'isaacgym/python')+os.pathsep+str(baseline.ROOT)
    env['LD_LIBRARY_PATH'] = str(baseline.PYTHON.parent.parent/'lib')+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    completed, started = [], time.time()
    for job in plan:
        if Path(job['out']).exists():
            if not args.continue_evaluations:
                raise FileExistsError(job['out'])
            checked = validate(job)
        else:
            print('START '+job['name'], flush=True)
            baseline.run_child(job, OUTPUT, env, identity)
            checked = validate(job)
        completed.append(dict(name=job['name'], verification=checked))
        print('COMPLETE '+job['name'], flush=True)
    if any(baseline.sha(p) != value for p, value in identity['active_source_pins'].items()):
        raise ValueError('Seed17/original input source changed')
    baseline.write(OUTPUT/'comparison_completed.json', dict(completed=True, stages=completed,
        wall_s=time.time()-started, variant=VARIANT, seed=SEED))
    analyze()


if __name__ == '__main__':
    child() if sys.argv[1:2] == ['child'] else main()
