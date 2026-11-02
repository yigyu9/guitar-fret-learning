"""GPU를 쓰지 않고 실제 MixedScene/MixedPool의 같은 시점 평가 reset을 검사한다."""
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parent))
import initial_mix as mix
sys.path.insert(0,str(mix.ROOT))
import torch
from guitar_learning.gpu.scene import GpuScene


def body(x):
    return dict(pose=dict(p=dict(x=x,y=0.,z=0.),r=dict(x=0.,y=0.,z=0.,w=1.)),
        vel=dict(linear=dict(x=0.,y=0.,z=0.),angular=dict(x=0.,y=0.,z=0.)))


def goal(value):
    return dict(hold_target105=[value],state=dict(human_dof_states=[dict(pos=value,vel=0.)],
        human_body_states=[body(value)],guitar_body_states=[body(0.)],chair_body_states=[body(0.)]))


class ResetTests(unittest.TestCase):
    def run_case(self,partial):
        fake=SimpleNamespace()
        @contextmanager
        def context(settings):yield
        class Scene:
            def __init__(self,count):
                self.num_envs=count;self.device='cpu';self.physics_steps=0;self._last_reset_physics_step=None
                self._configured=True;self._reset_mask=torch.zeros(count,dtype=torch.bool)
                self._natural_press_bodies=torch.zeros(count,3,13);self._prepared_dofs=torch.zeros(1,2)
                self.initial_hold=torch.zeros(count,1);self.target=torch.zeros(count,1)
                self.initial_is_v9=torch.zeros(count,dtype=torch.bool);self.q=torch.zeros(count,1);self.goal=goal(1.)
                self.reset(torch.arange(count))
            def snapshot(self):return dict(q=self.q.clone(),body_state=self._natural_press_bodies.clone())
        class Pool:
            def __init__(self):
                self.scene=fake.TransitionScene(32);self.environment=SimpleNamespace(evaluation=False,contract={},_episode=lambda i,f:{})
                self.contract={};self.reset()
            def reset(self,indices=None):
                ids=torch.arange(32) if indices is None else torch.tensor(indices)
                return self.scene.reset(ids),[]
        fake.TransitionScene=Scene;fake.TransitionPool=Pool;fake.transition_runtime=context
        fake.natural=SimpleNamespace(digest=lambda path:'sha')
        settings=dict(initial_mix=dict(schema=mix.SCHEMA,candidate='/tmp/candidate',native_proof='/tmp/proof',
            candidate_sha256='sha',native_proof_sha256='sha',training_B_fraction=.5,evaluation_B_fraction=0.))
        def native_reset(scene,ids):
            # 실제 GpuScene의 중복 초기화 방지 조건도 모방해 바깥 guard만 고쳐 생기는 재발을 잡는다.
            if scene._last_reset_physics_step==scene.physics_steps and bool(scene._reset_mask[ids].all()):return
            scene.q[ids]=scene._prepared_dofs[:,:,0];scene._reset_mask[ids]=True
            scene._last_reset_physics_step=scene.physics_steps
        with patch.object(mix,'runtime',return_value=fake),patch.object(mix,'verify_native',return_value=goal(2.)),\
             patch.object(GpuScene,'reset',native_reset),patch.object(torch,'rand',side_effect=lambda count:torch.zeros(count)):
            with mix.mixed_runtime(settings):
                pool=fake.TransitionPool();self.assertTrue(pool.scene.initial_is_B.all())
                self.assertTrue((pool.scene.q==2.).all())
                pool.environment.evaluation=True
                if partial:
                    pool.reset([0]);self.assertFalse(pool.scene.initial_is_B[0]);self.assertTrue(pool.scene.initial_is_B[1:].all())
                    pool.reset(list(range(1,32)))
                else:pool.reset()
                self.assertFalse(pool.scene.initial_is_B.any())
                self.assertTrue((pool.scene.q==1.).all());self.assertTrue((pool.scene.target==1.).all())
                self.assertTrue((pool.scene._natural_press_bodies[:,0,0]==1.).all())
                self.assertFalse(pool.environment._episode(0,False)['initial_mix']['started_from_B'])
                # 같은 평가 모드의 중복 reset은 RNG 소비 없이 이전 결과를 유지한다.
                with patch.object(torch,'rand',side_effect=AssertionError('중복 reset 표본화')):pool.reset()
                pool.environment.evaluation=False;pool.reset()
                self.assertTrue(pool.scene.initial_is_B.all());self.assertTrue((pool.scene.q==2.).all())
        self.assertIs(fake.TransitionPool,Pool);self.assertIs(fake.TransitionScene,Scene)

    def test_evaluation_mode_forces_A_at_same_physics_step(self):self.run_case(False)
    def test_partial_evaluation_resets_clear_every_B_row(self):self.run_case(True)

if __name__=='__main__':unittest.main()
