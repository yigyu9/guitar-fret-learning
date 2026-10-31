"""연구용 준비·기하 비교가 원본 안전·압현 판정을 바꾸지 않는지 검사한다."""
import copy
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.contact import pad_target_geometry
from guitar_learning.gpu.finger_reward import finger_preparation_gate
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment, REWARD_TERMS
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.tool.experiments.finger_ablation_contact import (
    FLAGS, ResearchEnvironment, nearest_pad_quality, preparation_gate)


def make(config=None, count=2):
    metadata, snapshot = fixture(count)
    metadata['finger_ablation'] = dict.fromkeys(FLAGS, False)
    metadata['finger_ablation'].update(config or {})
    skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', exploration='independent',
        hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
    env = ResearchEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
    return env, snapshot, env.reset(range(count), snapshot)


def gate_at(times, ends=(1., 4.), presses=(0., 3.)):
    now = torch.tensor(times, dtype=torch.float64)
    onset = torch.tensor(presses, dtype=torch.float64)
    end = torch.tensor(ends, dtype=torch.float64)
    finger = torch.ones(len(presses), dtype=torch.long)
    contact = torch.zeros(len(times), 4, dtype=torch.bool)
    distance = torch.ones(len(times), len(presses))
    return now, onset, end, onset, finger, contact, distance


class ContactAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_baseline_exact_reward_observation_safety_contract(self):
        research, snapshot, obs = make()
        metadata, _ = fixture()
        skill = dict(schema='guitar_learning.finger_skill.v3', phase='J', exploration='independent',
            hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
        base = FingerSkillEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
        old = base.reset(range(2), snapshot)
        for key in obs:
            torch.testing.assert_close(obs[key], old[key], rtol=0, atol=0)
        torch.testing.assert_close(research._surface_potential(), base._surface_potential(), rtol=0, atol=0)
        for key, value in research._finger_preparation(research._score_time()).items():
            torch.testing.assert_close(value, base._finger_preparation(base._score_time())[key], rtol=0, atol=0)
        contract = copy.deepcopy(research.contract)
        contract['reward'].pop('finger_ablation')
        self.assertEqual(contract, base.contract)
        self.assertEqual(tuple(research.episode_reward_terms), REWARD_TERMS)
        self.assertIs(ResearchEnvironment._apply_failure_cost, FingerSkillEnvironment._apply_failure_cost)
        self.assertIs(ResearchEnvironment._safety, FingerSkillEnvironment._safety)
        self.assertIs(ResearchEnvironment._contacts, FingerSkillEnvironment._contacts)

    def test_preparation_earlier_shared_gate_preserves_current_press(self):
        args = gate_at([.5, 1.5, 1.9, 2., 2.5, 3., 4.])
        old = finger_preparation_gate(*args)
        new = preparation_gate(*args)
        torch.testing.assert_close(new['gate'][:, 0], torch.tensor([0., 1., .5, 0., 0., 0., 0.], dtype=torch.float64))
        self.assertGreater(float(old['gate'][3, 0]), float(new['gate'][3, 0]))
        torch.testing.assert_close(new['tracking_weight'], 1-new['idle_weight'])
        # 모든 실제 압현 구간은 대기 보상이0이며 준비 가중치는1이다.
        self.assertTrue((new['tracking_weight'][[0, 5, 6], 0] == 1).all())

    def test_short_medium_gap_and_nonfinite_scope_unchanged(self):
        for next_press in (1.2, 1.4, 1.59):
            args = gate_at([1.05, 1.15, 1.25, 1.35], ends=(1., 3.), presses=(0., next_press))
            old, new = finger_preparation_gate(*args), preparation_gate(*args)
            for key in old:
                torch.testing.assert_close(old[key], new[key], rtol=0, atol=0)
        args = list(gate_at([1.9]))
        args[-1][:] = torch.nan
        result = preparation_gate(*args)
        self.assertTrue(result['nonfinite_veto'][0, 0])
        self.assertEqual(float(result['gate'][0, 0]), 0.)
        result = preparation_gate(*args, target_mask=torch.zeros(1, 2, dtype=torch.bool))
        self.assertFalse(result['nonfinite_veto'].any())

    def test_real_pad_geometry_same_witness_not_other_sample_normal(self):
        points = torch.zeros(1, 4, 2, 3)
        points[:, :, 0] = torch.tensor([.004, .02, .004])
        points[:, :, 1] = torch.tensor([.01, .02, 0.])
        normals = torch.zeros_like(points)
        normals[:, :, 0, 2] = 1.  # 최근접 표본은 잘못된 방향이다.
        normals[:, :, 1, 2] = -1.  # 다른 표본의 좋은 방향을 섞으면 안 된다.
        starts = torch.zeros(1, 6, 3)
        ends = starts.clone(); ends[..., 1] = 1.
        plane = torch.tensor([0., 0., 1., 0.])
        result = pad_target_geometry(points, normals, torch.zeros_like(points),
            torch.ones(4, 2, dtype=torch.bool), starts, ends, torch.zeros(1, 1),
            torch.full((1, 1), .04), torch.tensor([0]), torch.tensor([1]),
            torch.ones(1, 4, dtype=torch.bool), plane)
        self.assertEqual(int(result['sample_index'][0, 0]), 0)
        torch.testing.assert_close(result['delta'], torch.tensor([[[-.004, 0., -.004]]]))
        quality = nearest_pad_quality(result['delta'], result['normal_cos'],
            result['signed_height'], ends[:, :1]-starts[:, :1], plane)
        self.assertEqual(float(quality[0, 0]), 0.)
        self.assertFalse(result['positive'].any())
        # 같은 점의 방향만 고치면 위치 오차에 따른 유한 품질이 된다.
        quality = nearest_pad_quality(result['delta'], torch.ones_like(quality),
            result['signed_height'], ends[:, :1]-starts[:, :1], plane)
        torch.testing.assert_close(quality, torch.tensor([[1/(1+2/9)]]))

    def test_geometry_finite_far_preserved_near_penalty_bounded(self):
        env, _, _ = make(dict(geometry=True, preparation=True))
        self.assertTrue(torch.isfinite(env._surface_potential()).all())
        distance = torch.tensor([0., .005, .02, .04])
        near = (1-distance/.02).clamp(0, 1)
        self.assertTrue(((1-.7*near) >= .3-1e-7).all())
        torch.testing.assert_close((1-.7*near)[2:], torch.ones(2))
        # 연구 설정은 독립적으로 명시되며 원본 종료 계약은 건드리지 않는다.
        self.assertTrue(env.contract['reward']['finger_ablation']['flags']['geometry'])
        baseline, _, _ = make()
        self.assertEqual(env.contract['termination'], baseline.contract['termination'])
        self.assertEqual(env.contract['task']['contact_measurement'], baseline.contract['task']['contact_measurement'])

    def test_shared_observation_gate_and_original_pbrs_terminal(self):
        env, snapshot, _ = make(dict(preparation=True, geometry=True))
        # 제어 끝점에서 관측에 저장된 gate와 보상·추종이 읽는 gate는 같다.
        def advance(failed=False):
            env.begin_control(torch.zeros(2, 39))
            for _ in range(4):
                env.substep(dict(snapshot, physics_step=env.clock+1))
            if failed:
                env.tick_failure[:, 0] = True
            return env.end_control()
        advance()
        torch.testing.assert_close(env.preparation_gate,
            env._finger_preparation(env._score_time())['gate'])
        with patch.object(env, '_surface_potential', side_effect=[torch.full((2,), .8), torch.full((2,), .2)]):
            advance()
        torch.testing.assert_close(env.terms['song_left_approach'], torch.full((2,), .99*.2-.8))
        with patch.object(env, '_surface_potential', side_effect=[torch.full((2,), .8), torch.full((2,), .9)]):
            _, _, cost, done, _, _ = advance(failed=True)
        torch.testing.assert_close(env.terms['song_left_approach'], torch.full((2,), -.8))
        self.assertTrue(done.all())
        self.assertTrue((cost >= 5).all())

    def test_unknown_or_nonboolean_research_config_rejected(self):
        metadata, _ = fixture()
        for config in (None, {}, dict.fromkeys(FLAGS, 1), dict(dict.fromkeys(FLAGS, False), extra=False)):
            metadata['finger_ablation'] = config
            with self.assertRaisesRegex(ValueError, 'five boolean'):
                ResearchEnvironment(metadata)


if __name__ == '__main__':
    unittest.main()
