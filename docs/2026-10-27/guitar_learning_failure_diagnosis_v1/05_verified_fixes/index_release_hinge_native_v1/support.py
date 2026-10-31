"""Fresh Jv3 no-NN three-note runtime; named pure helpers retain source bodies."""
import ast
import copy
from contextlib import contextmanager
from dataclasses import asdict, replace
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.song.finger_phrases import FingerPhrase, BalancedPhraseSampler, build_phrase_catalog
from guitar_learning.tool.experiments.short_finger_learning import runtime, runner

SCHEMA = 'diagnostic.release_hinge_native.v1'
CAP = .25
INDICES = (4, 7, 8)
HERE = Path(__file__).resolve().parent
SOURCES = {
    'prefix': HERE.parent/'index_prefix_4_7_8_v1/prefix_runtime.py',
    'timing': HERE.parent/'index_prefix_release_transfer_v1/schedule.py',
    'guard': HERE.parent/'index_candidate_dip_guard_v1/probe.py',
    'learning': HERE.parent/'low_effort_index_prefix_learning_v1/learning.py',
    'codec': HERE.parent/'index_prefix_goal_codec_v1/codec.py',
    'effort': HERE.parent/'finger_effort_limit_v1/probe.py',
}
IMPORT_MIGRATIONS = {'guitar_learning.core.finger_control': 'guitar_learning.core.control'}
REUSED = {
    'prefix': ('view_and_catalog', 'compact_episode', 'PrefixPool._wrist_feedback'),
    'timing': ('boundaries', 'negative_weight', 'wrist_weight'),
    'guard': ('target_filter',),
    'learning': ('current_goal', 'guard_descriptor'),
    'codec': ('bounds', 'encode', 'decode', 'desired_reference', 'convert'),
    'effort': ('private_contract', 'expected_properties'),
}


def source_node(path, qualified):
    nodes = ast.parse(path.read_text()).body
    for part in qualified.split('.'):
        node = next(n for n in nodes if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == part)
        nodes = node.body
    return node


def _reuse(source, qualified, alias=None):
    """Compile one explicitly named function, never execute the historical module."""
    node = copy.deepcopy(source_node(SOURCES[source], qualified))
    assert isinstance(node, ast.FunctionDef) and not node.decorator_list
    node.name = alias or node.name
    for child in ast.walk(node):
        if isinstance(child, ast.ImportFrom) and child.module in IMPORT_MIGRATIONS:
            child.module = IMPORT_MIGRATIONS[child.module]
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCES[source]), 'exec'), globals())


for _source, _names in REUSED.items():
    for _name in _names:
        _reuse(_source, _name, '_codec_desired_reference' if _name == 'desired_reference' else None)
del _source, _names, _name
# The original producer substituted this staged wrist timing before execution.
transition_fraction = wrist_weight
_TIMING_PROBE = SimpleNamespace(parent=SimpleNamespace(support=lambda: SimpleNamespace(timing=SimpleNamespace(negative_weight=negative_weight))))


def desired_reference(pool):
    schedule = pool.spec['reference_release_schedule']
    reference = dict(ramp_s=pool.spec['teacher']['ramp_s'], selected_targets_rad=dict(zip(
        pool.spec['learned_action_names'], schedule['reference_selected_rad'])))
    return _codec_desired_reference(_TIMING_PROBE, pool, reference)


def reference_raw(pool):
    desired = desired_reference(pool)
    c = pool.controller
    raw = runtime.trajectory_actions(desired, c.target[:, c.active], pool.teacher_reference,
        c.action_low, c.action_high, pool.incremental_mask, max_speed=4.)
    ids = pool.spec['learned_action_indices']
    raw[:, ids] = encode(desired[:, ids], *bounds(pool))
    return raw


@contextmanager
def effort_loader(calls):
    from guitar_learning.runtime import prepared_reset_v1
    original = prepared_reset_v1.load_prepared_reset_contract
    def changed():
        source = original()
        private, document = private_contract(source)
        calls.append((source, document))
        return private
    prepared_reset_v1.load_prepared_reset_contract = changed
    try:
        yield
    finally:
        prepared_reset_v1.load_prepared_reset_contract = original


def verify_native(scene, source, document):
    actual = scene.pd_properties
    baseline = expected_properties(source, actual.dtype)
    expected = baseline.copy()
    expected['effort'][document['native_indices']] = CAP
    assert np.array_equal(actual, expected)
    changed = {key: np.flatnonzero(actual[key] != baseline[key]).tolist() for key in actual.dtype.names}
    assert changed['effort'] == document['native_indices']
    assert all(not ids for key, ids in changed.items() if key != 'effort')
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted, source)
    assert scene.physics_steps == 0
    assert scene.hand_collision['enabled_distinct_finger_pairs'] == 90
    assert scene._hand_collision_readback_count == scene.num_envs == 128
    return dict(**document, actual_native_PD105={key: actual[key].tolist() for key in actual.dtype.names},
        original_profile_native_PD105={key: baseline[key].tolist() for key in actual.dtype.names},
        changed_native_field_indices=changed, expected_readback_exact=True, native_environments=128,
        property_scope='Full105 final-env readback; current GpuScene constructor asserts every native field for all128 environments',
        loader_scope='Only during _create_scene; original verified loader called once; finally restored')


