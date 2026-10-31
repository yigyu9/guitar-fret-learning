"""가중치 고정·팔 학습·엄격 이전·동적 손가락 출력을 CPU에서 검사한다."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import torch
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
_entry=nested_input_paths();_entry.__enter__()
from guitar_learning.tool.experiments import arm_refinement as a
from guitar_learning.portability import portable
from guitar_learning.training.ppo import PPOConfig
v=a.v


class RefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.source=torch.load(v.TRANSFER,map_location='cpu',weights_only=False)
        cls.arch=v.localize(cls.source['identity']['architecture'])

    def model(self,size='small',stage='B'):
        with a.refinement_context(): settings=v.train_settings(.1)
        config=settings['structured_press']
        if stage=='free_v9':config=v.sp.load_configuration(config['geometry'],config['song'],stage)
        contract=copy.deepcopy(self.arch['contract']);contract['structured_press']=config
        return a.ArmRefinementPolicy(self.arch['state_dim'],size=size,contract=contract,structured=config,factor=.1),settings

    def data(self,n=8):
        return (torch.randn(n,self.arch['state_dim'])*.1,torch.randn(n,7,24)*.1,
            torch.ones(n,7,dtype=torch.bool),torch.randn(n,8,24)*.1,torch.ones(n,8,dtype=torch.bool))

    def test_frozen_function_and_std_survive_actual_PPO_but_arm_changes(self):
        model,_=self.model(size='large')
        model.initialize_from(v.TRANSFER,expected_sha256=v.digest(v.TRANSFER))
        data=self.data()
        actor={id(p) for p in model.actor_parameters()};value={id(p) for p in model.value_parameters()}
        self.assertFalse(actor & value)
        frozen={k:x.clone() for k,x in model.state_dict().items() if k.startswith(tuple(a.CONFIG['freeze_actor']))}
        with torch.no_grad():old=model.act(*data)
        buffer={k:x.reshape((2,4)+x.shape[1:]) for k,x in zip(('state','events','mask','priority_events','priority_mask'),data)}
        for key in ('latent','logp','reward_value','cost_value'):buffer[key]=old[key].reshape((2,4)+old[key].shape[1:])
        buffer.update(old_mean=old['mean'].reshape(2,4,39),old_log_std=old['log_std'].reshape(2,4,39),
            next_reward_value=torch.zeros(2,4),next_cost_value=torch.zeros(2,4),reward=torch.arange(8.).reshape(2,4)/10,
            cost=torch.zeros(2,4),terminated=torch.zeros(2,4,dtype=torch.bool),truncated=torch.zeros(2,4,dtype=torch.bool),
            valid=torch.ones(2,4,dtype=torch.bool),duration=torch.ones(2,4,dtype=torch.long))
        trainer=v.sp.StructuredTrainer(model,PPOConfig(epochs=1,minibatch_size=8,retry_lr_factor=.5))
        trainer.update(buffer)
        now=model(*data)
        self.assertTrue(torch.equal(old['mean'][:,17:33],now['mean'][:,17:33]))
        self.assertTrue(torch.equal(old['log_std'][:,17:33],now['log_std'][:,17:33]))
        self.assertFalse(torch.equal(old['mean'][:,:12],now['mean'][:,:12]))
        for key,x in frozen.items():self.assertTrue(torch.equal(x,model.state_dict()[key]),key)
        self.assertFalse(torch.equal(now['mean'][0,17:21],now['mean'][1,17:21]))
        self.assertEqual(int(model.active_mask.sum()),16)

    def test_initial_weights_and_rng_match_original_variance_constructor(self):
        torch.manual_seed(7);model,_=self.model(size='large')
        model.initialize_from(v.TRANSFER,expected_sha256=v.digest(v.TRANSFER));rng=torch.get_rng_state().clone()
        torch.manual_seed(7)
        settings=v.train_settings(.1);contract=copy.deepcopy(self.arch['contract']);contract['structured_press']=settings['structured_press']
        control=a.BASE_VARIANCE(self.arch['state_dim'],size='large',contract=contract,structured=settings['structured_press'],factor=.1)
        control.initialize_from(v.TRANSFER,expected_sha256=v.digest(v.TRANSFER))
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        actual=torch.load(a.CONTROL_INITIAL,map_location='cpu',weights_only=False)
        for key,x in model.state_dict().items():
            self.assertTrue(torch.equal(x,control.state_dict()[key]),key)
            self.assertTrue(torch.equal(x,actual['model'][key]),key)
        data=self.data();self.assertTrue(torch.equal(model(*data)['mean'],control(*data)['mean']))
        self.assertFalse(torch.equal(model(*data)['mean'][0,17:21],model(*data)['mean'][1,17:21]))
        self.assertTrue(torch.equal(model(*data)['log_std'],control(*data)['log_std']))

    def test_own_checkpoint_free_transfer_and_wrong_scope_rejection(self):
        model,settings=self.model(size='large');model.initialize_from(v.TRANSFER,expected_sha256=v.digest(v.TRANSFER))
        trainer=v.sp.StructuredTrainer(model,PPOConfig(**settings['ppo']))
        schedule=v.official.ExposureSchedule(settings['finger_skill']['planned_transitions'])
        pool=SimpleNamespace(environment=SimpleNamespace(sampler=SimpleNamespace(state_dict=lambda:{})))
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary);(out/'settings.json').write_text(json.dumps(portable(settings)))
            with a.refinement_context():
                pins=v.official._pins(settings,out)
                metadata=v.official.checkpoint_metadata(settings,schedule,pool,input_pins=pins,settings_path=out/'settings.json')
            path=out/'model.pt';trainer.save(path,metadata=metadata)
            free,_=self.model(size='large',stage='free_v9');free.initialize_from(path,expected_sha256=v.digest(path))
            self.assertEqual(int(free.active_mask.sum()),33)
            for key,x in model.state_dict().items():
                if key!='active_mask':self.assertTrue(torch.equal(x,free.state_dict()[key]),key)
            old=a.BASE_VARIANCE(self.arch['state_dim'],size='large',contract=model.architecture['contract'],structured=model.structured,factor=.1)
            with self.assertRaisesRegex(ValueError,'mismatch'):v.sp.StructuredTrainer(old).load(path)
        original=v.VariancePolicy
        try:
            with a.refinement_context():raise RuntimeError('test cleanup')
        except RuntimeError:pass
        self.assertIs(v.VariancePolicy,original)
        with self.assertRaisesRegex(ValueError,'settings required'):
            with a.refinement_context():
                settings=v.train_settings(.1);settings.pop('arm_only_refinement')
                with v.variant_runtime(settings):pass


if __name__=='__main__':unittest.main()
