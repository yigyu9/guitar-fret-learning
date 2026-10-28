"""Fresh4 first attempts for the two preregistered grid selections; root GPU only."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('oracle_grid_probe',BASE/'probe.py')
parent=importlib.util.module_from_spec(spec); sys.modules[spec.name]=parent; spec.loader.exec_module(parent)
SELECTED=dict(index=115,middle=114)


def document_for(finger,grid):
    selected=grid['rows'][SELECTED[finger]]
    assert selected['valid'] and selected['grid_index']==SELECTED[finger]
    doc=copy.deepcopy(grid)
    doc.update(valid_count=4,original_grid_row_count=225,selected_grid_index=SELECTED[finger],
        original_reference_target_rad=grid['rows'][112]['target_rad'],selected_offset_deg=selected['offset_deg'],
        selected_target_rad=selected['target_rad'],scope='same selected scripted target in four envs; not four seeds or a new reference')
    doc['rows']=[dict(copy.deepcopy(selected),env_id=i,detailed_trace=i==0,
        attempt_id='%s_grid%06d_env%d_first'%(finger,SELECTED[finger],i)) for i in range(4)]
    doc['executed_detail_grid_indices']=[SELECTED[finger]]
    return doc


def identify(episodes,statistics,document):
    assert parent.complete(episodes,4) and len(statistics)==4
    for values in (episodes,statistics):
        assert sorted(r['env_id'] for r in values)==list(range(4))
        for row in values:
            expected=document['rows'][row['env_id']]
            assert row['grid_index']==expected['grid_index']
            row['attempt_id']=expected['attempt_id']
    for row in episodes:
        assert row['target_id']==document['source_target_id'] and row['selected_target_count']==1
    assert len({r['attempt_id'] for r in episodes})==4


def acceptance(episodes):
    assert parent.complete(episodes,4)
    achieved=sum(bool(r['achieved']) for r in episodes)
    clean=sum(r['clean_fraction'] for r in episodes)/4
    wrong=sum(r['audible_wrong_fraction'] for r in episodes)/4
    physical=sum(bool(r['termination']['physical_failure']) for r in episodes)
    wrist=sum(bool(r['termination']['wrist_failure']) for r in episodes)
    return dict(attempts=4,achieved=achieved,mean_clean=clean,mean_wrong=wrong,physical_failures=physical,wrist_failures=wrist,
        passed=achieved==4 and clean>=.70 and wrong<=.10 and physical==0 and wrist==0,
        scope='scripted original music predicate reproduction only; high proximal load and posture require separate review')


def evidence():
    seal=parent.read(BASE/'preparation_seal.json')
    assert seal['independent_review']=='passed_no_findings'
    paths=set(map(Path,seal['input_pins']))
    paths.update((BASE/'preparation_seal.json',BASE/'01_launcher.json',HERE/'PLAN.md',Path(__file__).resolve()))
    for folder in (BASE/'analysis/results_v1',):
        review=parent.read(folder/'review.json')
        assert review['verdict']=='PASS' and not review['findings']
        verification=parent.read(folder/'verification.json')
        for key in ('input_sha256','verified_input_sha256'):
            for p,h in verification[key].items(): assert parent.sha(p)==h,p
            paths.update(map(Path,verification[key]))
        paths.update(p for p in folder.iterdir() if p.is_file())
    for finger in SELECTED:
        paths.update(BASE/'runs'/finger/name for name in ('evaluation.json','selection.json','statistics.json','settings.json','report.json','inputs_before.json','inputs_after.json','gpu_scene_final.json','training_contract.json'))
    for p,h in seal['input_pins'].items(): assert parent.sha(p)==h,p
    return paths


def prepare():
    import tempfile
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    inputs=HERE/'cpu_inputs'; parent.reject_existing(inputs); parent.reject_existing(HERE/'preparation_seal.json')
    paths=evidence(); inputs.mkdir()
    checks={}; commands=[]
    for finger,index in SELECTED.items():
        grid=parent.read(BASE/'cpu_inputs'/(finger+'_grid.json'))
        episodes=parent.read(BASE/'runs'/finger/'evaluation.json')['episodes']
        assert parent.choose(episodes,grid)==parent.read(BASE/'runs'/finger/'selection.json')
        assert parent.choose(episodes,grid)['selected_grid_index']==index
        document=document_for(finger,grid); config=parent.settings(finger,4)
        old=parent.read(BASE/'cpu_inputs'/(finger+'_settings.json')); expected=copy.deepcopy(old)
        expected['num_envs']=4
        expected['finger_skill']['planned_transitions']=4*old['horizon']*old['updates']
        expected['finger_skill']['full_song_after']=expected['finger_skill']['planned_transitions']//4
        assert config==expected
        reference=read_reference(parent.INPUTS[finger][1],config['song']['short_learning'])
        names=document['joint_names']; original=[reference['selected_targets_rad'][n] for n in names]
        assert document['original_reference_target_rad']==original
        assert all(abs(x+math.radians(d)-y)<1e-12 for x,d,y in zip(original,document['selected_offset_deg'],document['selected_target_rad']))
        assert all(lo<=x<=hi for x,lo,hi in zip(document['selected_target_rad'],document['native_lower_rad'],document['native_upper_rad']))
        assert all(r['target_rad']==document['selected_target_rad'] for r in document['rows'])
        assert [r['env_id'] for r in document['rows']]==list(range(4))
        assert [r['env_id'] for r in document['rows'] if r['detailed_trace']]==[0]
        parent.write(inputs/(finger+'_targets.json'),document); parent.write(inputs/(finger+'_settings.json'),config)
        paths.update((inputs/(finger+'_targets.json'),inputs/(finger+'_settings.json')))
        checks[finger]=dict(selected_grid_index=index,source_target_id=document['source_target_id'],joint_names=names,
            original_reference_target_deg=[math.degrees(q) for q in original],offset_deg=document['selected_offset_deg'],
            selected_target_deg=[math.degrees(q) for q in document['selected_target_rad']],
            distinct_attempt_ids=[r['attempt_id'] for r in document['rows']],assigned_quotas=[1]*4,detail_env_ids=[0],reference_unmodified=True,
            settings_difference_scope=['num_envs','finger_skill.planned_transitions','finger_skill.full_song_after'],
            workload_scaling_only=True,short_learning_contract_unchanged=True)
        commands.append([parent.PYTHON,'-B',str(HERE/'probe.py'),'--finger',finger,'--execute'])
    # No new pool mock: pure denominator, failure, identity and exact acceptance boundaries.
    doc=document_for('index',parent.read(BASE/'cpu_inputs/index_grid.json'))
    rows=[dict(env_id=i,grid_index=115,target_id=doc['source_target_id'],selected_target_count=1,achieved=True,
        clean_fraction=.70,audible_wrong_fraction=.10,termination=dict(physical_failure=False,wrist_failure=False)) for i in range(4)]
    stats=[dict(env_id=i,grid_index=115) for i in range(4)]; identify(rows,stats,doc)
    assert acceptance(rows)['passed']; rows[0]['achieved']=False; assert not acceptance(rows)['passed']
    rows[0]['termination']['physical_failure']=True; assert acceptance(rows)['attempts']==4 and acceptance(rows)['physical_failures']==1
    for bad in (rows[:3],[rows[0]]*4):
        try: acceptance(bad)
        except AssertionError: pass
        else: raise AssertionError('Missing or duplicate env accepted')
    with tempfile.TemporaryDirectory() as tmp:
        link=Path(tmp)/'old'; link.symlink_to(Path(tmp)/'missing')
        try: parent.reject_existing(link)
        except FileExistsError: pass
        else: raise AssertionError('Dangling output accepted')
    parent.write(inputs/'settings.json',parent.read(inputs/'index_settings.json')); paths.add(inputs/'settings.json')
    parent.write(HERE/'cpu_verification.json',dict(CPU_only=True,CUDA_initialized=False,GPU_executed=False,
        checks=checks,commands=commands,no_NN_or_checkpoint=True,parent_collect_unmodified=True,
        pure_checks=['same target four distinct env first attempts','original+offset=selected and bounds','env0 detail only',
            'acceptance boundary and failures retain denominator','missing/duplicate env and dangling output rejected'],
        scope='CPU prepared only; root native completion and independent actual review required'))
    paths.add(HERE/'cpu_verification.json')
    pins=runner._pins(parent.read(inputs/'settings.json'),inputs,paths)
    parent.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,attempts_per_finger=4,
        selected_grid_indices=SELECTED,scope='CPU preparation only; root executes after independent preparation PASS'))
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(pins),attempts_per_finger=4)))


def execute(finger,out,seal):
    import numpy as np
    import torch
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    document=parent.read(HERE/'cpu_inputs'/(finger+'_targets.json')); config=parent.settings(finger,4)
    assert document==document_for(finger,parent.read(BASE/'cpu_inputs'/(finger+'_grid.json')))
    assert config==parent.read(HERE/'cpu_inputs'/(finger+'_settings.json'))
    reference=read_reference(parent.INPUTS[finger][1],config['song']['short_learning'])
    out.mkdir(parents=True,exist_ok=False); runner.write(out/'settings.json',config)
    pins=runner._pins(config,out,[HERE/'preparation_seal.json',*map(Path,seal['input_pins'])])
    runner.write(out/'inputs_before.json',pins)
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32=False
    pool=None; failure=None; completed=False; started=time.monotonic(); resources={}
    try:
        pool=ShortPool(config,out)
        assert pool.contract==parent.read(BASE/'runs'/finger/'training_contract.json')
        runner.write(out/'training_contract.json',pool.contract)
        episodes,statistics,details,ticks=parent.collect(pool,document,reference)
        identify(episodes,statistics,document)
        assert list(details)==[0] and all(sum(p['samples'] for p in s['phases'].values())==r['steps'] for s,r in zip(statistics,episodes))
        runner.write(out/'evaluation.json',dict(assigned_quotas=[1]*4,episodes=episodes,summary=runner.summary(episodes),
            acceptance=acceptance(episodes),policy_performance=False,scope='four env first attempts of the same selected scripted goal; failures included'))
        metadata=parent.read(BASE/'runs'/finger/'statistics.json')
        runner.write(out/'statistics.json',dict(phase_order=metadata['phase_order'],phase_scope=metadata['phase_scope'],
            gate_order=metadata['gate_order'],metric_order=metadata['metric_order'],rows=statistics,scope=metadata['scope']))
        trace=details[0]; filename='trace_grid%06d_env0_first.npz'%SELECTED[finger]
        np.savez_compressed(out/filename,**{k:np.asarray([r[k] for r in trace]) for k in trace[0]})
        runner.write(out/'trace_metadata.json',dict(joint_names=pool.scene.names,body_names=pool.scene.metadata['body_names'],
            env_id=0,attempt_id=document['rows'][0]['attempt_id'],grid_index=SELECTED[finger],file=filename,
            wrist_control=pool.spec['wrist_control'],scope='env0 own first attempt60Hz only; grid ID retained, env/attempt explicitly distinct; no240Hz force maximum'))
        resources.update(physics_steps=pool.scene.physics_steps,control_ticks=ticks)
        assert pool.scene.physics_steps==ticks*4 and ticks<=pool.spec['view']['duration_ticks']
        assert not list(out.glob('*.pt')); completed=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error)); raise
    finally:
        close_failure=None
        try:
            if pool is not None: pool.close()
        except BaseException as error:
            close_failure=dict(type=type(error).__name__,message=str(error))
        changed=[p for p,h in pins.items() if not Path(p).is_file() or parent.sha(p)!=h]
        missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        scene=parent.read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
        verified=not changed and not missing
        scene_valid=(scene.get('closed') is True and scene.get('environment_count')==4 and scene.get('physx_use_gpu') is True
            and scene.get('use_gpu_pipeline') is True and scene.get('diagnostic_guitar_mode')=='fixed'
            and scene.get('hand_collision',{}).get('enabled_distinct_finger_pairs')==90
            and scene.get('hand_collision_native_readback_environments')==4
            and scene.get('physics_steps')==resources.get('physics_steps'))
        runner.write(out/'inputs_after.json',dict(verified=verified,changed_paths=changed,unpinned_project_sources=missing,input_pins=pins))
        runner.write(out/'report.json',dict(completed=completed and verified and close_failure is None and scene_valid,
            closed=scene.get('closed') is True,scene_valid=scene_valid,failure=failure,close_failure=close_failure,changed_inputs=changed,unpinned_project_sources=missing,
            wall_s=time.monotonic()-started,resources=resources,selected_grid_index=SELECTED[finger],assigned_first_attempts=4,no_NN_or_checkpoint=True))
        if failure is None and (not verified or close_failure or not scene_valid): raise RuntimeError('Reproduction close/source verification failed; outputs preserved')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true'); parser.add_argument('--execute',action='store_true')
    parser.add_argument('--finger',choices=tuple(SELECTED)); args=parser.parse_args()
    sys.path.insert(0,str(parent.ROOT))
    if args.prepare:
        if args.execute: raise ValueError('Separate CPU prepare and native execute')
        prepare(); return
    if not args.execute:
        print('CPU --prepare; root only --finger index/middle --execute; no native imported.'); return
    if args.finger is None: raise ValueError('Predeclared finger required')
    out=HERE/'runs'/args.finger; parent.reject_existing(out)
    if out.parent.is_symlink(): raise ValueError('Output parent symlink refused')
    seal=parent.read(HERE/'preparation_seal.json')
    if seal['independent_review']!='passed_no_findings': raise ValueError('Independent preparation review required')
    if any(not Path(p).is_file() or parent.sha(p)!=h for p,h in seal['input_pins'].items()): raise ValueError('Preparation input changed')
    import isaacgym  # Original native-before-Torch import order, root-only branch.
    execute(args.finger,out,seal)


if __name__=='__main__': main()
