"""A 모델을 사용하지 않는 fresh 분포와 엄격 재개를 CPU에서 검사한다."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import torch
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
_entry=nested_input_paths();_entry.__enter__()
from guitar_learning.tool.experiments import fresh_variance as f
v=f.v


class FreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.saved=f.settings()
        fixture=v.ROOT.parents[1]/'index_full33_seed7_v1/100/train/J/training_contract.json'
        cls.contract=json.loads(fixture.read_text());cls.contract['structured_press']=cls.saved['structured_press']

    def make(self,size='small',kind=f.policy):
        kwargs=dict(size=size,contract=copy.deepcopy(self.contract),structured=self.saved['structured_press'])
        if kind is f.policy or kind is f.BASE_VARIANCE:kwargs['factor']=.1
        return kind(601,**kwargs)

    def test_no_A_load_initial_weights_rng_means_equal_only_four_std_change(self):
        torch.manual_seed(7);base=self.make(size='large',kind=v.BASE_POLICY);rng=torch.get_rng_state()
        torch.manual_seed(7)
        with patch.object(torch,'load',side_effect=AssertionError('fresh must not load A')):
            model=self.make(size='large');settings=f.settings()
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for key,x in base.state_dict().items():
            self.assertTrue(torch.equal(x,model.state_dict()[key]),key)
        data=(torch.zeros(2,601),torch.zeros(2,7,24),torch.ones(2,7,dtype=torch.bool),
            torch.zeros(2,8,24),torch.ones(2,8,dtype=torch.bool))
        a,b=base(*data),model(*data)
        self.assertTrue(torch.equal(a['mean'],b['mean']))
        others=list(range(17))+list(range(21,39))
        self.assertTrue(torch.equal(a['log_std'][:,others],b['log_std'][:,others]))
        self.assertTrue(torch.allclose(a['log_std'][:,17:21].exp()*.1,b['log_std'][:,17:21].exp()))
        self.assertTrue(torch.equal(a['reward_value'],b['reward_value']))
        self.assertTrue(torch.equal(a['cost_value'],b['cost_value']))
        self.assertEqual(int(model.active_mask.sum()),33)
        self.assertNotIn('structured_transfer',settings)

    def test_strict_resume_preserves_model_Adam_and_rng_and_rejects_old_policies(self):
        model=self.make();trainer=v.sp.StructuredTrainer(model)
        # 두 Adam의 비어 있지 않은 상태도 strict load가 실제 복원하는지 검사한다.
        for optimizer in (trainer.actor_optimizer,trainer.value_optimizer):
            optimizer.zero_grad()
            loss=sum(p.square().sum() for group in optimizer.param_groups for p in group['params'])
            loss.backward();optimizer.step()
        trainer.updates=100
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.pt';trainer.save(path)
            snapshot=torch.load(path,map_location='cpu',weights_only=False)
            other=self.make();loaded=v.sp.StructuredTrainer(other);loaded.load(path)
            target=Path(d)/'restored.pt';loaded.save(target);restored=torch.load(target,map_location='cpu',weights_only=False)
            for key in ('model','actor_optimizer','value_optimizer','updates','torch_rng','cuda_rng','numpy_rng','python_rng'):
                self.assertTrue(f.exact(snapshot[key],restored[key]),key)
            for kind in (v.BASE_POLICY,f.BASE_VARIANCE):
                with self.assertRaisesRegex(ValueError,'mismatch'):v.sp.StructuredTrainer(self.make(kind=kind)).load(path)

    def test_settings_flag_scope_and_factory_cleanup(self):
        for key in ('fresh_variance','variance_variant'):
            settings=copy.deepcopy(self.saved);settings.pop(key)
            with self.assertRaises(ValueError):f.validate(settings)
        settings=copy.deepcopy(self.saved);settings['structured_press']['stage']='B'
        with self.assertRaises(ValueError):f.validate(settings)
        before=v.VariancePolicy,v.official._pins,v.official._policy
        with self.assertRaises(RuntimeError):
            with f.runtime(self.saved):
                self.assertIs(v.VariancePolicy,f.policy)
                raise RuntimeError('cleanup')
        self.assertEqual(before,(v.VariancePolicy,v.official._pins,v.official._policy))
        with f.runtime(self.saved):pass
        self.assertEqual(before,(v.VariancePolicy,v.official._pins,v.official._policy))


if __name__=='__main__':unittest.main()
