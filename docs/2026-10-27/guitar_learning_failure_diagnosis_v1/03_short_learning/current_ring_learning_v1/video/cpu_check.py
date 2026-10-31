"""CUDA/NN/checkpoint 없이 영상 scoped hook과 원128 평가 보존을 검사한다."""
import copy
from contextlib import contextmanager, redirect_stderr
import io
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('current_ring_video_cpu_subject', HERE/'video.py')
subject = importlib.util.module_from_spec(spec); spec.loader.exec_module(subject)


def run_case(fail=False, cleanup=False):
    calls = dict(step=0, evaluate=0, records=0, finish=0)
    fake_torch = types.SimpleNamespace(is_tensor=lambda value: False)
    native = object(); acquire = lambda: native
    gymapi = types.SimpleNamespace(acquire_gym=acquire)
    renderer = types.ModuleType('guitar_learning.tool.demonstration.render_finger_skill')
    class Capture:
        def __init__(self, *args): self.episode=None; self.samples=[]
        def record(self, *args):
            calls['records'] += 1
            assert len(args) == 6 and args[-1] == [{'env_id':0}]
            self.episode = args[-1][0]
    camera_original=dict(hand=((1,2,3),(4,5,6)),fullbody=((0,2.7,1),(0,0,0)))
    renderer.CAMERAS=camera_original
    renderer._EnvZeroCapture=Capture
    def create_cameras(*args):
        assert renderer.CAMERAS['hand'] == camera_original['hand']
        assert renderer.CAMERAS['fullbody'] == ((-.10,3.4,1.1),(-.15,-.10,.65))
        return dict(hand=1,fullbody=2)
    renderer._create_cameras=create_cameras
    renderer._encoder=lambda path: str(path)
    probe=types.ModuleType('guitar_learning.tool.validation.hand_contact_probe')
    probe.GraphicsGym=lambda value: ('graphics_only',value)
    def finish(value):
        calls['finish'] += 1
        if cleanup: raise RuntimeError('cleanup fixture')
        return 0, []
    probe.finish_video=finish
    def step(action):
        calls['step'] += 1
        return ('observation',1,2,False,True,[{'env_id':0}])
    pool=types.SimpleNamespace(scene=object(),step=step)
    class Optimizer:
        def state_dict(self): return dict(state={2:dict(step=9)},param_groups=[dict(lr=.001)])
    policy=types.SimpleNamespace(state_dict=lambda:dict(weight=[1.,2.]))
    trainer=types.SimpleNamespace(policy=policy,actor_optimizer=Optimizer(),value_optimizer=Optimizer(),updates=300,cost_weight=1.)
    def evaluate(pool, policy, spec, args, out):
        calls['evaluate'] += 1
        assert args.episodes == 128
        result=pool.step('same_action')
        assert result[0]=='observation'
        if fail: raise ValueError('primary fixture')
        return 'all128 original evaluator'
    factory=lambda *args,**kwargs: trainer
    runner=types.SimpleNamespace(_evaluate=evaluate,DecisionPPOTrainer=factory)
    state=dict(cleanup_errors=[],encoding={},trainer_unchanged=False)
    modules={'isaacgym':types.SimpleNamespace(gymapi=gymapi),'numpy':types.ModuleType('numpy'),'torch':fake_torch,
        renderer.__name__:renderer,probe.__name__:probe}
    error=None
    with patch.dict(sys.modules,modules):
        try:
            with subject.hooks(runner,state,Path('/unused-video-cpu-fixture')):
                assert gymapi.acquire_gym() == ('graphics_only',native)
                assert runner.DecisionPPOTrainer() is trainer
                value=runner._evaluate(pool,policy,{},types.SimpleNamespace(episodes=128),Path('/unused'))
                assert value=='all128 original evaluator'
        except ValueError as caught: error=str(caught)
    assert error == ('primary fixture' if fail else None)
    assert calls == dict(step=1,evaluate=1,records=1,finish=2)
    assert pool.step is step and runner._evaluate is evaluate and runner.DecisionPPOTrainer is factory
    assert gymapi.acquire_gym is acquire and state['render_hooks_restored']
    assert renderer.CAMERAS is camera_original
    assert len(state['cleanup_errors']) == (2 if cleanup else 0)
    assert state['trainer_unchanged'] is (not fail)
    return dict(original_step_calls=1,original_evaluator_calls=1,original128_quota_preserved=True,
        endpoint_before_reset=True,fullbody_camera_scoped_and_restored=True,all_hooks_restored=True,primary_error_preserved=error)



def primary_and_reporting_failure():
    @contextmanager
    def binding(*args):
        def fail(*unused): raise ValueError('primary execution fixture')
        yield types.SimpleNamespace(run=fail)
    @contextmanager
    def hooks(*args): yield
    stderr=io.StringIO()
    with tempfile.TemporaryDirectory() as directory, patch.object(subject,'HERE',Path(directory)), \
        patch.object(subject,'gate',return_value=({'input_pins':{}},set())), \
        patch.object(subject.learning,'binding',binding), patch.object(subject,'hooks',hooks), \
        patch.object(subject.pre,'sha',return_value='fixture-sha'), \
        patch.object(subject.pre,'write',side_effect=OSError('report write fixture')), \
        patch.dict(sys.modules,{'isaacgym':types.ModuleType('isaacgym')}), redirect_stderr(stderr):
        try:
            subject.execute()
        except ValueError as error:
            assert str(error)=='primary execution fixture'
        else: raise AssertionError('Primary execution error was lost')
    assert 'report write fixture' in stderr.getvalue()
    return dict(primary_execution_error_preserved=True,report_write_error_reported_on_stderr=True)


def main():
    successes=[run_case(),run_case(True),run_case(True,True),primary_and_reporting_failure()]
    fake_torch=types.SimpleNamespace(is_tensor=lambda value:False)
    original={'groups':[{'lr':.001}],'updates':300}
    assert subject.same(original,copy.deepcopy(original),fake_torch)
    assert not subject.same(original,{'groups':[{'lr':.002}],'updates':300},fake_torch)
    assert not subject.same(original,{'groups':[{'lr':.001}],'updates':299},fake_torch)
    assert not any(name=='isaacgym' or name=='torch' or name.startswith('numpy') for name in sys.modules)
    report=dict(schema='diagnostic.current_ring_video_cpu.v1',passed=True,python=sys.version,
        source_sha256=subject.pre.sha(HERE/'video.py'),tests=successes,real_native_imports=0,real_NN_constructions=0,
        real_checkpoint_loads=0,real_GPU_execution=False,limitation='Mocked hook/lifecycle only; actual pixels, strict load, model/optimizer tensors and replay equality await reviewed native execution.')
    subject.pre.write(HERE/'cpu_verification.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
