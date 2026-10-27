"""Joint settings reject legacy actors and changed source task semantics."""
import copy
from pathlib import Path
import tempfile
import unittest

import torch

from guitar_learning.tool.experiments.joint.settings import settings_document
from guitar_learning.tests.test_joint_transfer import joint_settings


class JointSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_explicit_joint_schema_and_unchanged_native_source_semantics(self):
        with tempfile.TemporaryDirectory() as folder:
            raw,_=joint_settings(folder);settings=settings_document(raw)
            self.assertEqual(settings['specialist']['role'],'joint')
            self.assertEqual(settings['timing']['pre_roll_s'],3.)
            for changed in [dict(raw,joint={'schema':'unknown'}),dict(raw,specialist={'role':'left'}),
                dict(raw,joint_experts={'left_settings':raw['joint_experts']['left_settings']}),
                dict(raw,joint={'schema':raw['joint']['schema'],'preflight_gate':'relative.json'}),
                dict(raw,actor_initialization='legacy.pt'),dict(raw,musical_quality={'changed':True}),
                dict(raw,seed=9),dict(raw,tempo_scale=2.)]:
                with self.assertRaises(ValueError):settings_document(changed)
            changed=copy.deepcopy(raw);changed['timing']['stage_index']=2
            with self.assertRaises(ValueError):settings_document(changed)
            changed=copy.deepcopy(raw);changed['joint_experts']['right_settings']=changed['joint_experts']['left_settings']
            with self.assertRaises(ValueError):settings_document(changed)


if __name__=='__main__':unittest.main()
