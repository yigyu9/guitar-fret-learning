"""CPU-only derived geometry/task checks; native4 verifier stays in original parent."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    from guitar_learning.tests.test_gpu_environment import fixture
    teacher=probe.grid.read(probe.TEACHER);reference=probe.grid.read(probe.REFERENCE)
    a=probe.grid.read(probe.prior.INPUTS['index'][0]);aref=probe.grid.read(probe.prior.INPUTS['index'][1])
    geometry=probe.grid.read(probe.HERE/'cpu_inputs/geometry_derivation.json')
    assert geometry==probe.geometry_derivation()
    np.testing.assert_allclose(np.array(teacher['wrist_position_G_m'])-a['wrist_position_G_m'],geometry['delta_G_m'],rtol=0,atol=1e-16)
    assert teacher['arm_targets_rad']==a['arm_targets_rad'] and teacher['wrist_quaternion_G_xyzw']==a['wrist_quaternion_G_xyzw']
    assert reference['selected_targets_rad']==aref['selected_targets_rad']
    assert not {'source_row','source_time_s','diagnostic_metadata','native_direct_readback','success'}&teacher.keys()
    config=probe.grid.read(probe.HERE/'cpu_inputs/index_settings.json');short=config['song']['short_learning']
    expected=probe.grid.read(probe.HERE/'cpu_inputs/expected_environment.json')
    meta,_=fixture(1);meta['action_contract']=probe.grid.read(probe.prior.FRESH/'runs/index/training_contract.json')['action']['target_contract']
    env=runtime.ShortEnvironment(meta,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    assert env.contract==expected and short['view']['duration_ticks']==257 and env.selected_index==7
    saved=(probe.prior.HERE,probe.prior.INPUTS,runtime.ShortPool);closed=[]
    class Pool:
        def __init__(self,settings,out):
            self.spec=copy.deepcopy(short);self.environment=SimpleNamespace(contract=copy.deepcopy(expected),task=env.task,selected_index=7)
            if mode=='bad_task':self.environment.selected_index=4
            if mode=='bad_contract':self.environment.contract['task']['short_learning']['view']['duration_ticks']=221
        def close(self):
            closed.append(True)
            if mode=='bad_contract':raise RuntimeError('CPU close failure')
    with tempfile.TemporaryDirectory() as folder:
        with patch.object(runtime,'ShortPool',Pool):
            for mode in ('good','bad_task','bad_contract'):
                out=Path(folder)/mode;out.mkdir();state=dict(cleanup_errors=[]);before=len(closed)
                try:
                    with probe.selected_inputs(state):runtime.ShortPool(config,out)
                except AssertionError:assert mode!='good' and len(closed)==before+1
                else:assert mode=='good' and state['task_verified']
                assert state['aliases_restored'] and probe.prior.HERE is saved[0] and probe.prior.INPUTS is saved[1] and runtime.ShortPool is Pool
                assert state['cleanup_errors']==([dict(type='RuntimeError',message='CPU close failure')] if mode=='bad_contract' else [])
        assert runtime.ShortPool is saved[2]
        root=Path(folder)/'guard';out=root/'runs/index';out.mkdir(parents=True);sentinel=out/'sentinel';sentinel.write_bytes(b'keep')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('gate must not run')):
            try:probe.launch()
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            assert sentinel.read_bytes()==b'keep' and not list(out.glob('*.json'))
            sentinel.unlink();out.rmdir();out.symlink_to(root/'absent')
            try:probe.launch()
            except (FileExistsError,ValueError):pass
            else:raise AssertionError('Dangling output admitted')
        # Early failed env0 has no post-ramp evidence; retain all4 failed attempts.
        out=Path(folder)/'postcheck';out.mkdir()
        episodes=[dict(env_id=i,target_id=probe.B_ID,steps=1,achieved=False,clean_fraction=0.,audible_wrong_fraction=0.,
            reward_components={str(j):0. for j in range(9)},termination=dict(physical_failure=True,wrist_failure=False)) for i in range(4)]
        probe.grid.write(out/'evaluation.json',dict(assigned_quotas=[1]*4,episodes=episodes,policy_performance=False))
        probe.grid.write(out/'settings.json',config);probe.grid.write(out/'trace_metadata.json',dict(joint_names=meta['joint_names']))
        native=probe.grid.read(probe.prior.FRESH/'runs/index/native_effort_readback.json');probe.grid.write(out/'native_effort_readback.json',native)
        target=np.array(expected['action']['target_contract']['reference105_rad'])[None]
        trace=dict(target=target,time_s=np.array([1/60]),source_time_s=np.array([1/60+short['view']['score_offset_s']]),
            wrist_goal_G_m=np.zeros((1,3)),wrist_goal_G_xyzw=np.array([[0.,0.,0.,1.]]))
        np.savez(out/'trace_env0_episode0.npz',**trace)
        result=probe.postcheck(out);assert result['acceptance']['attempts']==4 and not result['acceptance']['passed']
        assert result['post_ramp_endpoint_samples']==0 and result['selected_targets_and_wrist_goal_match'] is None
        trace['source_time_s']+=.001;np.savez(out/'trace_env0_episode0.npz',**trace)
        try:probe.postcheck(out)
        except AssertionError:pass
        else:raise AssertionError('Wrong score clock admitted')
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    return dict(geometry_two_formulas_exact=True,center_helper_tolerance_m=1e-12,arm12_quaternion_selected4_exact=True,
        wrist_position_only_cell_delta=True,finite_inward_cells_validated=True,source7_clock_duration257_exact=True,
        expected_B_environment_exact=True,native_B_trials=0,scope_identity_restored=True,
        bad_task_and_bad_contract_rejected_primary_preserved=True,constructor_close_error_preserved=True,
        existing_output_unchanged_symlink_rejected_before_gate=True,early4failures_preserved_without_postramp_claim=True,
        wrong_score_clock_rejected=True,scope='CPU fixtures only; no B native pose/positive contact/reachability claim')