class Environment(runtime.ShortEnvironment):
    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        spec = copy.deepcopy(song['short_learning'])
        if (spec['schema'] != SCHEMA or spec['finger'] != 1 or spec['mode'] != 'incremental' or
                spec['candidate_dip_guard'] != guard_descriptor()):
            raise ValueError('Explicit fresh three-note Jv3 noNN contract required')
        FingerSkillEnvironment.__init__(self, metadata, bundle=bundle, song=song, skill=skill, device=device, hand=hand)
        view, self.catalog = view_and_catalog(self.task)
        if view != spec['view'] or spec['learned_action_indices'] != list(runtime.selected_actions(1)):
            raise ValueError('Three-note prefix view/action mask mismatch')
        assert self.contract['observation']['dimension'] == 557
        self.selected_indices = INDICES
        self.sampler = BalancedPhraseSampler(self.catalog)
        self.contract['task']['short_learning'] = spec
        self.contract['task']['finger_skill'].update(scope='fixed_source_subset', catalog_sha256=self.catalog.fingerprint,
            reset_selection='same original notes4/7/8 on every reset', planned_transitions=None, full_song_after=None)
        self.contract['diagnostics']['short_learning'] = dict(scope='fresh Jv3 557state noNN; original three-note predicates/rewards and current-goal guard')
        self.contract['action']['target_contract']['diagnostic_candidate_dip_guard'] = guard_descriptor()

    def _episode(self, index, failed):
        row = super()._episode(index, failed)
        row['prefix_release'] = dict(clock='original score seconds', values=[dict(
            source_index=i, released=bool(self.note['released'][index, i]),
            release_s=float(self.note['release_s'][index, i])) for i in INDICES])
        return row


class Pool(runtime.ShortPool):
    environment_class_override = Environment
    record_first_controls = True
    _wrist_feedback = _wrist_feedback

    def __init__(self, settings, out):
        self.cleanup_errors = []
        self.guard_rows = []
        self.pending = None
        self.native_targets = None
        try:
            super().__init__(settings, out)
            assert self.num_envs == 128 and self.observation['state'].shape == (128, 557)
            self.first = torch.ones(self.num_envs, dtype=torch.bool, device=self.scene.device)
            self.dip = self.scene.names.index('LH:index3')
            self.ai = self.controller.active.tolist().index(self.dip)
            assert self.ai == 20 and self.controller.rate[self.dip] == 4
            self.obs_index = self.contract['observation']['fields'].index('target_error.LH:index3')
            self.guard_counts = torch.zeros(4, 3, dtype=torch.long, device=self.scene.device)
            self.native_targets = self.controller.targets
            self.controller.targets = self.targets
        except BaseException:
            try:
                self.close()
            except BaseException as error:
                self.cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
            raise

    def _create_scene(self, settings, out):
        calls = []
        scene = None
        from guitar_learning.runtime import prepared_reset_v1
        original = prepared_reset_v1.load_prepared_reset_contract
        try:
            with effort_loader(calls):
                scene = super()._create_scene(settings, out)
            assert prepared_reset_v1.load_prepared_reset_contract is original and len(calls) == 1
            self.effort_readback = verify_native(scene, *calls[0])
            return scene
        except BaseException:
            if scene is not None:
                try:
                    scene.close()
                except BaseException as error:
                    self.cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
            raise

    def targets(self, action, snapshot):
        env = self.environment
        col, present = current_goal(env._score_time(), env.end[list(INDICES)])
        index = col.new_tensor(INDICES)[col]
        rows = torch.arange(self.num_envs, device=self.scene.device)
        failed = env.failure.any(-1) | env.wrist_failure | env.wrist_severe_failure
        target, self.pending = target_filter(self.controller, self.native_targets, action, snapshot,
            torch.ones_like(present), env.candidate[rows, index] & present, env.wrong[rows, index],
            failed, self.dip, self.ai, True)
        self.pending.update(first_attempt=self.first.clone(), current_goal=torch.where(present, index, -torch.ones_like(index)),
            start_clock=env.clock.clone())
        return target

    def step(self, action):
        self.pending = None
        result = super().step(action)
        r = self.pending
        if r is None:
            raise RuntimeError('Missing current-goal DIP audit')
        env = self.environment
        r['clock'] = env.clock.clone()
        r['post_failure'] = (env.failure.any(-1) | env.wrist_failure | env.wrist_severe_failure).clone()
        r['submit_error_rad'] = (self.scene.target[:, self.dip]-r['final_target_rad']).abs()
        expected = ((self.scene.target[:, self.dip]-self.scene.q[:, self.dip])/env.scales[self.obs_index]).clamp(-10, 10)
        r['observation_error'] = (result[0]['state'][:, self.obs_index]-expected).abs()
        valid = r['finite']
        assert bool(((r['submit_error_rad'][valid] == 0) & (r['observation_error'][valid] == 0)).all())
        for j, i in enumerate((*INDICES, -1)):
            mask = r['current_goal'] == i
            self.guard_counts[j] += torch.stack((mask.sum(), (mask & r['blocked']).sum(),
                (mask & (r['raw_target_rad'] < r['old_target_rad'])).sum()))
        if self.record_first_controls:
            self.guard_rows.append({k: np.where(r['first_attempt'].cpu().numpy(), v.detach().cpu().numpy(),
                np.zeros_like(v.detach().cpu().numpy())) for k, v in r.items()})
            assert len(self.guard_rows) <= self.spec['view']['duration_ticks']
        for row in result[-1]:
            self.first[row['env_id']] = False
        return result

    def close(self):
        if self.native_targets is not None:
            self.controller.targets = self.native_targets
        return super().close()
