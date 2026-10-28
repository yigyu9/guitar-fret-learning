"""Original current strict runner; pin extras and evaluation identity observation only."""
import hashlib
import json
import pickle
import random
from pathlib import Path
from common import HERE, OLD, sha, write, reject_existing, owned


def model_hash(policy):
    value = hashlib.sha256()
    for key, tensor in sorted(policy.state_dict().items()):
        value.update(key.encode()); value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return value.hexdigest()


def rng_hash():
    import numpy as np
    import torch
    state = (random.getstate(), np.random.get_state(), torch.get_rng_state().numpy(),
        [v.cpu().numpy() for v in torch.cuda.get_rng_state_all()] if torch.cuda.is_initialized() else [])
    return hashlib.sha256(pickle.dumps(state)).hexdigest()


def main():
    from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
    args = parser().parse_args()
    requested = Path(args.out).absolute()
    reject_existing(requested)  # Before native import or dangling symlink resolution.
    out = requested.resolve()
    if args.command == 'evaluate' and (Path(args.checkpoint).resolve() != HERE/'runs/index_initial/initial.pt'
            or args.episodes != 4 or args.control not in ('reference', 'zero', 'random')
            or (args.control == 'reference' and Path(args.reference).resolve() != OLD/'reference_index_row1.json')):
        raise ValueError('Only own fresh current initial checkpoint and predeclared4 attempts')
    if args.command == 'train' and (Path(args.teacher).resolve() != OLD/'teacher_index_row1.json'
            or args.mode != 'incremental' or args.initial_std != .1711710544767014 or args.size != 'large'
            or args.num_envs != 4 or args.horizon != 32 or args.updates != 1 or args.save_every != 50
            or args.seed != 7 or args.song != '05_BN2-131-B_solo'):
        raise ValueError('Only predeclared original index bootstrap1update required')
    seal = json.loads((HERE/'preparation_seal.json').read_text())
    if any(not Path(p).is_file() or sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation changed')
    import isaacgym  # Before NumPy/Torch, as required by original native entrypoint.
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.wrist import WRIST_CONTROL
    originals = runner._pins, runner._evaluate, runner.DecisionPPOTrainer
    trainers, audit = [], {}
    identity, failure = None, None

    def pins(settings, output, extra=()):
        nonlocal identity
        stat = out.stat(); identity = (stat.st_dev, stat.st_ino)
        if not owned(out, identity) or (out/'report.json').exists():
            raise RuntimeError('Output ownership differs')
        if settings['song']['short_learning']['wrist_control'] != seal['wrist_control']:
            raise ValueError('Exact sealed current wrist contract required')
        return originals[0](settings, output, [*extra, HERE/'preparation_seal.json', *map(Path, seal['input_pins'])])

    def trainer(*values, **kwargs):
        result = originals[2](*values, **kwargs); trainers.append(result); return result

    def evaluate(pool, policy, spec, arguments, output):
        audit.update(model_before=model_hash(policy), RNG_before=rng_hash(), updates_before=trainers[0].updates)
        try:
            return originals[1](pool, policy, spec, arguments, output)
        finally:
            audit.update(model_after=model_hash(policy), RNG_after=rng_hash(), updates_after=trainers[0].updates)

    try:
        runner._pins, runner._evaluate, runner.DecisionPPOTrainer = pins, evaluate, trainer
        runner.run(args)  # Original full source/config/model/optimizer/RNG strict load.
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        runner._pins, runner._evaluate, runner.DecisionPPOTrainer = originals
        if owned(out, identity):
            base = json.loads((out/'report.json').read_text()) if (out/'report.json').is_file() else {}
            scene = json.loads((out/'gpu_scene_final.json').read_text()) if (out/'gpu_scene_final.json').is_file() else {}
            after = json.loads((out/'inputs_after.json').read_text()) if (out/'inputs_after.json').is_file() else {}
            checks = dict(base_complete=base.get('completed') is True and base.get('closed') is True,
                source_verified=after.get('verified') is True,
                sealed_inputs_unchanged=all(Path(p).is_file() and sha(p) == h for p, h in seal['input_pins'].items()),
                exact_wrist_control=WRIST_CONTROL == seal['wrist_control'], scene_closed=scene.get('closed') is True,
                native_GPU=scene.get('physx_use_gpu') is True and scene.get('use_gpu_pipeline') is True,
                native_four_environments=scene.get('environment_count') == 4,
                actual_fixed_guitar=scene.get('diagnostic_guitar_mode') == 'fixed',
                original_physics_budget=scene.get('physics_steps', -1) == 128 if args.command == 'train'
                    else 0 < scene.get('physics_steps', -1) <= 884 and scene['physics_steps'] % 4 == 0)
            if args.command == 'evaluate':
                evaluation = json.loads((out/'evaluation.json').read_text()) if (out/'evaluation.json').is_file() else {}
                episodes = evaluation.get('episodes', [])
                audit_ready = all(key in audit for key in ('model_before','model_after','RNG_before',
                    'RNG_after','updates_before','updates_after'))
                audit['RNG_scope'] = ('Original random-policy sampling consumes RNG; wrapper draws none' if args.control == 'random'
                    else 'Deterministic policy/reference/zero must preserve RNG state')
                checks.update(evaluation_audit_captured=audit_ready, model_unchanged=audit_ready and audit['model_before'] == audit['model_after'],
                    deterministic_RNG_unchanged=audit_ready and (args.control == 'random' or audit['RNG_before'] == audit['RNG_after']),
                    updates_zero=audit_ready and audit['updates_before'] == audit['updates_after'] == 0,
                    all_four_attempts=evaluation.get('assigned_quotas') == [1]*4 and len(episodes) == 4
                        and sorted(e['env_id'] for e in episodes) == list(range(4)))
            else:
                initial = torch.load(out/'initial.pt', map_location='cpu', weights_only=False) if (out/'initial.pt').is_file() else {}
                final = torch.load(out/'final.pt', map_location='cpu', weights_only=False) if (out/'final.pt').is_file() else {}
                checks.update(fresh_initial_updates_zero=initial.get('updates') == 0, only_one_bootstrap_update=final.get('updates') == 1)
            write(out/'precheck_audit.json', dict(completed=failure is None and all(checks.values()), failure=failure,
                checks=checks, audit=audit, sampling_scope='original env0 first attempt60Hz trace only; no all-env240Hz force claim',
                base_report_sha256=sha(out/'report.json') if (out/'report.json').is_file() else None))
            if failure is None and not all(checks.values()):
                raise RuntimeError('Precheck audit failed; original outputs preserved')


if __name__ == '__main__':
    main()
