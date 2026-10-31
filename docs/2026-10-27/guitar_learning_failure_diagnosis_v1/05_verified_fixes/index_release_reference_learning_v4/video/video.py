"""Sealed deterministic replay of one specific V4 NN checkpoint and evaluation."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = importlib.util.spec_from_file_location('video_v4_parent',PARENT/'experiment.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
base = parent.base


def preflight(checkpoint,evaluation):
    checkpoint,evaluation = Path(checkpoint).resolve(),Path(evaluation).resolve()
    pins = dict(parent.gate())
    report = base.read(evaluation/'learning_report.json')
    assert report['completed'] and report['closed'] and not report['failure'] and not report['cleanup_errors']
    assert all(report[k] == 0 for k in ('fit_steps','PPO_updates','selected_reference_calls'))
    acceptance = base.read(evaluation/'acceptance.json')
    assert not acceptance['stochastic'] and acceptance['policy_performance']
    assert acceptance['acceptance']['attempts'] == 128
    freeze = base.read(evaluation/'evaluation_freeze.json')
    assert freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen']
    assert freeze['checkpoint_sha_before'] == freeze['checkpoint_sha_after'] == base.sha(checkpoint)
    audit = base.read(evaluation/'inputs_after.json')
    assert audit['verified'] and not base.changed_pins(audit['input_pins'])
    pins.update(audit['input_pins'])
    assert base.read(evaluation/'settings.json') == base.read(PARENT/'inputs/settings.json')
    assert base.read(evaluation/'evaluation.json')['assigned_quotas'] == [1]*128
    for name in ('learning_report.json','acceptance.json','evaluation_freeze.json','inputs_after.json',
                 'settings.json','evaluation.json','learning_control_env0.npz','training_contract.json'):
        path = evaluation/name; pins[str(path)] = base.sha(path)
    pins[str(checkpoint)] = base.sha(checkpoint)
    return pins


def prepare(checkpoint,evaluation):
    pins = preflight(checkpoint,evaluation)
    (HERE/'inputs').mkdir(exist_ok=False)
    shutil.copy2(PARENT/'inputs/settings.json',HERE/'inputs/settings.json')
    base.write(HERE/'inputs/replay.json',dict(checkpoint=str(Path(checkpoint).resolve()),
        evaluation=str(Path(evaluation).resolve()),deterministic=True,selected_control='actual V4 NN only'))
    for path in [*HERE.glob('*.py'),HERE/'PLAN.md',HERE/'cpu_verification.json',*list((HERE/'inputs').glob('*.json'))]:
        pins[str(path.resolve())] = base.sha(path)
    base.write(HERE/'preparation_seal.json',dict(input_pins=pins,independent_review='pending',
        source='specific deterministic NN evaluation; environment0 first attempt preselected'))


def gate():
    old = base.HERE
    try:
        base.HERE = HERE
        return base.gate()
    finally: base.HERE = old


def execute():
    replay = base.read(HERE/'inputs/replay.json')
    preflight(replay['checkpoint'],replay['evaluation'])
    pins = gate()  # All source/review/checkpoint evidence before numerical/native imports.
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    sys.path.insert(0,str(PARENT)); sys.path.insert(0,str(parent.cap.v2.ROOT))
    import runtime as rt
    import learn
    from guitar_learning.tool.demonstration import render_finger_skill as render
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    from cameras import pool_type
    out = HERE/'runs/replay'
    original,holders,failure = rt.GoalPool,[],None
    try:
        rt.GoalPool = pool_type(original,gymapi,np,render,GraphicsGym,finish_video,base,out,holders)
        learn.evaluate(replay['checkpoint'],base.read(HERE/'inputs/settings.json'),pins,out,stochastic=False)
        capture = holders[0].video_capture
        assert len(capture.samples) == 354 and len(capture.frame_times_s) == 177
        source = Path(replay['evaluation'])
        assert base.read(out/'evaluation.json')['episodes'] == base.read(source/'evaluation.json')['episodes']
        with np.load(out/'learning_control_env0.npz',allow_pickle=False) as current, \
             np.load(source/'learning_control_env0.npz',allow_pickle=False) as before:
            for key in ('q','target','body_state','candidate','raw_goal_normalized','decoded_goal_rad'):
                np.testing.assert_array_equal(current[key],before[key])
            for key in ('q','target','body_state'):
                np.testing.assert_array_equal(np.asarray([r[key] for r in capture.samples]),current[key])
            force_difference = float(np.max(np.abs(current['net_body_force_n']-before['net_body_force_n'])))
        base.write(out/'video_verification.json',dict(completed=True,actual_NN=True,deterministic=True,
            checkpoint_sha256=base.sha(replay['checkpoint']),all128ledger_and_q_target_body_candidate_rawgoals_exact=True,
            force_difference_max_N=force_difference,force_difference_is_separate=True,
            controls=354,frames=177,fps=30,size=[1280,720],duration_s=5.9,env_id=0,first_attempt=True))
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error))
        raise
    finally:
        rt.GoalPool = original
        if out.is_dir():
            try:
                changed = base.changed_pins(pins)
                closed = bool(holders) and bool(getattr(holders[0],'closed',False))
                completed = failure is None and not changed and closed
                base.write(out/'video_report.json',dict(completed=completed,failure=failure,
                    source_alias_restored=rt.GoalPool is original,
                    scene_closed=closed,changed_inputs=changed,native_pixels=True,actual_NN=True))
                if failure is None and not completed: raise RuntimeError('Video input/lifecycle audit failed')
            except BaseException:
                if failure is None: raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    for name in ('preflight','prepare'):
        child = sub.add_parser(name);child.add_argument('--checkpoint',required=True);child.add_argument('--evaluation',required=True)
    sub.add_parser('gate-check');sub.add_parser('execute')
    args = parser.parse_args()
    if args.action in ('preflight','prepare'):
        if args.action == 'prepare': prepare(args.checkpoint,args.evaluation)
        else: preflight(args.checkpoint,args.evaluation); print(json.dumps(dict(ready=True,native_runs=0)))
    elif args.action == 'gate-check':
        assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'));gate()
        print(json.dumps(dict(ready=True,stdlib_only=True)))
    else: execute()
