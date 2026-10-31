"""원128환경 마지막300 평균정책을 바꾸지 않고 native 손·전신 영상만 덧붙인다."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('current_ring_learning_video_parent', HERE.parent/'experiment.py')
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)
pre = learning.pre
ROOT = learning.ROOT
BASE = HERE.parent/'runs/evaluation_000300'
SCHEMA = 'diagnostic.current_ring_learning_video.v1'


def same(a, b, torch):
    """실제 optimizer의 중첩 tensor도 값과 구조를 모두 비교한다."""
    if type(a) is not type(b): return False
    if torch.is_tensor(a): return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict): return a.keys() == b.keys() and all(same(a[k], b[k], torch) for k in a)
    if isinstance(a, (tuple, list)): return len(a) == len(b) and all(same(x, y, torch) for x, y in zip(a, b))
    return a == b


def trainer_state(trainer):
    return copy.deepcopy(dict(model=trainer.policy.state_dict(), actor=trainer.actor_optimizer.state_dict(),
        value=trainer.value_optimizer.state_dict(), updates=trainer.updates, cost_weight=trainer.cost_weight))


@contextmanager
def hooks(runner, state, out):
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    renderer = importlib.import_module('guitar_learning.tool.demonstration.render_finger_skill')
    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras, _encoder, _EnvZeroCapture
    cameras_original = renderer.CAMERAS
    renderer.CAMERAS = dict(cameras_original, fullbody=((-.10, 3.4, 1.1), (-.15, -.10, .65)))
    acquire, evaluate, factory = gymapi.acquire_gym, runner._evaluate, runner.DecisionPPOTrainer
    def trainer(*args, **kwargs):
        value = factory(*args, **kwargs); state['trainer'] = value; return value
    def render(pool, policy, spec, args, destination):
        before = trainer_state(state['trainer'])
        cameras, videos, capture = {}, {}, None
        step = pool.step
        primary = None
        try:
            cameras = _create_cameras(pool.scene, gymapi)
            for name in cameras: videos[name] = _encoder(out/(name+'.mp4'))
            capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
            state['capture'] = capture
            def observed(action):
                result = step(action)
                capture.record(None, *result[1:])
                return result
            pool.step = observed
            result = evaluate(pool, policy, spec, args, destination)
            state['trainer_unchanged'] = same(before, trainer_state(state['trainer']), torch)
            if not state['trainer_unchanged'] or capture.episode is None: raise ValueError('Model/optimizer mutation or missing first episode')
            return result
        except BaseException as error:
            primary = error; raise
        finally:
            pool.step = step
            for name, process in videos.items():
                try:
                    code, errors = finish_video(process)
                    state['encoding'][name] = code
                    state['cleanup_errors'].extend(errors)
                except BaseException as error:
                    state['cleanup_errors'].append(repr(error))
            if capture and capture.samples:
                try:
                    np.savez_compressed(out/('partial_poses.npz' if primary else 'poses.npz'),
                        **{key: np.stack([row[key] for row in capture.samples]) for key in capture.samples[0]})
                    pre.write(out/'capture.json', dict(frames=len(capture.frame_times_s), frame_times_s=capture.frame_times_s,
                        first_physics_step=int(capture.samples[0]['physics_step']), last_physics_step=int(capture.samples[-1]['physics_step']),
                        episode=capture.episode, environment=0, first_attempt_only=True, fps=30, width=1280, height=720,
                        selection='predeclared last300 mean; env0 first attempt; all128 evaluation attempts retained',
                        mapping='frame n = control endpoint 2*(n+1); no t0 frame; no frame for odd last endpoint'))
                except BaseException as error:
                    state['cleanup_errors'].append(repr(error))
    gymapi.acquire_gym = lambda: GraphicsGym(acquire())
    runner._evaluate, runner.DecisionPPOTrainer = render, trainer
    try: yield
    finally:
        gymapi.acquire_gym, runner._evaluate, runner.DecisionPPOTrainer = acquire, evaluate, factory
        renderer.CAMERAS = cameras_original
        state['render_hooks_restored'] = (gymapi.acquire_gym, runner._evaluate, runner.DecisionPPOTrainer) == (acquire, evaluate, factory) and renderer.CAMERAS is cameras_original


def compare(out):
    import numpy as np
    actual, expected = pre.read(out/'evaluation.json'), pre.read(BASE/'evaluation.json')
    learning.complete_evaluation(actual)
    if actual != expected: raise ValueError('All128 first-attempt results differ from original last300 evaluation')
    with np.load(out/'trace_env0_episode0.npz') as actual, np.load(BASE/'trace_env0_episode0.npz') as expected:
        if set(actual.files) != set(expected.files): raise ValueError('Trace field set differs')
        differences = {}
        for key in actual.files:
            a, b = actual[key], expected[key]
            if a.shape != b.shape or a.dtype != b.dtype: raise ValueError('Trace shape/dtype differs: '+key)
            if key == 'net_body_force_n':
                differences[key] = float(np.max(np.abs(a-b)))
                if not np.allclose(a, b, rtol=0, atol=1e-4): raise ValueError('Native force difference exceeds declared 1e-4N tolerance')
            elif not np.array_equal(a, b): raise ValueError('Non-force trace differs: '+key)
    return dict(all128_first_attempts_exact=True, all_nonforce_trace_fields_exact=True, force_max_abs_difference_n=differences['net_body_force_n'], force_tolerance_n=1e-4)


def inputs():
    seal, paths = learning.gate('evaluate')
    cpu = pre.read(HERE/'cpu_verification.json')
    if not cpu['passed'] or cpu['source_sha256'] != pre.sha(HERE/'video.py'):
        raise ValueError('Current video source CPU verification required')
    for directory in (HERE.parent/'runs/train', BASE):
        report = pre.read(directory/'diagnostic_report.json')
        if not report['completed']: raise ValueError('Completed source training and last300 mean evaluation required')
        if directory == BASE and (report['phase'] != 'evaluate' or report['update'] != 300 or report['sampling'] != 'mean'):
            raise ValueError('Predeclared last300 mean evaluation required')
        pre.verify_pins(report['result_sha256'])
        paths.update(map(Path, report['result_sha256']))
        paths.update((directory/'diagnostic_report.json', directory/'diagnostic_inputs_after.json'))
    paths.update((HERE/'PLAN.md', HERE/'video.py', HERE/'cpu_check.py', HERE/'cpu_verification.json'))
    return paths


def prepare():
    # Torch/Isaac/NN/checkpoint를 읽지 않는다. 원 평가 완료 후에만 봉인한다.
    paths = inputs()
    paths.update(ROOT/path for path in ('guitar_learning/tool/demonstration/render_finger_skill.py',
        'guitar_learning/tool/demonstration/__init__.py', 'guitar_learning/tool/validation/hand_contact_probe.py'))
    pre.write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending',
        input_pins={str(path):pre.sha(path) for path in sorted(paths)}, review_documents_sha256={}))


def gate():
    seal = pre.read(HERE/'preparation_seal.json'); pre.verify_pins(seal['input_pins'])
    review = pre.read(HERE/'review.json')
    if (seal['schema'] != SCHEMA or seal['independent_review'] != 'passed_no_findings' or review['verdict'] != 'PASS' or
        review['findings'] or review['reviewed_sha256'] != seal['input_pins'] or
        set(seal['review_documents_sha256']) != {str(HERE/'review.json'), str(HERE/'REVIEW.md')}):
        raise ValueError('Own exact-map independent review required')
    pre.verify_pins(seal['review_documents_sha256'])
    return seal, set(map(Path, seal['input_pins'])) | set(map(Path, seal['review_documents_sha256'])) | {HERE/'preparation_seal.json'}


def execute():
    seal, paths = gate(); out = HERE/'runs/replay'; pre.reject_existing(out)
    state = dict(pool=None, scene=None, cleanup_errors=[], NN_constructions=0, aliases_restored=False,
        loader_restored=False, encoding={}, trainer_unchanged=False, render_hooks_restored=False)
    failure, matched = None, None
    try:
        import isaacgym
        with learning.binding(paths, state, 'mean') as runner, hooks(runner, state, out):
            try:
                runner.run(argparse.Namespace(command='evaluate', checkpoint=str(learning.checkpoint(300)),
                    control='policy', reference=None, episodes=128, out=str(out)))
                matched = compare(out)
            finally:
                if state['pool'] is not None: state['pool'].close()
    except BaseException as error:
        failure = pre.error_info(error); raise
    finally:
        try:
            out.mkdir(parents=True, exist_ok=True)
            changed = [path for path, sha in seal['input_pins'].items() if not Path(path).is_file() or pre.sha(path) != sha]
            audit = state['scene'].diagnostics if state['scene'] is not None else {}
            ok = (failure is None and bool(matched) and state['trainer_unchanged'] and state['render_hooks_restored'] and
                state['aliases_restored'] and state['loader_restored'] and not changed and not state['cleanup_errors'] and
                state['encoding'] == dict(hand=0, fullbody=0) and audit.get('closed') is True and audit.get('environment_count') == 128)
            pre.write(out/'video_report.json', dict(schema=SCHEMA, completed=ok, failure=failure, comparison=matched,
                checkpoint=str(learning.checkpoint(300)), checkpoint_sha256=pre.sha(learning.checkpoint(300)),
                trainer_unchanged=state['trainer_unchanged'], training_updates=0, encoding_exit_codes=state['encoding'],
                cleanup_errors=state['cleanup_errors'], changed_inputs=changed, scene=audit,
                render_hooks_restored=state['render_hooks_restored'], aliases_restored=state['aliases_restored'], loader_restored=state['loader_restored']))
            if failure is None and not ok: raise RuntimeError('Native render audit failed')
        except BaseException as reporting_error:
            if failure is None:
                raise
            # 보고 자체가 실패해도 최초 실행·비교 오류를 유지한다.
            print('Video audit reporting failed while preserving primary error: '+repr(reporting_error), file=sys.stderr)



if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('command', choices=('prepare', 'gate', 'execute'))
    args = parser.parse_args()
    if args.command == 'prepare': prepare()
    elif args.command == 'gate': gate(); print('PASS')
    else: execute()
