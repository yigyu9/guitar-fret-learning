"""Pure CPU fake-native checks; never import Isaac Gym, Torch or GL."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('solver_variant', Path(__file__).with_name('probe_solver_variant.py'))
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def params():
    return NS(dt=1/240., substeps=1, gravity=(0,0,-9.81),
        physx=NS(num_position_iterations=4, num_velocity_iterations=2, solver_type=1))


class FakeGym:
    marker = 'forwarded'
    def create_sim(self, *args):
        self.args = args
        self.actual = copy.deepcopy(args[-1])
        return 'sim'
    def get_sim_params(self, sim):
        assert sim == 'sim'
        return self.actual
    def destroy_sim(self, sim):
        assert sim == 'sim'
        self.destroyed = getattr(self,'destroyed',0)+1


class SolverVariantTests(unittest.TestCase):
    def test_only_position_iterations_changed_and_actual_readback_recorded(self):
        gym, records, original = FakeGym(), [], params()
        before = copy.deepcopy(vars(original)); before['physx'] = vars(original.physx).copy()
        proxy = tool.GymProxy(gym, records)
        self.assertEqual(proxy.marker, 'forwarded')
        self.assertEqual(proxy.create_sim(0,-1,'physx',original), 'sim')
        self.assertEqual(gym.args[:3], (0,-1,'physx'))
        after = vars(original).copy(); after['physx'] = vars(original.physx).copy()
        before['physx']['num_position_iterations'] = 16
        self.assertEqual(before, after)
        self.assertEqual(records[0]['requested_before']['position_iterations'],4)
        self.assertEqual(records[0]['actual_readback']['position_iterations'],16)
        with self.assertRaises(ValueError): proxy.create_sim(0,-1,'physx',params())

    def test_wrong_baseline_rejected_before_create(self):
        for field, value in (('position',8),('velocity',4),('dt',1/120.),('substeps',2)):
            gym, original = FakeGym(), params()
            if field == 'position': original.physx.num_position_iterations = value
            elif field == 'velocity': original.physx.num_velocity_iterations = value
            else: setattr(original, field, value)
            with self.assertRaises(ValueError): tool.GymProxy(gym,[]).create_sim(0,-1,'physx',original)
            self.assertFalse(hasattr(gym,'args'))

    def test_native_readback_must_confirm_override(self):
        class IgnoresOverride(FakeGym):
            def get_sim_params(self, sim): return params()
        class QueryFails(FakeGym):
            def get_sim_params(self, sim): raise RuntimeError('readback failed')
        for gym, error in ((IgnoresOverride(),ValueError),(QueryFails(),RuntimeError)):
            with self.assertRaises(error): tool.GymProxy(gym,[]).create_sim(0,-1,'physx',params())
            self.assertEqual(gym.destroyed,1)

    def test_report_pins_new_contract_and_patch_restoration_without_sdk(self):
        gym = FakeGym(); acquire = lambda:gym
        api = NS(acquire_gym=acquire); old_write = tool.base.write
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            def fake_main():
                tool.base.write(out/'settings.json',dict(num_envs=6))
                tool.base.write(out/'inputs_before.json',{str(out/'settings.json'):tool.base.sha(out/'settings.json')})
                api.acquire_gym().create_sim(0,-1,'physx',params())
                tool.base.write(out/'training_contract.json',dict(schema='original'))
                tool.base.write(out/'report.json',dict(completed=True,changed_inputs=[]))
                return 0
            with patch.dict(sys.modules,{'isaacgym':NS(gymapi=api)}), patch.object(tool.base,'main',fake_main):
                self.assertEqual(tool.main(),0)
            self.assertIs(api.acquire_gym,acquire); self.assertIs(tool.base.write,old_write)
            contract = json.loads((out/'training_contract.json').read_text())
            report = json.loads((out/'report.json').read_text())
            before = json.loads((out/'inputs_before.json').read_text())
            after = json.loads((out/'inputs_after.json').read_text())
            self.assertEqual(contract['schema'],tool.SCHEMA)
            self.assertEqual(contract['source_training_contract']['schema'],'original')
            self.assertTrue(report['completed']); self.assertEqual(before,after)
            self.assertIn(str(Path(tool.__file__).resolve()),before)
            self.assertEqual(report['runtime_override']['native_create_sim_records'][0]['actual_readback']['position_iterations'],16)
            self.assertTrue((out/'runtime_override_contract.json').is_file())


if __name__ == '__main__':
    unittest.main()
