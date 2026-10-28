"""Schedule/codec/finite-boundary and bounded observer/restore CPU fixtures."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe, config, metadata):
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.tool.experiments.short_finger_learning import runtime, runner
    extra = probe.prefix.support(); short = config['song']['short_learning']; view = short['view']; declared = short['release_transfer']
    original = probe.prefix.settings()
    unchanged = copy.deepcopy(config); other = unchanged['song']['short_learning']; del other['release_transfer']
    other['prefix']['transition'] = original['song']['short_learning']['prefix']['transition']
    other['result_scope'] = original['song']['short_learning']['result_scope']; assert unchanged == original
    parent_tests = probe.module('release_frozen_prefix_checks',probe.PREFIX/'cpu_checks.py')
    common = parent_tests.check(probe.prefix,original,metadata)
    boundaries = probe.timing.boundaries(view)
    np.testing.assert_allclose(boundaries,[3.1703,3.2703,3.712,3.832],rtol=0,atol=1e-12)
    assert abs(sum(declared['durations_s'])-.6617) < 1e-12
    samples = torch.tensor([0.,2.,3.1703,3.2203,3.2703,3.5,3.712,3.772,3.832,5.9],dtype=torch.float64)
    np.testing.assert_allclose(probe.timing.negative_weight(samples,view),[0,0,0,.5,1,1,1,.5,0,0],rtol=0,atol=1e-12)
    expected = [min(1.,max(0.,(float(t)-3.2703)/.4417)) for t in samples]
    np.testing.assert_allclose(probe.timing.wrist_weight(samples,view),expected,rtol=0,atol=1e-12)
    assert [probe.timing.phase(t,view) for t in (0.,*boundaries,5.9)] == [0,1,2,3,4,4]
    for edge in boundaries:
        left,right = probe.timing.negative_weight(torch.tensor([edge-1e-9,edge+1e-9],dtype=torch.float64),view)
        assert abs(float(right-left)) < 3e-8
    # Use the frozen inverse codec and its native incremental update, no new solver.
    controller = metadata['action_contract']; names = controller['action_order']; selected = short['learned_action_indices']
    native = [metadata['joint_names'].index(n) for n in ACTIVE_NAMES]
    reference = torch.tensor(controller['reference105_rad'])[native]
    low,high = torch.tensor(controller['action_lower_rad']),torch.tensor(controller['action_upper_rad'])
    mask = torch.zeros(39,dtype=torch.bool); mask[12:33] = True
    current = reference[None].repeat(4,1); maximum = 0.
    positive = current.clone(); positive[:,selected] = torch.tensor(declared['reference_selected_rad'])
    for k in range(1,355):
        time = torch.full((4,),k/60,dtype=torch.float64); ramp = min(1.,k/120)
        desired = reference+ramp*(positive-reference)
        desired[:,selected] += probe.timing.negative_weight(time,view).float()[:,None]*(torch.tensor(declared['negative_selected_rad'])-torch.tensor(declared['reference_selected_rad']))
        action = extra.trajectory_actions(desired,current,reference,low,high,mask,max_speed=4.)
        target = torch.maximum(low[selected],torch.minimum(high[selected],current[:,selected]+action[:,selected]*4/60))
        maximum = max(maximum,float((target-current[:,selected]).abs().max()))
        torch.testing.assert_close(target,desired[:,selected],rtol=0,atol=2e-6)
        assert bool(torch.isfinite(target).all()) and maximum <= 4/60+2e-6
        current[:,selected] = target
    # All first-attempt endpoints retained; same-endpoint failure/force NaN cannot certify events.
    observer = probe.timing.Observer(view)
    for clock in range(1,1417):
        candidate = [[clock<772,clock>=901,clock>=901] for _ in range(4)]
        loaded = [[clock<772 or clock>=901]*3 for _ in range(4)]
        failed = [False,clock==772,False,clock==4]
        force = [1. if loaded[0][0] else 0.]*4
        if clock==772: force[2] = float('nan')
        observer.observe([clock,clock,clock,clock if clock<=4 else 1],candidate,loaded,[[False]*3 for _ in range(4)],force,failed)
        if clock==4: observer.finish([dict(env_id=3,steps=1,reason='terminal_failure')])
    rows = observer.rows
    assert rows[0]['first_valid_post_A_candidate_fall']['clock']==772
    assert rows[1]['first_post_A_candidate_fall']['censored'] and rows[1]['first_valid_post_A_candidate_fall'] is None
    assert rows[2]['first_valid_post_A_candidate_fall'] is None and rows[2]['phases']['release']['nonfinite_force_samples']==1
    assert rows[3]['last_clock']==4 and rows[3]['first_censored_clock']==4
    assert rows[1]['phases']['move']['valid_samples']==0 and rows[0]['phases']['move']['first_valid_B_candidateoff_loadedoff'] is not None
    # Constructor rejection + close exception retains the primary error and every alias/hook.
    env = extra.PrefixEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    expected = torch.zeros(4,67,dtype=torch.bool); expected[:,[4,7,8]] = True
    closed=[]; instances=[]
    class FakePool:
        def __init__(self,*args):
            self.environment = SimpleNamespace(contract=copy.deepcopy(env.contract),task=env.task,selected_indices=(4,7,8),M=67,
                focus_mask=expected.clone(),duration_ticks=torch.full((4,),354),substep=lambda snapshot:None)
            self.scene = SimpleNamespace(metadata=metadata); self.spec=short; instances.append(self)
            self.original = self.environment.substep
            if mode=='bad_contract': self.environment.contract['task']['short_learning']['view']['duration_ticks']=373
        def close(self):
            closed.append(True)
            if mode=='bad_contract': raise RuntimeError('CPU close error')
    saved = (probe.prefix.HERE,probe.prefix.settings,extra.PrefixPool,extra.transition_fraction,extra.trajectory_actions,
             probe.prefix.base.HERE,probe.prefix.base.INPUTS,probe.prefix.base.settings,runtime.ShortPool,runner._evaluate)
    with tempfile.TemporaryDirectory() as temp:
        with patch.object(extra,'PrefixPool',FakePool):
            for mode in ('good','bad_contract','body_error'):
                out=Path(temp)/mode;out.mkdir();state=dict(cleanup_errors=[]);count=len(closed)
                try:
                    with probe.execution_scope(state):
                        runtime.ShortPool(config,out)
                        assert runner._evaluate is extra.evaluate
                        if mode=='body_error': raise ValueError('CPU body error')
                except AssertionError: assert mode=='bad_contract' and len(closed)==count+1
                except ValueError: assert mode=='body_error'
                else: assert mode=='good' and state['task_verified']
                assert state['aliases_restored'] and state['schedule_aliases_restored'] and state['observer_hooks_restored']
                assert instances[-1].environment.substep is instances[-1].original
                assert bool(state['cleanup_errors']) == (mode=='bad_contract')
        now = (probe.prefix.HERE,probe.prefix.settings,extra.PrefixPool,extra.transition_fraction,extra.trajectory_actions,
               probe.prefix.base.HERE,probe.prefix.base.INPUTS,probe.prefix.base.settings,runtime.ShortPool,runner._evaluate)
        assert all(a is b for a,b in zip(saved,now))
        root=Path(temp)/'guard';out=root/'runs/index';out.mkdir(parents=True);sentinel=out/'keep';sentinel.write_bytes(b'keep')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('must reject before gate')):
            try: probe.launch()
            except FileExistsError: pass
            else: raise AssertionError('Existing output admitted')
            assert sentinel.read_bytes()==b'keep';sentinel.unlink();out.rmdir();out.symlink_to(root/'absent')
            try: probe.launch()
            except (FileExistsError,ValueError): pass
            else: raise AssertionError('Symlink admitted')
    assert not torch.cuda.is_initialized()
    return dict(CPU_only=True,GPU_executed=False,native_trials=0,frozen_prefix_regressions=common,
        only_declared_schedule_tag_changed=True,N_source_constant_target=True,three_phase_bounds_finite_continuous=True,
        original_inverse_codec_all354ticks_bounds_rate_verified=True,codec_max_step_rad=maximum,
        first4_observer_clock_failure_same_endpoint_latch_and_retry_mask=True,nonfinite_force_event_uncertified=True,
        constructor_primary_and_close_error_preserved=True,all_aliases_and_instance_hooks_restored=True,
        existing_output_unchanged_symlink_rejected_before_gate=True)
