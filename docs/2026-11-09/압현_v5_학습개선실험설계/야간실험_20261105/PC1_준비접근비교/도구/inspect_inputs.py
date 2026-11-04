"""Read-only, single-thread CPU checks for the sealed PC1 B/P runtime."""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import sys

PROFILE_DIFFS = {
    'compact_press.improvement_profile', 'compact_press_v5.profile',
    'compact_press_v5.preparation.enabled', 'compact_press_v5.preparation.factor',
}
BUDGET = 16777216
QUARTER = 4194304
PER_UPDATE = 32768


def require(condition, message):
    if not condition:
        raise ValueError(message)


def differences(left, right, prefix=''):
    if isinstance(left, dict) and isinstance(right, dict):
        result = {}
        for key in sorted(set(left) | set(right)):
            path = prefix + '.' + key if prefix else key
            if key not in left or key not in right:
                result[path] = [left.get(key), right.get(key)]
            else:
                result.update(differences(left[key], right[key], path))
        return result
    return {} if type(left) is type(right) and left == right else {prefix: [left, right]}


def check_profile_diff(left, right):
    actual = differences(left, right)
    require(set(actual) == PROFILE_DIFFS, 'B/P settings differ outside the exact profile allowlist: ' + str(actual))
    return actual


def check_boundary(updates, committed):
    require(type(updates) is int and 0 <= updates <= 512, 'invalid global optimizer updates')
    require(type(committed) is int and committed == updates * PER_UPDATE,
            'committed transitions must equal updates * 32768')
    return dict(resume_boundary=updates in (0, 128, 256, 384),
                evaluation_boundary=updates in (0, 128, 256, 384, 512))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_modules(runtime):
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(runtime))
    import torch
    torch.set_num_threads(1)
    from guitar_learning.tool.experiments import compact_press_v5 as native, press_sequence as sequence
    from guitar_learning.portability import portable
    require(Path(native.__file__).resolve().is_relative_to(runtime) if sys.version_info >= (3, 9)
            else str(Path(native.__file__).resolve()).startswith(str(runtime) + os.sep),
            'inspection imported code outside requested runtime')
    require('isaacgym' not in sys.modules, 'CPU inspection must not import isaacgym')
    return torch, native, sequence, portable


def actual_settings(native, portable):
    settings = {profile: native.build_settings(song='press_sequence_c1_v1', size='large',
        num_envs=1024, horizon=32, updates=512, checkpoint_every=128, seed=7,
        include_pelvis=False, initial_support_std=.15, initial_finger_std=.35,
        improvement_profile=profile) for profile in ('corrected', 'preparation')}
    for value in settings.values():
        native.validate_settings(value)
        require(value['finger_skill']['planned_transitions'] == BUDGET and
                value['finger_skill']['full_song_after'] == QUARTER, 'original exposure budget changed')
        require(value['ppo']['epochs'] == 2 and value['ppo']['minibatch_size'] == 4096 and
                value['ppo']['actor_lr'] == .00003 and value['ppo']['value_lr'] == .0003,
                'PPO settings changed')
    portable_settings = {key: portable(value) for key, value in settings.items()}
    return portable_settings, check_profile_diff(portable_settings['corrected'], portable_settings['preparation'])


def tensor_digest(model, torch):
    require(isinstance(model, dict) and model, 'nonempty model state_dict required')
    digest = hashlib.sha256()
    for key in sorted(model):
        value = model[key]
        require(isinstance(value, torch.Tensor) and torch.isfinite(value).all().item(),
                'nonfinite or invalid model tensor: ' + key)
        value = value.detach().cpu().contiguous()
        header = json.dumps([key, str(value.dtype), list(value.shape)], separators=(',', ':')).encode('utf-8')
        raw = value.numpy().tobytes(order='C')
        digest.update(len(header).to_bytes(8, 'big'))
        digest.update(header)
        digest.update(len(raw).to_bytes(8, 'big'))
        digest.update(raw)
    return digest.hexdigest()


