"""CPU checks only for the thin render dispatch; reviewed guard math is reused."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch
import sys


def check(video):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training import finger_skill_runner
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    outer=(video.B.base.output,video.B.base.checkpoint,video.B.base.HERE,video.B.base.gate,video.B.base.effort_scope)
    aliases=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer,runner._pins,finger_skill_runner._pins)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);out=root/'runs/guard';out.mkdir(parents=True);(out/'keep').write_text('preserve')
        with patch.object(video,'HERE',root),patch.object(video,'gate',side_effect=AssertionError('Must reject output before gate')):
            try:video.launch()
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            assert (out/'keep').read_text()=='preserve';(out/'keep').unlink();out.rmdir();out.symlink_to(root/'missing')
            try:video.launch()
            except (ValueError,FileExistsError):pass
            else:raise AssertionError('Dangling output admitted')
            out.unlink()
        calls=[]
        def fake_render(phase,control,update):
            assert (phase,control,update)==('render',None,300)
            assert video.B.base.output(phase,None,update)==out and video.B.base.checkpoint(update)==video.B.checkpoint(300)
            state=dict(out=out,cleanup_errors=[])
            with video.B.base.effort_scope(set(),state) as current:
                assert current is runner and runner.ShortPool is runtime.ShortPool and runner.ShortPool is not aliases[0]
                assert runner._pins is finger_skill_runner._pins and runner._pins is not aliases[-1]
                assert runner._evaluate is not aliases[2] and runner.DecisionPPOTrainer is not aliases[3]
                calls.append('render entered; evaluator/trainer callbacks unused')
                raise RuntimeError('CPU renderer primary')
        with patch.object(video,'HERE',root),patch.object(video,'gate',return_value=({},set())),patch.object(video.B.base,'launch',fake_render),patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}):
            try:video.launch()
            except RuntimeError as error:assert str(error)=='CPU renderer primary'
            else:raise AssertionError('Primary renderer error swallowed')
            assert calls==['render entered; evaluator/trainer callbacks unused']
            with patch.object(video,'finish',side_effect=ValueError('CPU cleanup secondary')):
                try:video.launch()
                except RuntimeError as error:assert str(error)=='CPU renderer primary'
                else:raise AssertionError('Secondary cleanup masked primary')
        assert outer==(video.B.base.output,video.B.base.checkpoint,video.B.base.HERE,video.B.base.gate,video.B.base.effort_scope)
        assert aliases==(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer,runner._pins,finger_skill_runner._pins)
        # A renderer failure retains the whole128 completed prefix plus separate aborted control.
        out.mkdir();row=dict(first_attempt=np.ones(128,bool),final_target_rad=np.ones(128,np.float32))
        audit=dict(rows=[row],aborted_control=dict(first_attempt=np.ones(128,bool)),observer_aliases_restored=True)
        error=dict(type='BrokenPipeError',message='CPU native encoder fixture')
        video.finish(out,audit,{},error)
        with np.load(out/'dip_control60.npz') as raw:assert raw['first_attempt'].shape==(1,128)
        with np.load(out/'dip_aborted_control.npz') as raw:assert raw['first_attempt'].shape==(128,)
        r=video.grid.read(out/'guard_video_report.json');override=video.grid.read(out/'execution_override.json')
        assert r['failure']==error and not r['completed'] and r['checks']['evaluation_callback_not_used']
        assert override['evaluator_fingerprint_callback_used'] is False
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,original_render_phase_output_checkpoint=True,existing_output_and_symlink_pre_gate_rejection=True,
        observer_runtime_alias_and_two_pins_scope=True,all_aliases_restored_on_renderer_error=True,primary_and_secondary_errors_preserved=True,
        partial_whole128_sidecar_saved=True,evaluator_fingerprint_not_claimed=True,
        limits='No native scene, codec/pixels, renderer numerical identity or new full128 outcome certified; original guard CPU/math and strictcap128 reviews reused')
