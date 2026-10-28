"""Original strict evaluator; four precontrol native-J snapshots, no intervention."""
import hashlib
import json
import pickle
import random
from pathlib import Path
from common import HERE, CLOCKS, CHECKPOINT, LIMIT, protocol, sha, write, owned, reject_existing


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
    requested_out = Path(args.out).absolute()
    reject_existing(requested_out)  # Before native import or resolution of a dangling output symlink.
    out = requested_out.resolve()
    from common import OLD
    if (args.command != 'evaluate' or Path(args.checkpoint).resolve() != CHECKPOINT or args.control != 'reference'
            or args.episodes != 4 or Path(args.reference).resolve() != OLD/'reference_index_row1.json'):
        raise ValueError('Exactly original index initial/reference/four attempts required')
    seal = json.loads((HERE/'preparation_seal.json').read_text())
    if any(not Path(p).is_file() or sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation inputs changed')
    import isaacgym  # Native extension must precede NumPy/Torch imports.
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    original_pool, original_eval = runner.ShortPool, runner._evaluate
    original_pins, original_trainer = runner._pins, runner.DecisionPPOTrainer
    rows, instances, trainers = [], [], []
    identity, failure = None, None
    audit = {}

    class ObservedPool(original_pool):
        def __init__(self, settings, output):
            if settings['num_envs'] != 4 or settings['song']['short_learning']['finger'] != 1:
                raise ValueError('Original index/four environment task required')
            super().__init__(settings, output)
            instances.append(self)
            self.first = torch.ones(4, dtype=torch.bool, device=self.scene.device)
            self.control_calls, self.four_substeps = 0, True

        def step(self, actions):
            snapshot = self.scene.snapshot()
            before = self.environment.clock.clone()
            clock = int(before[0])
            if clock in CLOCKS and bool(self.first[0]) and clock not in [int(r['clock'][0]) for r in rows]:
                # All fields copied before original feedback/step; never refresh or mutate native tensors.
                row = {k: snapshot[k].detach().clone().cpu().numpy() for k in
                    ('q', 'qd', 'target', 'body_state', 'jacobian', 'physics_step', 'reset_body_snapshot')}
                row.update(clock=before.cpu().numpy(), first_attempt=self.first.cpu().numpy().copy(),
                    physical_failure=(self.environment.tick_failure.any(-1) | self.environment.failure.any(-1)).cpu().numpy(),
                    wrist_failure=(self.environment.wrist_failure | self.environment.wrist_severe_failure).cpu().numpy(),
                    input_action=actions.detach().clone().cpu().numpy())
                rows.append(row)
            result = super().step(actions)  # Exactly one original call, unchanged object and action.
            self.control_calls += 1
            self.four_substeps &= bool(torch.equal(self.environment.clock, before+4))
            for episode in result[-1]:
                self.first[episode['env_id']] = False
            return result

    def trainer(*args, **kwargs):
        value = original_trainer(*args, **kwargs); trainers.append(value); return value

    def evaluate(pool, policy, spec, arguments, output):
        audit.update(model_before=model_hash(policy), RNG_before=rng_hash(), updates_before=trainers[0].updates)
        try:
            return original_eval(pool, policy, spec, arguments, output)
        finally:
            audit.update(model_after=model_hash(policy), RNG_after=rng_hash(), updates_after=trainers[0].updates)

    def pins(settings, output, extra=()):
        nonlocal identity
        stat = out.stat(); identity = (stat.st_dev, stat.st_ino)
        if not owned(out, identity) or (out/'report.json').exists():
            raise RuntimeError('Output ownership differs')
        return original_pins(settings, output, [*extra, HERE/'preparation_seal.json', *map(Path, seal['input_pins'])])

    try:
        runner.ShortPool, runner._evaluate = ObservedPool, evaluate
        runner._pins, runner.DecisionPPOTrainer = pins, trainer
        runner.run(args)  # Original source validation + complete trainer.load; no bypass.
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        runner.ShortPool, runner._evaluate = original_pool, original_eval
        runner._pins, runner.DecisionPPOTrainer = original_pins, original_trainer
        if owned(out, identity):
            pool = instances[0] if instances else None
            arrays = {k: np.stack([row[k] for row in rows]) for k in rows[0]} if rows else {}
            if pool:
                arrays['body_COM_local_m'] = pool.scene.com.detach().cpu().numpy().copy()
            nbytes = sum(a.nbytes for a in arrays.values())
            base = json.loads((out/'report.json').read_text()) if (out/'report.json').is_file() else {}
            evaluation = json.loads((out/'evaluation.json').read_text()) if (out/'evaluation.json').is_file() else {}
            scene = pool.scene.diagnostics if pool else {}
            checks = dict(base_complete=base.get('completed') is True and base.get('closed') is True,
                four_captures=len(rows) == 4,
                clocks=len(rows) == 4 and np.array_equal(arrays['clock'], np.array(CLOCKS)[:, None]*np.ones((4, 4), dtype=int)),
                scene_clock_agrees=bool(rows) and np.array_equal(arrays['clock'], arrays['physics_step']),
                all_first=bool(rows) and bool(arrays['first_attempt'].all()),
                no_stale_J=bool(rows) and not bool(arrays['reset_body_snapshot'].any()),
                native_J_shape=bool(rows) and arrays['jacobian'].shape == (4, 4, 65, 6, 105),
                finite=bool(rows) and all(np.isfinite(v).all() for v in arrays.values()),
                bounded=nbytes <= LIMIT and bool(pool) and pool.control_calls <= 221,
                four_substeps=bool(pool) and pool.four_substeps,
                original_four_quotas=evaluation.get('assigned_quotas') == [1]*4 and len(evaluation.get('episodes', [])) == 4,
                model_unchanged=bool(audit) and audit['model_before'] == audit['model_after'],
                RNG_unchanged=bool(audit) and audit['RNG_before'] == audit['RNG_after'],
                updates_zero=bool(audit) and audit['updates_before'] == audit['updates_after'] == 0,
                pins_unchanged=all(Path(p).is_file() and sha(p) == h for p, h in seal['input_pins'].items()),
                scene_closed=scene.get('closed') is True,
                native_GPU=scene.get('physx_use_gpu') is True and scene.get('use_gpu_pipeline') is True)
            with (out/'precontrol_native.npz').open('xb') as stream:
                np.savez_compressed(stream, **arrays)
            write(out/'coordinate_audit_report.json', dict(protocol=protocol(), completed=failure is None and all(checks.values()),
                failure=failure, checks=checks, audit=audit, uncompressed_bytes=nbytes, scene=scene,
                joint_names=pool.scene.names if pool else None, body_names=pool.scene.body_names if pool else None,
                human_bodies=pool.scene.human_bodies if pool else None,
                base_report_sha256=sha(out/'report.json') if (out/'report.json').is_file() else None))
            if failure is None and not all(checks.values()):
                raise RuntimeError('Coordinate observation audit failed; artifacts preserved')


if __name__ == '__main__':
    main()
