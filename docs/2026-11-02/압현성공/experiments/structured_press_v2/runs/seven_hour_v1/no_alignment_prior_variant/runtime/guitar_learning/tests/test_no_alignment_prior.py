"""팔 bias 외 초기 동일성과 저장 모델의 정상 복원을 CPU에서 검증한다."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import torch
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
_entry=nested_input_paths();_entry.__enter__()
from guitar_learning.tool.experiments import no_alignment_prior as n


class PriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        settings=n.sp.build_settings('virtual_finger_v9_index_s3_f4','free_v9',
            n.ROOT/'guitar_learning/assets/structured_press_v2/catalog.json')
        cls.config=settings['structured_press']
        fixture=n.ROOT.parents[1]/'index_full33_seed7_v1/100/train/J/training_contract.json'
        cls.contract=json.loads(fixture.read_text())
        cls.contract['structured_press']=cls.config

    def model(self,kind):
        return kind(557+n.sp.EXTRA_DIM,size='small',contract=copy.deepcopy(self.contract),structured=self.config)

    def test_only_initial_arm_bias_changes_without_random_consumption(self):
        torch.manual_seed(7);base=self.model(n.BASE_POLICY);rng=torch.get_rng_state().clone()
        torch.manual_seed(7);model=self.model(n.NoAlignmentPriorPolicy)
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for key,value in base.state_dict().items():
            expected=value.clone()
            if key=='core.support_head.bias':expected[:12]=0
            self.assertTrue(torch.equal(expected,model.state_dict()[key]),key)
        data=(torch.zeros(4,601),torch.zeros(4,7,24),torch.ones(4,7,dtype=torch.bool),
            torch.zeros(4,8,24),torch.ones(4,8,dtype=torch.bool))
        old,new=base(*data),model(*data)
        self.assertTrue(torch.equal(old['mean'][:,12:],new['mean'][:,12:]))
        self.assertFalse(torch.equal(old['mean'][:,:12],new['mean'][:,:12]))
        for key in ('log_std','reward_value','cost_value'):self.assertTrue(torch.equal(old[key],new[key]),key)
        self.assertEqual(int(model.active_mask.sum()),33)

    def test_strict_resume_restores_learned_bias_and_rejects_original_schema(self):
        model=self.model(n.NoAlignmentPriorPolicy)
        with torch.no_grad():model.core.support_head.bias[:12].fill_(.123)
        trainer=n.sp.StructuredTrainer(model)
        with tempfile.TemporaryDirectory() as temp:
            checkpoint=Path(temp)/'model.pt';trainer.save(checkpoint)
            restored=self.model(n.NoAlignmentPriorPolicy);n.sp.StructuredTrainer(restored).load(checkpoint)
            self.assertTrue(torch.equal(model.core.support_head.bias,restored.core.support_head.bias))
            with self.assertRaisesRegex(ValueError,'mismatch'):
                n.sp.StructuredTrainer(self.model(n.BASE_POLICY)).load(checkpoint)

    def test_factory_flag_required_and_all_factories_restored(self):
        previous=n.sp.StructuredPolicy,n.sp.build_settings,n.sp.structured_runtime,n.official._pins,n.official._policy
        with self.assertRaisesRegex(RuntimeError,'cleanup'):
            with n.no_prior_context():
                settings=n.sp.build_settings('virtual_finger_v9_index_s3_f4','free_v9',
                    n.ROOT/'guitar_learning/assets/structured_press_v2/catalog.json')
                self.assertEqual(settings['no_alignment_prior'],n.CONFIG)
                with n.sp.structured_runtime(self.config):
                    with self.assertRaisesRegex(ValueError,'flag required'):
                        n.official._policy({},SimpleNamespace())
                    raise RuntimeError('cleanup')
        self.assertEqual(previous,(n.sp.StructuredPolicy,n.sp.build_settings,n.sp.structured_runtime,n.official._pins,n.official._policy))
        with n.no_prior_context():pass
        self.assertEqual(previous,(n.sp.StructuredPolicy,n.sp.build_settings,n.sp.structured_runtime,n.official._pins,n.official._policy))


if __name__=='__main__':unittest.main()
