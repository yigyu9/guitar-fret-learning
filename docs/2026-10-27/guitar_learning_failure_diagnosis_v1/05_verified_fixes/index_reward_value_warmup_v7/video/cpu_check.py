"""Python3.8 stdlib fixtures; no checkpoint, warmup, model, or native execution."""
import importlib.machinery
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch
import video


def check():
    complete = dict(assigned_quotas=[1]*128,episodes=[dict(env_id=i,selected_target_count=3,
        notes=[dict(source_index=n) for n in (4,7,8)]) for i in range(128)])
    video.validate_ledger(complete)
    missing = copy.deepcopy(complete);del missing['episodes']
    short = copy.deepcopy(complete);short['episodes'].pop()
    duplicate = copy.deepcopy(complete);duplicate['episodes'][-1]['env_id'] = 0
    two_notes = copy.deepcopy(complete);two_notes['episodes'][0]['notes'].pop()
    wrong_note = copy.deepcopy(complete);wrong_note['episodes'][0]['notes'][2]['source_index'] = 9
    wrong_count = copy.deepcopy(complete);wrong_count['episodes'][0]['selected_target_count'] = 2
    for invalid in (missing,short,duplicate,two_notes,wrong_note,wrong_count):
        try: video.validate_ledger(invalid)
        except (KeyError,AssertionError): pass
        else: raise AssertionError('Incomplete or malformed source ledger admitted')
    try: video.parent.gate();parent_gate = 'PASS'
    except (AssertionError,FileNotFoundError):
        path = video.PARENT/'preparation_seal.json'
        if path.is_file():
            seal = video.base.read(path)
            assert seal['independent_review'] == 'pending' and not video.base.changed_pins(seal['input_pins'])
            parent_gate = 'pending independent review; source pins verified'
        else: parent_gate = 'pending core preparation; no parent seal yet'
    previous_video = sys.modules.get('video')
    try:
        sys.modules['video'] = video.adapter
        reused_result = video.module('warmup_video_v6_CPU',video.SOURCE/'cpu_check.py').check()
    finally:
        if previous_video is None: sys.modules.pop('video',None)
        else: sys.modules['video'] = previous_video
    names = ('runtime','learn','cameras')
    saved = {name:sys.modules.get(name) for name in names}
    sentinels = {name:ModuleType('existing_'+name) for name in names}
    sys.modules.update(sentinels)
    old = video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base,video.reused.preflight
    paths = list(sys.path)
    try:
        for failure in ('none','body','learn_load'):
            sentinel = RuntimeError('V7 local module fixture')
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
                            assert sys.modules['runtime'] is modules['runtime'] and sys.modules['learn'] is modules['learn']
                            assert sys.modules['cameras'] is video.cameras and implementation.PARENT == video.PARENT
                            assert implementation.preflight is video.preflight
                            if failure == 'body': raise sentinel
            except RuntimeError as error: assert error is sentinel and failure != 'none'
            else: assert failure == 'none'
            assert all(sys.modules[name] is sentinels[name] for name in names) and sys.path == paths
            assert (video.reused.HERE,video.reused.PARENT,video.reused.parent,video.reused.base,video.reused.preflight) == old
    finally:
        for name,original in saved.items():
            if original is None: sys.modules.pop(name,None)
            else: sys.modules[name] = original
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp);evaluation = folder/'evaluation';evaluation.mkdir()
        video.base.write(evaluation/'settings.json',dict(fixture=True))
        (folder/'PLAN.md').write_text('fixture');video.base.write(folder/'cpu_verification.json',dict(fixture=True))
        checkpoint = folder/'fixture.pt';checkpoint.write_bytes(b'not a model; never loaded')
        old = video.HERE,video.preflight
        try:
            video.HERE,video.preflight = folder,lambda *args:{str(checkpoint):video.base.sha(checkpoint)}
            video.prepare(checkpoint,evaluation)
            replay = folder/'inputs/replay.json'
            info = video.base.read(replay)
            assert info['selected_control'] == 'actual V7 NN only' and info['accepted_value_warmup_steps'] == 1000
            assert video.base.read(folder/'inputs/settings.json') == dict(fixture=True)
            assert video.base.read(folder/'preparation_seal.json')['input_pins'][str(replay)] == video.base.sha(replay)
        finally: video.HERE,video.preflight = old
    assert not any(name in sys.modules for name in ('torch','numpy','isaacgym'))
    return dict(CPU_only=True,native_runs=0,checkpoint_loads=0,value_warmup_steps=0,parent_gate=parent_gate,
        actual_V7_local_modules_with_stub_loaders=True,success_body_and_loader_errors_restore_all_aliases=True,
        actual_V7_label_accepted1000_declaration_and_replay_SHA=True,sealed_evaluation_settings_copied=True,
        source128_unique_envs_and_three_notes384_verified=True,malformed_ledger_negative_fixtures=6,
        immutable_V6_camera_lifecycle=reused_result,selected_final300_pair_pending=True,
        python_version=sys.version.split()[0],interpreter=sys.executable)


if __name__ == '__main__': print(json.dumps(check(),indent=2))
