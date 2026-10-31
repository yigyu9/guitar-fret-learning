"""실제 rl38 CPU. current 환경·원루프의 test-double·실제 Gaussian만 사용하며 NN/native는0이다."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('ring_learning_cpu_target',HERE/'experiment.py')
e=importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
pre=e.pre


def rejected(call,kind=Exception):
    try: call()
    except kind: return
    raise AssertionError('Invalid CPU fixture accepted')


def preflight_cases():
    # NumPy/Torch보다 먼저 stdlib acceptance gate 전체를 검사한다.
    with tempfile.TemporaryDirectory() as folder,patch.object(e,'HERE',Path(folder)):
        h=Path(folder); pin=h/'input'; pin.write_text('fixed'); pins={str(pin):pre.sha(pin)}
        for control in ('reference','zero'):
            out=h/'runs'/('preflight_'+control); out.mkdir(parents=True)
            rows=[dict(env_id=i,achieved=control=='reference',clean_fraction=float(control=='reference'),audible_wrong_fraction=0.,termination=dict(physical_failure=False,wrist_failure=False)) for i in range(128)]
            value=dict(condition=control,policy_performance=False,assigned_quotas=[1]*128,episodes=rows)
            pre.write(out/'evaluation.json',value)
            pre.write(out/'diagnostic_inputs_after.json',dict(verified=True,input_pins=pins))
            pre.write(out/'diagnostic_report.json',dict(completed=True,NN_constructions=0,phase='preflight',result_sha256={str(out/'evaluation.json'):pre.sha(out/'evaluation.json')}))
        assert e.preflight_gate()
        out=h/'runs/preflight_zero'; original=pre.read(out/'evaluation.json')
        for change in ('duplicate','zero_success','missing'):
            value=copy.deepcopy(original)
            if change=='duplicate': value['episodes'][1]['env_id']=0
            elif change=='zero_success':
                for row in value['episodes']: row['achieved']=True
            else: value['episodes'].pop()
            pre.write(out/'evaluation.json',value)
            report=pre.read(out/'diagnostic_report.json'); report['result_sha256']={str(out/'evaluation.json'):pre.sha(out/'evaluation.json')};pre.write(out/'diagnostic_report.json',report)
            rejected(e.preflight_gate,ValueError)
        pre.write(out/'evaluation.json',original)
        rejected(e.preflight_gate,ValueError)  # result SHA mismatch
    assert not {'numpy','torch','isaacgym'} & set(sys.modules)


def native_cases():
    import numpy as np
    from guitar_learning.runtime import prepared_reset_v1
    fixture_spec=importlib.util.spec_from_file_location('ring_reviewed_cpu_fixture',e.PRE/'cpu_check.py')
    fixture_module=importlib.util.module_from_spec(fixture_spec); fixture_spec.loader.exec_module(fixture_module)
    source=prepared_reset_v1.load_prepared_reset_contract(); saved=copy.deepcopy(source); helpers=pre.effort_helpers()
    scene,document,actual,flat=fixture_module.native_fixture(source,helpers)
    scene.num_envs=128; scene.envs=list(range(128)); scene.actors=[(0,1,2)]*128; scene._hand_collision_readback_count=128
    scene.names=source['initial']['joint_names']
    result=e.verify128(scene,source,document)
    assert len(result['direct_readback_environments'])==128 and len(result['actual_native_PD105'])==10
    rejected(lambda:pre.native_readback(scene,source,document,helpers),AssertionError)  # frozen4 gate 그대로
    for field in actual.dtype.names:
        bad=actual.copy(); bad[field][0]=not bool(bad[field][0]) if field=='hasLimits' else bad[field][0]+1
        with patch.object(scene.gym,'get_actor_dof_properties',side_effect=lambda env,actor:bad.copy() if env==127 else actual.copy()):
            rejected(lambda:e.verify128(scene,source,document),ValueError)
    bad=copy.deepcopy(flat); bad[0].filter^=1
    with patch.object(scene.gym,'get_actor_rigid_shape_properties',side_effect=lambda env,actor:copy.deepcopy(bad if env==127 else flat)):
        rejected(lambda:e.verify128(scene,source,document),ValueError)
    np.testing.assert_equal(source,saved)
    return fixture_module


def gaussian_cases():
    import torch
    from guitar_learning.training.policy import FingerSkillPolicy
    class Toy:
        act=FingerSkillPolicy.act  # 원정책의 Normal 생성/selected4 표본 코드 자체를 사용한다.
        def __call__(self,*args):
            return dict(mean=torch.zeros(128,39),log_std=torch.full((128,39),float(__import__('math').log(pre.STD))))
        def _active_mask(self):
            value=torch.zeros(39,dtype=torch.bool); value[pre.SELECTED]=True; return value
        def log_probability(self,mean,std,latent): return latent[:,pre.SELECTED].sum(-1)
    toy=Toy(); act=e.private_act(toy.act,'cpu'); state=torch.zeros(128,557)
    outer=torch.get_rng_state().clone(); generator=torch.Generator().manual_seed(7)
    for _ in range(2):
        result=act(state,None,None,None,None,deterministic=True)
        expected=torch.zeros(128,39); expected[:,pre.SELECTED]=torch.randn((128,4),generator=generator)*pre.STD
        assert torch.equal(result['latent'],expected) and torch.equal(result['action'],expected.tanh())
        assert torch.equal(torch.get_rng_state(),outer)
    def bad(*args,**kwargs):
        torch.randn(128,4); raise ValueError('sample error')
    rejected(lambda:e.private_act(bad,'cpu')(state),ValueError)
    assert torch.equal(torch.get_rng_state(),outer)
    rejected(lambda:e.NoNN().act(torch.zeros(128,561)),ValueError)
    assert torch.count_nonzero(e.NoNN().act(state)['action'])==0


def binding_cases(config):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    class Scene:
        def __init__(self):
            self.effort_caps=torch.zeros(105); self.pd_properties=np.zeros(105,dtype=[('effort',np.float32)])
        def close(self): raise RuntimeError('secondary scene close')
    class Pool:
        def __init__(self,config,out):
            self.scene=None
            try:
                self.scene=self._create_scene(config,out)
                self.controller=SimpleNamespace(caps=self.scene.effort_caps); self.contract=dict(native_backend={})
            except BaseException:
                self.close(); raise
        def _create_scene(self,config,out):
            prepared_reset_v1.load_prepared_reset_contract()
            return Scene()
        def close(self): raise RuntimeError('secondary pool close')
    originals=(runner.ShortPool,runtime.ShortPool,runner._pins,runner.ShortPolicy,runner.SCHEMA,prepared_reset_v1.load_prepared_reset_contract)
    real_read=pre.read
    def local_read(path): return config if Path(path)==HERE/'inputs/settings.json' else real_read(path)
    for fail in (True,False):
        state=dict(pool=None,scene=None,cleanup_errors=[],NN_constructions=0)
        with tempfile.TemporaryDirectory() as folder,patch.object(runner,'ShortPool',Pool),patch.object(runtime,'ShortPool',Pool),patch.object(pre,'read',side_effect=local_read),patch.object(e,'verify128',side_effect=ValueError('primary native mismatch') if fail else None,return_value=dict(cap_Nm=.25)):
            try:
                with e.binding({HERE/'PLAN.md'},state) as bound:
                    assert bound.SCHEMA==e.SCHEMA and runtime.ShortPool is bound.ShortPool
                    bound.ShortPool(config,Path(folder)).close()
                    raise ValueError('primary after constructor')
            except ValueError as error: assert str(error)==('primary native mismatch' if fail else 'primary after constructor')
        assert state['aliases_restored'] and state['loader_restored'] and state['cleanup_errors']
        assert (runner.ShortPool,runtime.ShortPool,runner._pins,runner.ShortPolicy,runner.SCHEMA,prepared_reset_v1.load_prepared_reset_contract)==originals
    # own schema를 벗어난 checkpoint는 모델 생성 전에 원 runner가 거부한다.
    state=dict(NN_constructions=0,cleanup_errors=[])
    with e.binding(set(),state),patch.object(torch,'load',return_value=dict(metadata=dict(schema='old.short.v2',input_pins={'x':'y'}))):
        rejected(lambda:runner.run(SimpleNamespace(command='evaluate',checkpoint='/unused',out='/unused_cpu')),ValueError)
    assert state['NN_constructions']==0


def original_loop_case(config):
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    calls=[]
    class Collector:
        def __init__(self,*args,**kwargs): pass
        def collect(self,horizon):
            assert horizon==32
            return dict(reward=torch.zeros(32,128),cost=torch.zeros(32,128),valid=torch.ones(32,128,dtype=torch.bool)),[]
    class Trainer:
        config=SimpleNamespace(gamma=.99,cost_gamma=1.)
        updates=0
        def save(self,path,metadata): calls.append((Path(path).name,self.updates)); assert metadata['schema']==e.SCHEMA
        def update(self,*args): self.updates+=1; return dict(actor_loss=0.)
    env=SimpleNamespace(reset_reward_window=lambda:None,reward_window_means=lambda count:dict(test_double=0.))
    progress=[]; pool=SimpleNamespace(environment=env,set_training_progress=progress.append)
    with tempfile.TemporaryDirectory() as folder,patch.object(runner,'DecisionCollector',Collector),patch('builtins.print'):
        metadata=dict(schema=e.SCHEMA,input_pins={str(HERE/'experiment.py'):pre.sha(HERE/'experiment.py')})
        runner._train(pool,object(),Trainer(),config,metadata,Path(folder))
        assert len((Path(folder)/'metrics.jsonl').read_text().splitlines())==300
    assert calls==[('initial.pt',0),('evaluation_000050.pt',50),('evaluation_000100.pt',100),('evaluation_000150.pt',150),('evaluation_000200.pt',200),('evaluation_000250.pt',250),('final.pt',300)]
    assert progress[-1]==1228800


def run():
    assert sys.version_info[:2]==(3,8) and os.environ.get('CUDA_VISIBLE_DEVICES')==''
    assert not {'numpy','torch','isaacgym'} & set(sys.modules)
    e.base_gate(); preflight_cases()
    import numpy as np
    import torch
    torch.set_num_threads(1)
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    config=e.configuration(); assert config['num_envs']==128 and config['updates']==300 and config['horizon']==32 and config['size']=='large' and config['seed']==7
    fixture_module=native_cases()
    forbidden=AssertionError('NN construction/checkpoint load forbidden in CPU preparation')
    with patch.object(torch.nn.Module,'__init__',side_effect=forbidden),patch.object(torch,'load',side_effect=forbidden):
        env,snapshot,obs,metadata=fixture_module.environment(config)
        assert tuple(obs['state'].shape)==(4,557) and env.selected_index==54
        env.clock[:]=torch.tensor([4,8,12,16]); env.reset([0],snapshot); assert env.clock.tolist()==[0,8,12,16]
        gaussian_cases(); binding_cases(config); original_loop_case(config)
    supervisor=ast.parse((HERE/'supervise.py').read_text()); compile(supervisor,str(HERE/'supervise.py'),'exec')
    main=next(n for n in supervisor.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    jobs=[n for n in main.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='jobs' for t in n.targets)) or (isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='jobs')]
    scope={}; exec(compile(ast.Module(body=jobs,type_ignores=[]),'<supervisor11jobs>','exec'),scope)
    assert [n for n,a in scope['jobs']]==['reference','zero','train',*['evaluation_%06d'%u for u in e.UPDATES],'evaluation_000300_stochastic']
    assert 'torch' not in (HERE/'supervise.py').read_text() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(schema=e.SCHEMA,completed=True,python=sys.version,CUDA_VISIBLE_DEVICES='',GPU=0,native=0,NN_construction=0,NN_forward=0,checkpoint_load=0,actual_PPO_updates=0,
        stdlib_base_and_preflight_gate=True,good128_preflight_and_duplicate_missing_zero_success_changed_SHA_rejected=True,
        current_settings557_Jv3_source54=True,partial_reset_preserved=True,synthetic128_all_PD105_fields10_direct=True,
        last_env_all10_PD_mutations_and_collision_mutation_rejected=True,frozen4_verifier_still_rejects128=True,
        selected4_original_policy_act_private_seed7_two_ticks_bitexact=True,global_RNG_and_error_RNG_restored=True,
        original_runner_bindings_and_loader_restored_after_constructor_and_later_errors=True,primary_and_cleanup_errors_preserved=True,
        old_checkpoint_schema_rejected_before_model_creation=True,original_train_loop_test_double_300_saves_0_50_to_300=True,
        synthetic_test_double_transitions=1228800,supervisor_syntax_and_11job_schedule=True,
        source_sha256={str(HERE/n):pre.sha(HERE/n) for n in ('experiment.py','cpu_check.py','supervise.py','PLAN.md')},
        limitation='No NN/native/real PPO executed. Original training loop uses a synthetic collector/trainer test double; Gaussian uses original act source bound to network-free toy forward. 128 native properties are synthetic fixtures until GPU preflight.')


if __name__=='__main__':
    result=run(); pre.write(HERE/'cpu_verification.json',result); print(json.dumps(result,ensure_ascii=False,indent=2))
