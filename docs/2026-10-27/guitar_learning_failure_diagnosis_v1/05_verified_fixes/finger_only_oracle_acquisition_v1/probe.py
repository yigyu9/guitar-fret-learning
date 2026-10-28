"""Fixed225 finger-only scripted oracle. CPU --prepare; --execute is root GPU only."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
INPUTS = dict(index=(DIAG/'03_short_learning/other_finger_precheck_v3/teacher_index_row1.json',
                    DIAG/'03_short_learning/other_finger_precheck_v3/reference_index_row1.json'),
              middle=(DIAG/'02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json',
                      DIAG/'03_short_learning/reference_middle_row8_v2.json'))
AXES = ((-10,-5,0,5,10),(-10,-5,0,5,10),(-5,0,5),(-5,0,5))
CRITERION = dict(achieved=True, minimum_clean=.70, maximum_wrong=.10,
    physical_or_wrist_failure_allowed=False, rank=['squared_offset_degrees','maximum_absolute_offset_degrees','grid_index'])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')


def reject_existing(path):
    if path.exists() or path.is_symlink(): raise FileExistsError(str(path))


def grid(reference, names, lower, upper):
    rows, count = [],0
    for index,offset in enumerate(itertools.product(*AXES)):
        target = [reference[n]+math.radians(d) for n,d in zip(names,offset)]
        reasons = [dict(joint=n,target_rad=x,lower_rad=lo,upper_rad=hi)
            for n,x,lo,hi in zip(names,target,lower,upper) if not lo <= x <= hi]
        detailed = all(d==0 for d in offset) or (sum(d!=0 for d in offset)==1 and
            all(d==0 or abs(d)==max(abs(a) for a in axis) for d,axis in zip(offset,AXES)))
        rows.append(dict(grid_index=index,offset_deg=list(offset),target_rad=target,valid=not reasons,
            excluded_reasons=reasons,env_id=count if not reasons else None,detailed_trace=detailed))
        count += not bool(reasons)
    assert len(rows)==225 and len({tuple(r['target_rad']) for r in rows})==225
    assert rows[112]['offset_deg']==[0,0,0,0] and rows[112]['valid']
    return dict(rows=rows,valid_count=count,baseline_grid_index=112,
        preregistered_detail_grid_indices=[r['grid_index'] for r in rows if r['detailed_trace']],
        executed_detail_grid_indices=[r['grid_index'] for r in rows if r['valid'] and r['detailed_trace']])


def choose(episodes, document):
    eligible = [r for r in episodes if r['achieved'] and r['clean_fraction']>=.70 and r['audible_wrong_fraction']<=.10
        and not r['termination']['physical_failure'] and not r['termination']['wrist_failure']]
    def rank(row):
        offset=document['rows'][row['grid_index']]['offset_deg']
        return (sum(d*d for d in offset),max(abs(d) for d in offset),row['grid_index'])
    eligible.sort(key=rank)
    return dict(criterion=CRITERION,eligible_grid_indices=[r['grid_index'] for r in eligible],
        selected_grid_index=eligible[0]['grid_index'] if eligible else None,
        scope='scripted candidate only; separate fresh4attempt reproduction and force/posture review still required')


def complete(episodes, count):
    return len(episodes)==count and sorted(r['env_id'] for r in episodes)==list(range(count))


def phase_masks(source,onset,end):
    return source < onset,(source >= onset) & (source < end),source >= end


def settings(finger,count):
    from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
    return make_settings(argparse.Namespace(teacher=str(INPUTS[finger][0]),mode='incremental',initial_std=.1711710544767014,
        song='05_BN2-131-B_solo',size='large',seed=7,num_envs=count,horizon=32,updates=1,save_every=50))


def prepare():
    import tempfile
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.tests.test_gpu_control import fake_scene
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    assert not torch.cuda.is_available()
    torch.set_num_threads(1)
    source=load_prepared_reset_contract(); initial=source['initial']
    scene,_=fake_scene(1,dtype=torch.float32); controller=BatchedController(scene,finger_action_mode='incremental')
    inputs=HERE/'cpu_inputs'; inputs.mkdir()
    evidence={Path(__file__).resolve(),HERE/'PLAN.md'}; checks={}; commands=[]
    for finger in INPUTS:
        provisional=settings(finger,225); short=provisional['song']['short_learning']
        names=short['learned_action_names']; ref=read_reference(INPUTS[finger][1],short)
        qids=[initial['joint_names'].index(n) for n in names]
        lower=[initial['native_PD_properties']['lower'][i] for i in qids]
        upper=[initial['native_PD_properties']['upper'][i] for i in qids]
        action_ids=[ACTIVE_NAMES.index(n) for n in names]
        torch.testing.assert_close(controller.action_low[action_ids],torch.tensor(lower),rtol=0,atol=2e-7)
        torch.testing.assert_close(controller.action_high[action_ids],torch.tensor(upper),rtol=0,atol=2e-7)
        document=grid(ref['selected_targets_rad'],names,lower,upper)
        assert document['valid_count']==dict(index=135,middle=180)[finger]
        actual_targets=torch.tensor([r['target_rad'] for r in document['rows'] if r['valid']])
        assert ((actual_targets>=controller.action_low[action_ids]) & (actual_targets<=controller.action_high[action_ids])).all()
        final=settings(finger,document['valid_count']); assert final['song']['short_learning']==short
        document.update(finger=finger,joint_names=names,native_lower_rad=lower,native_upper_rad=upper,
            reference_path=str(INPUTS[finger][1]),reference_sha256=sha(INPUTS[finger][1]),
            source_target_id=short['teacher']['source_target_id'],criterion=CRITERION)
        write(inputs/(finger+'_grid.json'),document); write(inputs/(finger+'_settings.json'),final)
        evidence.update((inputs/(finger+'_grid.json'),inputs/(finger+'_settings.json'),*INPUTS[finger]))
        evidence.update(map(Path,short['teacher']['source_evidence'])); evidence.update(map(Path,ref['source_evidence']))
        checks[finger]=dict(complete_grid_rows=225,valid=document['valid_count'],excluded=225-document['valid_count'],
            baseline=112,detail_preregistered=document['preregistered_detail_grid_indices'],detail_executed=document['executed_detail_grid_indices'],
            source_target_id=document['source_target_id'],selected_names=names)
        commands.append([PYTHON,'-B',str(HERE/'probe.py'),'--finger',finger,'--execute'])
    # Small pure checks: exclusion, fixed ordering, ranking, failure denominator and dangling-output guard.
    test=grid(dict(zip(('a','b','c','d'),(0.,)*4)),('a','b','c','d'),(-1.,)*4,(1.,)*4)
    assert test['valid_count']==225 and len(test['preregistered_detail_grid_indices'])==9
    def row(index,**kw):
        value=dict(grid_index=index,env_id=index,achieved=True,clean_fraction=.70,audible_wrong_fraction=.10,
            termination=dict(physical_failure=False,wrist_failure=False)); value.update(kw); return value
    assert choose([row(112),row(111)],test)['selected_grid_index']==112
    assert choose([row(111),row(109)],test)['selected_grid_index']==109
    a=next(r['grid_index'] for r in test['rows'] if r['offset_deg']==[5,5,5,5])
    b=next(r['grid_index'] for r in test['rows'] if r['offset_deg']==[-10,0,0,0])
    assert choose([row(b),row(a)],test)['selected_grid_index']==a
    assert choose([row(112,achieved=False)],test)['selected_grid_index'] is None
    assert choose([row(112,clean_fraction=.69)],test)['selected_grid_index'] is None
    assert choose([row(112,audible_wrong_fraction=.11)],test)['selected_grid_index'] is None
    assert choose([row(112,termination=dict(physical_failure=True,wrist_failure=False))],test)['selected_grid_index'] is None
    assert choose([row(112,termination=dict(physical_failure=False,wrist_failure=True))],test)['selected_grid_index'] is None
    assert complete([dict(env_id=0,reason='terminal_failure'),dict(env_id=1)],2)
    assert not complete([dict(env_id=0),dict(env_id=0)],2)
    assert phase_masks(3.,3.,4.)==(False,True,False) and phase_masks(4.,3.,4.)==(False,False,True)
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'old'; path.mkdir(); link=Path(temp)/'link'; link.symlink_to(Path(temp)/'absent')
        for item in (path,link):
            try: reject_existing(item)
            except FileExistsError: pass
            else: raise AssertionError('Existing/dangling output accepted')
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    write(HERE/'cpu_verification.json',dict(CPU_only=True,GPU_executed=False,grid_checks=checks,commands=commands,
        pure_checks=['Cartesian order/duplicate/bounds/baseline','rank and eligibility boundaries/failure rejection','complete first-attempt denominator',
            'audible source_onset<=source_time<source_end','existing/dangling output rejected'],
        GPU_resource_scope='225 settings supported; actual135/180; scene contact-pair floor remains1048576; physical GPU fit not CPU-certified; measured before/after pool on root run',
        controller_bounds_float32_match=True,all_valid_targets_inside_actual_controller_bounds=True,
        no_NN_or_checkpoint_created=True,CUDA_initialized=False))
    evidence.add(HERE/'cpu_verification.json')
    read_settings=read(inputs/'index_settings.json'); write(inputs/'settings.json',read_settings)
    evidence.update((inputs/'settings.json',))
    pins=runner._pins(read_settings,inputs,evidence)
    write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,grid_valid_counts=dict(index=135,middle=180),
        scope='CPU prepared scripted oracle; root GPU only; no NN/checkpoint, no native fit or success claim'))
    print(json.dumps(dict(CPU_only=True,pins=len(pins),valid=dict(index=135,middle=180),GPU_executed=False)))


def read(path):
    return json.loads(Path(path).read_text())


def collect(pool,document,reference):
    import torch
    from guitar_learning.gpu.geometry import apply,conjugate,multiply,rotvec
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.tool.experiments.short_finger_learning.runner import compact_episode
    env=pool.environment; count=pool.num_envs; spec=pool.spec
    valid=[r for r in document['rows'] if r['valid']]
    assert len(valid)==count
    goals=pool.teacher_reference.repeat(count,1)
    selected=spec['learned_action_indices']; goals[:,selected]=goals.new_tensor([r['target_rad'] for r in valid])
    done=torch.zeros(count,dtype=torch.bool,device=goals.device)
    samples=torch.zeros(count,3,dtype=torch.long,device=goals.device)
    sums=torch.zeros(count,3,20,device=goals.device); squares=sums.clone()
    minima=torch.full_like(sums,float('inf')); maxima=-minima
    gate_counts=torch.zeros(count,3,6,dtype=torch.long,device=goals.device)
    names=pool.scene.names; qids=[names.index(n) for n in spec['learned_action_names']]
    bodyids=[pool.scene.metadata['body_names'].index('human/LH:'+document['finger']+str(i)) for i in (1,2,3)]
    details={r['env_id']:[] for r in valid if r['detailed_trace']}; episodes=[]
    env.set_evaluation(True,full_song=False)
    for tick in range(spec['view']['duration_ticks']):
        active=~done
        fraction=((env._local_time()+1/60)/reference['ramp_s']).clamp(0,1).to(goals)
        desired=pool.teacher_reference+fraction[:,None]*(goals-pool.teacher_reference)
        action=trajectory_actions(desired,pool.controller.target[:,pool.controller.active],pool.teacher_reference,
            pool.controller.action_low,pool.controller.action_high,pool.incremental_mask,max_speed=4.)
        _,_,_,terminated,truncated,finished=pool.step(action)
        scene=pool.scene; local=env._local_time(); index=env.selected_index
        body=scene.body_state; guitar=body[:,env.guitar_index]; wrist=body[:,env.wrist_index]; fb=pool.last_wrist_feedback
        force=scene.snapshot()['contact_force']
        position=guitar[:,:3]+apply(guitar[:,3:7],fb['position_goal_G_m'])-wrist[:,:3]
        rotation=rotvec(multiply(multiply(guitar[:,3:7],fb['quaternion_goal_G_xyzw']),conjugate(wrist[:,3:7])))
        q=scene.q[:,qids]; target=scene.target[:,qids]
        data=torch.cat((q*180/math.pi,target*180/math.pi,(target-q)*180/math.pi,
            torch.linalg.vector_norm(force[:,bodyids],dim=-1),env.surface_distance[:,index,None]*1000,
            env.surface_height[:,index,None]*1000,env.surface_alignment[:,index,None],
            torch.linalg.vector_norm(position,dim=-1,keepdim=True)*1000,
            torch.linalg.vector_norm(rotation,dim=-1,keepdim=True)*180/math.pi),1)
        gates=torch.stack([v[:,index] for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,
            env.contact_loaded_target,env.candidate,env.wrong)],1)
        source_target=spec['view']['source_target']
        for p,phase in enumerate(phase_masks(env._score_time(),source_target['onset_s'],source_target['end_s'])):
            mask=active & phase; samples[:,p]+=mask
            sums[:,p]+=torch.where(mask[:,None],data,0); squares[:,p]+=torch.where(mask[:,None],data.square(),0)
            minima[:,p]=torch.minimum(minima[:,p],torch.where(mask[:,None],data,float('inf')))
            maxima[:,p]=torch.maximum(maxima[:,p],torch.where(mask[:,None],data,-float('inf')))
            gate_counts[:,p]+=gates & mask[:,None]
        for i,trace in details.items():
            if bool(active[i]):
                row=dict(time_s=float(local[i]),source_time_s=float(env._score_time()[i]),
                    q=scene.q[i].cpu().numpy().copy(),target=scene.target[i].cpu().numpy().copy(),body_state=body[i].cpu().numpy().copy(),
                    net_body_force_n=force[i].cpu().numpy().copy(),scripted_action=action[i].cpu().numpy().copy(),
                    executed_action=pool.last_executed_action[i].cpu().numpy().copy(),candidate=bool(env.candidate[i,index]),wrong=bool(env.wrong[i,index]),
                    surface_distance_m=float(env.surface_distance[i,index]),surface_height_m=float(env.surface_height[i,index]))
                for key,source in (('wrist_feedback_active','active'),('wrist_pose_error_world','pose_error_world'),
                    ('wrist_requested_delta_rad','requested_delta_rad'),('wrist_requested_arm_rad','requested_arm_rad'),
                    ('wrist_candidate_arm_rad','candidate_arm_rad'),('wrist_goal_G_m','position_goal_G_m'),
                    ('wrist_goal_G_xyzw','quaternion_goal_G_xyzw')):
                    row[key]=fb[source][i].cpu().numpy().copy()
                trace.append(row)
        for row in finished:
            i=row['env_id']
            if not bool(done[i]):
                episodes.append(dict(grid_index=valid[i]['grid_index'],**compact_episode(row,spec))); done[i]=True
        if bool(done.all()): break
        ids=(terminated|truncated).nonzero().flatten()
        if ids.numel(): pool.reset(ids)  # Original evaluator resets ended rows; quotas never accept their later attempts.
    if not complete(episodes,count): raise RuntimeError('Not all assigned first attempts completed within original tick budget')
    statistics=[]
    for i in range(count):
        phases={}
        for p,name in enumerate(('before','audible','after')):
            n=int(samples[i,p]); phases[name]=dict(samples=n,gate_counts=gate_counts[i,p].cpu().tolist(),
                min=minima[i,p].cpu().tolist() if n else None,max=maxima[i,p].cpu().tolist() if n else None,
                mean=(sums[i,p]/n).cpu().tolist() if n else None,rms=(squares[i,p]/max(n,1)).sqrt().cpu().tolist() if n else None)
        statistics.append(dict(env_id=i,grid_index=valid[i]['grid_index'],phases=phases))
    return sorted(episodes,key=lambda r:r['env_id']),statistics,details,tick+1


def execute(finger,out,seal):
    import numpy as np
    import torch
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    document=read(HERE/'cpu_inputs'/(finger+'_grid.json')); config=settings(finger,document['valid_count'])
    assert config==read(HERE/'cpu_inputs'/(finger+'_settings.json'))
    reference=read_reference(INPUTS[finger][1],config['song']['short_learning'])
    out.mkdir(parents=True,exist_ok=False); runner.write(out/'settings.json',config)
    pins=runner._pins(config,out,[HERE/'preparation_seal.json',*map(Path,seal['input_pins'])])
    runner.write(out/'inputs_before.json',pins)
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32=False
    pool=None; failure=None; completed=False; started=time.monotonic(); resource={}
    try:
        resource['before_pool_free_total_bytes']=list(torch.cuda.mem_get_info())
        pool=ShortPool(config,out)
        resource['after_pool_free_total_bytes']=list(torch.cuda.mem_get_info())
        runner.write(out/'training_contract.json',pool.contract)
        episodes,statistics,details,ticks=collect(pool,document,reference)
        runner.write(out/'evaluation.json',dict(assigned_quotas=[1]*pool.num_envs,episodes=episodes,summary=runner.summary(episodes),
            criterion=CRITERION,policy_performance=False,scope='all valid grid rows first attempt, including failures; no NN or checkpoints'))
        runner.write(out/'statistics.json',dict(phase_order=['before','audible','after'],
            phase_scope='source_time<source_onset; source_onset<=source_time<source_end; source_time>=source_end',
            gate_order=['loaded','position','position_facing','positive','candidate','wrong'],
            metric_order=[prefix+str(i) for prefix in ('actual_q_deg_','target_q_deg_','target_minus_actual_deg_') for i in range(4)]+
                ['finger1_resultant_N','finger2_resultant_N','finger3_resultant_N','nearest_distance_mm','nearest_height_mm','nearest_normal_cos','wrist_position_error_mm','wrist_rotation_error_deg'],
            rows=statistics,scope='60Hz endpoint statistics only; body1/2/3 resultant separately; no240Hz maximum, string pressure or contact partner claim'))
        runner.write(out/'selection.json',choose(episodes,document))
        for i,trace in details.items():
            np.savez_compressed(out/('trace_grid%06d.npz'%episodes[i]['grid_index']),**{k:np.asarray([r[k] for r in trace]) for k in trace[0]})
        runner.write(out/'trace_metadata.json',dict(joint_names=pool.scene.names,body_names=pool.scene.metadata['body_names'],
            grid_indices=document['executed_detail_grid_indices'],wrist_control=pool.spec['wrist_control'],
            scope='preregistered baseline+single-axis extrema; excluded rows have no trace; each own first attempt60Hz including failure endpoint',
            wrist_fields='original runner wrist field names; pose_error is pre-control, q/body/target are post-step; candidate/reset/delta meanings are sealed wrist v3 contract'))
        resource.update(physics_steps=pool.scene.physics_steps,control_ticks=ticks,max_allocated_bytes=torch.cuda.max_memory_allocated(),
            max_reserved_bytes=torch.cuda.max_memory_reserved())
        assert pool.scene.physics_steps==ticks*4 and ticks<=pool.spec['view']['duration_ticks']
        completed=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error)); raise
    finally:
        close_failure=None
        try:
            if pool is not None: pool.close()
        except BaseException as error:
            close_failure=dict(type=type(error).__name__,message=str(error))
        changed=[p for p,h in pins.items() if not Path(p).is_file() or sha(p)!=h]
        missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        scene=read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
        verified=not changed and not missing
        runner.write(out/'inputs_after.json',dict(verified=verified,changed_paths=changed,unpinned_project_sources=missing,input_pins=pins))
        runner.write(out/'report.json',dict(completed=completed and verified and close_failure is None and scene.get('closed') is True,
            closed=scene.get('closed') is True,failure=failure,close_failure=close_failure,changed_inputs=changed,unpinned_project_sources=missing,
            wall_s=time.monotonic()-started,resources=resource,grid_rows=225,assigned_valid_attempts=document['valid_count'],no_NN_or_checkpoint=True))
        if failure is None and (not verified or close_failure or not scene.get('closed')): raise RuntimeError('Oracle close/source verification failed; original outputs preserved')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true'); parser.add_argument('--execute',action='store_true')
    parser.add_argument('--finger',choices=tuple(INPUTS)); args=parser.parse_args()
    sys.path.insert(0,str(ROOT))
    if args.prepare:
        if args.execute: raise ValueError('CPU preparation and native execution are separate')
        prepare(); return
    if not args.execute:
        print('CPU --prepare; root only --finger index/middle --execute. No native imported.'); return
    if args.finger is None: raise ValueError('Predeclared finger required')
    out=HERE/'runs'/args.finger
    reject_existing(out)
    if out.parent.is_symlink(): raise ValueError('Output parent symlink refused')
    seal=read(HERE/'preparation_seal.json')
    if seal['independent_review']!='passed_no_findings': raise ValueError('Independent reviewed CPU seal required')
    if any(not Path(p).is_file() or sha(p)!=h for p,h in seal['input_pins'].items()): raise ValueError('Preparation source/settings changed')
    import isaacgym  # Original import order, before NumPy/Torch; only root executes this branch.
    execute(args.finger,out,seal)


if __name__=='__main__': main()
