"""CPU checks for the metadata adapter; no native render or source mutation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(video):
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.finger_skill_runner import _validate_pins
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1);assert video.grid.sha(video.CHECKPOINT)==video.SHA
    payload=torch.load(video.CHECKPOINT,map_location='cpu',weights_only=False);extra=video.parent.support();settings=video.parent.settings()
    metadata=video.header(payload,0,settings,extra.SCHEMA);before=copy.deepcopy(payload['metadata']);assert metadata is payload['metadata'];_validate_pins(metadata)
    for field in ('schema','steps','updates'):
        bad=copy.deepcopy(payload)
        if field=='schema':bad['metadata']['schema']=extra.SCHEMA
        elif field=='steps':bad['metadata']['actual_initialization']['steps']=999
        else:bad['updates']=300
        try:video.header(bad,0,settings,extra.SCHEMA)
        except ValueError:pass
        else:raise AssertionError('Wrong schema/procedure/PPO update admitted')
    policy=extra.PrefixPolicy(contract=payload['identity']['architecture']['contract'],size=settings['size'],fresh=False)
    trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']));assert trainer._identity()==payload['identity'] and len(payload['model'])==73
    topology=False
    try:trainer.load(video.CHECKPOINT)
    except ValueError as error:assert str(error)=='CUDA RNG topology mismatch' and payload['cuda_rng'] is not None;topology=True
    else:assert payload['cuda_rng'] is None
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'CPU_projection.pt';torch.save(dict(payload,cuda_rng=None),p);trainer.load(p)
    assert trainer.updates==0 and all(torch.equal(v,payload['model'][k]) for k,v in policy.state_dict().items())
    for name in ('actor_optimizer','value_optimizer'):
        actual=getattr(trainer,name).state_dict();assert not actual['state'] and actual==payload[name]
    assert payload['metadata']==before and video.grid.sha(video.CHECKPOINT)==video.SHA
    # Exercise the narrow alias/metadata scope with the same body arguments, never native.
    helper=video.module('warmstart_native_prefix_renderer',video.HELPER);original=(helper.producer,helper.header,helper.grid);reference=extra.reference_action
    outputs=[]
    for fail in (False,True):
        state=dict(reference_calls=0,metadata_outputs=[],aliases_restored=False)
        with patch.object(video.grid,'write',side_effect=lambda p,v:outputs.append((str(p),v))):
            try:
                with video.adapter(helper,state):
                    assert helper.producer is video.parent and helper.header is video.header
                    assert helper.header(payload,0,settings,extra.SCHEMA) is metadata
                    raw=dict(schema='old_video_output',checkpoint_training_updates=0,training_updates=0,selected_target_count=3)
                    helper.grid.write(video.OUT/'capture_metadata.json',raw)
                    assert raw['schema']=='old_video_output' and outputs[-1][1]['schema']==video.VIDEO_SCHEMA and outputs[-1][1]['PPO_updates']==0
                    assert outputs[-1][1]['actual_initialization']==video.recovery.descriptor()
                    helper.grid.write(video.OUT/'report.json',raw)
                    if fail:extra.reference_action(None)
            except RuntimeError as error:assert fail and str(error)=='No reference/N allowed in warmstart NN video'
            else:assert not fail
        assert state['aliases_restored'] and (helper.producer,helper.header,helper.grid)==original and extra.reference_action is reference
        assert state['reference_calls']==int(fail) and set(state['metadata_outputs'])=={'capture_metadata.json','report.json'}
    # Only a fake native module/body: preserve the primary error and failure sidecar.
    with tempfile.TemporaryDirectory() as temp:
        original_write=video.grid.write
        for mode in ('encoder','metadata'):
            out=Path(temp)/mode;fake=SimpleNamespace(producer=object(),header=object(),grid=object())
            aliases=(fake.producer,fake.header,fake.grid)
            def fail_write(path,value):
                if mode=='metadata' and Path(path).name=='capture_metadata.json':raise OSError('CPU metadata write error')
                original_write(path,value)
            def fail_body(checkpoint,path,update,seal,paths):
                assert checkpoint==video.CHECKPOINT and path==out and update==0
                path.mkdir()
                if mode=='metadata':
                    try:fake.grid.write(path/'capture_metadata.json',{})
                    finally:fake.grid.write(path/'report.json',dict(completed=False))
                else:
                    fake.grid.write(path/'report.json',dict(completed=False));raise BrokenPipeError('CPU original encoder error')
            fake.render_native=fail_body
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}),patch.object(video,'OUT',out),patch.object(video,'gate',return_value=({},set())),patch.object(video,'module',return_value=fake),patch.object(video.grid,'write',side_effect=fail_write):
                try:video.execute()
                except OSError as error:assert str(error)==('CPU metadata write error' if mode=='metadata' else 'CPU original encoder error')
                else:raise AssertionError('Primary file/encoder failure swallowed')
            report=video.grid.read(out/'initialization_video_report.json')
            assert not report['completed'] and report['failure']['type']==('OSError' if mode=='metadata' else 'BrokenPipeError')
            assert report['checks']['aliases_restored'] and not report['checks']['actual_metadata_recorded'] and report['reference_calls']==0
            assert (fake.producer,fake.header,fake.grid)==aliases and (out/'report.json').is_file() and not (out/'capture_metadata.json').exists()
    # Reuse the completed original capture/camera/BrokenPipe proof by immutable SHA.
    qa=video.parent.HERE/'native_video_v1/qa/results_v1';review=video.grid.read(qa/'review.json')
    assert video.grid.sha(qa/'review.json')=='541586a680b8eaa2b7ee15c56e249e0a0d140fc8868096cace679dcac8db6fb3'
    assert review['verdict']=='PASS' and not review['findings']
    verification=video.grid.read(qa/'verification.json');assert verification['verified_input_sha256'][str(video.HELPER)]==video.grid.sha(video.HELPER)
    code="""import runpy,sys,json
v=runpy.run_path(sys.argv[1],run_name='warmstart_video_fresh_gate')
blocked=False
try:v['gate']()
except (FileNotFoundError,AssertionError):blocked=True
assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
print(json.dumps({'unreviewed_blocked':blocked,'stdlib_only':True}))
"""
    value=subprocess.run([video.grid.PYTHON,'-B','-c',code,str(video.HERE/'render.py')],capture_output=True,text=True,check=True)
    fresh=json.loads(value.stdout);assert fresh['stdlib_only']
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,actual_checkpoint=str(video.CHECKPOINT),checkpoint_sha256=video.SHA,model73_exact=True,original_identity_exact=True,
        metadata_original_unmodified=True,new_schema_procedure_PPO0_validated=True,wrong_schema_steps_updates_rejected=True,freshFalse=True,
        original_CPU_load_CUDA_topology_rejected=topology,CPU_projection_only_cuda_rng_omitted=True,original_full_model_optimizer_load=True,PPO_updates=0,PPO_optimizers_empty=True,
        aliases_exception_metadata_reference_forbidden=True,primary_encoder_error_and_failure_sidecar_preserved=True,failed_metadata_not_marked_recorded=True,fresh_process_gate=fresh,reused_original_capture_QA_review_sha256=video.grid.sha(qa/'review.json'),
        native_CUDA_restore_executed=False,native_pixels_codec_executed=False,
        scope='Original checkpoint untouched; CPU projection excludes only CUDA RNG restoration; native must full-load original file. Frozen original helper proof reused without recapture.')
