"""손가락별 진행 관측의 CPU 검사. 실제 도달·압현 성공을 증명하지 않는다."""
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.finger_progress import (
    FingerProgressEnvironment, FINGER_PROGRESS_FIELDS, FINGER_PROGRESS_SCHEMA,
    allocate_progress, reset_progress, advance_progress, progress_observation, progress_contract)
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.song.task import ScoreTarget, SongTask
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.tests import test_finger_skill_environment as skill_fixtures


class FingerProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def data(self, count=2):
        # 검지는 뒤에 준비하고, 중지는 먼저 유지한다. 검지의 다음 음도 포함한다.
        return dict(onset=torch.tensor([4., 1., 7.], dtype=torch.float64),
            end=torch.tensor([6., 5., 8.], dtype=torch.float64),
            press=torch.tensor([4., 1., 7.], dtype=torch.float64),
            finger=torch.tensor([1, 2, 1]), scope=torch.ones(count, 3, dtype=torch.bool),
            candidate=torch.tensor([[False, True, False]]*count),
            wrong=torch.zeros(count, 3, dtype=torch.bool), ready=torch.ones(count, 4, dtype=torch.bool))

    def tick(self, state, time, **data):
        now = torch.full_like(state['last_time'], time)
        return advance_progress(state, now=now, **data)

    def test_index_prepares_while_middle_holds(self):
        data = self.data(); state = allocate_progress(2)
        state = self.tick(state, 2.5, **data)
        self.assertEqual(state['phase'][0].tolist(), [2, 4, 0, 0])
        self.assertEqual(state['target'][0].tolist(), [0, 1, -1, -1])
        self.assertGreater(float(state['clean_run'][0, 1]), 0.)

    def test_index_changes_without_resetting_middle_timer(self):
        data = self.data(); data['end'][0] = 3.
        state = self.tick(allocate_progress(2), 2.999, **data)
        before = state['target_elapsed'][:, 1].clone()
        # 검지의 미래 목표를 준비 창에 넣고, 검지 앞 음만 종료한다.
        data['press'][2] = 5.; data['onset'][2] = 5.
        state = self.tick(state, 3.001, **data)
        self.assertEqual(state['target'][0, 0].item(), 2)
        torch.testing.assert_close(state['target_elapsed'][:, 1], before+.002)
        self.assertEqual(state['phase'][0, 1].item(), 4)

    def test_middle_ends_without_resetting_index_hold(self):
        data = self.data(); data['candidate'][:, 0] = True
        state = self.tick(allocate_progress(2), 4.999, **data)
        before = state['clean_run'][:, 0].clone()
        state = self.tick(state, 5.001, **data)
        self.assertEqual(state['phase'][0, :2].tolist(), [4, 5])
        torch.testing.assert_close(state['clean_run'][:, 0], before+.002)

    def test_audible_current_beats_future_and_next_prepare_beats_release(self):
        data = self.data(); data['onset'][0] = 1.; data['press'][0] = 1.
        data['end'][0] = 3.; data['onset'][2] = 3.; data['press'][2] = 3.
        state = self.tick(allocate_progress(2), 2.5, **data)
        self.assertEqual(state['target'][0, 0].item(), 0)
        state = self.tick(state, 3.001, **data)
        self.assertEqual(state['target'][0, 0].item(), 2)
        self.assertEqual(state['phase'][0, 0].item(), 3)

    def test_partial_reset_and_inactive_rows_preserve_other_state(self):
        data = self.data(); state = self.tick(allocate_progress(2), 2.5, **data)
        old = {k:v.clone() for k,v in state.items()}
        reset_progress(state, torch.tensor([0]), torch.tensor([0., 2.5]))
        for key in state: torch.testing.assert_close(state[key][1], old[key][1])
        self.assertTrue((state['target'][0] == -1).all())
        state = self.tick(state, 2.6, active=torch.tensor([True, False]), **data)
        for key in state: torch.testing.assert_close(state[key][1], old[key][1])

    def test_empty_score_and_unassigned_fingers_are_finite_idle(self):
        data = self.data()
        for key in ('onset', 'end', 'press', 'finger'): data[key] = data[key][:0]
        for key in ('scope', 'candidate', 'wrong'): data[key] = data[key][:, :0]
        state = self.tick(allocate_progress(2), 1., **data)
        self.assertTrue((state['target'] == -1).all())
        observation = progress_observation(state, torch.ones(2), data['onset'], data['end'], data['press'])
        self.assertEqual(observation.shape, (2, 56))
        self.assertTrue(torch.isfinite(observation).all())

    def test_clean_requires_own_audible_time_and_no_wrong(self):
        data = self.data(); data['candidate'].fill_(True); data['wrong'][:, 1] = True
        state = self.tick(allocate_progress(2), 2.5, **data)
        self.assertNotEqual(state['phase'][0, 0].item(), 4)  # 검지는 아직 미래 음이다.
        self.assertEqual(state['phase'][0, 1].item(), 3)
        self.assertTrue((state['clean_run'] == 0).all())

    def test_horizon_boundary_and_duplicate_observation_do_not_reset(self):
        data = self.data(); state = self.tick(allocate_progress(2), 2.5, **data)
        for _ in range(32): state = self.tick(state, float(state['last_time'][0])+1/240., **data)
        old = {k:v.clone() for k,v in state.items()}
        progress_observation(state, state['last_time'], data['onset'], data['end'], data['press'])
        again = self.tick(state, float(state['last_time'][0]), **data)
        for key in state: torch.testing.assert_close(state[key], old[key]); torch.testing.assert_close(again[key], old[key])
        self.assertGreater(float(state['clean_run'][0, 1]), .13)

    def test_own_alignment_loss_does_not_clear_other_alignment(self):
        data = self.data(); data['onset'][1] = 4.; data['press'][1] = 4.
        state = self.tick(allocate_progress(2), 2.5, **data)
        before = state['aligned_run'][:, 1].clone()
        data['ready'][:, 0] = False
        state = self.tick(state, 2.502, **data)
        self.assertEqual(state['phase'][0, :2].tolist(), [1, 2])
        self.assertTrue((state['aligned_run'][:, 0] == 0).all())
        torch.testing.assert_close(state['aligned_run'][:, 1], before+.002)

    def test_contract_observation_layout_and_reward_methods_are_explicit(self):
        spec = progress_contract(67)
        self.assertEqual(len(spec['fields']), 56)
        self.assertEqual(len(spec['scales']), 56)
        for finger in range(4): self.assertEqual(spec['scales'][finger*14+7], 66.)
        for name in ('_reward_components', '_surface_potential', '_apply_failure_cost',
                     '_safety', '_left_wrong_contacts', '_finger_preparation'):
            self.assertIs(getattr(FingerProgressEnvironment, name), getattr(FingerSkillEnvironment, name))

    def environment(self, cls):
        metadata, snapshot = fixture(2)
        def target(name, finger, onset, end):
            return ScoreTarget(name, name, finger, 6, finger, 1, onset, end, onset, onset-3., end-3.)
        task = SongTask((target('middle', 2, 3., 5.), target('index', 1, 4., 6.)),
            lookahead_s=4., episode_duration_s=6.5)
        with patch('guitar_learning.gpu.environment.make_task', return_value=task):
            env = cls(metadata, bundle=BUNDLE, song=SONG, device='cpu',
                skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                    hold_ticks=1, exploration='independent', planned_transitions=400, full_song_after=100))
        env.set_evaluation(True, full_song=True)
        env.reset(range(2), snapshot)
        return env, snapshot

    def test_environment_extends_observation_without_changing_reward_or_ledger(self):
        class ExistingE4(FingerSkillEnvironment):
            natural_preparation = dict(schema='guitar_learning.natural_preparation.v3', condition='E4')
        base, snapshot = self.environment(ExistingE4)
        env, _ = self.environment(FingerProgressEnvironment)
        self.assertEqual(env.contract['finger_progress']['schema'], FINGER_PROGRESS_SCHEMA)
        self.assertEqual(env.contract['observation']['dimension'], 613)
        self.assertEqual(env.contract['observation']['fields'][-56:], list(FINGER_PROGRESS_FIELDS))
        self.assertEqual(env.contract['reward'], base.contract['reward'])
        for _ in range(32):
            first = skill_fixtures.FingerSkillEnvironmentTests.advance(base, snapshot)
            second = skill_fixtures.FingerSkillEnvironmentTests.advance(env, snapshot)
            for key in ('state',):
                torch.testing.assert_close(second[0][key][:, :557], first[0][key], rtol=0, atol=0)
            for i in (1, 2, 3, 4): torch.testing.assert_close(second[i], first[i], rtol=0, atol=0)
            for key in base.note: torch.testing.assert_close(env.note[key], base.note[key], rtol=0, atol=0)
        self.assertTrue(torch.isfinite(env.observation()['state']).all())
        old = {k:v[1].clone() for k,v in env.finger_progress.items()}
        env.reset([0], snapshot)
        for key,value in old.items(): torch.testing.assert_close(env.finger_progress[key][1], value, rtol=0, atol=0)
        episode = env._episode(1, False)
        self.assertEqual(len(episode['finger_progress']['phase_seconds']), 4)
        self.assertEqual(episode['finger_progress']['source_target_ids'], ['middle', 'index'])


if __name__ == '__main__': unittest.main()
