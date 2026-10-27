"""Script replay and300-row BC interfaces; fixtures are not native validation."""
import copy
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
import torch._dynamo  # Load lazy optimizer registrations before temporary module stubs.
from guitar_learning import imitation_io, timing_environment
from guitar_learning.imitation import SCHEMA, dataset_manifest
from guitar_learning.specialist_policy import SpecialistPolicy
from guitar_learning.timing_curriculum import TimingConfig
from guitar_learning.timing_demonstration import (CAPTURE_SCHEMA, replay_actions, capture,
    load_dataset, fit_actor, save_initialization, fit)
from guitar_learning.timing_transfer import apply_actor_initialization
from guitar_learning.tests.test_imitation import arrays as old_arrays, contract as old_contract
from guitar_learning.tests import test_timing_transfer as transfer_fixtures
from guitar_learning.tests import test_timing_environment as environment_fixtures


class FakeTimingEnvironment:
    def __init__(self, contract, terminal_tick=300, raises=False):
        self.contract, self.terminal_tick, self.raises = contract, terminal_tick, raises
        self.actions, self.closed = [], False
    def observation(self):
        return dict(state=np.full(536, len(self.actions)/300., np.float32),
            events=np.zeros((64, 24), np.float32), mask=np.ones(64, bool),
            priority_events=np.zeros((2, 24), np.float32), priority_mask=np.ones(2, bool))
    def reset(self): return self.observation(), {'training_contract': self.contract}
    def step(self, action):
        self.actions.append(action.copy())
        tick = len(self.actions)
        if self.raises and tick == self.terminal_tick: raise RuntimeError('synthetic native exception')
        terminated = tick == self.terminal_tick
        success = terminated and tick == 300
        timing = dict(stage_success=success)
        info = dict(cost=0., timing=timing, specialist=dict(stage_success=success),
            score_time_s=tick/60.-1., music=dict(matched50=0),
            native_control=dict(physics_samples240=[{'native': {'physics_step': tick*4+i}} for i in range(4)]),
            physics_measurements=[{'physics_step': tick*4+i} for i in range(4)])
        if terminated:
            info['episode'] = dict(reason='timeline_complete' if success else 'terminal_failure',
                timing=timing, music=info['music'])
        return self.observation(), 0., terminated, False, info
    def close(self): self.closed = True