def inspect_checkpoint(args, torch, native, sequence, portable, expected):
    before = sha256(args.checkpoint)
    require(before == args.sha, 'checkpoint SHA differs from manifest')
    # The official reader validates inputs/settings/architecture/clock before any local construction.
    settings = native.read_checkpoint(args.checkpoint)
    selection = argparse.Namespace(command='evaluate', checkpoint=args.checkpoint, target='C1', song=None)
    require(sequence.checked_selection(selection) == 'C1', 'checkpoint target is not C1')
    sequence.verify_checkpoint_clock(args.checkpoint, sequence.checked_target('C1'))
    saved = portable(settings)
    allowed = {'updates', 'max_wall_seconds'}
    diff = differences(expected[args.profile], saved)
    require(set(diff) <= allowed, 'checkpoint settings mismatch: ' + str(diff))
    require(type(settings['updates']) is int and 1 <= settings['updates'] <= 512, 'invalid attempt update budget')
    if settings.get('max_wall_seconds') is not None:
        wall = settings['max_wall_seconds']
        require(type(wall) in (int, float) and math.isfinite(wall) and wall > 0, 'invalid wall budget')
    payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    metadata = payload['metadata']
    curriculum = metadata['curriculum']
    updates = payload['updates']
    boundaries = check_boundary(updates, curriculum['committed_transitions'])
    from guitar_learning.training.finger_skill_runner import ExposureSchedule
    schedule = ExposureSchedule(BUDGET, QUARTER)
    schedule.load_state_dict(curriculum)
    require(metadata.get('original_phase_budget') == BUDGET, 'original planned budget changed')
    exposure = metadata.get('exposure_transitions')
    require(isinstance(exposure, dict) and set(exposure) == {'phrases', 'full_song'} and
            all(type(value) is int and value >= 0 for value in exposure.values()) and
            sum(exposure.values()) == curriculum['committed_transitions'], 'invalid committed exposure counters')
    from guitar_learning.song.finger_phrases import build_phrase_catalog, BalancedPhraseSampler
    from guitar_learning.tool.prepare_press_targets import source_clock_task
    task = source_clock_task(settings['song_training']['bundle'],
                             pre_roll_s=settings['song']['pre_roll_s'], tail_s=settings['song']['tail_s'])
    sampler = BalancedPhraseSampler(build_phrase_catalog(task, preparation_s=3., tail_s=settings['song']['tail_s']))
    sampler.load_state_dict(metadata['sampler'])
    import random
    import numpy as np
    random.Random().setstate(payload['python_rng'])
    np.random.RandomState().set_state(payload['numpy_rng'])
    torch.Generator(device='cpu').set_state(payload['torch_rng'])
    cuda_rng = payload['cuda_rng']
    require(cuda_rng is None or (isinstance(cuda_rng, list) and all(
        isinstance(state, torch.Tensor) and state.dtype == torch.uint8 and state.ndim == 1
        for state in cuda_rng)), 'invalid saved CUDA RNG state')
    from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
    from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
    spec = settings['compact_press']
    policy = CompactPressV5Policy(spec['state_dim'], event_dim=26, size=settings['size'],
        contract=payload['identity']['architecture']['contract'],
        initial_support_std=spec['initial_support_std'], initial_finger_std=spec['initial_finger_std'])
    trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
    require(payload['identity'] == trainer._identity(), 'strict PPO identity/config mismatch')
    tensor_sha = tensor_digest(payload['model'], torch)
    policy.load_state_dict(payload['model'], strict=True)
    for name, optimizer in (('actor_optimizer', trainer.actor_optimizer), ('value_optimizer', trainer.value_optimizer)):
        state = payload[name]
        require(isinstance(state, dict) and (updates == 0 or bool(state.get('state'))), 'missing Adam state')
        optimizer.load_state_dict(state)
        for parameter, values in optimizer.state.items():
            require(set(values) == {'step', 'exp_avg', 'exp_avg_sq'}, 'invalid Adam state keys')
            for key in ('exp_avg', 'exp_avg_sq'):
                require(values[key].shape == parameter.shape and torch.isfinite(values[key]).all().item(),
                        'invalid Adam moment: ' + key)
            require(float(values['step']) >= 0 and math.isfinite(float(values['step'])), 'invalid Adam step')
    require(payload.get('cost_weight') == 1., 'fixed PPO cost weight changed')
    std = payload['model']['log_std'].detach().cpu().clamp(-5, 2).exp()
    require(list(std.shape) == [33], 'expected 17 support and 16 finger std values')
    if updates == 0:
        require(torch.allclose(std[:17], torch.full((17,), .15)) and
                torch.allclose(std[17:], torch.full((16,), .35)), 'initial role std differs from 0.15/0.35')
    roles = {name: dict(count=len(values), values=values.tolist(), mean=float(values.mean()),
                       min=float(values.min()), max=float(values.max()))
             for name, values in (('support17', std[:17]), ('finger16', std[17:]))}
    require(before == sha256(args.checkpoint), 'checkpoint changed while inspecting')
    require('isaacgym' not in sys.modules, 'CPU inspection imported isaacgym')
    return dict(completed=True, sha256=before, updates=updates,
        committed_transitions=curriculum['committed_transitions'], curriculum=curriculum,
        exposure_transitions=exposure, profile=args.profile, tensor_sha256=tensor_sha,
        role_std=roles, settings=saved, execution_settings_differences=diff, **boundaries)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--settings-check', action='store_true')
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--sha')
    parser.add_argument('--profile', choices=('corrected', 'preparation'))
    args = parser.parse_args(argv)
    try:
        require(args.settings_check or args.checkpoint is not None, 'choose --settings-check or --checkpoint')
        require(args.checkpoint is None or (args.sha and args.profile), 'checkpoint requires --sha and --profile')
        with contextlib.redirect_stdout(sys.stderr):
            torch, native, sequence, portable = runtime_modules(args.runtime.resolve())
            audit = sequence.checked_target('C1')
            expected, diff = actual_settings(native, portable)
            result = (inspect_checkpoint(args, torch, native, sequence, portable, expected)
                      if args.checkpoint else dict(completed=True, input_audit=audit,
                          settings=expected, settings_differences=diff, invariants=dict(
                              planned_transitions=BUDGET, full_song_after=QUARTER,
                              transitions_per_update=PER_UPDATE, initial_tensor_digest='pending native initial.pt')))
        print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
        return 0
    except Exception as error:
        print(json.dumps(dict(completed=False, error=str(error), error_type=type(error).__name__), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
