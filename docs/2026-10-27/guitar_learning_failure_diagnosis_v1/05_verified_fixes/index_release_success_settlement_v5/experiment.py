"""V5 입력 봉인을 먼저 검사하고 fit·PPO·독립 평가를 실행한다."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_release_reference_learning_v4'
spec = importlib.util.spec_from_file_location('settlement_v5_parent_experiment', SOURCE/'experiment.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
base = parent.base


def gate():
    parent.capture_ready()
    pins = parent.gate()
    old = base.HERE
    try:
        base.HERE = HERE
        own = base.gate()
    finally:
        base.HERE = old
    assert all(own.get(path) == digest for path,digest in pins.items())
    return own


def prepare():
    pins = parent.capture_ready()
    pins.update(parent.gate())
    sys.path[:0] = [str(HERE),str(parent.cap.v2.ROOT)]
    import runtime as rt
    import torch
    from guitar_learning.training.finger_skill_runner import _pins
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
    assert 'isaacgym' not in sys.modules
    (HERE/'inputs').mkdir(exist_ok=False)
    base.write(HERE/'inputs/settings.json',rt.settings())
    extra = set(map(Path,pins)) | {HERE/name for name in ('PLAN.md','runtime.py','learn.py',
        'experiment.py','evaluation_schedule.json','cpu_check.py','cpu_verification.json','launch_training.py','inputs/settings.json')}
    extra.update(SOURCE/'runs/fit'/name for name in ('fresh.pt','fit.pt'))
    current = _pins(rt.settings(),HERE/'inputs',extra)
    base.write(HERE/'preparation_seal.json',dict(independent_review='pending', input_pins=current,
        schema=rt.SCHEMA,old_checkpoint_compatibility=False,planned_fit_steps=1000,planned_PPO_updates=300))
    print(json.dumps(dict(prepared=True,CPU_only=True,pins=len(current))))


def execute(args):
    pins = gate()  # 숫자/Isaac 라이브러리보다 입력과 검수를 먼저 검사한다.
    if args.stage != 'fit':
        checkpoint = Path(args.checkpoint).resolve()
        pins[str(checkpoint)] = base.sha(checkpoint)
    import isaacgym
    sys.path[:0] = [str(HERE),str(parent.cap.v2.ROOT)]
    import learn
    settings = base.read(HERE/'inputs/settings.json')
    out = Path(args.out).resolve()
    if args.stage == 'fit': learn.fit(parent.CAPTURE/'runs/candidate',settings,pins,out)
    elif args.stage == 'train': learn.train(checkpoint,settings,pins,out)
    else: learn.evaluate(checkpoint,settings,pins,out,stochastic=args.stochastic)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage',required=True)
    sub.add_parser('prepare'); sub.add_parser('gate-check')
    for name in ('fit','train','evaluate'):
        child = sub.add_parser(name); child.add_argument('--out',required=True)
        if name != 'fit': child.add_argument('--checkpoint',required=True)
        if name == 'evaluate': child.add_argument('--stochastic',action='store_true')
    args = parser.parse_args()
    if args.stage == 'prepare': prepare()
    elif args.stage == 'gate-check':
        gate(); assert not any(name in sys.modules for name in ('numpy','torch','isaacgym'))
        print(json.dumps(dict(ready=True,stdlib_only=True)))
    else: execute(args)