class TimingDemonstrationTests(unittest.TestCase):
    def setUp(self):
        environment_fixtures.TimingEnvironmentTests.setUp(self)
        self.threads = torch.get_num_threads(); torch.set_num_threads(1)
        self.root = Path(self.folder.name)
        self.settings = dict(specialist=dict(role='left'), timing=asdict(TimingConfig()))
        self.native_contract = transfer_fixtures.TimingTransferTests.contract(self)
        self.teacher = self.root/'teacher'; self.teacher.mkdir()
        data = old_arrays('left')
        data['action'][:] = 0.; data['action'][:, 0] = np.arange(240)/300.
        np.savez_compressed(self.teacher/'demonstration.npz', **data)
        (self.teacher/'reset.json').write_text(json.dumps(dict(training_contract=old_contract('left'))))
        (self.teacher/'result.json').write_text(json.dumps(dict(success=True, ticks=240, observation_dimension=505)))
        self.settings_path = self.root/'settings.json'; self.settings_path.write_text('{}')

    def tearDown(self):
        environment_fixtures.TimingEnvironmentTests.tearDown(self)
        torch.set_num_threads(self.threads)

    def capture(self, name='capture', terminal_tick=300, raises=False):
        env = FakeTimingEnvironment(copy.deepcopy(self.native_contract), terminal_tick, raises)
        args = SimpleNamespace(teacher=self.teacher, settings=self.settings_path, out=self.root/name)
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
             patch.object(timing_environment, 'build_environment', return_value=env), \
             patch.object(imitation_io, 'pin_inputs', side_effect=lambda paths: dataset_manifest(paths)), \
             patch.object(imitation_io, 'verify_inputs', side_effect=lambda pins: dataset_manifest(pins) == pins):
            if raises:
                with self.assertRaisesRegex(RuntimeError, 'synthetic native exception'): capture(self.settings, args)
                result = json.loads((args.out/'result.json').read_text())
            else: result = capture(self.settings, args)
        self.assertTrue(env.closed)
        return args.out, result, env

    def test_teacher240_then_final_hold60_and_action_before_observation_alignment(self):
        out, result, env = self.capture()
        self.assertTrue(result['completed'] and result['success'])
        self.assertEqual(result['ticks'], 300)
        self.assertEqual(result['replay']['final_action_hold_ticks'], 60)
        data = load_dataset(out, self.settings)
        self.assertEqual(data['state'].shape, (300, 536))
        self.assertAlmostEqual(float(data['state'][0, 0]), 0.)
        self.assertAlmostEqual(float(data['state'][-1, 0]), 299/300., places=6)
        np.testing.assert_array_equal(data['action'][:240, 0], np.arange(240, dtype=np.float32)/300.)
        np.testing.assert_array_equal(data['action'][240:], np.repeat(data['action'][239:240], 60, axis=0))
        self.assertTrue(np.all(data['action'][:, 33:] == 0))
        with gzip.open(out/'trace.json.gz', 'rt') as stream: rows = json.load(stream)
        self.assertEqual(len(rows), 300)
        self.assertEqual(len(rows[-1]['samples240']), 4)
        self.assertEqual(len(rows[-1]['measurements']), 4)

    def test_physical_failure_and_exception_keep_partial_artifacts_and_close(self):
        for raises in (False, True):
            out, result, env = self.capture('failure_'+str(raises), terminal_tick=11, raises=raises)
            self.assertFalse(result['success'] or result['completed'])
            self.assertTrue((out/'demonstration.npz').is_file() and (out/'trace.json.gz').is_file())
            self.assertEqual(result['ticks'], 10 if raises else 11)
            if raises: self.assertEqual(result['failure']['type'], 'RuntimeError')
            with self.assertRaises(ValueError): load_dataset(out, self.settings)

    def test_invalid_teacher_success_length_actions_and_role_reject_before_scene(self):
        actions = np.zeros((240, 39), np.float32)
        for bad in (actions[:239], np.full((240, 39), float('nan'), np.float32),
                    np.ones((240, 39), np.float32), np.full((240, 39), 1.1, np.float32)):
            with self.assertRaises(ValueError): replay_actions(bad, 'left')
        (self.teacher/'result.json').write_text(json.dumps(dict(success=False, ticks=240, observation_dimension=505)))
        args = SimpleNamespace(teacher=self.teacher, settings=self.settings_path, out=self.root/'invalid')
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
             patch.object(timing_environment, 'build_environment') as build:
            with self.assertRaises(ValueError): capture(self.settings, args)
            build.assert_not_called()
        self.assertFalse(args.out.exists())

    def test_dataset_requires_full_same_role_configuration_and_true_boolean_masks(self):
        out, _, _ = self.capture()
        different = copy.deepcopy(self.settings); different['timing']['stage_index'] = 1
        with self.assertRaises(ValueError): load_dataset(out, different)
        different = copy.deepcopy(self.settings); different['specialist']['role'] = 'right'
        with self.assertRaises(ValueError): load_dataset(out, different)
        with np.load(out/'demonstration.npz') as archive: data = {key: archive[key].copy() for key in archive.files}
        data['mask'] = data['mask'].astype(np.float32)
        np.savez_compressed(out/'demonstration.npz', **data)
        with self.assertRaisesRegex(ValueError, 'boolean'): load_dataset(out, self.settings)

    def test_full300_fit_changes_only_active_actor_and_saves_compatible_bc_schema(self):
        out, _, _ = self.capture()
        data = load_dataset(out, self.settings)
        for key in ('state', 'events', 'priority_events'): data[key][:] = 0.
        data['action'][:] = 0.; data['action'][:240, :33] = .1; data['action'][240:, :33] = .5
        model = SpecialistPolicy(536, size='small', role='left', frozen_partner=False, contract=data['contract'])
        with torch.no_grad(): model.log_std.fill_(-4.)
        before = {key: value.clone() for key, value in model.state_dict().items()}
        result = fit_actor(model, data, steps=1, batch_size=300, lr=1e-5)
        self.assertEqual(result['rows'], 300)
        self.assertEqual(result['batch_size'], 300)
        self.assertAlmostEqual(result['initial_training_mse'], .8*.1**2+.2*.5**2, places=6)
        self.assertLess(result['training_mse'], result['initial_training_mse'])
        self.assertFalse(result['converged'])
        self.assertTrue(result['changed_model_keys'])
        allowed = ('actor_encoders.left.', 'actor_heads.left.')
        for key, value in model.state_dict().items():
            if not key.startswith(allowed): self.assertTrue(torch.equal(value, before[key]), key)
        checkpoint = self.root/'timing_actor.pt'
        save_initialization(model, checkpoint, data=data, fit_result=result)
        payload = torch.load(checkpoint, weights_only=False)
        self.assertEqual(payload['schema'], SCHEMA)
        self.assertEqual(payload['dataset_schema'], CAPTURE_SCHEMA)
        self.assertNotIn('identity', payload); self.assertNotIn('updates', payload)
        target = SpecialistPolicy(536, size='small', role='left', frozen_partner=False, contract=data['contract'])
        transfer = apply_actor_initialization(target, checkpoint, kind='bc')
        self.assertEqual(transfer['expanded'], [])
        self.assertTrue(torch.equal(model.actor_heads['left'].weight, target.actor_heads['left'].weight))
        with self.assertRaises(FileExistsError): save_initialization(model, checkpoint, data=data, fit_result=result)

    def test_fit_pipeline_transfers_old_actor_then_trains_all300_rows(self):
        dataset, _, _ = self.capture()
        legacy = transfer_fixtures.TimingTransferTests.contract(self, legacy=True)
        source = SpecialistPolicy(505, size='small', role='left', frozen_partner=False, contract=legacy)
        actor = self.root/'source_actor.pt'
        torch.save(dict(schema=SCHEMA, role='left', architecture=source.architecture,
            dataset_manifest={'synthetic': 'CPU fixture'}, training={'steps': 1}, model=source.state_dict()), actor)
        settings = dict(self.settings, actor_initialization=str(actor), actor_initialization_kind='bc',
                        size='small', device='cpu', seed=7, initial_std=.02)
        args = SimpleNamespace(dataset=dataset, settings=self.settings_path, out=self.root/'fit', steps=1)
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
             patch.object(imitation_io, 'pin_inputs', side_effect=lambda paths: dataset_manifest(paths)), \
             patch.object(imitation_io, 'verify_inputs', side_effect=lambda pins: dataset_manifest(pins) == pins):
            result = fit(settings, args)
        self.assertTrue(result['completed'] and result['source_unchanged'])
        self.assertEqual(result['fit']['batch_size'], 300)
        self.assertEqual(result['ppo_updates'], 0)
        initialization = json.loads((args.out/'actor_initialization.json').read_text())
        self.assertEqual(initialization['expanded'][0]['source_columns'], 505)
        self.assertEqual(initialization['expanded'][0]['target_columns'], 536)
        self.assertEqual(torch.load(args.out/'actor_initialization.pt', weights_only=False)['training']['rows'], 300)


if __name__ == '__main__': unittest.main()
