"""입력을 먼저 검증한 뒤 새557 정책의 fit/PPO/독립 평가를 순서대로 실행한다."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CAPTURE = HERE/'capture'
spec = importlib.util.spec_from_file_location('learning_v4_capture_source', CAPTURE/'capture.py')
cap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cap
spec.loader.exec_module(cap)
base = cap.base


def capture_ready():
    """원504핀과 실제 수집·검수 증거를 숫자 라이브러리 없이 확인한다."""
    old = base.HERE
    try:
        base.HERE = CAPTURE
        pins = base.gate()
    finally:
        base.HERE = old
    folder = CAPTURE/'runs/candidate'
    report = base.read(folder/'report.json')
    assert report['completed'] and report['closed'] and report['completed_attempts'] == 128
    assert not report['failure'] and not report['cleanup_errors']
    assert all(report[key] == 0 for key in ('NN_constructors','checkpoint_loads','PPO_updates','fit_steps'))
    audit = base.read(folder/'inputs_after.json')
    assert audit['verified'] and audit['input_pins'] == pins
    verified = base.read(folder/'capture_verification.json')
    assert verified['completed'] and verified['rows'] == 1416 and verified['state_dim'] == 557
    assert verified['q_target_body_candidate_and128ledger_exact'] and verified['source_contract_exact']
    review = base.read(CAPTURE/'actual_review.json')
    assert review['verdict'] == 'PASS' and not review['findings']
    paths = [CAPTURE/'preparation_seal.json',CAPTURE/'actual_review.json',CAPTURE/'REVIEW_ACTUAL.md']
    paths += [folder/name for name in ('observations4.npz','capture_verification.json',
        'report.json','inputs_after.json','training_contract.json','evaluation.json')]
    pins.update({str(path.resolve()): base.sha(path) for path in paths})
    return pins


def gate():
    old = base.HERE
    try:
        base.HERE = HERE
        return base.gate()
    finally:
        base.HERE = old


def prepare():
    pins = capture_ready()
    sys.path.insert(0,str(HERE))
    sys.path.insert(0,str(cap.v2.ROOT))
    import runtime as rt
    import torch
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
    assert 'isaacgym' not in sys.modules
    from guitar_learning.training.finger_skill_runner import _pins
    settings = rt.settings()
    (HERE/'inputs').mkdir(exist_ok=False)
    base.write(HERE/'inputs/settings.json',settings)
    extra = set(map(Path,pins)) | {HERE/name for name in (
        'PLAN.md','runtime.py','learn.py','cpu_check.py','cpu_verification.json','experiment.py')}
    extra.add(HERE/'inputs/settings.json')
    current = _pins(settings,HERE/'inputs',extra)
    base.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=current,
        schema=rt.SCHEMA, old_checkpoint_compatibility=False, planned_fit_steps=1000, planned_PPO_updates=300))
    print(json.dumps(dict(prepared=True,CPU_only=True,pins=len(current))))


def execute(args):
    capture_ready()
    pins = gate()  # 검수·입력 SHA 검사는 Isaac/Torch import보다 먼저 수행한다.
    if args.stage != 'fit':
        assert args.checkpoint is not None
        checkpoint = Path(args.checkpoint).resolve()
        pins[str(checkpoint)] = base.sha(checkpoint)
    import isaacgym
    sys.path.insert(0,str(HERE))
    sys.path.insert(0,str(cap.v2.ROOT))
    import learn
    settings = base.read(HERE/'inputs/settings.json')
    out = Path(args.out).resolve()
    if args.stage == 'fit':
        learn.fit(CAPTURE/'runs/candidate',settings,pins,out)
    elif args.stage == 'train':
        learn.train(checkpoint,settings,pins,out)
    else:
        learn.evaluate(checkpoint,settings,pins,out,stochastic=args.stochastic)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage',required=True)
    sub.add_parser('prepare')
    sub.add_parser('gate-check')
    for name in ('fit','train','evaluate'):
        child = sub.add_parser(name)
        child.add_argument('--out',required=True)
        if name != 'fit':
            child.add_argument('--checkpoint',required=True)
        if name == 'evaluate':
            child.add_argument('--stochastic',action='store_true')
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare()
    elif args.stage == 'gate-check':
        assert not any(name in sys.modules for name in ('numpy','torch','isaacgym'))
        capture_ready(); gate()
        print(json.dumps(dict(ready=True,stdlib_only=True)))
    else:
        execute(args)
