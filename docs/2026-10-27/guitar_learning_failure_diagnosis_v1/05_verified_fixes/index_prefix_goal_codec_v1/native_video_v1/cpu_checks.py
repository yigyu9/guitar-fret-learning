"""Goal-render header/identity/one-conversion/cleanup checks without native execution."""
import copy
from contextlib import contextmanager,redirect_stderr
import json
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(video):
    import numpy as np
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.finger_skill_runner import _validate_pins
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    payload=torch.load(video.CHECKPOINT,map_location='cpu',weights_only=False);before=copy.deepcopy(payload['metadata']);settings=video.parent.settings();extra=video.parent.support();codec=video.source.support()
    metadata=video.header(payload,0,settings,extra.SCHEMA);assert metadata is payload['metadata'];_validate_pins(metadata)
    for kind in ('schema','policy','layer','updates','procedure'):
        bad=copy.deepcopy(payload)
        if kind=='schema':bad['metadata']['schema']=extra.SCHEMA
        elif kind=='policy':bad['identity']['architecture']['schema']='diagnostic.index_prefix_policy.v1'
        elif kind=='layer':bad['identity']['architecture']['contract']['action'].pop('policy_output_adapter')
        elif kind=='updates':bad['updates']=300
        else:bad['metadata']['actual_initialization']['steps']=2000
        try:video.header(bad,0,settings,extra.SCHEMA)
        except ValueError:pass
        else:raise AssertionError('Wrong goal checkpoint identity admitted: '+kind)
    policy=codec.policy_type(video.source)(contract=payload['identity']['architecture']['contract'],size='large',fresh=False)
    trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']));assert trainer._identity()==payload['identity']
    try:trainer.load(video.CHECKPOINT)
    except ValueError as error:assert str(error)=='CUDA RNG topology mismatch'
    else:raise AssertionError('Unexpected CPU CUDA restore')
    with tempfile.TemporaryDirectory() as temp:
        projected=Path(temp)/'CPU_projection.pt';torch.save(dict(payload,cuda_rng=None),projected);trainer.load(projected)
    assert trainer.updates==0 and len(policy.state_dict())==73 and all(torch.equal(v,payload['model'][n]) for n,v in policy.state_dict().items())
    assert trainer.actor_optimizer.state_dict()==payload['actor_optimizer'] and trainer.value_optimizer.state_dict()==payload['value_optimizer'] and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
    assert payload['metadata']==before and video.grid.sha(video.CHECKPOINT)==video.SHA
    helper=video.module('goal_original_native_renderer',video.HELPER);aliases=(helper.producer,helper.header,helper.grid,codec.convert)
    requested=torch.ones(1,39);raw=torch.zeros(1,39);absolute=torch.ones(1,4)
    @contextmanager
    def fake_scope(probe,stage,seal,paths,observed):
        assert probe is video.source and stage=='evaluate'
        observed.update(reference_calls=0,goal_aliases_restored=True,records=[])
        yield
    for fail in (False,True):
        state=dict(conversion_calls=0,metadata_outputs=[],aliases_restored=False)
        with patch.object(codec,'execution_scope',fake_scope),patch.object(codec,'convert',return_value=(requested,absolute)) as delegate,patch.object(video.grid,'write'):
            expected=(helper.producer,helper.header,helper.grid,codec.convert)
            try:
                with video.adapter(helper,state):
                    assert helper.header(payload,0,settings,extra.SCHEMA) is metadata
                    with helper.producer.execution_scope('evaluate',{},set(),{}):result=codec.convert(object(),raw)
                    assert result[0] is requested and result[1] is absolute and delegate.call_count==state['conversion_calls']==1
                    value=dict(schema='old',selected_target_count=3);helper.grid.write(video.OUT/'capture_metadata.json',value)
                    assert value['schema']=='old' and video.grid.write.call_args[0][1]['schema']==video.VIDEO_SCHEMA
                    if fail:raise BrokenPipeError('CPU encoder primary')
            except BrokenPipeError:assert fail
            assert (helper.producer,helper.header,helper.grid,codec.convert)==expected and state['aliases_restored']
    assert (helper.producer,helper.header,helper.grid,codec.convert)==aliases
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);write=video.grid.write
        for mode in ('good','encoder','metadata','raw'):
            out=root/mode;fake=SimpleNamespace(producer=object(),header=object(),grid=object());old=(fake.producer,fake.header,fake.grid)
            def body(checkpoint,path,update,seal,paths):
                assert checkpoint==video.CHECKPOINT and update==0 and path==out;path.mkdir()
                observed={}
                with fake.producer.execution_scope('evaluate',seal,paths,observed):codec.convert(object(),raw)
                try:fake.grid.write(path/'capture_metadata.json',{})
                finally:fake.grid.write(path/'report.json',dict(completed=mode in ('good','raw'),episode_summary=dict(steps=1)))
                if mode=='encoder':raise BrokenPipeError('original encoder primary')
            def output(path,value):
                if mode=='metadata' and Path(path).name=='capture_metadata.json':raise OSError('metadata primary')
                write(path,value)
            fake.render_native=body
            def raw_save(state):
                if mode=='raw':raise OSError('typed raw secondary')
                return True
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}),patch.object(video,'OUT',out),patch.object(video,'gate',return_value=({},set())),patch.object(video,'module',return_value=fake),\
                    patch.object(codec,'execution_scope',fake_scope),patch.object(codec,'convert',return_value=(requested,absolute)),patch.object(video.grid,'write',side_effect=output),patch.object(video,'save_goals',side_effect=raw_save):
                try:video.execute()
                except OSError as error:assert mode!='good' and str(error)=={'encoder':'original encoder primary','metadata':'metadata primary','raw':'typed raw secondary'}[mode]
                else:assert mode=='good'
            report=video.grid.read(out/'goal_video_report.json');assert report['completed']==(mode=='good') and report['checks']['goal_conversion_once'] and report['checks']['aliases_restored']
            if mode=='metadata':assert not report['checks']['metadata_recorded'] and not (out/'capture_metadata.json').exists()
            if mode=='raw':assert report['secondary_failure']['message']=='typed raw secondary' and not report['checks']['typed_goal_records_saved']
            assert (fake.producer,fake.header,fake.grid)==old
        # Helper completed; preserve the first typed-raw error even if its audit write also fails.
        out=root/'double';stderr=io.StringIO()
        def successful_body(checkpoint,path,update,seal,paths):path.mkdir();write(path/'report.json',dict(completed=True,episode_summary=dict(steps=1)))
        fake=SimpleNamespace(producer=object(),header=object(),grid=object(),render_native=successful_body)
        old=(fake.producer,fake.header,fake.grid,codec.convert)
        def failed_report(path,value):
            if Path(path).name=='goal_video_report.json':raise OSError('audit secondary')
            write(path,value)
        with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}),patch.object(video,'OUT',out),patch.object(video,'gate',return_value=({},set())),patch.object(video,'module',return_value=fake),patch.object(video,'save_goals',side_effect=ValueError('typed raw primary')),patch.object(video.grid,'write',side_effect=failed_report),redirect_stderr(stderr):
            try:video.execute()
            except ValueError as error:assert str(error)=='typed raw primary'
            else:raise AssertionError('Typed raw first error hidden by audit write failure')
        assert 'audit secondary' in stderr.getvalue() and (fake.producer,fake.header,fake.grid,codec.convert)==old
        row={k:np.asarray(1) for k in ('start_clock','clock','raw_goal_normalized','decoded_goal_rad','requested_NN_action','old_target_rad','final_target_rad','raw_DIP_target_rad','final_DIP_target_rad','current_goal')};row['env_id']=0
        out=root/'typed';out.mkdir()
        with patch.object(video,'OUT',out):assert video.save_goals(dict(observed=dict(records=[row])))
        for name in ('observations4.npz','goal_codec_env0.npz'):
            data=dict(np.load(out/name,allow_pickle=False));assert all(np.array_equal(a,np.asarray([row[k]])) for k,a in data.items())
        for name in ('existing','symlink'):
            out=root/name
            if name=='existing':out.mkdir()
            else:out.symlink_to(root/'missing')
            with patch.object(video,'OUT',out),patch.object(video,'evidence',side_effect=AssertionError('late evidence')) as evidence:
                try:video.gate()
                except FileExistsError:pass
                else:raise AssertionError('Existing output allowed')
                evidence.assert_not_called()
    audit=video.recovery.module('goal_video_global_names_audit',video.recovery.HERE/'audit.py');static={p.name:audit.unresolved(p) for p in video.HERE.glob('*.py')};assert not any(static.values())
    qa=video.parent.HERE/'native_video_v1/qa/results_v1';review=video.grid.read(qa/'review.json');assert video.grid.sha(qa/'review.json')=='541586a680b8eaa2b7ee15c56e249e0a0d140fc8868096cace679dcac8db6fb3';assert review['verdict']=='PASS' and not review['findings']
    assert video.grid.read(qa/'verification.json')['verified_input_sha256'][str(video.HELPER)]==video.grid.sha(video.HELPER)
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    return dict(CPU_only=True,GPU_executed=False,checkpoint_sha256=video.SHA,metadata_original_unmodified=True,model73_identity_exact=True,PPO_empty0=True,
        wrong_schema_policy_layer_update_procedure_rejected=True,original_CPU_CUDA_topology_rejected=True,CPU_projection_only_cuda_rng_omitted=True,
        goal_conversion_one_delegate_call=True,goal_scope_evaluate_only=True,aliases_exception_restore=True,metadata_write_failure_truthful=True,typed_raw_write_error_preserved=True,typed_raw_primary_and_audit_secondary_preserved=True,
        primary_encoder_error_and_report_preserved=True,typed_goal_records_saved_and_reloaded=True,existing_and_symlink_output_rejected_before_evidence=True,symtable_referenced_globals=static,
        reused_capture_QA_review_sha256=video.grid.sha(qa/'review.json'),native_full_CUDA_restore_executed=False,native_pixels_codec_executed=False,
        scope='CPU adapter/identity only; original capture camera/encoder/BrokenPipe proof reused; actual renderer must full-load original checkpoint and perform once-per-control conversion counter check')
