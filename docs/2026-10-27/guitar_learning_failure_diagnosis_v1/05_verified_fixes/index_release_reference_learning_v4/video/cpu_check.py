"""Stdlib camera lifecycle fixtures; no checkpoint, Torch, or native load."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from cameras import pool_type


def check():
    events,artifacts,holders = [],{},[]
    class Scalar:
        def clone(self): return self
        def __sub__(self,other): return 0.
        def detach(self): return self
        def cpu(self): return self
        def numpy(self): return self
        def copy(self): return 1.
    gym = SimpleNamespace(acquire_gym=lambda:'native',Vec3=lambda *args:args)
    original_acquire = gym.acquire_gym
    class Pool:
        def __init__(self,settings,out):
            assert gym.acquire_gym() == ('graphics','native')
            if settings.get('base_failure'): raise ValueError('base constructor fixture')
            self.scene = SimpleNamespace(gym=SimpleNamespace(set_camera_location=lambda *args:None),envs=[0])
            self.environment = SimpleNamespace(episode_reward_terms={str(i):[Scalar()] for i in range(9)})
            self.closed = False
        def step(self,action):
            events.append('NN-native-step');return None,[Scalar()],None,None,None,[]
        def close(self): self.closed = True;events.append('scene-close')
    class Capture:
        def __init__(self,*args): self.samples,self.frame_times_s,self.episode = [],[],None
        def record(self,*args):
            events.append('capture-before-reset');self.samples.append({})
    render = SimpleNamespace(_create_cameras=lambda *args:dict(hand=1,fullbody=2),
        _encoder=lambda path:object(),_EnvZeroCapture=Capture)
    base = SimpleNamespace(save_rows=lambda path,rows:artifacts.update({path.name:list(rows)}),
                           write=lambda path,value:artifacts.update({path.name:value}))
    np = SimpleNamespace(asarray=lambda value:value)
    with tempfile.TemporaryDirectory() as temp:
        Factory = pool_type(Pool,gym,np,render,lambda native:('graphics',native),
            lambda video:(0,[]),base,Path(temp),holders)
        pool = Factory({},Path(temp));assert gym.acquire_gym is original_acquire
        result = pool.step(None)
        assert result[0] is None and events[:2] == ['NN-native-step','capture-before-reset']
        assert len(pool.video_capture.samples[0]['reward_components9']) == 9
        pool.close();assert pool.closed and len(artifacts['native_capture.npz']) == 1
        assert not artifacts['capture.json']['completed']
        try: Factory(dict(base_failure=True),Path(temp))
        except ValueError as error: assert str(error) == 'base constructor fixture'
        else: raise AssertionError('Constructor failure swallowed')
        assert gym.acquire_gym is original_acquire
        class BrokenCapture(Capture):
            def record(self,*args):
                super().record(*args);raise BrokenPipeError('original record pipe')
        render._EnvZeroCapture = BrokenCapture
        broken = Factory({},Path(temp))
        try: broken.step(None)
        except BrokenPipeError as error: assert str(error) == 'original record pipe'
        else: raise AssertionError('Record pipe failure swallowed')
        assert set(broken.video_capture.samples[-1]) == {'reward','reward_components9'}
        broken.close();assert broken.closed
        sentinel = RuntimeError('camera constructor fixture')
        def bad_cameras(*args): raise sentinel
        render._create_cameras = bad_cameras
        try: Factory({},Path(temp))
        except RuntimeError as error: assert error is sentinel
        else: raise AssertionError('Camera constructor failure swallowed')
        assert holders[-1].closed and gym.acquire_gym is original_acquire
    assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
    import video
    fit = video.PARENT/'runs/fit'
    evaluation = video.PARENT/'runs/fit_deterministic'
    preflight_tested = False
    if (evaluation/'learning_report.json').is_file():
        video.preflight(fit/'fit.pt',evaluation)
        try: video.preflight(fit/'fresh.pt',evaluation)
        except AssertionError: pass
        else: raise AssertionError('Mismatched checkpoint/evaluation admitted')
        preflight_tested = True
    assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
    return dict(CPU_only=True,native_runs=0,checkpoint_loads=0,stdlib_only=True,
        constructor_acquire_restored_on_success_and_failure=True,actual_step_before_capture=True,
        partial_reward9_row_survives_encoder_pipe_error=True,scene_closed_after_camera_failure=True,
        primary_exception_preserved=True,source_replay_pending_checkpoint_selection=True,
        existing_fit_deterministic_preflight_and_wrong_checkpoint_rejection=preflight_tested,
        python_version=sys.version.split()[0],interpreter=sys.executable)


if __name__ == '__main__':
    print(json.dumps(check(),indent=2))
