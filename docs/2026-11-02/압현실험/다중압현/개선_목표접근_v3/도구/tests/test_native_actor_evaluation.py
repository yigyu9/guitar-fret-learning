import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_actor_evaluation as native


class GateTests(unittest.TestCase):
    def manifest_fixture(self):
        artifact = native.STUDY/'로그/test_bootstrap/actor_initialization.pt'
        report = artifact.with_name('report.json')
        plan = native.STUDY/'입력/test_bootstrap.json'
        manifest = dict(schema=native.SCHEMA, sealed=True, num_envs=1, controls=330,
            training_updates=0, policy_control='deterministic_actor_only',
            source_checkpoint=str(native.PILOT), prior_guard_report=str(native.PRIOR),
            actor_artifact=str(artifact), actor_sha256='actor-sha', bootstrap_report=str(report),
            bootstrap_plan=str(plan), out=str(native.STUDY/'로그/test_actor_eval'), python=sys.executable)
        required = [Path(native.__file__).resolve(), native.STUDY/'도구/teacher_bootstrap.py',
            artifact, report, plan, native.PRIOR, native.NOMINAL, native.PILOT,
            native.TRAIN/'도구/prepare.py', native.TRAIN/'도구/pair_environment.py']
        hashes = {str(path): 'sha-'+path.name for path in required}
        hashes[str(artifact)] = 'actor-sha'
        manifest['pins'] = dict(hashes)
        path = native.STUDY/'입력/test_actor_eval.json'
        hashes[str(path)] = 'manifest-sha'
        bootstrap = dict(completed=True, cpu_only=True, std_critic_buffers_unchanged=True,
            optimizer_rng_transferred=False, artifact=str(artifact), artifact_sha256='actor-sha',
            plan=str(plan), plan_sha256=hashes[str(plan)], source_sha256={str(native.PILOT): hashes[str(native.PILOT)]})
        prior = dict(completed=True, capture_completed=True, protocol_completed=True,
            final_state_verified=True, failure=None,
            impact=dict(maximum_elapsed_ratio=1.1, inspection_errors=[], severe=False))
        documents = {str(path): manifest, str(native.NOMINAL): dict(pins={str(native.PILOT): hashes[str(native.PILOT)]}),
                     str(native.PRIOR): prior, str(report): bootstrap}
        return path, manifest, hashes, documents

    def verify_fixture(self, path, hashes, documents):
        with patch.object(native, 'sha', side_effect=lambda p: hashes[str(p)]), \
             patch.object(native, 'read', side_effect=lambda p: documents[str(p)]):
            return native.verify_manifest(path, 'manifest-sha')

    def test_exact_pinned_manifest_and_prior_guard_pass(self):
        path, manifest, hashes, documents = self.manifest_fixture()
        self.assertEqual(self.verify_fixture(path, hashes, documents), manifest)

    def test_unsealed_wrong_budget_or_missing_pin_are_rejected(self):
        for field, value in [('sealed', False), ('controls', 329), ('num_envs', 2),
                             ('policy_control', 'scripted_targets'), ('training_updates', 1)]:
            path, manifest, hashes, documents = self.manifest_fixture()
            manifest[field] = value
            with self.assertRaises(ValueError):
                self.verify_fixture(path, hashes, documents)
        path, manifest, hashes, documents = self.manifest_fixture()
        manifest['pins'].pop(manifest['bootstrap_report'])
        with self.assertRaises(ValueError):
            self.verify_fixture(path, hashes, documents)

    def test_prior_delay_unknown_or_at25percent_is_rejected(self):
        for value in (None, True, 1.25, float('nan')):
            path, manifest, hashes, documents = self.manifest_fixture()
            documents[str(native.PRIOR)]['impact']['maximum_elapsed_ratio'] = value
            with self.assertRaises(ValueError):
                self.verify_fixture(path, hashes, documents)

    def test_report_artifact_plan_and_source_sha_mismatch_are_rejected(self):
        for key in ('artifact_sha256', 'plan_sha256', 'artifact', 'plan'):
            path, manifest, hashes, documents = self.manifest_fixture()
            documents[manifest['bootstrap_report']][key] = 'changed'
            with self.assertRaises(ValueError):
                self.verify_fixture(path, hashes, documents)
        path, manifest, hashes, documents = self.manifest_fixture()
        manifest['pins'][str(native.PILOT)] = 'changed'
        with self.assertRaises(ValueError):
            self.verify_fixture(path, hashes, documents)

    def test_full_settings_keep_exposure_while_only_capture_env_count_changes(self):
        from prepare import load_cases, make_settings
        case = next(case for case in load_cases() if case['case_id'] == 'index_middle_same')
        full = make_settings(case, native.TRAIN/'입력/song_bundles/index_middle_same')
        before = copy.deepcopy(full)
        capture = native.validate_settings(full)
        self.assertEqual(full, before)
        expected = copy.deepcopy(full); expected['num_envs'] = 1
        self.assertEqual(capture, expected)
        self.assertEqual(capture['finger_skill']['planned_transitions'], 204800)
        for key, value in [('planned_transitions', 1280), ('full_song_after', 320)]:
            bad = copy.deepcopy(full); bad['finger_skill'][key] = value
            with self.assertRaises(ValueError):
                native.validate_settings(bad)

    def test_native_contract_mismatch_is_rejected_without_projection(self):
        native.capture_contract(dict(task=dict(planned=204800)), dict(task=dict(planned=204800)))
        with self.assertRaises(ValueError):
            native.capture_contract(dict(task=dict(planned=1280)), dict(task=dict(planned=204800)))

    def test_outcomes_do_not_promote_early_or_unsafe_failure(self):
        good = dict(termination={}, simultaneous_press=dict(success=True))
        self.assertEqual(native.evaluation_outcome(good, True, True), 'policy_simultaneous_clean_success')
        self.assertEqual(native.evaluation_outcome(good, False, True), 'inspection_error')
        self.assertEqual(native.evaluation_outcome(good, True, False), 'incomplete_episode')
        good['termination']['physical_failure'] = True
        self.assertEqual(native.evaluation_outcome(good, True, True), 'physical_failure')

    def test_final_state_failure_records_null_and_unavailable_impact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest_path = root/'manifest.json'
            manifest_path.write_text('{}')
            out = root/'run'
            manifest = dict(out=str(out), python=sys.executable)
            baseline = dict(status='running', finished=200, results={})
            process = MagicMock()
            process.poll.return_value = 0
            process.wait.return_value = 0
            with patch.object(native, 'verify_manifest', return_value=manifest), \
                 patch.object(native, 'readiness', return_value=(True, 'ready', {})), \
                 patch.object(native, '_state', side_effect=[baseline, RuntimeError('final read failed'),
                                                             RuntimeError('cleanup read failed')]), \
                 patch.object(native.subprocess, 'Popen', return_value=process), \
                 patch.object(native, 'read', return_value=dict(capture_completed=True,
                     protocol_completed=True, outcome='policy_hold_failed')), \
                 patch.object(native, 'stop_own_group') as stop, \
                 patch.object(native, 'impact') as impact, \
                 patch('builtins.print'):
                with self.assertRaisesRegex(RuntimeError, 'final read failed'):
                    native.parent(manifest_path)
            after = json.loads((out/'single_after.json').read_text())
            report = json.loads((out/'guard_report.json').read_text())
            self.assertIsNone(after)
            self.assertFalse(report['final_state_verified'])
            self.assertFalse(report['completed'])
            self.assertFalse(report['impact']['available'])
            self.assertTrue(report['impact']['severe'])
            self.assertIsNone(report['impact']['maximum_elapsed_ratio'])
            self.assertIn('cleanup read failed', report['final_state_error'])
            impact.assert_not_called()
            stop.assert_called_once_with(process)


