"""Only the three-note view, moving wrist goal, and bounded no-NN collector."""
import copy
from dataclasses import asdict, replace
import math

import numpy as np
import torch

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.song.finger_phrases import FingerPhrase, BalancedPhraseSampler, build_phrase_catalog
from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
from guitar_learning.tool.experiments.short_finger_learning import runtime, runner
from guitar_learning.tool.validation.press_acquisition import trajectory_actions

SCHEMA = 'diagnostic.index_prefix_4_7_8.v1'
INDICES = (4, 7, 8)


def view_and_catalog(task):
    targets = [task.targets[i] for i in INDICES]
    assert len(task.targets) == 67 and all(t.finger == 1 for t in targets)
    offset = targets[0].onset_s-3.
    next_press = min(t.press_s for i, t in enumerate(task.targets)
                     if t.finger == 1 and i not in INDICES and t.press_s >= targets[-1].end_s)
    end = max(t.end_s for t in targets)
    minimum = math.floor((end-offset)*60+1e-9)+1
    desired = math.ceil((end-offset+.5)*60-1e-9)
    maximum = math.floor((next_press-offset)*60+1e-9)
    ticks = min(desired, maximum)
    assert ticks >= minimum
    phrase = FingerPhrase('diagnostic-index-prefix-4-7-8', INDICES, targets[0].press_s,
                         end, next_press, ticks, offset, (3, 0, 0, 0))
    catalog = replace(build_phrase_catalog(task), phrases=(phrase,), preparation_s=targets[0].press_s-offset)
    view = dict(source_indices=list(INDICES), source_targets=[asdict(t) for t in targets],
                score_offset_s=offset, duration_ticks=ticks, local_press_s=targets[0].press_s-offset,
                local_end_s=end-offset, next_press_s=next_press, minimum_ticks=minimum,
                desired_ticks=desired, maximum_ticks=maximum, catalog_sha256=catalog.fingerprint,
                source_sha256=catalog.source_sha256,
                scope='67 unchanged targets; selected index1 notes4/7/8; conditional same-finger next-press cap, not original all-finger closed group')
    return view, catalog


def transition_fraction(local_time, view):
    start = view['source_targets'][0]['end_s']-view['score_offset_s']
    finish = view['source_targets'][1]['press_s']-view['score_offset_s']
    return ((local_time-start)/(finish-start)).clamp(0, 1)


class PrefixEnvironment(runtime.ShortEnvironment):
    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        spec = copy.deepcopy(song['short_learning'])
        if spec['schema'] != SCHEMA or spec['mode'] != song['finger_action_mode']:
            raise ValueError('Explicit prefix contract required')
        SimplifiedFingerEnvironment.__init__(self, metadata, bundle=bundle, song=song, skill=skill, device=device, hand=hand)
        view, self.catalog = view_and_catalog(self.task)
        if view != spec['view'] or spec['learned_action_indices'] != list(runtime.selected_actions(1)):
            raise ValueError('Three-note prefix view/action mask mismatch')
        self.selected_indices = INDICES
        self.sampler = BalancedPhraseSampler(self.catalog)
        self.contract['task']['short_learning'] = spec
        self.contract['task']['finger_skill'].update(scope='fixed_source_subset', catalog_sha256=self.catalog.fingerprint,
            reset_selection='same original notes4/7/8 on every reset', planned_transitions=None, full_song_after=None)
        self.contract['diagnostics']['short_learning'] = dict(scope='three-note noNN prefix; original predicates/rewards; native release latches observed')

    def _episode(self, index, failed):
        row = super()._episode(index, failed)
        row['prefix_release'] = dict(clock='original score seconds', values=[dict(
            source_index=i, released=bool(self.note['released'][index, i]),
            release_s=float(self.note['release_s'][index, i])) for i in INDICES])
        return row


class PrefixPool(runtime.ShortPool):
    environment_class_override = PrefixEnvironment

    def _wrist_feedback(self, desired, fraction):
        # The original v3 feedback is retained; only its Cartesian pose schedule differs.
        snapshot = self.scene.snapshot(); env = self.environment
        position, quaternion = runtime.interpolated_pose(self.initial_wrist_position, self.initial_wrist_quaternion,
            desired.new_tensor(self.spec['teacher']['wrist_position_G_m']),
            desired.new_tensor(self.spec['teacher']['wrist_quaternion_G_xyzw']), fraction)
        weight = transition_fraction(env._local_time()+1/60, self.spec['view']).to(desired)
        position = position+weight[:, None]*desired.new_tensor(self.spec['prefix']['delta_G_m'])
        error, jacobian = runtime.wrist_error_and_jacobian(snapshot, env.wrist_index, env.guitar_index,
            self.scene.com[env.wrist_index], self.wrist_position_groups, position, quaternion)
        active = ~snapshot['reset_body_snapshot']
        arm, correction, delta, candidate = runtime.bounded_wrist_target(desired[:, :12], self.wrist_correction,
            self.previous_arm_request, snapshot['q'][:, self.controller.active[:12]], jacobian, error, active,
            self.controller.action_low[:12], self.controller.action_high[:12], self.controller.rate[self.controller.active[:12]])
        self.wrist_correction.copy_(correction); self.previous_arm_request.copy_(arm); desired[:, :12] = arm
        self.last_wrist_feedback = dict(active=active.clone(), pose_error_world=error.clone(), requested_delta_rad=delta.clone(),
            requested_arm_rad=arm.clone(), candidate_arm_rad=candidate.clone(), position_goal_G_m=position.clone(),
            quaternion_goal_G_xyzw=quaternion.clone())
        return desired


