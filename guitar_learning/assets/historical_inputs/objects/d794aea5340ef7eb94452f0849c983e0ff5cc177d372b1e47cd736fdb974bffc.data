"""CPU-only explicit actor migration tests; no native performance claim."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
from guitar_learning import actionable_preparation_environment as E
from guitar_learning import training_environment
from guitar_learning.actionable_preparation_transfer import apply_actor_initialization, validate_contracts
from guitar_learning.imitation import SCHEMA
from guitar_learning.music_task import ScoreTask
from guitar_learning.ppo import PPOTrainer
from guitar_learning.specialist_policy import SpecialistPolicy
from guitar_learning.timing_curriculum import TimingConfig
from guitar_learning.tests.test_skill_environment import LongRecordedSession
from guitar_learning.tests import test_timing_environment as fixtures


class ActionableTransferTests(unittest.TestCase):
    def setUp(self):
        fixtures.TimingEnvironmentTests.setUp(self)
        self.threads=torch.get_num_threads(); torch.set_num_threads(1)

    def tearDown(self):
        fixtures.TimingEnvironmentTests.tearDown(self)
        torch.set_num_threads(self.threads)

    def contract(self, role='left', modern=False, stage=1):
        if not modern:
            env=fixtures.TimingEnvironmentTests.environment(self,role,timing=TimingConfig(stage_index=stage))
        else:
            sessions=[]
            def factory(config,out):
                session=LongRecordedSession(config,out);sessions.append(session);return session
            def contacts(scene):
                return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
            with patch.object(training_environment,'ContactEnvironment',E.PersistentContactEnvironment):
                env=E.ActionablePreparationEnvironment({},Path(self.folder.name)/str(len(self.environments)),
                    task=ScoreTask.from_bundle('data/song_bundles/05_BN2-131-B_solo'),role=role,
                    timing=TimingConfig(stage_index=stage,pre_roll_s=3.),session_factory=factory,contact_reader=contacts)
            self.environments.append(env)
        env.reset()
        return copy.deepcopy(env.contract)

    def model(self,contract,role='left'):
        return SpecialistPolicy(536,size='small',role=role,frozen_partner=False,contract=contract)

    def payload(self,model,kind):
        if kind=='bc':
            return dict(schema=SCHEMA,role=model.role,architecture=copy.deepcopy(model.architecture),
                dataset_manifest={'CPU fixture':'not native evidence'},training={'steps':1},model=copy.deepcopy(model.state_dict()))
        return dict(identity=PPOTrainer(model)._identity(),updates=12,model=copy.deepcopy(model.state_dict()))

    def save(self,payload):
        path=Path(self.folder.name)/'source.pt';torch.save(payload,path);return path

    def test_allowed_clock_shift_preserves_original_score_and_all505_scales(self):
        source=self.contract();target=self.contract(modern=True)
        ratios=validate_contracts(source,target,'left')
        self.assertEqual(ratios[:505],[1.]*505)
        self.assertTrue(any(abs(r-1.4)<1e-12 for r in ratios[505:]))
        self.assertTrue(all(r==1. or abs(r-1.4)<1e-12 for r in ratios[505:]))
        self.assertEqual(source['task']['timing']['original_targets'],target['task']['timing']['original_targets'])
        self.assertAlmostEqual(target['task']['targets'][0]['onset_s']-source['task']['targets'][0]['onset_s'],2.)
        self.assertEqual(validate_contracts(target,target,'left'),[1.]*536)

    def test_bc_ppo_column_compensation_and_only_active_actor_std_copied(self):
        for role,kind in (('left','bc'),('right','ppo')):
            with self.subTest(role=role,kind=kind):
                source=self.model(self.contract(role),role)
                target=self.model(self.contract(role,modern=True),role)
                with torch.no_grad():
                    source.actor_heads[role].weight.normal_(0.,.03)
                    source.actor_heads[role].bias.normal_(0.,.03)
                    source.log_std.fill_(-4.2)
                before=copy.deepcopy(target.state_dict());metadata=copy.deepcopy(target.architecture)
                trainer=PPOTrainer(target)
                result=apply_actor_initialization(target,self.save(self.payload(source,kind)),kind=kind)
                self.assertTrue(result['rescaled_input_columns'])
                ratio=torch.tensor(validate_contracts(source.architecture['contract'],target.architecture['contract'],role))
                first='actor_encoders.'+role+'.state.0.weight'
                for key,value in target.state_dict().items():
                    if key.startswith(('actor_encoders.'+role+'.','actor_heads.'+role+'.')):
                        expected=source.state_dict()[key]*(ratio.unsqueeze(0) if key==first else 1.)
                        self.assertTrue(torch.equal(value,expected),key)
                    elif key!='log_std':self.assertTrue(torch.equal(value,before[key]),key)
                active=target.role_slices[role];inactive=slice(33,39) if role=='left' else slice(0,33)
                self.assertTrue(torch.equal(target.log_std[active],source.log_std[active]))
                self.assertTrue(torch.equal(target.log_std[inactive],before['log_std'][inactive]))
                self.assertEqual(target.architecture,metadata)
                self.assertEqual(trainer.updates,0)
                self.assertFalse(trainer.actor_optimizer.state);self.assertFalse(trainer.value_optimizer.state)
                raw=torch.randn(3,536)*.1
                oldscales=torch.tensor(source.architecture['contract']['observation']['scales'])
                newscales=torch.tensor(target.architecture['contract']['observation']['scales'])
                rest=(torch.randn(3,64,24),torch.ones(3,64,dtype=torch.bool),
                    torch.randn(3,2,24),torch.ones(3,2,dtype=torch.bool))
                self.assertTrue(torch.allclose(source.act(raw/oldscales,*rest,deterministic=True)['action'],
                    target.act(raw/newscales,*rest,deterministic=True)['action'],atol=1e-6,rtol=1e-6))

    def test_new_to_new_copies_exactly_without_rescaling(self):
        contract=self.contract('right',modern=True)
        source=self.model(contract,'right');target=self.model(contract,'right')
        result=apply_actor_initialization(target,self.save(self.payload(source,'bc')),kind='bc')
        self.assertEqual(result['rescaled_input_columns'],[])
        for key,value in target.state_dict().items():
            if key.startswith(('actor_encoders.right.','actor_heads.right.')):
                self.assertTrue(torch.equal(value,source.state_dict()[key]),key)

    def test_physics_safety_goal_stage_and_unknown_changes_reject_before_mutation(self):
        source=self.model(self.contract());good=self.payload(source,'ppo')
        target=self.model(self.contract(modern=True));before=copy.deepcopy(target.state_dict())
        mutations=[
            lambda c:c['termination'].__setitem__('guitar_displacement_m',.09),
            lambda c:c['action'].__setitem__('smoothing_alpha',.3),
            lambda c:c['action']['target_contract']['rates_rad_s'].__setitem__(0,.9),
            lambda c:c['task']['targets'][0].__setitem__('finger',2),
            lambda c:c['observation']['fields'].__setitem__(0,'different_joint'),
            lambda c:c['observation']['scales'].__setitem__(0,2.),
            lambda c:c['observation']['scales'].__setitem__(510,6.),
            lambda c:c['observation']['timing_history'].__setitem__('hidden',True),
            lambda c:c['task']['timing']['config'].__setitem__('stage_index',0),
            lambda c:c['reward']['timing']['config'].__setitem__('success_bonus',2.),
            lambda c:c['termination'].__setitem__('preparation_seconds',1.),
            lambda c:c['task']['timing']['original_targets'][0].__setitem__('string',3)]
        for index,mutate in enumerate(mutations):
            payload=copy.deepcopy(good);mutate(payload['identity']['architecture']['contract'])
            with self.subTest(index=index),self.assertRaises(ValueError):
                apply_actor_initialization(target,self.save(payload),kind='ppo')
            for key,value in target.state_dict().items():self.assertTrue(torch.equal(value,before[key]),key)
        bad=copy.deepcopy(target.architecture['contract']);bad['task']['actionable_preparation']['initial_policy_preparation_s']=1.
        with self.assertRaises(ValueError):validate_contracts(source.architecture['contract'],bad,'left')

    def test_legacy505_and_nonfinite_inactive_tensors_reject_transactionally(self):
        source=self.model(self.contract());target=self.model(self.contract(modern=True));before=copy.deepcopy(target.state_dict())
        bad=copy.deepcopy(source.architecture['contract']);bad['observation']['dimension']=505
        with self.assertRaises(ValueError):validate_contracts(bad,target.architecture['contract'],'left')
        payload=self.payload(source,'bc');payload['model']['cost_critic.weight'][0,0]=float('nan')
        with self.assertRaises(ValueError):apply_actor_initialization(target,self.save(payload),kind='bc')
        for key,value in target.state_dict().items():self.assertTrue(torch.equal(value,before[key]),key)

    def test_strict_ppo_resume_still_rejects_new_contract(self):
        source=PPOTrainer(self.model(self.contract()));target=PPOTrainer(self.model(self.contract(modern=True)))
        path=Path(self.folder.name)/'strict.pt';source.save(path)
        with self.assertRaisesRegex(ValueError,'mismatch'):target.load(path)


if __name__=='__main__':unittest.main()