class PolicyAlignmentTests(unittest.TestCase):
    def fixture(self):
        import torch
        from types import SimpleNamespace
        observation = dict(state=torch.full((1, 557), .2), events=torch.zeros(1, 64, 24),
            mask=torch.zeros(1, 64, dtype=torch.bool), priority_events=torch.zeros(1, 8, 24),
            priority_mask=torch.zeros(1, 8, dtype=torch.bool))
        class Policy:
            calls = []
            def act(self, deterministic, **values):
                self.calls.append(dict(deterministic=deterministic, state=values['state'].clone()))
                action = torch.zeros(1, 39); action[:, 17] = values['state'][:, 0]
                return dict(action=action)
        class Pool:
            def __init__(self):
                self.observation = observation
                self.physics_step = 0
                self.environment = SimpleNamespace(action=None)
                self.scene = SimpleNamespace(snapshot=lambda: dict(physics_step=torch.tensor([self.physics_step])))
            def step(self, action):
                self.physics_step += 4
                self.environment.action = action.clone()
                self.observation = {key: value.clone() for key, value in self.observation.items()}
                self.observation['state'] += .1
                return self.observation, torch.zeros(1), torch.zeros(1), torch.tensor([False]), torch.tensor([False]), []
        class Capture:
            def __init__(self): self.rows = []
            def record(self, tick, *unused): self.rows.append(tick)
        return Policy(), Pool(), Capture(), {key: [] for key in native.FIELDS+('action',)}

    def test_each_tick_uses_new_preaction_observation_and_same_endpoint_action(self):
        import numpy as np
        policy, pool, capture, rows = self.fixture()
        native.policy_control_step(policy, pool, 0, capture, rows)
        native.policy_control_step(policy, pool, 1, capture, rows)
        self.assertEqual(capture.rows, [0, 1])
        self.assertTrue(all(call['deterministic'] is True for call in policy.calls))
        self.assertAlmostEqual(float(rows['state'][0][0]), .2, places=6)
        self.assertAlmostEqual(float(rows['state'][1][0]), .3, places=6)
        self.assertAlmostEqual(float(rows['action'][0][17]), .2, places=6)
        np.testing.assert_array_equal(rows['action'][-1], pool.environment.action[0].numpy())

    def test_bad_policy_action_and_skipped_endpoint_are_rejected(self):
        import torch
        policy, pool, capture, rows = self.fixture()
        with patch.object(policy, 'act', return_value=dict(action=torch.full((1, 39), float('nan')))):
            with self.assertRaises(ValueError):
                native.policy_control_step(policy, pool, 0, capture, rows)
        policy, pool, capture, rows = self.fixture()
        pool.physics_step = 4
        with self.assertRaises(ValueError):
            native.policy_control_step(policy, pool, 0, capture, rows)
        self.assertEqual(rows['state'], [])


if __name__ == '__main__':
    unittest.main()
