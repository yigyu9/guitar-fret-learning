"""새 자연스러운 압현 실행기의 조건 격리·직접각·엄격 이전·복구 CPU 검사."""
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.training import finger_skill_runner as runner, rollout, ppo
from guitar_learning.portability import portable, settings_digest, PATH_SCHEMA


SONG = 'virtual_finger_v9_middle_s3_f6'


def make(condition='E0', distribution='aligned', axes='goal4'):
    settings = natural.build_settings(SONG, condition, distribution, axes, size='small')
    config = settings['natural_press']
    class Environment(natural.NaturalEnvironment):
        natural_press = config
        natural_preparation = dict(schema='guitar_learning.natural_preparation.v3',condition=condition)
    metadata, snapshot = fixture(2)
    environment = Environment(metadata,bundle=natural.ROOT/'data/song_bundles'/SONG,
        song=settings['song'],skill=settings['finger_skill'],device='cpu',hand='left')
    environment.reset([0,1],snapshot)
    policy = natural.NaturalPolicy(601,size='small',contract=environment.contract,natural_press=config)
    return settings, environment, policy


class NaturalRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_catalog_and_exact_condition_settings(self):
        provenance = natural.verify_catalog()
        self.assertEqual(len(provenance['active_physical_inputs']),144)
        self.assertEqual(len(provenance['historical_creation_only']),1)
        baseline = natural.build_settings(SONG)
        for condition in natural.CONDITIONS:
            settings = natural.build_settings(SONG,condition)
            settings['natural_press']['condition'] = 'E0'
            self.assertEqual(settings,baseline)
        for axes,count in (('goal4',4),('arm16',16),('full33',33)):
            config = natural.load_configuration(SONG,'E0','v9',axes)
            self.assertEqual(len(config['active_axes']),count)
            self.assertFalse(config['phase_arm_support'])
        wrong = copy.deepcopy(baseline['natural_press']);wrong['finger_std_floor'] = .01
        with self.assertRaises(ValueError):natural.validate_config(wrong)

    def test_observation_policy_distribution_and_free_goal_all_phases(self):
        for condition in natural.CONDITIONS:
            settings, environment, policy = make(condition)
            self.assertEqual(environment.contract['observation']['dimension'],601)
            self.assertEqual(environment.contract['reward']['natural_preparation']['condition'],condition)
            self.assertFalse(policy.core.support_head.weight.requires_grad)
            self.assertTrue(policy.core.finger_heads['middle'][-1].weight.requires_grad)
            self.assertFalse(policy.core.finger_heads['index'][-1].weight.requires_grad)
            for phase in (0,1,2):
                environment.motion_phase.fill_(phase)
                obs = environment.observation()
                result = policy.act(*(obs[k] for k in rollout.FIELDS),deterministic=False)
                self.assertEqual(result['action'].shape,(2,39))
                self.assertTrue(torch.isfinite(result['logp']).all())
                self.assertTrue(torch.equal(result['action'],result['latent'].tanh()))
                self.assertTrue(torch.allclose(result['log_std'][:,21:25].exp(),torch.full((2,4),.15)))
                self.assertEqual(policy._active_mask().nonzero().flatten().tolist(),[21,22,23,24])
        _,_,policy = make(axes='arm16')
        self.assertTrue(policy.core.support_head.weight.requires_grad)

    def test_factory_restoration_including_exception(self):
        original = runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner.checkpoint_metadata,runner._pins
        config = natural.load_configuration(SONG)
        for error in (False,True):
            try:
                with natural.natural_runtime(config):
                    self.assertIs(rollout.GpuPool,natural.NaturalPool)
                    if error:raise RuntimeError('복구 검사')
            except RuntimeError:pass
            self.assertEqual(original,(runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner.checkpoint_metadata,runner._pins))

    def test_execution_uses_fixed_hold_not_phase_relatch(self):
        config = natural.load_configuration(SONG,'E0','v9','goal4')
        pool = natural.NaturalPool.__new__(natural.NaturalPool)
        pool.natural_press = config
        fixed = torch.full((2,39),.3)
        pool.execution_hold_action = fixed
        env = SimpleNamespace(action_min=torch.full((2,39),float('inf')),action_max=torch.full((2,39),-float('inf')),
            hold_action=torch.full((2,39),-.9),last_applied_action=torch.zeros(2,39),observation=lambda:{'state':'next'})
        pool.environment = env
        pool.controller = SimpleNamespace(target=torch.zeros(2,39),active=torch.arange(39),reference=torch.zeros(39),
            action_low=-torch.ones(39),action_high=torch.ones(39))
        actions = torch.full((2,39),.8);captured=[]
        def step(self,value):captured.append(value.clone());return ({},None,None,None)
        with patch.object(rollout.GpuPool,'step',step):
            for phase in (0,1,2):
                env.motion_phase = torch.full((2,),phase)
                pool.step(actions)
        for executed in captured:
            self.assertTrue(torch.equal(executed[:,:12],fixed[:,:12]))
            self.assertTrue(torch.equal(executed[:,21:25],actions[:,21:25]))
        self.assertTrue(all(torch.equal(captured[0],value) for value in captured))

    def test_v9_goal4_reset_moves_arm_toward_fixed_ik_only(self):
        config = natural.load_configuration(SONG,'E0','v9','goal4')
        catalog,goal = natural.catalog_goal(config)
        reference = torch.tensor(catalog['reference105'])
        active = torch.tensor(catalog['action_indices'])
        pool = natural.NaturalPool.__new__(natural.NaturalPool)
        pool.natural_press,pool.num_envs = config,2
        pool.scene = SimpleNamespace(device='cpu',initial_hold=reference.expand(2,-1).clone(),initial_is_v9=torch.ones(2,dtype=torch.bool))
        env = SimpleNamespace(hold_action=torch.zeros(2,39),last_applied_action=torch.zeros(2,39),
            previous_action=torch.zeros(2,39),start_v9=torch.zeros(2,dtype=torch.bool),observation=lambda:{})
        pool.environment = env
        pool.controller = SimpleNamespace(device='cpu',reference=reference,active=active,target=reference.expand(2,-1).clone(),
            action_low=torch.tensor(catalog['action_lower']),action_high=torch.tensor(catalog['action_upper']))
        with patch.object(rollout.GpuPool,'reset',return_value=({},[])):
            pool.reset()
        c = pool.controller
        expected = natural.normalized_action(torch.tensor(goal['hold_target105'])[active],reference[active],c.action_low,c.action_high)
        self.assertTrue(torch.equal(pool.execution_hold_action[:,:12],expected[:12].expand(2,-1)))
        self.assertTrue(torch.equal(pool.execution_hold_action[:,12:],torch.zeros(2,27)))
        self.assertTrue(torch.equal(c.target,reference.expand(2,-1)))
        self.assertTrue(torch.equal(env.hold_action,torch.zeros(2,39)))

    def test_new_schema_strict_model_only_transfer_and_rng(self):
        settings,environment,source = make()
        trainer = natural.NaturalTrainer(source,ppo.PPOConfig(**settings['ppo']))
        metadata = dict(schema=runner.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
            input_contract=dict(schema=PATH_SCHEMA,required={},lineage=[],run_settings=None))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'source.pt';trainer.save(path,metadata=metadata)
            _,_,target = make(distribution='v9',axes='full33')
            before = torch.get_rng_state().clone()
            natural.initialize_policy(target,path,natural.digest(path))
            self.assertTrue(torch.equal(before,torch.get_rng_state()))
            for key,value in source.state_dict().items():
                if key != 'active_mask':self.assertTrue(torch.equal(value,target.state_dict()[key]),key)
            self.assertEqual(int(target.active_mask.sum()),33)
            payload = torch.load(path,map_location='cpu',weights_only=False)
            payload['identity']['architecture']['schema'] = 'guitar_learning.structured_press_policy.v2'
            torch.save(payload,path)
            with self.assertRaises(ValueError):natural.initialize_policy(target,path,natural.digest(path))
            with self.assertRaises(ValueError):natural.initialize_policy(target,path,'wrong-sha')

    def test_strict_resume_restores_both_adam_and_cpu_rng(self):
        settings,_,policy = make()
        trainer = natural.NaturalTrainer(policy,ppo.PPOConfig(**settings['ppo']))
        for optimizer,parameters in ((trainer.actor_optimizer,policy.actor_parameters()),
                (trainer.value_optimizer,policy.value_parameters())):
            optimizer.zero_grad()
            sum(p.square().sum()*1e-7 for p in parameters).backward()
            optimizer.step()
        trainer.updates = 1
        trainer.actor_optimizer.param_groups[0]['natural_press_stable_updates'] = 9
        metadata = dict(schema=runner.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
            input_contract=dict(schema=PATH_SCHEMA,required={},lineage=[],run_settings=None))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'resume.pt';trainer.save(path,metadata=metadata)
            saved = torch.load(path,map_location='cpu',weights_only=False)
            _,_,restored_policy = make()
            restored = natural.NaturalTrainer(restored_policy,ppo.PPOConfig(**settings['ppo']))
            restored.load(path)
            self.assertEqual(restored.updates,1)
            self.assertTrue(torch.equal(torch.get_rng_state(),saved['torch_rng']))
            for name in ('actor_optimizer','value_optimizer'):
                expected = saved[name];actual = getattr(restored,name).state_dict()
                self.assertEqual(actual['param_groups'],expected['param_groups'])
                self.assertEqual(actual['state'].keys(),expected['state'].keys())
                self.assertTrue(actual['state'])
                for key,value in expected['state'].items():
                    for field,tensor in value.items():
                        self.assertTrue(torch.equal(tensor,actual['state'][key][field]))
            wrong = dict(saved);wrong['identity'] = copy.deepcopy(saved['identity'])
            wrong['identity']['architecture']['natural_press']['condition'] = 'E1'
            torch.save(wrong,path)
            with self.assertRaises(ValueError):restored.load(path)


if __name__ == '__main__':unittest.main()
