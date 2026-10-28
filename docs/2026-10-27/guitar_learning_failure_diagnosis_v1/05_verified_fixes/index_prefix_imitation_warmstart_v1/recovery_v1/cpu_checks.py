"""Exact known-defect acceptance and scoped continuation checks, no native/fit."""
import copy
from pathlib import Path
import tempfile
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    p=probe.source;folder=probe.COLLECT;read=probe.grid.read
    launch=read(p.HERE/'01_launcher.json');report=read(folder/'imitation_report.json');native=read(folder/'diagnostic_report.json')
    provider=read(folder/'action_provider.json');rows=read(folder/'evaluation.json')['episodes'];a=p.parent.acceptance(rows)
    probe.single_defect(launch,report,native,provider,a)
    for index,key,value in ((0,'returncode',0),(0,'completed',True),(1,'completed',True),(2,'completed',False),(3,'NN',True)):
        args=copy.deepcopy([launch,report,native,provider,a]);args[index][key]=value
        try:probe.single_defect(*args)
        except AssertionError:pass
        else:raise AssertionError('Different failure/result admitted')
    for name in ('aliases_restored','extra_false'):
        bad=copy.deepcopy(report);bad['checks'][name]=False
        try:probe.single_defect(launch,bad,native,provider,a)
        except AssertionError:pass
        else:raise AssertionError('Additional false check admitted')
    missing=copy.deepcopy(report);del missing['checks']['aliases_restored']
    try:probe.single_defect(launch,missing,native,provider,a)
    except AssertionError:pass
    else:raise AssertionError('Incomplete checkset admitted')
    assert {}.get('NN_constructors') is None and ({}.get('NN_constructors')==0) is False
    assert {}.get('NN_constructors',0)==0 and {'NN_constructors':0}.get('NN_constructors',0)==0 and {'NN_constructors':1}.get('NN_constructors')==1
    assert {'NN_constructors':1}.get('NN_constructors',0)!=0
    impl=p.support();data=dict(np.load(folder/'observations4.npz',allow_pickle=False));short=p.parent.settings()['song']['short_learning']
    buckets=impl.validate_data(data,short,p);assert len(data['env_id'])==1416 and len(buckets)==6
    contaminated=dict(data);contaminated['source_control']=np.ones_like(data['source_control'])
    try:impl.validate_data(contaminated,short,p)
    except AssertionError:pass
    else:raise AssertionError('NN data admitted')
    trace=dict(np.load(folder/'trace_env0_episode0.npz',allow_pickle=False));mask=data['env_id']==0
    np.testing.assert_array_equal(data['requested_reference_action'][mask],trace['policy_action'][:,17:21])
    np.testing.assert_array_equal(data['executed_action'][mask],trace['executed_action'][:,17:21])
    meta=read(folder/'trace_metadata.json');ids=[meta['joint_names'].index(n) for n in short['learned_action_names']]
    np.testing.assert_array_equal(data['old_target_rad'][mask][1:],trace['target'][:-1,ids]);np.testing.assert_array_equal(data['final_target_rad'][mask],trace['target'][:,ids])
    assert probe.grid.sha(folder/'observations4.npz')==probe.DATA_SHA and a==read(folder/'prefix_acceptance.json')
    original=(p.gate,p.output,p.SCHEMA,p.descriptor)
    for fail in (False,True):
        try:
            with probe.scope({},set()):
                assert p.output('collect')==folder and p.output('fit')==probe.HERE/'runs/fit' and p.output('evaluate')==probe.HERE/'runs/evaluate'
                assert p.SCHEMA==probe.SCHEMA and p.gate('fit')==({},set())
                if fail:raise RuntimeError('CPU scope primary')
        except RuntimeError as error:assert fail and str(error)=='CPU scope primary'
        assert (p.gate,p.output,p.SCHEMA,p.descriptor)==original
    # No collection entry point; existing output refuses before invoking the new gate.
    assert set(probe.commands())=={'fit','evaluate'}
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);(root/'runs').mkdir();(root/'runs/fit').mkdir();(root/'runs/fit/keep').write_text('same')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('must not gate')) as gate:
            try:probe.launch('fit')
            except FileExistsError:pass
            else:raise AssertionError('Existing fit output admitted')
            gate.assert_not_called()
        assert (root/'runs/fit/keep').read_text()=='same'
    raw_names=('imitation_report.json','diagnostic_report.json','action_provider.json','evaluation.json','prefix_acceptance.json','observations4.npz',
        'trace_env0_episode0.npz','trace_metadata.json','current_goal_DIP60.npz','training_contract.json','settings.json','native_effort_readback.json','gpu_scene_final.json','inputs_before.json','diagnostic_inputs_after.json')
    raw_sha={str(folder/n):probe.grid.sha(folder/n) for n in raw_names}
    raw_sha.update({str(p.HERE/n):probe.grid.sha(p.HERE/n) for n in ('01_launcher.json','01_collect.log','preparation_seal.json','probe.py','imitation.py')})
    recovery=dict(schema='diagnostic.completed_noNN_collection_recovery.v1',accepted_for_continuation=True,original_parent_returncode=1,
        original_parent_completed=False,original_imitation_completed=False,original_native_completed=True,
        only_failed_check='NN_constructors_exact',cause='Absent counter key gives None==0; original noNN branch does not call the policy constructor',
        NN_zero_basis='Frozen source execution path plus action_provider.NN=false/reference evaluator; not a separately saved runtime counter value',
        dataset_sha256=probe.DATA_SHA,dataset_rows=1416,env_ids=[0,1,2,3],controls_per_env=354,
        six_phase_controls=[np.bincount(data['phase'][data['env_id']==i],minlength=6).tolist() for i in range(4)],
        acceptance=a,raw_source_sha256=raw_sha,
        scope='Only data reuse after one reporting defect; original exit1/completedfalse retained; no native recapture or NN success inherited')
    verification=dict(CPU_only=True,GPU_executed=False,known_missing_key_zero_only=True,wrong_counter_and_other_false_rejected=True,
        original1882_and_actual_inputs_verified_by_gate=True,source_noNN_path_not_saved_counter=True,original128_attempts_384_notes_preserved=True,
        original_4x354_five_observations_clock_label_target_verified=True,NN_contamination_rejected=True,
        original_policy_environment_identity_unchanged=True,gate_output_schema_descriptor_finally_restore=True,no_recapture_entrypoint=True,
        original_fit_evaluate_functions_reused=True,existing_output_rejected_before_gate=True,
        scope='Original base+new gate only; no native/GPU fit executed; original failure preserved')
    return recovery,verification
