"""Bind the frozen V4 native-camera replay to the current V5 NN evaluator."""
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


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


parent = module('settlement_video_parent',PARENT/'experiment.py')
reused = module('settlement_video_frozen_replay',SOURCE/'video.py')
cameras = module('settlement_video_frozen_cameras',SOURCE/'cameras.py')
base = parent.base


@contextmanager
def replay_scope():
    old = reused.HERE,reused.PARENT,reused.parent,reused.base
    path = list(sys.path)
    names = ('runtime','learn','cameras')
    aliases = {name:sys.modules.get(name) for name in names}
    try:
        reused.HERE,reused.PARENT,reused.base = HERE,PARENT,base
        reused.parent = SimpleNamespace(gate=parent.gate,cap=parent.parent.cap)
        for name in ('runtime','learn'): sys.modules.pop(name,None)
        sys.modules['cameras'] = cameras
        sys.path[:0] = [str(PARENT),str(parent.parent.cap.v2.ROOT)]
        yield reused
    finally:
        reused.HERE,reused.PARENT,reused.parent,reused.base = old
        sys.path[:] = path
        for name,original in aliases.items():
            if original is None: sys.modules.pop(name,None)
            else: sys.modules[name] = original


def preflight(checkpoint,evaluation):
    reused.gate()  # Frozen reused implementation still matches its own reviewed source pins.
    schedule = base.read(PARENT/'evaluation_schedule.json')['primary_video']
    assert schedule == dict(checkpoint_updates=300,selection='last regardless of score',control='deterministic')
    assert base.read(Path(evaluation)/'learning_report.json')['schema'] == 'diagnostic.release_success_settlement.v5'
    assert base.read(Path(evaluation)/'acceptance.json')['checkpoint_updates'] == 300
    with replay_scope() as implementation:
        return implementation.preflight(checkpoint,evaluation)


def prepare(checkpoint,evaluation):
    preflight(checkpoint,evaluation)
    with replay_scope() as implementation: implementation.prepare(checkpoint,evaluation)
    replay = HERE/'inputs/replay.json'
    selected = base.read(replay)
    selected['selected_control'] = 'actual V5 NN only'
    replay.write_text(json.dumps(selected,indent=2)+'\n')
    seal = HERE/'preparation_seal.json'
    value = base.read(seal)
    value['input_pins'][str(replay)] = base.sha(replay)
    extra = [SOURCE/name for name in ('video.py','cameras.py','cpu_check.py','review.json')]
    value['input_pins'].update({str(path):base.sha(path) for path in extra})
    value['schema'] = 'diagnostic.release_success_settlement.v5.video'
    seal.write_text(json.dumps(value,indent=2)+'\n')


def gate():
    with replay_scope() as implementation: return implementation.gate()


def execute():
    pair = base.read(HERE/'inputs/replay.json')
    preflight(pair['checkpoint'],pair['evaluation'])
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
        print('PASS: own reviewed V5 video gate; stdlib only')
    else: execute()
