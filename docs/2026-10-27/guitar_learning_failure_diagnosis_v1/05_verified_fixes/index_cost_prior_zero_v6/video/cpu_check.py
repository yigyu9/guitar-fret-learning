"""Actual Python3.8, stdlib-only video binding fixtures; no model/native load."""
from contextlib import contextmanager
import importlib.machinery
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch
import video


def check():
    try:
        video.parent.gate();parent_gate = 'PASS'
    except (AssertionError,FileNotFoundError):
        seal = video.base.read(video.PARENT/'preparation_seal.json')
        assert seal['independent_review'] == 'pending' and not video.base.changed_pins(seal['input_pins'])
        parent_gate = 'pending independent review; source pins verified'
    video.reused.gate()
    saved = {name:sys.modules.get(name) for name in ('video','cameras')}
    try:
        sys.modules['video'],sys.modules['cameras'] = video.reused,video.cameras
        camera_result = video.module('cost_prior_video_camera_fixture',video.SOURCE/'cpu_check.py').check()
    finally:
        for name,old in saved.items():
            if old is None: sys.modules.pop(name,None)
            else: sys.modules[name] = old
    names = ('runtime','learn','cameras')
    saved = {name:sys.modules.get(name) for name in names}
    sentinels = {name:ModuleType('existing_'+name) for name in names}
    sys.modules.update(sentinels)
    old = video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base
    paths = list(sys.path)
    try:
        for failure in ('none','body','learn_load'):
            sentinel = RuntimeError('V6 module failure fixture')
            class Loader:
                def __init__(self,path): self.path = path
                def create_module(self,spec): return None
                def exec_module(self,module):
                    module.__file__ = str(self.path)
                    if module.__name__ == 'learn' and failure == 'learn_load': raise sentinel
            def factory(name,path):
                assert Path(path) == video.PARENT/(name+'.py')
                return importlib.machinery.ModuleSpec(name,Loader(path),origin=str(path))
            try:
                with patch('importlib.util.spec_from_file_location',factory):
                    with video.parent.local_modules(include_learn=True) as modules:
                        with video.replay_scope() as implementation:
                            assert sys.modules['runtime'] is modules['runtime']
                            assert sys.modules['learn'] is modules['learn']
                            assert sys.modules['cameras'] is video.cameras
                            assert implementation.PARENT == video.PARENT
                            assert implementation.parent.cap is video.parent.parent.parent.cap
                            if failure == 'body': raise sentinel
            except RuntimeError as error: assert error is sentinel and failure != 'none'
            else: assert failure == 'none'
            assert all(sys.modules[name] is sentinels[name] for name in names)
            assert sys.path == paths
            assert (video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base) == old
    finally:
        for name,old_module in saved.items():
            if old_module is None: sys.modules.pop(name,None)
            else: sys.modules[name] = old_module
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp);old = video.HERE,video.preflight,video.replay_scope
        def prepare_fixture(*args):
            (folder/'inputs').mkdir();replay = folder/'inputs/replay.json'
            video.base.write(replay,dict(selected_control='actual V4 NN only'))
            video.base.write(folder/'preparation_seal.json',dict(input_pins={str(replay):video.base.sha(replay)},independent_review='pending'))
        @contextmanager
        def fixture_scope(): yield type('Fixture',(),dict(prepare=staticmethod(prepare_fixture)))
        try:
            video.HERE,video.preflight,video.replay_scope = folder,lambda *args:None,fixture_scope
            video.prepare('checkpoint fixture','evaluation fixture')
            replay = folder/'inputs/replay.json'
            assert video.base.read(replay)['selected_control'] == 'actual V6 NN only'
            assert video.base.read(folder/'preparation_seal.json')['input_pins'][str(replay)] == video.base.sha(replay)
        finally: video.HERE,video.preflight,video.replay_scope = old
    previous = video.PARENT.parent/'index_release_success_settlement_v5'
    try: video.preflight(previous/'runs/ppo/final.pt',previous/'runs/ppo_eval_000300_det')
    except AssertionError: pass
    else: raise AssertionError('V5 evaluation admitted as V6')
    assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
    return dict(CPU_only=True,native_runs=0,checkpoint_loads=0,parent_gate=parent_gate,
        parent_pin_count=len(video.base.read(video.PARENT/'preparation_seal.json')['input_pins']),
        actual_local_modules_context_with_stub_loaders=True,
        success_body_error_and_loader_error_restore_aliases_paths_globals=True,
        actual_V6_label_and_replay_pin_SHA=True,V5_schema_rejected=True,
        reused_camera_lifecycle=camera_result,final300_pair_pending=True,
        python_version=sys.version.split()[0],interpreter=sys.executable)


if __name__ == '__main__': print(json.dumps(check(),indent=2))
