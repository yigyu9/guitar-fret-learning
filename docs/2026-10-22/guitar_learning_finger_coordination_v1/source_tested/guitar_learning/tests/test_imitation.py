"""Actor-only cloning contracts; synthetic arrays do not certify native success."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from guitar_learning.imitation.imitation import SCHEMA, load_dataset, dataset_manifest, fit_actor, save_initialization, apply_actor_initialization
from guitar_learning.skills.specialist_policy import SpecialistPolicy


def contract(role='left'):
    return dict(schema='guitar_learning.training.v1', observation=dict(dimension=505,
        event_dim=24, capacity=64, priority_slots=2), action={}, reward={}, termination={},
        task=dict(specialist=dict(role=role, skill='hold' if role == 'left' else 'cross',
                                 imitation_profile='synthetic_cpu_fixture')))


def arrays(role='left'):
    rng = np.random.RandomState(7)
    action = np.zeros((240, 39), dtype=np.float32)
    action[:, :33] = .1 if role == 'left' else 0.
    if role == 'right': action[:, 33:] = -.1
    return dict(state=rng.normal(0., .01, (240, 505)).astype(np.float32),
        events=rng.normal(0., .01, (240, 64, 24)).astype(np.float32),
        mask=np.ones((240, 64), dtype=bool),
        priority_events=rng.normal(0., .01, (240, 2, 24)).astype(np.float32),
        priority_mask=np.ones((240, 2), dtype=bool), action=action)


class ImitationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.out = Path(self.folder.name)
        self.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    def tearDown(self):
        torch.set_num_threads(self.old_threads)
        self.folder.cleanup()

    def capture(self, role='left', **result):
        (self.out/'result.json').write_text(json.dumps(dict(success=True, ticks=240,
            observation_dimension=505, **result)))
        (self.out/'reset.json').write_text(json.dumps(dict(training_contract=contract(role))))
        np.savez(self.out/'demonstration.npz', **arrays(role))
        return load_dataset(self.out, role)

    def model(self, role='left'):
        torch.manual_seed(7)
        return SpecialistPolicy(505, size='small', role=role, contract=contract(role))

    def snapshot(self, model):
        return {key: value.clone() for key, value in model.state_dict().items()}

    def assert_unchanged(self, model, before):
        for key, value in model.state_dict().items():
            self.assertTrue(torch.equal(value, before[key]), key)

    def test_capture_exact_fields_contract_and_hashes(self):
        for role in ('left', 'right'):
            data = self.capture(role)
            self.assertEqual(data['role'], role)
            self.assertEqual(data['state'].shape, (240, 505))
            self.assertEqual(data['contract'], contract(role))
            self.assertEqual(data['manifest'], dataset_manifest([
                self.out/'result.json', self.out/'reset.json', self.out/'demonstration.npz']))
            load_dataset(self.out, role, expected_contract=contract(role))
            mismatched = contract(role); mismatched['reward']['new'] = 1.
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                load_dataset(self.out, role, expected_contract=mismatched)

    def test_failed_capture_wrong_role_and_malformed_arrays_rejected(self):
        self.capture()
        for result in (dict(success=False, ticks=240, observation_dimension=505),
                       dict(success=True, ticks=239, observation_dimension=505),
                       dict(success=True, ticks=True, observation_dimension=505),
                       dict(success=True, ticks=240, observation_dimension=468)):
            (self.out/'result.json').write_text(json.dumps(result))
            with self.assertRaises(ValueError): load_dataset(self.out, 'left')
        self.capture()
        with self.assertRaises(ValueError): load_dataset(self.out, 'right')
        for key, value in (('state', np.zeros((239, 505), np.float32)),
                ('events', np.full((240, 64, 24), np.nan, np.float32)),
                ('mask', np.ones((240, 64), np.float32)),
                ('action', np.ones((240, 39), np.float32)),
                ('action', np.full((240, 39), 1.1, np.float32))):
            source = arrays(); source[key] = value
            np.savez(self.out/'demonstration.npz', **source)
            with self.subTest(key=key), self.assertRaises(ValueError): load_dataset(self.out, 'left')

    def test_fit_changes_only_active_actor_and_reduces_action_error(self):
        data, model = self.capture(), self.model()
        before = self.snapshot(model)
        log = []
        result = fit_actor(model, data, steps=100, batch_size=240, tolerance=1e-5,
                           log_callback=log.append)
        self.assertLess(result['training_mse'], result['initial_training_mse']*.01)
        self.assertEqual(result['steps'], 100)
        self.assertEqual(log, result['log'])
        changed = False
        for key, value in model.state_dict().items():
            if key.startswith(('actor_encoders.left.', 'actor_heads.left.')):
                changed |= not torch.equal(value, before[key])
            else:
                self.assertTrue(torch.equal(value, before[key]), key)
        self.assertTrue(changed)
        self.assertNotIn('updates', result)

    def test_invalid_fit_contract_rejected_before_parameter_changes(self):
        data, model = self.capture(), self.model()
        before = self.snapshot(model)
        data['contract']['termination']['changed'] = True
        with self.assertRaisesRegex(ValueError, 'contract'): fit_actor(model, data, steps=1)
        self.assert_unchanged(model, before)

    def test_initialization_roundtrip_is_actor_only_and_exclusive(self):
        data, source, target = self.capture(), self.model(), self.model()
        with torch.no_grad():
            source.actor_heads['left'].bias.fill_(.2)
            source.log_std[:33].fill_(-2.)
            target.log_std.fill_(-4.)
        path = self.out/'initialization.pt'
        fit = dict(steps=0, training_mse=.01, scope='synthetic fixture')
        save_initialization(source, path, dataset_manifest=data['manifest'], fit_result=fit)
        payload = torch.load(path, map_location='cpu', weights_only=False)
        self.assertEqual(payload['schema'], SCHEMA)
        self.assertNotIn('updates', payload)
        self.assertNotIn('identity', payload)
        with self.assertRaises(FileExistsError):
            save_initialization(source, path, dataset_manifest=data['manifest'], fit_result=fit)
        before = self.snapshot(target)
        evidence = apply_actor_initialization(target, path)
        for key, value in target.state_dict().items():
            if key.startswith(('actor_encoders.left.', 'actor_heads.left.')):
                self.assertTrue(torch.equal(value, source.state_dict()[key]), key)
            elif key != 'log_std':
                self.assertTrue(torch.equal(value, before[key]), key)
        self.assertTrue(torch.equal(target.log_std[:33], source.log_std[:33]))
        self.assertTrue(torch.equal(target.log_std[33:], before['log_std'][33:]))
        self.assertEqual(evidence['dataset_manifest'], data['manifest'])
        self.assertEqual(evidence['training'], fit)
        self.assertNotIn('updates', evidence)

    def test_nonfinite_inactive_tensor_and_mismatched_schema_reject_before_copy(self):
        data, source, target = self.capture(), self.model(), self.model()
        path = self.out/'initialization.pt'
        save_initialization(source, path, dataset_manifest=data['manifest'], fit_result=dict(steps=0))
        payload = torch.load(path, map_location='cpu', weights_only=False)
        cases = []
        broken = copy.deepcopy(payload); broken['model']['cost_critic.weight'].fill_(float('nan')); cases.append(broken)
        broken = copy.deepcopy(payload); broken['architecture']['contract']['task']['specialist']['imitation_profile'] = 'wrong'; cases.append(broken)
        broken = copy.deepcopy(payload); broken['schema'] = 'guitar_learning_ppo_v1'; cases.append(broken)
        broken = copy.deepcopy(payload); broken['updates'] = 1; cases.append(broken)
        broken = copy.deepcopy(payload); broken['model'].pop('log_std'); cases.append(broken)
        before = self.snapshot(target)
        for index, candidate in enumerate(cases):
            malformed = self.out/('bad%d.pt'%index); torch.save(candidate, malformed)
            with self.subTest(index=index), self.assertRaises(ValueError):
                apply_actor_initialization(target, malformed)
            self.assert_unchanged(target, before)


if __name__ == '__main__': unittest.main()
