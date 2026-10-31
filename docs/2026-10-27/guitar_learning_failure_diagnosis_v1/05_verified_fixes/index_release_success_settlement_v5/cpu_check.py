"""실제 rl38 CPU에서 지급 수명·원장·계약·V4 연결을 검사한다. native 성공 검사는 아니다."""
import copy
import inspect
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
import torch
import runtime as rt
import learn
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.tests.test_gpu_environment import fixture


def make():
    metadata, snapshot = fixture(4)
    settings = rt.settings()
    env = rt.Environment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],
        skill=settings['finger_skill'],device='cpu')
    env.reset(range(4),snapshot)
    return env,snapshot


def check():
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    env,snapshot = make()
    assert env.note['settlement_closed'].dtype == torch.bool
    deadline = float(env.end[4]+.1)
    now = torch.full((4,),deadline-1/240.,dtype=torch.float64)
    env._score_time = lambda: now
    env.focus_mask[:,4] = True
    env.finger_weights[:,4] = torch.tensor([1.,2.,1.,1.],dtype=torch.float64)
    env.note['left'][:,4] = False
    # 부모 substep의 출력만 통제한다. V5 연산·원장·기존 최종 가중은 실제 코드를 쓴다.
    def parent_step(self,sample):
        newly = ~self.note['left'][:,4]
        self.note['left'][:,4] = True
        self.terms['song_left_success'] += (.5*newly*self.finger_weights[:,4]).float()
        self.terms['song_left_success'] += torch.tensor([.5,.5,.5,.5])  # B 달성은 보존해야 한다.
    env.terms = {name:torch.full((4,),.125) for name in (
        'song_left_approach','song_left_contact','song_clean_hold','song_left_success',
        'song_wrong_press','song_finger_standby','song_thumb_support','action_change')}
    env.terms['song_left_success'].zero_()
    other = {key:value.clone() for key,value in env.terms.items() if key != 'song_left_success'}
    with patch.object(rt.v4.shared.Environment,'substep',parent_step):
        env.substep(snapshot)
        torch.testing.assert_close(env.terms['song_left_success'],torch.full((4,),.5),rtol=0,atol=0)
        assert not env.note['settlement_closed'].any()
        assert all(torch.equal(env.terms[key],value) for key,value in other.items())
        env.note['released'][:,4] = torch.tensor([True,True,True,False])
        env.note['release_s'][:,4] = torch.tensor([deadline,deadline,deadline+.00001,0.],dtype=torch.float64)
        now[:] = deadline
        env.substep(snapshot)
        # 끝 경계는 포함하고 초과·미해제는 거부한다. B의 .5는 매번 보존한다.
        torch.testing.assert_close(env.terms['song_left_success'],torch.tensor([1.5,2.,1.,1.]),rtol=0,atol=0)
        assert env.note['settlement_closed'][:,4].all()
        with patch.object(rt.v4.shared.Environment,'_prepare_control_end',lambda self,failed:None):
            env._prepare_control_end(torch.tensor([False,True,False,False]))
        torch.testing.assert_close(env.note['settlement_paid'][:,4],torch.tensor([.25,0.,0.,0.],dtype=torch.float64),rtol=0,atol=0)
        torch.testing.assert_close(env.note['settlement_suppressed'][:,4],torch.tensor([0.,.5,0.,0.],dtype=torch.float64),rtol=0,atol=0)
        old = env.note['settlement_entitled_raw'].clone()
        now[:] += 1/240.
        env.substep(snapshot)
        assert torch.equal(old,env.note['settlement_entitled_raw'])
    # 달성 없는 해제와 음 종료 전 해제, 기한 전 종료는 지급으로 바꾸지 않는다.
    edge,sample = make()
    edge.terms = {'song_left_success':torch.zeros(4)}
    end = float(edge.end[4]); deadline2 = float(edge.end[4]+.1)
    edge._score_time = lambda: torch.full((4,),deadline2,dtype=torch.float64)
    edge.note['left'][:,4] = torch.tensor([False,True,True,True])
    edge.note['released'][:,4] = True
    edge.note['release_s'][:,4] = torch.tensor([end,end-.00001,end,deadline2],dtype=torch.float64)
    with patch.object(rt.v4.shared.Environment,'substep',lambda self,sample:None):
        edge.substep(sample)
    expected = .5*edge.finger_weights[:,4]*torch.tensor([False,False,True,True])
    expected = expected.double()
    torch.testing.assert_close(edge.note['settlement_entitled_raw'][:,4],expected,rtol=0,atol=1e-7)
    early,sample = make()
    early.terms = {'song_left_success':torch.zeros(4)}
    early._score_time = lambda: torch.full((4,),float(early.end[4]+.1)-1/240.,dtype=torch.float64)
    early.note['left'][:,4] = True; early.note['released'][:,4] = True
    early.note['release_s'][:,4] = early.end[4]
    with patch.object(rt.v4.shared.Environment,'substep',lambda self,sample:None), \
         patch.object(rt.v4.shared.Environment,'_prepare_control_end',lambda self,failed:None):
        early.substep(sample)
        early._prepare_control_end(torch.ones(4,dtype=torch.bool))
    assert not early.note['settlement_closed'].any() and not early.note['settlement_paid'].any()
    # 실제 부모 240Hz 판정과 60Hz 실패 clamp를 통과한다. 접촉만 합성 snapshot으로 전환한다.
    actual,sample = make()
    deadline3 = actual.end[4]+.1
    actual.score_offset[:] = deadline3-1/240.
    actual.begin_control(torch.zeros(4,39))
    actual.note['left'][:,4] = True
    actual.note['ever'][:,4] = True
    actual.previous_candidate[:,4] = True
    for i in range(4):
        actual.substep(dict(sample,physics_step=actual.clock+1))
        if i == 0:
            assert actual.note['released'][:,4].all()
            assert actual.note['settlement_closed'][:,4].all()
            torch.testing.assert_close(actual.note['release_s'][:,4],deadline3.expand(4),rtol=0,atol=0)
            assert not actual.note['settlement_paid'].any()
        if i == 2: actual.tick_failure[1,0] = True
    actual.end_control()
    received = .25*actual.finger_weights[:,4].double(); received[1] = 0
    torch.testing.assert_close(actual.note['settlement_paid'][:,4],received,rtol=0,atol=0)
    torch.testing.assert_close(actual.episode_reward_terms['song_left_success'].double(),received,rtol=0,atol=0)
    # 실제 부분 reset을 사용하여 H 경계와 다른 행의 원장이 보존되는지 확인한다.
    before = {key:value.clone() for key,value in env.note.items() if key.startswith('settlement_')}
    del env._score_time
    env.reset([1],snapshot)
    for key,old in before.items():
        assert not env.note[key][1].any()
        assert torch.equal(env.note[key][[0,2,3]],old[[0,2,3]])
    source = inspect.getsource(TensorSongEnvironment.end_control)
    assert source.index('self._prepare_control_end(failed)') < source.index("self.terms[key].clamp_max(0)")
    raw = {key:value.clone() for key,value in env.terms.items()}
    env.control_performance_penalty = torch.zeros(4)
    assert set(FingerSkillEnvironment._reward_components(env,{})) == {
        'song_left_approach','song_left_contact','song_clean_hold','song_left_success','song_wrong_press',
        'song_performance_deficit','song_finger_standby','song_thumb_support','action_change'}
    contract = rt.attach(rt.base.read(rt.SOURCE/'capture/runs/candidate/training_contract.json'))
    config = rt.settings(); config.update(device='cpu',size='small')
    learn.seed(); own = rt.GoalPolicy(contract=contract,size='small')
    learn.seed(); old = rt.v4.GoalPolicy(contract=rt.v4.attach(rt.base.read(rt.SOURCE/'capture/runs/candidate/training_contract.json')),size='small')
    assert all(torch.equal(value,old.state_dict()[key]) for key,value in own.state_dict().items())
    assert own.architecture['schema'] != old.architecture['schema']
    trainer = learn.DecisionPPOTrainer(own,learn.PPOConfig(**config['ppo']))
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'own.pt'
        pins = {str(Path(__file__).resolve()):rt.base.sha(Path(__file__))}
        trainer.save(path,metadata=learn.metadata(config,pins))
        restored = learn.DecisionPPOTrainer(rt.GoalPolicy(contract=contract,size='small'),learn.PPOConfig(**config['ppo']))
        learn.load(restored,path,config)
        oldtrainer = learn.DecisionPPOTrainer(old,learn.PPOConfig(**config['ppo']))
        oldtrainer.save(Path(temp)/'old.pt',metadata=dict(learn.metadata(config,pins),schema=rt.v4.SCHEMA))
        try: learn.load(restored,Path(temp)/'old.pt',config)
        except ValueError: pass
        else: raise AssertionError('V4 checkpoint admitted')
    assert sys.modules['runtime'] is rt and learn.parent.rt is rt
    assert learn.parent.train.__globals__['rt'] is rt
    assert rt.v4.GoalPool.environment_class_override is rt.v4.shared.Environment
    assert rt.GoalPool.environment_class_override is rt.Environment
    import launch_training as launch
    import os
    for broken_record in (False,True):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp); (home/'runs/fit').mkdir(parents=True)
            (home/'runs/fit/fit.pt').write_bytes(b'fixture')
            rt.base.write(home/'runs/fit/initial_tensor_equality.json',{'fixture':{'exact':True}})
            class Child:
                pid, code, terminated = os.getpid(), None, False
                def poll(self): return self.code
                def wait(self): self.code = -15 if self.terminated else 0; return self.code
                def terminate(self): self.terminated = True
            child = Child()
            original_write = launch.ex.base.write
            def write(path,value):
                if broken_record and path.name == 'process.json': raise OSError('process audit fixture')
                return original_write(path,value)
            with patch.object(launch,'HERE',home), patch.object(launch.ex,'gate',lambda:{}), \
                 patch.object(launch.subprocess,'Popen',return_value=child) as popen, \
                 patch.object(launch.ex.base,'write',write):
                try: launch.main()
                except OSError as error: assert broken_record and str(error) == 'process audit fixture'
                else: assert not broken_record
                assert popen.call_count == 1
                result = rt.base.read(home/'execution_training/exit.json')
                assert result['process_terminal'] and not result['changed_inputs']
                assert result['returncode'] == (-15 if broken_record else 0)
                assert bool(result['failure']) == broken_record
                try: launch.main()
                except FileExistsError: pass
                else: raise AssertionError('Duplicate supervisor launched')
                assert popen.call_count == 1
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,native_runs=0,full_fit_steps=0,PPO_updates=0,python_version=sys.version.split()[0],
        interpreter=sys.executable,original_A_credit_removed_only=True,B_credit_and_other_raw_terms_exact=True,
        deadline_inclusive_and_late_release_rejected=True,early_release_and_unachieved_rejected=True,terminal_before_deadline_no_catchup=True,no_release_no_payout=True,once_only=True,
        failed_control_suppression_ledger=True,actual_partial_reset_preserves_other_rows=True,
        actual_same_substep_deadline_release_then_payout=True,actual_later_substep_failure_suppresses_payout=True,original_failure_clamp_after_prepare=True,nine_terms_only=True,initial_policy_tensors_exact=True,
        own_strict_roundtrip_and_V4_rejected=True,scoped_parent_import_alias_restored=True,supervisor_zero_exit_duplicate_lock_and_primary_failure_cleanup=True)


if __name__ == '__main__': print(json.dumps(check(),indent=2))
