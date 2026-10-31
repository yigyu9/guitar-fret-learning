"""Verify stdlib-only inputs/review before importing numerical or native libraries."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_cost_prior_zero_v6'
AUDIT = HERE.parent/'index_reward_gradient_audit_v1'
spec = importlib.util.spec_from_file_location('warmup_v7_v6_experiment',SOURCE/'experiment.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
base = parent.base


@contextmanager
def local_modules(include_learn=False):
    paths = list(sys.path)
    aliases = {name:sys.modules.get(name) for name in ('runtime','learn')}
    try:
        sys.path[:0] = [str(HERE),str(parent.parent.parent.cap.v2.ROOT)]
        loaded = {}
        for name in ('runtime','learn') if include_learn else ('runtime',):
            spec = importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
        yield loaded
    finally:
        sys.path[:] = paths
        for name,old in aliases.items():
            if old is None: sys.modules.pop(name,None)
            else: sys.modules[name] = old


def evidence():
    pins = parent.gate()
    review = base.read(AUDIT/'actual_analysis_review.json')
    assert review['verdict'] == 'PASS' and not review['findings']
    checked = review['reviewed_sha256']
    assert len(checked) == 660
    assert all(base.sha(path) == digest for path,digest in checked.items())
    # The reviewed map is provenance only. Numerical training opens runs/fit exclusively.
    pins.update(checked)
    for path in (AUDIT/'actual_analysis_review.json',AUDIT/'actual_collection_review.json'):
        pins[str(path)] = base.sha(path)
    for name in ('collection.json','inputs_before.json','inputs_after.json','learning_report.json','first_attempts.json'):
        path = AUDIT/'runs/fit'/name
        assert checked[str(path)] == base.sha(path)
    assert all(checked[str(AUDIT/'runs/fit'/('buffer_%02d.npz'%i))] == base.sha(AUDIT/'runs/fit'/('buffer_%02d.npz'%i)) for i in range(12))
    return pins


def prepare():
    pins = evidence()
    for filename in ('PLAN.md','runtime.py','learn.py','experiment.py','cpu_check.py','cpu_verification.json','launch_training.py','dataset_precheck.json'):
        path = HERE/filename
        pins[str(path)] = base.sha(path)
    plan = HERE.parents[3]/'plans/guitar_learning_reward_value_warmup_20261028.md'
    pins[str(plan)] = base.sha(plan)
    base.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,
        actor_fit_steps=1000,value_warmup_steps=1000,planned_PPO_updates=300,
        training_data='V6fit12buffers_only; other versions are reviewed provenance only'))
    assert not any(name in sys.modules for name in ('numpy','torch','isaacgym'))
    print(json.dumps(dict(prepared=True,pins=len(pins),stdlib_only=True)))


def gate():
    old_pins = evidence()
    old = base.HERE
    try:
        base.HERE = HERE
        pins = base.gate()
    finally: base.HERE = old
    assert all(pins.get(path) == digest for path,digest in old_pins.items())
    return pins


def execute(args):
    pins = gate()
    import isaacgym
    with local_modules(include_learn=True) as modules:
        rt,learn = modules['runtime'],modules['learn']
        settings = rt.settings()
        if args.stage == 'fit':
            learn.fit(parent.parent.parent.CAPTURE/'runs/candidate',settings,pins,Path(args.out).resolve())
        else:
            checkpoint = Path(args.checkpoint).resolve()
            pins[str(checkpoint)] = base.sha(checkpoint)
            if args.stage == 'train': learn.train(checkpoint,settings,pins,Path(args.out).resolve())
            else: learn.evaluate(checkpoint,settings,pins,Path(args.out).resolve(),stochastic=args.stochastic)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage',required=True)
    sub.add_parser('prepare');sub.add_parser('gate-check')
    for name in ('fit','train','evaluate'):
        child = sub.add_parser(name);child.add_argument('--out',required=True)
        if name != 'fit': child.add_argument('--checkpoint',required=True)
        if name == 'evaluate': child.add_argument('--stochastic',action='store_true')
    args = parser.parse_args()
    if args.stage == 'prepare': prepare()
    elif args.stage == 'gate-check':
        gate();assert not any(name in sys.modules for name in ('numpy','torch','isaacgym'));print('{"ready":true,"stdlib_only":true}')
    else: execute(args)
