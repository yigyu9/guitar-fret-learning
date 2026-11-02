"""CPU synthetic acceptance tests. No native scene, CUDA or physical claims."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from inputs import ROOT
sys.path.insert(0, str(ROOT))
from simultaneous import summarize


def metadata():
    return dict(schema='multi_press.trace.v1', evidence_kind='synthetic',
                audible_window_s=[3., 4.5], assigned_indices=list(range(12, 20)),
                arm_indices=list(range(12)), target_ids=['a', 'b'],
                preparation_status='ready', arrival_fit_status='found', execution_completed=True)


def trace(contact=lambda t: [True, True], end_step=1080):
    for step in range(end_step+1):
        now = step/240.
        yield dict(physics_step=4000+step, score_time_s=now,
                   candidate=contact(now), wrong=[False, False],
                   physical_failure=False, wrist_failure=False, guitar_escape=False,
                   actual_q105=[0.]*105, target105=[0.]*105,
                   wrist_G_pose7=[0., 0., 0., 0., 0., 0., 1.],
                   guitar_world_pose7=[0., 0., 0., 0., 0., 0., 1.])


class IntegrationTests(unittest.TestCase):
    def test_full_window_counts_360_intervals_with_left_endpoint(self):
        result = summarize(trace(), metadata())
        self.assertEqual(result['outcome'], 'simultaneous_hold_success')
        self.assertAlmostEqual(result['simultaneous_clean_s'], 1.5, places=12)
        self.assertFalse(result['physical_success_certified'])

    def test_two_individual_achievements_with_no_overlap_fail(self):
        result = summarize(trace(lambda t: [t < 3.75, t >= 3.75]), metadata())
        self.assertTrue(all(r['achieved'] for r in result['per_target']))
        self.assertEqual(result['simultaneous_clean_s'], 0.)
        self.assertEqual(result['outcome'], 'simultaneous_hold_failed')

    def test_one_target_success_cannot_be_pair_success(self):
        result = summarize(trace(lambda t: [True, False]), metadata())
        self.assertEqual(result['outcome'], 'individual_press_failed')
        self.assertEqual(result['simultaneous_fraction'], 0.)

    def test_wrong_break_and_reentry_require_two_valid_endpoints(self):
        rows = list(trace()); rows[840]['wrong'][1] = True
        result = summarize(rows, metadata())
        self.assertAlmostEqual(result['simultaneous_clean_s'], 1.5-2/240., places=12)
        self.assertAlmostEqual(result['wrong_any_s'], 1/240., places=12)
        self.assertEqual(result['outcome'], 'simultaneous_hold_failed')
        self.assertLess(result['longest_simultaneous_clean_s'], 1.5)

    def test_holes_duplicates_nonfinite_shapes_and_bad_start_are_errors(self):
        good = list(trace())
        bad = []
        bad.append(good[:800]+good[801:])
        bad.append(good[:800]+[good[799]]+good[800:])
        bad.append(good[1:])
        for field, value in [('candidate', [True]), ('score_time_s', float('nan')),
                             ('actual_q105', [0.]*104), ('wrist_G_pose7', [0.]*7)]:
            rows = copy.deepcopy(good); rows[800][field] = value; bad.append(rows)
        for rows in bad:
            with self.assertRaises(ValueError):
                summarize(rows, metadata())

    def test_early_failure_preserves_planned_denominator(self):
        rows = list(trace(end_step=800)); rows[-1]['physical_failure'] = True
        result = summarize(rows, metadata())
        self.assertEqual(result['outcome'], 'physical_or_wrist_failure')
        self.assertEqual(result['planned_duration_s'], 1.5)
        self.assertLess(result['simultaneous_fraction'], .23)
        rows[-1]['physical_failure'] = False
        self.assertEqual(summarize(rows, metadata())['outcome'], 'inspection_error')

    def test_failure_before_audible_never_succeeds(self):
        rows = list(trace()); rows[100]['guitar_escape'] = True
        self.assertEqual(summarize(rows, metadata())['outcome'], 'physical_or_wrist_failure')

    def test_geometry_and_preparation_failure_are_separate(self):
        info = metadata(); info['preparation_status'] = 'failed'
        self.assertEqual(summarize([], info)['outcome'], 'preparation_failed')
        info['preparation_status'] = 'geometry_unresolved'
        self.assertEqual(summarize([], info)['outcome'], 'preparation_geometry_unresolved')
        info['preparation_status'] = 'ready'; info['arrival_fit_status'] = 'unresolved'
        self.assertEqual(summarize([], info)['outcome'], 'arrival_geometry_unresolved')

    def test_tracking_and_motion_are_not_force_attribution(self):
        rows = list(trace())
        for row in rows[241:]:
            row['actual_q105'][12] = .2; row['target105'][12] = .3
            row['actual_q105'][0] = .01; row['wrist_G_pose7'][0] = .002
        result = summarize(rows, metadata())
        self.assertAlmostEqual(result['tracking']['assigned']['max_rad'], .1)
        self.assertAlmostEqual(result['motion']['assigned_actual_max_change_rad'], .2)
        self.assertAlmostEqual(result['motion']['wrist_relative_translation_max_m'], .002)


class ActiveEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(1)

    def setup_pair(self, same_string=False):
        import torch
        from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
        from guitar_learning.song.task import ScoreTask, ScoreTarget
        from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
        metadata, row = fixture(1)
        targets = tuple(ScoreTarget(str(i), str(i), 0 if same_string else i, 12+i if same_string else 12,
                                   i+2, 1, 0., 1.5, 0., 0., 1.5) for i in range(2))
        skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', exploration='independent',
                     hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
        with patch('guitar_learning.gpu.environment.make_task', return_value=ScoreTask(targets)):
            env = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
        env.set_evaluation(True, full_song=True); env.reset([0], row)
        # Isolate one actual pad sample per assigned finger; synthetic body poses only.
        env.surface_valid.zero_(); env.pad_valid.zero_(); env.pad_valid[1:3, 0] = True
        return env, row

    def placed(self, env, row):
        from guitar_learning.tests.test_gpu_environment import place_pad_sample, press_goal
        row = place_pad_sample(env, row, 2, press_goal(env, 0))
        return place_pad_sample(env, row, 3, press_goal(env, 1))

    def test_distinct_authorized_fingers_do_not_mark_each_other_wrong(self):
        env, row = self.setup_pair(); row = self.placed(env, row); env.reset([0], row)
        self.assertEqual(env.candidate.tolist(), [[True, True]])
        self.assertEqual(env.wrong.tolist(), [[False, False]])
        obs = env.observation()
        self.assertEqual(obs['state'].shape, (1, 557))
        self.assertTrue(obs['mask'][0, :2].all())
        self.assertEqual(obs['events'][0, :2, 9].tolist(), [1., 1.])

    def test_episode_requires_two_targets_but_latches_allow_nonoverlap(self):
        import torch
        env, row = self.setup_pair(); row = self.placed(env, row); env.reset([0], row)
        one = {k: v.clone() for k, v in row.items()}
        one['contact_force'][:, env.pad_indices[2]] = 0.
        two = {k: v.clone() for k, v in row.items()}
        two['contact_force'][:, env.pad_indices[1]] = 0.
        for tick in range(96):
            snapshot = one if tick < 45 else two
            env.begin_control(torch.zeros(1, 39))
            for _ in range(4):
                env.substep(dict(snapshot, physics_step=env.clock+1))
            env.end_control()
            if tick == 44:
                result = env._episode(0, False)
                self.assertEqual(result['song']['left_success_count'], 1)
                self.assertFalse(result['song']['stage_success'])
        self.assertEqual(env.note['left'].tolist(), [[True, True]])
        self.assertEqual(env.note['best_clean_streak'].shape, (1, 2))
        result = env._episode(0, False)['song']
        self.assertTrue(result['stage_success'])
        self.assertNotIn('simultaneous_clean_s', result)

    def test_score_rejects_two_independent_frets_on_same_string(self):
        with self.assertRaisesRegex(ValueError, 'conflicting audible targets'):
            self.setup_pair(same_string=True)


class GeometryContractTests(unittest.TestCase):
    def test_explicit_task_roundtrip_keeps_identical_audible_windows(self):
        from dataclasses import asdict
        import json
        from build_inputs import make_diagnostic_task
        from guitar_learning.song.task import ScoreTask, ScoreTarget
        from inputs import STUDY
        for case in json.loads((STUDY/'설계/cases.json').read_text())['cases']:
            task = make_diagnostic_task(case)
            rows = json.loads(json.dumps([asdict(t) for t in task.targets]))
            decoded = ScoreTask(tuple(ScoreTarget(**r) for r in rows))
            self.assertEqual(task.targets, decoded.targets)
            self.assertEqual([(t.onset_s, t.end_s) for t in task.targets], [(3., 4.5)]*2)

    def test_arrival_requires_identity_order_and_unit_poses(self):
        import json
        from common_pose import CommonPose, validate_arrival
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from inputs import STUDY, sha
        case = json.loads((STUDY/'설계/cases.json').read_text())['cases'][0]
        contract = load_gpu_prepared_reset_contract('left'); initial = contract['initial']
        state = copy.deepcopy(contract['state'])
        for name, row in zip(initial['human_body_names'], state['human_body_states']):
            row['body_name'] = name
        arrival = dict(schema='multi_press.arrival.v1', evidence_kind='synthetic', case_id=case['case_id'],
            target_ids=[r['target_id'] for r in case['targets']], joint_names=initial['joint_names'],
            human_body_names=initial['human_body_names'], physics_step=100, scene_id='cpu_fixture',
            body_names=dict(human=initial['human_body_names'], guitar=initial['guitar_body_names'], chair=['box']),
            source_sha256={str(TOOLS/'common_pose.py'): sha(TOOLS/'common_pose.py')},
            state=state, q105=[r['pos'] for r in state['human_dof_states']])
        validate_arrival(arrival, case, contract)
        planner = CommonPose(case, arrival)
        self.assertLess(planner.reproduction, 1e-10)
        bad = []
        for field, value in [('case_id', 'wrong'), ('joint_names', []), ('human_body_names', []),
                             ('source_sha256', {}), ('physics_step', True)]:
            item = copy.deepcopy(arrival); item[field] = value; bad.append(item)
        item = copy.deepcopy(arrival)
        item['state']['human_body_states'][0:2] = reversed(item['state']['human_body_states'][0:2]); bad.append(item)
        item = copy.deepcopy(arrival)
        item['state']['guitar_body_states'][0]['pose']['r'] = dict(x=0., y=0., z=0., w=2.); bad.append(item)
        item = copy.deepcopy(arrival); item['q105'][0] += .01; bad.append(item)
        for item in bad:
            with self.assertRaises(ValueError):
                validate_arrival(item, case, contract)

    def test_pins_never_replace_existing_expectations(self):
        from inputs import merge_pins
        pins = {'original': 'old'}
        merge_pins(pins, {'new': 'hash'})
        with self.assertRaises(ValueError):
            merge_pins(pins, {'original': 'changed'})
        self.assertEqual(pins['original'], 'old')

    def test_case_and_assigned_joint_invariants(self):
        import json
        import numpy as np
        from common_pose import CommonPose, validate_case
        from inputs import STUDY
        case = json.loads((STUDY/'설계/cases.json').read_text())['cases'][0]
        invalid = copy.deepcopy(case); invalid['targets'][1]['string'] = invalid['targets'][0]['string']
        with self.assertRaises(ValueError):
            validate_case(invalid)
        planner = CommonPose(case)
        q, result = planner.fit(planner.q0, planner.arm+planner.finger, .010, 1)
        after, _ = planner.fit(q, planner.finger, -.0005, 1)
        untouched = sorted(set(range(105))-set(planner.arm+planner.finger))
        np.testing.assert_array_equal(q[untouched], planner.q0[untouched])
        np.testing.assert_array_equal(q[planner.arm], after[planner.arm])
        self.assertFalse(result['native_verified'])


if __name__ == '__main__':
    unittest.main()
