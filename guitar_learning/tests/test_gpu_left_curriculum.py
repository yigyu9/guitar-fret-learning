"""CPU checks for the GPU per-finger curriculum; no simulator imports."""
import unittest

import numpy as np

from guitar_learning.song import curriculum as gpu
from guitar_learning.song import curriculum as cpu


def episode(counts=(25, 18, 12, 12), near=(1., 1., 1., 1.),
            contact=(0., 0., 0., 0.), success=(0., 0., 0., 0.), safe=True):
    return dict(full_safe=safe, finger_metrics=[dict(target_count=n,
        near_fraction=near[i], contact_fraction=contact[i], success_fraction=success[i])
        for i, n in enumerate(counts)])


class GpuLeftCurriculumTests(unittest.TestCase):
    def test_fixed_contract_and_positive_weight_interpolation(self):
        self.assertEqual((gpu.GPU_WINDOW, gpu.GPU_STATE_SIZE), (256, 3331))
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        expected = {0.: (.2, .5, .5), .5: (.15, .75, .75),
                    1.: (.1, 1., 1.), 1.5: (.075, 1., 1.5), 2.: (.05, 1., 2.)}
        for progress, values in expected.items():
            state.progress = progress
            for key, value in zip(('wrist', 'contact', 'timing'), values):
                self.assertAlmostEqual(state.weights()[key], value)
            self.assertEqual(state.weights()['approach'], 1.)
        config = gpu.gpu_default_config()
        self.assertEqual(config['schema'], 'guitar_learning.gpu_left_surface_curriculum.v1')
        self.assertEqual(config['min_episodes'], 256)
        self.assertEqual(config['near_distance_m'], .01)
        self.assertEqual(config['near_required_s'], .1)
        config['weights']['approach'][0] = 99
        self.assertEqual(gpu.gpu_default_config()['weights']['approach'], [1., 1., 1.])

    def test_wrist_only_and_partial_window_cannot_advance(self):
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        wrist_only = episode(near=(0.,) * 4)
        wrist_only.update(reach_fraction=1., contact_fraction=1.)
        state.observe([wrist_only] * 256)
        self.assertEqual(state.progress, 0.)
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.observe([episode()] * 255)
        self.assertEqual(state.progress, 0.)
        state.observe([episode()])
        self.assertEqual(state.progress, .1)

    def test_each_present_finger_is_required(self):
        for i in range(4):
            state = gpu.GPULeftCurriculum((25, 18, 12, 12))
            near = [1.] * 4
            near[i] = .19
            state.observe([episode(near=near)] * 256)
            self.assertEqual(state.progress, 0.)

    def test_absent_fingers_excluded_and_extra_log_field_allowed(self):
        counts = (1, 0, 2, 0)
        state = gpu.GPULeftCurriculum(counts)
        item = episode(counts, near=(.2, 0., .2, 0.))
        for finger in item['finger_metrics']:
            finger['clean_fraction'] = 0.
        result = state.observe([item] * 256)
        self.assertEqual(state.progress, .1)
        self.assertEqual([f['target_count'] for f in result['recent_fingers']], list(counts))
        self.assertEqual(result['recent_fingers'][1]['near_fraction'], 0.)

    def test_failures_are_zero_rows_and_safe_threshold_is_enforced(self):
        for failed, expected in ((25, .1), (26, 0.)):
            state = gpu.GPULeftCurriculum((25, 18, 12, 12))
            state.observe([episode()] * (256 - failed) + [episode(safe=False)] * failed)
            self.assertEqual(state.progress, expected)
            np.testing.assert_array_equal(state.window[-failed:], 0.)
            self.assertAlmostEqual(state.summary()['recent_safe_fraction'], (256 - failed) / 256)
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.observe([episode()] * 256)
        state.observe([episode(safe=False)])
        self.assertEqual(state.progress, .1)
        state.observe([])
        self.assertEqual(state.progress, .1)

    def test_stage_gates_maximum_step_and_no_demotion(self):
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.observe([episode()] * 1024)
        self.assertEqual(state.progress, .1)
        for _ in range(9):
            state.observe([episode()])
        self.assertEqual((state.progress, state.summary()['stage']), (1., 'contact'))
        state.observe([episode()])
        self.assertEqual(state.progress, 1.)
        # Stage1 uses contact, without requiring the earlier near metric again.
        contact = episode(near=(0.,) * 4, contact=(1.,) * 4)
        state.observe([contact] * 256)
        self.assertEqual(state.progress, 1.1)
        for _ in range(9):
            state.observe([contact])
        self.assertEqual((state.progress, state.summary()['stage']), (2., 'hold_transition'))
        state.observe([episode(safe=False)] * 256)
        self.assertEqual(state.progress, 2.)
        state.observe([contact] * 256)
        self.assertEqual(state.progress, 2.)

    def test_contact_gate_requires_every_present_finger(self):
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.progress = 1.
        state.observe([episode(contact=(1., 1., 1., .19))] * 256)
        self.assertEqual(state.progress, 1.)

    def test_checkpoint_restores_ring_and_continuation(self):
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.observe([episode()] * 260)
        state.observe([episode(safe=False)] * 11)
        restored = gpu.GPULeftCurriculum((25, 18, 12, 12))
        vector = state.state_vector()
        restored.load_state(vector)
        vector[:] = 0
        np.testing.assert_array_equal(restored.state_vector(), state.state_vector())
        self.assertEqual(restored.summary(), state.summary())
        for items in ([episode()], [episode(safe=False)] * 31, [episode()] * 256):
            self.assertEqual(restored.observe(items), state.observe(items))
            np.testing.assert_array_equal(restored.state_vector(), state.state_vector())

    def test_invalid_counts_and_episode_payloads_do_not_mutate(self):
        for counts in (None, (), (1, 2, 3), (0, 0, 0, 0), (1, -1, 0, 0),
                       (True, 0, 0, 0), (1., 0, 0, 0), (float('inf'), 0, 0, 0)):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                gpu.GPULeftCurriculum(counts)
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        bad = []
        for field, value in (('full_safe', 1), ('finger_metrics', [])):
            item = episode(); item[field] = value; bad.append(item)
        for field, value in (('target_count', 24), ('target_count', True),
                             ('near_fraction', float('nan')), ('contact_fraction', 1.1),
                             ('success_fraction', -.1), ('near_fraction', '1'),
                             ('near_fraction', True)):
            item = episode(); item['finger_metrics'][0][field] = value; bad.append(item)
        item = episode(); del item['finger_metrics'][0]['success_fraction']; bad.append(item)
        for item in bad:
            before = state.state_vector()
            with self.subTest(item=item), self.assertRaises(ValueError):
                state.observe([episode(), item])
            np.testing.assert_array_equal(state.state_vector(), before)

    def test_invalid_vectors_are_rejected_without_mutation(self):
        state = gpu.GPULeftCurriculum((25, 18, 12, 12))
        state.observe([episode()])
        before = state.state_vector()
        bad = [np.zeros(27), before.reshape(1, -1)]
        for index, value in ((0, float('nan')), (0, 2.1), (1, 1.5), (1, 257),
                             (2, .5), (2, 256), (2, 0), (3, .5),
                             (4, 1.1), (4, -.1), (3 + 13, 1.)):
            vector = before.copy(); vector[index] = value; bad.append(vector)
        vector = before.copy(); vector[3] = 0.; bad.append(vector)
        for vector in bad:
            with self.subTest(vector=vector[:15]), self.assertRaises(ValueError):
                state.load_state(vector)
            np.testing.assert_array_equal(state.state_vector(), before)

    def test_cpu_27_value_state_is_unchanged_and_not_gpu_compatible(self):
        self.assertEqual((cpu.CPU_WINDOW, cpu.CPU_STATE_SIZE), (8, 27))
        state = cpu.CPULeftCurriculum()
        state.observe([dict(full_safe=True, reach_fraction=1., contact_fraction=0.)] * 4)
        self.assertEqual(state.progress, .1)
        restored = cpu.CPULeftCurriculum()
        restored.load_state(state.state_vector())
        np.testing.assert_array_equal(restored.state_vector(), state.state_vector())
        with self.assertRaises(ValueError):
            gpu.GPULeftCurriculum((25, 18, 12, 12)).load_state(state.state_vector())
        with self.assertRaises(ValueError):
            restored.load_state(gpu.GPULeftCurriculum((25, 18, 12, 12)).state_vector())


if __name__ == '__main__':
    unittest.main()
