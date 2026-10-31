"""V7 strict accepted-warmup NN replay through the immutable V6 video implementation."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE = PARENT.parent/'index_cost_prior_zero_v6/video'
SCHEMA = 'diagnostic.reward_value_warmup.v7'


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec);sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


parent = module('reward_warmup_video_parent',PARENT/'experiment.py')
adapter = module('reward_warmup_video_v6',SOURCE/'video.py')
reused,cameras,base = adapter.reused,adapter.cameras,parent.base


@contextmanager
def replay_scope():
    old = reused.HERE,reused.PARENT,reused.parent,reused.base,reused.preflight
    paths,old_cameras = list(sys.path),sys.modules.get('cameras')
    try:
        reused.HERE,reused.PARENT,reused.base = HERE,PARENT,base
        reused.parent = SimpleNamespace(gate=parent.gate,cap=old[2].cap)
        reused.preflight = preflight
        sys.modules['cameras'] = cameras
        yield reused
    finally:
        reused.HERE,reused.PARENT,reused.parent,reused.base,reused.preflight = old
        sys.path[:] = paths
        if old_cameras is None: sys.modules.pop('cameras',None)
        else: sys.modules['cameras'] = old_cameras


def preflight(checkpoint,evaluation):
    checkpoint,evaluation = Path(checkpoint).resolve(),Path(evaluation).resolve()
    pins = dict(parent.gate())
    report = base.read(evaluation/'learning_report.json')
    assert report['schema'] == SCHEMA and report['completed'] and report['closed']
    assert not report['failure'] and not report['cleanup_errors']
    assert all(report[k] == 0 for k in ('fit_steps','PPO_updates','selected_reference_calls'))
    acceptance = base.read(evaluation/'acceptance.json')
    assert not acceptance['stochastic'] and acceptance['policy_performance']
    assert acceptance['checkpoint_updates'] == 300 and acceptance['acceptance']['attempts'] == 128
    freeze = base.read(evaluation/'evaluation_freeze.json')
    assert freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen']
    assert freeze['checkpoint_sha_before'] == freeze['checkpoint_sha_after'] == base.sha(checkpoint)
    audit = base.read(evaluation/'inputs_after.json')
    assert audit['verified'] and not base.changed_pins(audit['input_pins'])
    pins.update(audit['input_pins'])
    validate_ledger(base.read(evaluation/'evaluation.json'))
    warmup = PARENT/'runs/fit/warmup_report.json'
    evidence = base.read(warmup)
    assert evidence['accepted'] is True and evidence['steps'] == 1000
    paths = [checkpoint,warmup,*[evaluation/name for name in ('learning_report.json','acceptance.json',
        'evaluation_freeze.json','inputs_after.json','settings.json','evaluation.json',
        'learning_control_env0.npz','training_contract.json')]]
    pins.update({str(path):base.sha(path) for path in paths})
    return pins


def validate_ledger(evaluation):
    assert evaluation['assigned_quotas'] == [1]*128
    episodes = evaluation['episodes']
    assert len(episodes) == 128 and sorted(row['env_id'] for row in episodes) == list(range(128))
    assert sum(len(row['notes']) for row in episodes) == 384
    assert all(row['selected_target_count'] == 3 and
        [note['source_index'] for note in row['notes']] == [4,7,8] for row in episodes)


def prepare(checkpoint,evaluation):
    pins = preflight(checkpoint,evaluation)
    (HERE/'inputs').mkdir(exist_ok=False)
    shutil.copy2(Path(evaluation)/'settings.json',HERE/'inputs/settings.json')
    base.write(HERE/'inputs/replay.json',dict(checkpoint=str(Path(checkpoint).resolve()),
        evaluation=str(Path(evaluation).resolve()),deterministic=True,selected_control='actual V7 NN only',
        accepted_value_warmup_steps=1000,selection='predeclared last300 regardless of score'))
    paths = [*HERE.glob('*.py'),HERE/'PLAN.md',HERE/'cpu_verification.json',*list((HERE/'inputs').glob('*.json')),
        SOURCE/'video.py',*[adapter.SOURCE/name for name in ('video.py','cameras.py','review.json')]]
    pins.update({str(path.resolve()):base.sha(path) for path in paths})
    base.write(HERE/'preparation_seal.json',dict(input_pins=pins,independent_review='pending',schema=SCHEMA+'.video'))


def gate():
    with replay_scope() as implementation: return implementation.gate()


def execute():
    pair = base.read(HERE/'inputs/replay.json')
    preflight(pair['checkpoint'],pair['evaluation']);gate()
    import isaacgym
    with parent.local_modules(include_learn=True) as modules:
        assert Path(modules['runtime'].__file__).resolve() == PARENT/'runtime.py'
        assert Path(modules['learn'].__file__).resolve() == PARENT/'learn.py'
        with replay_scope() as implementation: implementation.execute()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    for name in ('preflight','prepare'):
        child = sub.add_parser(name);child.add_argument('--checkpoint',required=True);child.add_argument('--evaluation',required=True)
    sub.add_parser('gate-check');sub.add_parser('execute')
    args = parser.parse_args()
    if args.action == 'preflight': preflight(args.checkpoint,args.evaluation)
    elif args.action == 'prepare': prepare(args.checkpoint,args.evaluation)
    elif args.action == 'gate-check':
        gate();assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
        print('PASS: own reviewed V7 video gate; stdlib only')
    else: execute()