def compact_episode(row, spec):
    notes = []
    for i, target, release in zip(INDICES, spec['view']['source_targets'], row['prefix_release']['values']):
        single = copy.deepcopy(spec); single['view'] = dict(source_index=i, source_target=target)
        single['teacher']['source_target_id'] = target['target_id']
        note = runner.compact_episode(row, single)
        notes.append({key: note[key] for key in ('target_id', 'achieved', 'clean_fraction', 'audible_wrong_fraction', 'missing_fraction', 'note')})
        assert release['source_index'] == i
        notes[-1].update(release)
    result = copy.deepcopy(note)
    for key in ('target_id', 'note'): del result[key]
    result.update(selected_target_count=3, notes=notes, achieved=all(n['achieved'] for n in notes),
        clean_fraction=sum(n['clean_fraction'] for n in notes)/3,
        audible_wrong_fraction=sum(n['audible_wrong_fraction'] for n in notes)/3,
        missing_fraction=sum(n['missing_fraction'] for n in notes)/3,
        aggregate_scope='all3 achievement; arithmetic mean quality for summary only; original acceptance applied separately to each note')
    return result


def evaluate(pool, policy, spec, args, out):
    assert pool.num_envs == args.episodes == 4 and args.control == 'reference'
    reference = runner.read_reference(args.reference, spec)
    goal = pool.teacher_reference.clone()
    for name, angle in reference['selected_targets_rad'].items(): goal[ACTIVE_NAMES.index(name)] = angle
    if bool(((goal < pool.controller.action_low) | (goal > pool.controller.action_high)).any()):
        raise ValueError('Reference exceeds original controller bounds')
    counts = [0]*4; rows = []; trace = []; observation = pool.observation
    pool.environment.set_evaluation(True, full_song=False)
    for _ in range(spec['view']['duration_ticks']):
        action = policy.act(*(observation[key] for key in runner.FIELDS), deterministic=True)['action']
        fraction = ((pool.environment._local_time()+1/60)/reference['ramp_s']).clamp(0, 1).to(action)
        desired = pool.teacher_reference+fraction[:, None]*(goal-pool.teacher_reference)
        action = trajectory_actions(desired, pool.controller.target[:, pool.controller.active], pool.teacher_reference,
            pool.controller.action_low, pool.controller.action_high, pool.incremental_mask, max_speed=4.)
        observation, _, _, terminated, truncated, finished = pool.step(action)
        if counts[0] == 0:
            env, scene = pool.environment, pool.scene; ids = list(INDICES)
            row = dict(time_s=float(env._local_time()[0]), source_time_s=float(env._score_time()[0]),
                policy_action=pool.last_policy_action[0].cpu().numpy().copy(), executed_action=pool.last_executed_action[0].cpu().numpy().copy(),
                q=scene.q[0].cpu().numpy().copy(), target=scene.target[0].cpu().numpy().copy(),
                body_state=scene.body_state[0].cpu().numpy().copy(), net_body_force_n=scene.snapshot()['contact_force'][0].cpu().numpy().copy(),
                candidate=env.candidate[0, ids].cpu().numpy().copy(), wrong=env.wrong[0, ids].cpu().numpy().copy(),
                surface_distance_m=env.surface_distance[0, ids].cpu().numpy().copy(), surface_height_m=env.surface_height[0, ids].cpu().numpy().copy(),
                released=env.note['released'][0, ids].cpu().numpy().copy(), release_s=env.note['release_s'][0, ids].cpu().numpy().copy())
            for name, value in pool.last_wrist_feedback.items(): row['wrist_'+name] = value[0].cpu().numpy().copy()
            trace.append(row)
        for row in finished:
            index = row['env_id']
            if counts[index] == 0: rows.append(compact_episode(row, spec)); counts[index] += 1
        if counts == [1]*4: break
        ids = (terminated | truncated).nonzero().flatten()
        if ids.numel(): observation = pool.reset(ids)[0]
    if counts != [1]*4: raise RuntimeError('Prefix first-attempt quotas incomplete')
    runner.write(out/'evaluation.json', dict(schema=SCHEMA, condition='reference', policy_performance=False, assigned_quotas=[1]*4,
        summary=runner.summary(rows), episodes=rows, scope=spec['result_scope']))
    if trace:
        np.savez_compressed(out/'trace_env0_episode0.npz', **{key: np.asarray([r[key] for r in trace]) for key in trace[0]})
        runner.write(out/'trace_metadata.json', dict(scope='env0 first attempt60Hz; failure endpoint included; three-note column order',
            joint_names=pool.scene.names, body_names=pool.scene.metadata['body_names'], source_indices=list(INDICES),
            source_target_ids=[t['target_id'] for t in spec['view']['source_targets']], wrist_control=spec['wrist_control'],
            wrist_feedback_scope='same precontrol actual versus next endpoint goal as original; score/local clocks explicit; no nativeqd trace'))
