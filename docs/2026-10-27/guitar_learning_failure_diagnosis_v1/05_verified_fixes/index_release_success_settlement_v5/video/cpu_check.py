"""Python3.8 stdlib fixture for reused cameras and exception-safe V5 binding."""
import json
import importlib.util
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import video


def check():
    video.parent.gate()
    video.reused.gate()
    # Run the existing camera lifecycle fixtures against their frozen V4 globals.
    saved = {name:sys.modules.get(name) for name in ('video','cameras')}
    try:
        sys.modules['video'],sys.modules['cameras'] = video.reused,video.cameras
        fixture = video.module('settlement_video_camera_fixture',video.SOURCE/'cpu_check.py')
        result = fixture.check()
    finally:
        for name,original in saved.items():
            if original is None: sys.modules.pop(name,None)
            else: sys.modules[name] = original
    old = video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base
    path = list(sys.path)
    names = ('runtime','learn','cameras')
    saved = {name:sys.modules.get(name) for name in names}
    sentinels = {name:ModuleType('existing_'+name) for name in names}
    sys.modules.update(sentinels)
    try:
        for fail in (False,True):
            error = RuntimeError('binding failure fixture')
            try:
                with video.replay_scope() as implementation:
                    assert implementation.HERE == video.HERE and implementation.PARENT == video.PARENT
                    assert implementation.parent.cap is video.parent.parent.cap
                    assert 'runtime' not in sys.modules and 'learn' not in sys.modules
                    assert sys.modules['cameras'] is video.cameras
                    assert Path(importlib.util.find_spec('runtime').origin) == video.PARENT/'runtime.py'
                    assert Path(importlib.util.find_spec('learn').origin) == video.PARENT/'learn.py'
                    if fail: raise error
            except RuntimeError as caught: assert caught is error and fail
            assert all(sys.modules[name] is sentinels[name] for name in names)
            assert (video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base) == old
            assert sys.path == path
    finally:
        for name,original in saved.items():
            if original is None: sys.modules.pop(name,None)
            else: sys.modules[name] = original
    assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
    old_evaluation = video.SOURCE.parent/'runs/ppo_eval_000300_det'
    try:
        video.preflight(video.SOURCE.parent/'runs/ppo_attempt02/final.pt',old_evaluation)
    except AssertionError: pass
    else: raise AssertionError('V4 reward-contract evaluation admitted as V5')
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        old = video.HERE,video.preflight,video.replay_scope
        def prepare_fixture(checkpoint,evaluation):
            (folder/'inputs').mkdir()
            replay = folder/'inputs/replay.json'
            video.base.write(replay,dict(selected_control='actual V4 NN only'))
            video.base.write(folder/'preparation_seal.json',dict(input_pins={str(replay):video.base.sha(replay)},independent_review='pending'))
        @contextmanager
        def scope_fixture():
            yield type('Fixture',(),dict(prepare=staticmethod(prepare_fixture)))
        try:
            video.HERE,video.preflight,video.replay_scope = folder,lambda *args:None,scope_fixture
            video.prepare('checkpoint fixture','evaluation fixture')
            replay = folder/'inputs/replay.json'
            assert video.base.read(replay)['selected_control'] == 'actual V5 NN only'
            assert video.base.read(folder/'preparation_seal.json')['input_pins'][str(replay)] == video.base.sha(replay)
        finally:
            video.HERE,video.preflight,video.replay_scope = old
    return dict(CPU_only=True,native_runs=0,checkpoint_loads=0,python_version=sys.version.split()[0],
        interpreter=sys.executable,reused_camera_lifecycle=result,
        V5_parent534_and_frozen_V4_video_gates_PASS=True,
        scoped_module_aliases_and_paths_restored_on_success_and_error=True,
        numerical_modules_resolve_only_V5=True,V4_evaluation_schema_rejected=True,
        prepared_selection_label_V5_and_SHA_updated=True,
        frozen_current_NN_evaluator_reused=True,final300_pair_pending=True)


if __name__ == '__main__': print(json.dumps(check(),indent=2))
