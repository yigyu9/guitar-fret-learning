"""소지 A200 엄격 이전·선택4축 분포·팩토리 복구를 CPU에서 검사한다."""
import copy
from pathlib import Path
import tempfile
import unittest
import torch
from torch.distributions import Normal,kl_divergence
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
_entry=nested_input_paths();_entry.__enter__()
from guitar_learning.tool.experiments import pinky_variance as p
v=p.v


class PinkyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.source=torch.load(p.TRANSFER,map_location='cpu',weights_only=False)

    def model(self,factor=.1):
        with p.pinky_context():settings=v.train_settings(factor)
        config=settings['structured_press'];contract=v.localize(copy.deepcopy(self.source['identity']['architecture']['contract']))
        contract['structured_press']=config
        model=v.VariancePolicy(601,size='large',contract=contract,structured=config,factor=factor)
        return model,settings

    def test_strict_source_transfer_and_pinky_four_axis_distribution(self):
        model,_=self.model();sha=v.digest(p.TRANSFER)
        model.initialize_from(p.TRANSFER,expected_sha256=sha)
        for key,x in self.source['model'].items():
            if key!='active_mask':self.assertTrue(torch.equal(x,model.state_dict()[key]),key)
        self.assertEqual(model.variance['selected_axes'],[29,30,31,32])
        base=v.BASE_POLICY(601,size='large',contract=model.architecture['contract'],structured=model.structured)
        base.load_state_dict(model.state_dict())
        data=(torch.zeros(2,601),torch.zeros(2,7,24),torch.ones(2,7,dtype=torch.bool),
            torch.zeros(2,8,24),torch.ones(2,8,dtype=torch.bool))
        old,new=base(*data),model(*data)
        self.assertTrue(torch.equal(old['mean'],new['mean']))
        self.assertTrue(torch.equal(old['log_std'][:,:29],new['log_std'][:,:29]))
        self.assertTrue(torch.allclose(new['log_std'][:,29:33].exp(),old['log_std'][:,29:33].exp()*.1))
        result=model.act(*data);active=model.active_mask
        normal=Normal(result['mean'][:,active],result['log_std'][:,active].exp());latent=result['latent'][:,active]
        correction=2*(torch.log(torch.tensor(2.))-latent-torch.nn.functional.softplus(-2*latent))
        self.assertTrue(torch.allclose(result['logp'],(normal.log_prob(latent)-correction).sum(-1),atol=2e-5))
        shifted=result['mean']+.001
        expected=kl_divergence(normal,Normal(shifted[:,active],result['log_std'][:,active].exp())).sum(-1)
        self.assertTrue(torch.allclose(model.analytic_kl(result['mean'],result['log_std'],shifted,result['log_std']),expected,atol=2e-5))
        self.assertEqual(sha,v.digest(p.TRANSFER))

    def test_constructor_rng_and_model_match_default_noise_control(self):
        torch.manual_seed(7);model,settings=self.model();model.initialize_from(p.TRANSFER,expected_sha256=v.digest(p.TRANSFER));rng=torch.get_rng_state()
        torch.manual_seed(7);base=v.BASE_POLICY(601,size='large',contract=model.architecture['contract'],structured=model.structured)
        base.initialize_from(p.TRANSFER,expected_sha256=v.digest(p.TRANSFER))
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for key,x in base.state_dict().items():self.assertTrue(torch.equal(x,model.state_dict()[key]),key)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'cp.pt';v.sp.StructuredTrainer(model).save(path)
            with self.assertRaisesRegex(ValueError,'mismatch'):v.sp.StructuredTrainer(base).load(path)

    def test_context_restores_and_factor_flag_rejects(self):
        before=v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins
        with self.assertRaises(RuntimeError):
            with p.pinky_context():
                self.assertEqual(v.TRANSFER,p.TRANSFER)
                with self.assertRaises(ValueError):v.train_settings(.05)
                with self.assertRaises(ValueError):
                    with v.variant_runtime({}):pass
                raise RuntimeError('cleanup')
        self.assertEqual(before,(v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins))
        with p.pinky_context():pass
        self.assertEqual(before,(v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins))


if __name__=='__main__':unittest.main()
