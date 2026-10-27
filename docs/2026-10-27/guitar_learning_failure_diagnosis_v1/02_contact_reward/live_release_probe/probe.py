"""Docs-only finite reference diagnostic; run-gpu is an explicit separate action."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SHORT = ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning'
CHECKPOINT = SHORT/'pilot_incremental_seed7_v2_retry2/train/initial.pt'
REFERENCE = SHORT/'reference_middle_row8_v2.json'
RELEASE_S = (None, 2.90, 2.92, 2.94, 2.96, 2.98, 3.00, 3.02,
             3.04, 3.06, 3.08, 3.12, 3.14, 3.16, 3.18, 3.22)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def protocol():
    return dict(schema='native_live_release_probe.v1', environments=128, conditions=16,
        repetitions=8, assignment='env_id % 16; first attempt only; no outcome selection',
        release_s=list(RELEASE_S), trigger='next control endpoint >= release_s (integer 240Hz clock)',
        release_target='selected middle four only -> original prepared035 reference; trajectory_actions max_speed=4',
        ramp_s=2., checkpoint=str(CHECKPOINT), reference=str(REFERENCE),
        policy_performance=False, training_updates=0,
        physics_hz=240, control_hz=60, substeps_per_control=4,
        stable_release=dict(minimum_span_s=.05, span='(last_clock-first_clock)/240; at least13 consecutive endpoints',
            eligible='first attempt; release requested; actual consecutive-clock post-request candidate loss previously observed; candidate and original position geometry absent; assigned distal resultant below original0.01N gate',
            interruption='ineligible sample or clock gap breaks span; episode/reset clock clears prior loss'),
        limits='unchanged native PD/ranges/predicates/rewards/termination; fixed guitar teacher-supported task',
        assignments=[dict(env_id=i, condition=i % 16, repetition=i//16,
                          release_s=RELEASE_S[i % 16]) for i in range(128)])


def release_mask(clock, *, torch):
    # ceil(t*60) is the first control endpoint meeting t; integer math avoids
    # a float32 rounding decision at exact values such as 2.90 and 3.00.
    import math
    thresholds = [10**9 if t is None else 4*math.ceil(t*60-1e-10) for t in RELEASE_S]
    threshold = torch.tensor(thresholds, device=clock.device)[torch.arange(128, device=clock.device) % 16]
    return clock+4 >= threshold


def replace_selected(action, retract, mask, selected, *, torch):
    result = action.clone()
    result[:, selected] = torch.where(mask[:, None], retract[:, selected], action[:, selected])
    return result


def stable_release_span(clock, first, requested, candidate, geometry, force_n, threshold_n):
    """Conservative observed span; no inferred coverage between missing samples."""
    previous_clock, previous_candidate, loss_seen = None, False, False
    start, count, best_start, best_end, best_count = None, 0, None, None, 0
    for at, live, release, contact, position, force in zip(clock, first, requested, candidate, geometry, force_n):
        at = int(at)
        consecutive = previous_clock is not None and at == previous_clock+1
        if not live or (previous_clock is not None and at <= previous_clock):
            loss_seen = False
            previous_candidate = False
        if live and release and consecutive and previous_candidate and not contact:
            loss_seen = True
        eligible = live and release and loss_seen and not contact and not position and force < threshold_n
        if eligible:
            if not consecutive or start is None:
                start, count = at, 1
            else:
                count += 1
            if count > best_count:
                best_start, best_end, best_count = start, at, count
        else:
            start, count = None, 0
        previous_clock = at if live else None
        previous_candidate = bool(contact) if live else False
    span_ticks = best_end-best_start if best_count else 0
    return dict(stable_release_50ms=span_ticks >= 12,
        max_contiguous_span_s=span_ticks/240., max_contiguous_samples=best_count,
        start_clock=best_start, end_clock=best_end)


def precommit(out):
    # CPU only. No Isaac Gym, scene, policy allocation or GPU call.
    import torch
    from guitar_learning.training.finger_skill_runner import _validate_pins
    from guitar_learning.tool.experiments.short_finger_learning.spec import SCHEMA, read_teacher, read_reference
    payload = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    metadata = payload['metadata']
    _validate_pins(metadata)
    settings = metadata['settings']
    spec = settings['song']['short_learning']
    if (metadata['schema'] != SCHEMA or settings['num_envs'] != 128 or
            payload['updates'] != 0 or spec['mode'] != 'incremental' or spec['finger'] != 2 or
            spec['learned_action_indices'] != [21, 22, 23, 24]):
        raise ValueError('Exact initial incremental middle4/128 checkpoint required')
    if read_teacher(spec['teacher']['input_path']) != spec['teacher']:
        raise ValueError('Strict teacher identity changed')
    read_reference(REFERENCE, spec)
    paths = [CHECKPOINT, REFERENCE, Path(__file__).resolve(),
             Path(spec['teacher']['input_path']), *map(Path, metadata['input_pins'])]
    value = dict(protocol=protocol(), input_pins={str(p): sha(p) for p in paths},
                 source_target_view=spec['view'], checkpoint_metadata_validated=True,
                 status='predeclared; CPU identity only; GPU evidence not collected')
    if Path(out).exists():
        raise FileExistsError(out)
    write(out, value)
    return value


def run_gpu(precommit_path, out):
    # Required Isaac import order; CPU tests/precommit run in separate processes.
    import isaacgym  # noqa: F401
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    sealed = json.loads(Path(precommit_path).read_text())
    if sealed['protocol'] != protocol():
        raise ValueError('Predeclared protocol differs')
    changed = [p for p, digest in sealed['input_pins'].items() if not Path(p).is_file() or sha(p) != digest]
    if changed:
        raise ValueError('Precommit inputs changed: '+str(changed))
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    original_pool, original_evaluate, original_pins = runner.ShortPool, runner._evaluate, runner._pins
    original_trainer = runner.DecisionPPOTrainer
    samples, control_samples, episodes, instances, trainers = [], [], [], [], []
    checks = dict(model_unchanged=False, trainer_updates_unchanged=False)
    failure = None

    class ProbePool(original_pool):
        def __init__(self, settings, output):
            super().__init__(settings, output)
            instances.append(self)
            self.first = torch.ones(128, dtype=torch.bool, device=self.scene.device)
            self.release_active = torch.zeros_like(self.first)
            self.learned = self.spec['learned_action_indices']
            self.q_indices = self.controller.active[self.learned]
            self.initial_target4 = self.controller.target[:, self.q_indices].detach().cpu().numpy().copy()
            env = self.environment
            self.distal = int(env.pad_indices[self.spec['finger']-1])
            original_substep = env.substep

            def observed_substep(snapshot):
                result = original_substep(snapshot)  # unchanged actual integration/ledger first
                s = env.selected_index
                row = dict(first_attempt=self.first, release_requested=self.release_active, clock=env.clock,
                    source_time_s=env._score_time(), local_time_s=env._local_time(),
                    candidate=env.candidate[:, s], wrong=env.wrong[:, s],
                    positive=env.contact_loaded_target[:, s],
                    surface_distance_m=env.surface_distance[:, s],
                    surface_height_m=env.surface_height[:, s], alignment=env.surface_alignment[:, s],
                    geometry=env.contact_geometry[:, s], facing=env.contact_facing[:, s],
                    distal_force_n=snapshot['contact_force'][:, self.distal],
                    distal_pose=snapshot['body_state'][:, self.distal],
                    guitar_pose=snapshot['body_state'][:, env.guitar_index],
                    q4=snapshot['q'][:, self.q_indices],
                    target4=self.controller.target[:, self.q_indices])
                for key in ('contact_progress', 'clean', 'clean_streak', 'best_clean_streak',
                            'left', 'released', 'release_s', 'contact_streak', 'best_contact_streak'):
                    row['note_'+key] = env.note[key][:, s]
                for key in ('wrong_source_flags', 'wrong_source_fret_min', 'wrong_source_fret_max'):
                    if hasattr(env, key):
                        row[key] = getattr(env, key)[:, s]
                samples.append({key: value.detach().cpu().numpy().copy() for key, value in row.items()})
                return result

            env.substep = observed_substep

        def step(self, action):
            mask = release_mask(self.environment.clock, torch=torch)
            self.release_active = mask
            desired = self.teacher_reference.expand(128, -1)
            retract = trajectory_actions(desired, self.controller.target[:, self.controller.active],
                self.teacher_reference, self.controller.action_low, self.controller.action_high,
                self.incremental_mask, max_speed=4.)
            action = replace_selected(action, retract, mask, self.learned, torch=torch)
            previous_terms = {key: value.clone() for key, value in self.environment.episode_reward_terms.items()}
            result = super().step(action)  # original teacher wrists, other B, four substeps
            env = self.environment
            row = dict(first_attempt=self.first, clock=env.clock, release_requested=mask,
                requested4=self.last_policy_action[:, self.learned],
                executed4=self.last_executed_action[:, self.learned],
                reward=result[1], cost=result[2])
            row.update({'reward_cumulative_'+key: value for key, value in env.episode_reward_terms.items()})
            row.update({'reward_increment_'+key: value-previous_terms[key]
                        for key, value in env.episode_reward_terms.items()})
            control_samples.append({key: value.detach().cpu().numpy().copy() for key, value in row.items()})
            for episode in result[-1]:
                i = episode['env_id']
                if bool(self.first[i]):
                    episode['live_release_probe'] = protocol()['assignments'][i]
                    s = env.selected_index
                    # Original serialized ledger omits these two release fields.
                    episode['live_selected_note'] = {key: value[i, s].detach().cpu().tolist()
                                                    for key, value in env.note.items()}
                    episodes.append(episode)
                    self.first[i] = False
            return result

    def evaluate(pool, policy, spec, args, output):
        before = {key: value.detach().clone() for key, value in policy.state_dict().items()}
        updates_before = trainers[0].updates
        try:
            return original_evaluate(pool, policy, spec, args, output)
        finally:
            checks['model_unchanged'] = all(torch.equal(before[key], value) for key, value in policy.state_dict().items())
            checks['trainer_updates_unchanged'] = trainers[0].updates == updates_before == 0

    def trainer(*args, **kwargs):
        value = original_trainer(*args, **kwargs)
        trainers.append(value)
        return value

    def pins(settings, output, extra=()):
        return original_pins(settings, output, [*extra, Path(__file__).resolve(),
            Path(precommit_path).resolve(), *map(Path, sealed['input_pins'])])

    try:
        runner.ShortPool, runner._evaluate, runner._pins = ProbePool, evaluate, pins
        runner.DecisionPPOTrainer = trainer
        runner.run(SimpleNamespace(command='evaluate', checkpoint=str(CHECKPOINT), out=str(out),
            control='reference', reference=str(REFERENCE), episodes=128))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        runner.ShortPool, runner._evaluate, runner._pins = original_pool, original_evaluate, original_pins
        runner.DecisionPPOTrainer = original_trainer
        if out.is_dir():
            write(out/'probe_failure.json', failure)
            write(out/'first_attempt_episodes.json', sorted(episodes, key=lambda row: row['env_id']))
            arrays = {key: np.stack([row[key] for row in samples]) for key in samples[0]} if samples else {}
            controls = {key: np.stack([row[key] for row in control_samples]) for key in control_samples[0]} if control_samples else {}
            np.savez_compressed(out/'physics240.npz', **arrays)
            np.savez_compressed(out/'control60.npz', **controls)
            checks.update(trace_finite=bool(arrays) and all(np.isfinite(v).all() for v in arrays.values()),
                control_finite=bool(controls) and all(np.isfinite(v).all() for v in controls.values()),
                all_first_attempts=len(episodes) == 128 and {row['env_id'] for row in episodes} == set(range(128)))
            checks['clock_contiguous'] = bool(arrays) and all(np.array_equal(
                arrays['clock'][:, i][arrays['first_attempt'][:, i]],
                np.arange(1, int(arrays['first_attempt'][:, i].sum())+1)) for i in range(128))
            checks['four_actual_substeps'] = len(samples) == 4*len(control_samples)
            pool = instances[0] if instances else None
            if arrays and pool and len(samples) % 4 == 0:
                targets = arrays['target4'][3::4]
                delta = np.diff(np.concatenate((pool.initial_target4[None], targets)), axis=0)
                live = arrays['first_attempt'][3::4]
                checks['target_rate_within_4_rad_per_s'] = bool((np.abs(delta[live]) <= 4/60+1e-6).all())
                lower = pool.controller.action_low[pool.learned].detach().cpu().numpy()
                upper = pool.controller.action_high[pool.learned].detach().cpu().numpy()
                checks['native_target_bounds'] = bool(((targets[live] >= lower-1e-6) & (targets[live] <= upper+1e-6)).all())
            else:
                checks['target_rate_within_4_rad_per_s'] = checks['native_target_bounds'] = False
            audit = pool.scene.diagnostics if pool else {}
            checks['lifecycle'] = bool(audit.get('closed') and audit.get('physx_use_gpu') and
                audit.get('use_gpu_pipeline') and audit.get('simulator_count') == 1 and audit.get('environment_count') == 128)
            changed = [p for p, digest in sealed['input_pins'].items() if not Path(p).is_file() or sha(p) != digest]
            checks['precommit_inputs_unchanged'] = not changed
            native_report = json.loads((out/'report.json').read_text()) if (out/'report.json').is_file() else {}
            checks['strict_runner_completed'] = native_report.get('completed') is True
            witnesses = []
            if arrays:
                threshold = CONTACT_CONTRACT['force_threshold_n']
                for episode in sorted(episodes, key=lambda row: row['env_id']):
                    i = episode['env_id']
                    live = arrays['first_attempt'][:, i]
                    t = arrays['local_time_s'][:, i]
                    spec = pool.spec
                    window = live & (t >= spec['view']['local_press_s']) & (t <= spec['view']['local_end_s'])
                    note = episode['live_selected_note']
                    progress = arrays['note_contact_progress'][:, i]
                    short = bool(0 < note['contact_progress'] < 1 and not note['left'] and
                                 np.any(window & (progress > 0) & (progress < 1)))
                    # These are native geometry/body-resultant witnesses, never pair/pressure certification.
                    after = live & arrays['release_requested'][:, i]
                    force = np.linalg.norm(arrays['distal_force_n'][:, i], axis=-1)
                    candidate = live & arrays['candidate'][:, i]
                    previous = np.r_[False, candidate[:-1]]
                    loss = after & previous & ~candidate
                    low = force < threshold
                    separated = ~arrays['geometry'][:, i]  # original pad position geometry gate
                    # Geometry/load can settle after the actual candidate-loss sample.
                    loss_seen = np.maximum.accumulate(loss)
                    joint = np.flatnonzero(after & loss_seen & ~candidate & low & separated)
                    stable = stable_release_span(arrays['clock'][:, i], live,
                        arrays['release_requested'][:, i], arrays['candidate'][:, i],
                        arrays['geometry'][:, i], force, threshold)
                    witnesses.append(dict(env_id=i, condition=i % 16, short_only_witness=short,
                        candidate_seen=bool(np.any(live & arrays['candidate'][:, i])),
                        after_release_candidate_absent=bool(np.any(after & ~arrays['candidate'][:, i])),
                        actual_candidate_loss_after_release_request=bool(loss.any()),
                        after_release_native_body_load_low=bool(np.any(after & (force < threshold))),
                        after_release_max_surface_distance_m=float(arrays['surface_distance_m'][:, i][after].max()) if after.any() else None,
                        geometry_absent_candidate_loss_load_low_same_sample=bool(len(joint)),
                        stable_release=stable,
                        joint_sample=dict(clock=int(arrays['clock'][joint[0], i]),
                            local_time_s=float(t[joint[0]]), surface_distance_m=float(arrays['surface_distance_m'][joint[0], i]),
                            distal_resultant_n=float(force[joint[0]])) if len(joint) else None,
                        note=note, reward_components=episode['reward_components'], reason=episode['reason']))
            write(out/'probe_report.json', dict(protocol=protocol(), completed=failure is None and all(checks.values()),
                checks=checks, failure=failure, changed_precommit_inputs=changed, witnesses=witnesses,
                missing_first_attempt_env_ids=sorted(set(range(128))-{r['env_id'] for r in episodes}),
                body_names=dict(distal=pool.scene.body_names[pool.distal], guitar=pool.scene.body_names[pool.environment.guitar_index]) if pool else None,
                selected_joint_names=pool.spec['learned_action_names'] if pool else None,
                hook='post original environment.substep; original ShortPool.step except selected4 release action substitution',
                reward_scope='control60 reward_cumulative_* are episode sums; never sum these endpoint values',
                limitations='resultant force does not identify contact pairs or certify string pressure; facing-negative coverage not guaranteed',
                training_updates=0, policy_performance=False))
            if failure is None and not all(checks.values()):
                raise RuntimeError('Live diagnostic audit failed; preserve outputs and inspect probe_report.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pre = sub.add_parser('precommit')
    pre.add_argument('--out', type=Path, required=True)
    live = sub.add_parser('run-gpu')
    live.add_argument('--precommit', type=Path, required=True)
    live.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'precommit':
        precommit(args.out)
    else:
        run_gpu(args.precommit, args.out)


if __name__ == '__main__':
    main()
