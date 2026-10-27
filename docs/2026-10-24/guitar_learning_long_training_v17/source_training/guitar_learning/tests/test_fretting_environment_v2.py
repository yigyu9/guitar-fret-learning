"""CPU sampling/lifecycle integration; fake dynamics are not a contact trial."""
import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np
from .test_environment_v4 import FakeSession
from .test_geometry_v1 import fixture, body
from guitar_learning.core.fretting_v1 import FretTarget, FretContract
from guitar_learning.tool.validation.fretting_environment import FrettingEnvironment


class ContactSession(FakeSession):
    def __init__(self, config, out):
        super().__init__(config, out)
        self.state, humans, guitars = fixture()
        humans.append('LH:index2')
        self.state['human_body_states'].append(body([.025, .801, 0]))
        self.scene.human_bodies, self.scene.guitar_bodies = humans, guitars
        previous = self.scene.native
        def native():
            result = copy.deepcopy(self.state)
            result.update(previous())
            return result
        self.scene.native = native


def contacts(scene):
    if scene.steps >= 483:
        return []
    return [dict(body0_name='guitar/G:fret5', body1_name='human/LH:index2',
                 localPos0=dict(x=.025, y=.001, z=0),
                 localPos1=dict(x=0, y=0, z=0), **{'lambda': 1.})]


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environment = FrettingEnvironment({}, Path(self.folder.name), action_half_range_rad=.002,
                    session_factory=ContactSession, contact_reader=contacts,
                    fret_target=FretTarget(1, 5, 'index'), fret_contract=FretContract(.05),
                    note_start_step=480, note_end_step=484)

    def tearDown(self):
        self.environment.close()
        self.folder.cleanup()

    def test_every_physics_sample_and_measured_loss_are_recorded(self):
        sample, metadata = self.environment.reset()
        self.assertTrue(sample['fretting_measurement']['fretting_contact_candidate'])
        self.assertIsNone(sample['fretting_progress']['intentional_music_release'])
        _, info = self.environment.step(np.zeros(39))
        samples = info['physics_samples240']
        self.assertEqual([s['native_contacts']['physics_step'] for s in samples], [481, 482, 483, 484])
        self.assertEqual([s['fretting_progress']['fretting_contact_candidate'] for s in samples], [True, True, False, False])
        self.assertTrue(samples[2]['fretting_progress']['measured_contact_release'])
        self.assertEqual(samples[-1]['fretting_progress']['note_contact_hold_fraction'], .5)
        self.assertEqual(self.environment.session.preparation_calls, 120)
        self.assertEqual(self.environment.session.policy_calls, 1)

    def test_reset_starts_fresh_tracking_and_closes_old_session(self):
        self.environment.reset()
        first = self.environment.session
        self.environment.step(np.zeros(39))
        sample, _ = self.environment.reset()
        self.assertTrue(first.closed)
        self.assertEqual(sample['fretting_progress']['consecutive_valid_span_s'], 0)
        self.assertEqual(sample['fretting_progress']['note_observed_coverage_fraction'], 0)

    def test_contact_reader_cannot_modify_physical_state(self):
        def corrupt(scene):
            self.environment.session.q[0] += .1
            return []
        self.environment.contact_reader = corrupt
        with self.assertRaisesRegex(RuntimeError, 'Contact query changed'):
            self.environment.reset()


if __name__ == '__main__':
    unittest.main()
