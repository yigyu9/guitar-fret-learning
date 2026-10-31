"""V6 actual NN video through the frozen V4 camera evaluator and V6 local_modules."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE = PARENT.parent/'index_release_reference_learning_v4/video'
SCHEMA = 'diagnostic.cost_prior_zero.v6'


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


parent = module('cost_prior_video_parent',PARENT/'experiment.py')
reused = module('cost_prior_video_frozen_replay',SOURCE/'video.py')
cameras = module('cost_prior_video_frozen_cameras',SOURCE/'cameras.py')
base = parent.base


@contextmanager
def replay_scope():
    old = reused.HERE,reused.PARENT,reused.parent,reused.base
    paths,original_cameras = list(sys.path),sys.modules.get('cameras')
    try:
        reused.HERE,reused.PARENT,reused.base = HERE,PARENT,base
        reused.parent = SimpleNamespace(gate=parent.gate,cap=parent.parent.parent.cap)
        sys.modules['cameras'] = cameras
        yield reused
    finally:
        reused.HERE,reused.PARENT,reused.parent,reused.base = old
        sys.path[:] = paths
        if original_cameras is None: sys.modules.pop('cameras',None)
        else: sys.modules['cameras'] = original_cameras


def preflight(checkpoint,evaluation):
    reused.gate()
    schedule = base.read(PARENT/'evaluation_schedule.json')['primary_video']
    assert schedule == dict(checkpoint_updates=300,selection='last regardless of score',control='deterministic')
    assert base.read(Path(evaluation)/'learning_report.json')['schema'] == SCHEMA
    assert base.read(Path(evaluation)/'acceptance.json')['checkpoint_updates'] == 300
    with replay_scope() as implementation: return implementation.preflight(checkpoint,evaluation)


def prepare(checkpoint,evaluation):
    preflight(checkpoint,evaluation)
    with replay_scope() as implementation: implementation.prepare(checkpoint,evaluation)
    replay = HERE/'inputs/replay.json'
    value = base.read(replay);value['selected_control'] = 'actual V6 NN only'
    replay.write_text(json.dumps(value,indent=2)+'\n')
    seal = HERE/'preparation_seal.json';value = base.read(seal)
    extra = [replay,*[SOURCE/name for name in ('video.py','cameras.py','cpu_check.py','review.json')]]
    value['input_pins'].update({str(path):base.sha(path) for path in extra})
    value['schema'] = SCHEMA+'.video'
    seal.write_text(json.dumps(value,indent=2)+'\n')


def gate():
    with replay_scope() as implementation: return implementation.gate()


def execute():
    pair = base.read(HERE/'inputs/replay.json')
    preflight(pair['checkpoint'],pair['evaluation'])
    gate()  # Own review and complete source pins before Isaac or numerical module loading.
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
        print('PASS: own reviewed V6 video gate; stdlib only')
    else: execute()
