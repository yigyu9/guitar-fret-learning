"""Read-only 128-first-attempt load observation around the strict native evaluator."""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from protocol import (HERE, REFERENCE, ENVIRONMENTS, CONTROLS, ENDPOINTS,
                      BYTE_LIMIT, REWARDS, NOTE, PHYSICS, CONTROL, Trace,
                      condition, failure_latch, protocol)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def owned(out, identity):
    return identity is not None and out.is_dir() and (out.stat().st_dev, out.stat().st_ino) == identity


def write(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def model_hash(policy):
    # Hash one tensor at a time; no saved model copy or extra forward call.
    value = hashlib.sha256()
    for key, tensor in sorted(policy.state_dict().items()):
        value.update(key.encode())
        value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return value.hexdigest()


def rng_hash():
    import pickle
    import random
    import numpy as np
    import torch
    state = (random.getstate(), np.random.get_state(), torch.get_rng_state().numpy(),
             [v.cpu().numpy() for v in torch.cuda.get_rng_state_all()] if torch.cuda.is_initialized() else [])
    return hashlib.sha256(pickle.dumps(state)).hexdigest()


def nearest_geometry(env, point_W, normal_W):
    """Original predicate on only the nearest sample; never replace env verdicts."""
    import torch
    from guitar_learning.gpu.geometry import apply, conjugate
    from guitar_learning.gpu.press_surface import project_press_strings
    from guitar_learning.gpu.fingertip_pad import pad_target_geometry
    point = apply(conjugate(env.guitar_q), point_W-env.guitar_body[:, :3])
    normal = apply(conjugate(env.guitar_q), normal_W)
    starts, ends = project_press_strings(env.starts, env.ends, env.press_plane)
    low = torch.minimum(env.frets[:, :-1, 1], env.frets[:, 1:, 1])
    high = torch.maximum(env.frets[:, :-1, 1], env.frets[:, 1:, 1])
    s = env.selected_index
    points = point[:, None, None].expand(-1, 4, 1, -1)
    return pad_target_geometry(points, normal[:, None, None].expand_as(points), torch.zeros_like(points),
        torch.ones((4, 1), dtype=torch.bool, device=point.device), starts, ends,
        low[:, env.fret[s:s+1]-1], high[:, env.fret[s:s+1]-1], env.string[s:s+1], env.finger[s:s+1],
        env.loaded[:, env.pad_indices], env.press_plane)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--control', choices=('policy', 'zero', 'reference'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError(str(out))
    assigned = condition(args.checkpoint, args.control)
    sealed = json.loads((HERE/'precommit.json').read_text())
    changed = [p for p, h in sealed['input_pins'].items() if not Path(p).is_file() or sha(p) != h]
    if changed:
        raise ValueError('Observation preparation inputs changed: '+str(changed[:5]))
    import isaacgym  # Original native extension import order, before NumPy/Torch.
    import numpy as np
    import torch
    from guitar_learning.gpu.geometry import apply
    from guitar_learning.core.control import LEFT_HAND_NAMES
    from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian
    from guitar_learning.tool.experiments.short_finger_learning import runner

    original_pool, original_evaluate = runner.ShortPool, runner._evaluate
    original_pins, original_trainer = runner._pins, runner.DecisionPPOTrainer
    physics, controls = Trace(PHYSICS, ENDPOINTS), Trace(CONTROL, CONTROLS)
    instances, trainers, episodes, identity = [], [], [], None
    audit, failure = {}, None

    class ObservedPool(original_pool):
        def __init__(self, settings, output):
            spec = settings['song']['short_learning']
            if (settings['num_envs'] != ENVIRONMENTS or spec['view']['duration_ticks'] != CONTROLS
                    or spec['mode'] != 'incremental' or spec['finger'] != 2
                    or 'ablation' in spec):
                raise ValueError('Exact corrected baseline middle4/128/218-control task required')
            super().__init__(settings, output)
            instances.append(self)
            self.first = torch.ones(ENVIRONMENTS, dtype=torch.bool, device=self.scene.device)
            self.failed = torch.zeros_like(self.first)
            self.qids = self.controller.active[self.spec['learned_action_indices']]
            self.handids = [self.scene.names.index(name) for name in LEFT_HAND_NAMES]
            env = self.environment
            self.distal_ids = [env._index['human/LH:'+name+'3']
                               for name in ('thumb', 'index', 'middle', 'ring', 'pinky')]
            self.distal = int(env.pad_indices[self.spec['finger']-1])
            native_substep = env.substep

            def observed_substep(snapshot):
                result = native_substep(snapshot)  # Original math, ledger and failure update first.
                selected = env.selected_index
                index = env.surface_sample[:, selected]
                local_index = index-(self.spec['finger']-1)*env.pad_local.shape[1]
                torch._assert_async(((local_index >= 0) & (local_index < env.pad_local.shape[1])).all(),
                                    'Nearest reward sample must belong to assigned distal')
                local = env.pad_local[self.spec['finger']-1, local_index]
                normal = env.pad_normals[self.spec['finger']-1, local_index]
                body = snapshot['body_state'][:, self.distal]
                offset = apply(body[:, 3:7], local-self.scene.com[self.distal])
                jacobian = point_jacobian(snapshot['jacobian'][:, self.distal-1], offset)
                measured = body[:, 7:10]+torch.cross(body[:, 10:13], offset, dim=-1)
                predicted = (jacobian@snapshot['qd'][..., None]).squeeze(-1)
                point_W = body[:, :3]+apply(body[:, 3:7], local)
                normal_W = apply(body[:, 3:7], normal)
                nearest = nearest_geometry(env, point_W, normal_W)
                physical = env.tick_failure.any(-1) | env.failure.any(-1)
                wrist = env.wrist_failure | env.wrist_severe_failure
                self.failed = failure_latch(self.first, self.failed, physical, wrist)
                row = dict(clock=env.clock, local_time_s=env._local_time(), source_time_s=env._score_time(),
                    first_attempt=self.first, tick_physical_failure=physical, tick_wrist_failure=wrist,
                    failure_latched=self.failed, candidate=env.candidate[:, selected], wrong=env.wrong[:, selected],
                    positive=env.contact_loaded_target[:, selected],
                    position_geometry_any=env.contact_geometry[:, selected], facing_geometry_any=env.contact_facing[:, selected],
                    nearest_position_geometry=nearest['position_geometry'][:, 0],
                    nearest_facing_geometry=nearest['facing_geometry'][:, 0],
                    nearest_sample_index=index, nearest_distance_m=env.surface_distance[:, selected],
                    nearest_height_m=env.surface_height[:, selected], nearest_normal_cos=env.surface_alignment[:, selected],
                    nearest_point_W=point_W, nearest_normal_W=normal_W,
                    actual_LH21=snapshot['q'][:, self.handids], target_LH21=snapshot['target'][:, self.handids],
                    qd_selected4=snapshot['qd'][:, self.qids], distal_force_W=snapshot['contact_force'][:, self.distal_ids],
                    guitar_pose=snapshot['body_state'][:, env.guitar_index], selected_distal_pose=body,
                    thumb3_pose=snapshot['body_state'][:, self.distal_ids[0]], point_jacobian_W=jacobian[:, :, self.qids],
                    point_velocity_W=measured, point_velocity_predicted_all_dof_W=predicted)
                physics.append({k: v.detach().cpu().numpy() for k, v in row.items()})
                return result

            env.substep = observed_substep

        def step(self, action):
            previous = torch.stack([self.environment.episode_reward_terms[k].clone() for k in REWARDS], -1)
            result = super().step(action)  # No substitutions; original teacher, action codec, four substeps.
            env, selected = self.environment, self.environment.selected_index
            cumulative = torch.stack([env.episode_reward_terms[k] for k in REWARDS], -1)
            row = dict(clock=env.clock, first_attempt=self.first, failure_latched=self.failed,
                policy_action_selected4=self.last_policy_action[:, self.spec['learned_action_indices']],
                executed_action_selected4=self.last_executed_action[:, self.spec['learned_action_indices']],
                reward=result[1], cost=result[2], reward_increment=cumulative-previous,
                reward_cumulative=cumulative, note_ledger=torch.stack([env.note[k][:, selected].double() for k in NOTE], -1))
            controls.append({k: v.detach().cpu().numpy() for k, v in row.items()})
            for episode in result[-1]:
                i = episode['env_id']
                if bool(self.first[i]):
                    episodes.append(dict(env_id=i, reason=episode['reason'], termination=episode['termination'],
                        reward_components=episode['reward_components'],
                        selected_note={k: env.note[k][i, selected].detach().cpu().tolist() for k in NOTE}))
                    self.first[i] = False
            return result

    def evaluate(pool, policy, spec, arguments, output):
        before_model, before_rng = model_hash(policy), rng_hash()
        before_updates = trainers[0].updates
        try:
            return original_evaluate(pool, policy, spec, arguments, output)
        finally:
            audit.update(model_sha256_before=before_model, model_sha256_after=model_hash(policy),
                RNG_sha256_before=before_rng, RNG_sha256_after=rng_hash(),
                trainer_updates_before=before_updates, trainer_updates_after=trainers[0].updates)

    def trainer(*values, **kwargs):
        value = original_trainer(*values, **kwargs)
        trainers.append(value)
        return value

    def pins(settings, output, extra=()):
        nonlocal identity
        stat = out.stat()  # Base runner has exclusively created this directory.
        identity = (stat.st_dev, stat.st_ino)
        if not owned(out, identity) or (out/'report.json').exists():
            raise RuntimeError('Unexpected output ownership before base pins')
        return original_pins(settings, output, [*extra, HERE/'precommit.json', *map(Path, sealed['input_pins'])])

    try:
        runner.ShortPool, runner._evaluate = ObservedPool, evaluate
        runner._pins, runner.DecisionPPOTrainer = pins, trainer
        runner.run(SimpleNamespace(command='evaluate', checkpoint=str(args.checkpoint.resolve()),
            out=str(out), control=args.control, reference=str(REFERENCE) if args.control == 'reference' else None,
            episodes=ENVIRONMENTS))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        runner.ShortPool, runner._evaluate = original_pool, original_evaluate
        runner._pins, runner.DecisionPPOTrainer = original_pins, original_trainer
        if owned(out, identity):
            pool = instances[0] if instances else None
            scene = pool.scene.diagnostics if pool else {}
            a, c = physics.values(), controls.values()
            first = a['first_attempt']
            residual = np.linalg.norm(a['point_velocity_predicted_all_dof_W']-a['point_velocity_W'], axis=-1)
            nofailure = first & ~a['failure_latched']
            velocity_audit = {name: dict(samples=int(mask.sum()), rms_m_s=float(np.sqrt(np.mean(residual[mask]**2))) if mask.any() else None,
                max_m_s=float(residual[mask].max()) if mask.any() else None)
                for name, mask in (('all_first_attempt', first), ('before_failure', nofailure))}
            base = json.loads((out/'report.json').read_text()) if (out/'report.json').is_file() else {}
            evaluation = json.loads((out/'evaluation.json').read_text()) if (out/'evaluation.json').is_file() else {}
            notes = sorted(episodes, key=lambda row: row['env_id'])
            note_bytes = json.dumps(notes, ensure_ascii=False, allow_nan=False).encode()
            checks = dict(strict_base_completed=base.get('completed') is True,
                all_first_attempts=len(notes) == ENVIRONMENTS and {v['env_id'] for v in notes} == set(range(ENVIRONMENTS)),
                original_quotas=evaluation.get('assigned_quotas') == [1]*ENVIRONMENTS,
                four_substeps=physics.count == controls.count*4,
                clocks=bool(physics.count) and all(np.array_equal(a['clock'][:, i][first[:, i]],
                    np.arange(1, first[:, i].sum()+1)) for i in range(ENVIRONMENTS)),
                model_unchanged=bool(audit) and audit['model_sha256_before'] == audit['model_sha256_after'],
                RNG_unchanged=bool(audit) and audit['RNG_sha256_before'] == audit['RNG_sha256_after'],
                trainer_updates_unchanged=bool(audit) and audit['trainer_updates_before'] == audit['trainer_updates_after'] == assigned['updates'],
                pins_unchanged=all(Path(p).is_file() and sha(p) == h for p, h in sealed['input_pins'].items()),
                bounded=physics.count <= ENDPOINTS and controls.count <= CONTROLS
                    and physics.nbytes+controls.nbytes+len(note_bytes) < BYTE_LIMIT,
                scene_closed=scene.get('closed') is True and scene.get('environment_count') == ENVIRONMENTS,
                native_gpu=scene.get('physx_use_gpu') is True and scene.get('use_gpu_pipeline') is True)
            # Exclusive new artifacts only; original report/evaluation/trace remain intact.
            for name in ('physics240.npz', 'control60.npz', 'first_attempt_notes.json', 'load_probe_report.json'):
                if (out/name).exists():
                    raise FileExistsError(str(out/name))
            with (out/'physics240.npz').open('xb') as stream:
                np.savez_compressed(stream, **a)
            with (out/'control60.npz').open('xb') as stream:
                np.savez_compressed(stream, **c)
            write(out/'first_attempt_notes.json', notes)
            write(out/'load_probe_report.json', dict(protocol=protocol(), condition=assigned,
                completed=failure is None and all(checks.values()), failure=failure, checks=checks,
                evaluation_audit=audit, velocity_audit=velocity_audit, scene=scene,
                selected_output_uncompressed_bytes=physics.nbytes+controls.nbytes+len(note_bytes),
                base_report_sha256=sha(out/'report.json') if (out/'report.json').is_file() else None,
                metadata=dict(hand_joint_names=list(LEFT_HAND_NAMES), selected_joint_names=pool.spec['learned_action_names'] if pool else None,
                    distal_body_names=[pool.scene.body_names[i] for i in pool.distal_ids] if pool else None,
                    selected_body_COM_local_m=pool.scene.com[pool.distal].cpu().tolist() if pool else None,
                    press_plane_G=pool.environment.press_plane.cpu().tolist() if pool else None,
                    thumb_rear_plane_G=pool.environment.thumb_support_plane.cpu().tolist() if pool else None),
                hook='post original environment.substep; original ShortPool.step unchanged; no policy/critic extra forwards or random draws'))
            if failure is None and not all(checks.values()):
                raise RuntimeError('Read-only load observation audit failed')


if __name__ == '__main__':
    main()
