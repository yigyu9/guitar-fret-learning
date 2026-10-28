"""One unverified source7 reference derived by translating A wrist position only."""
import argparse
import copy
from contextlib import contextmanager
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PRE=HERE.parent/'low_effort_finger_prelearning_v1'
spec=importlib.util.spec_from_file_location('target7_original_prelearning',PRE/'probe.py')
prior=importlib.util.module_from_spec(spec);sys.modules[spec.name]=prior;spec.loader.exec_module(prior)
grid,cap=prior.grid,prior.cap
A_ID='event-000004/string-3/note-4'
B_ID='event-000007/string-2/note-7'
TEACHER=HERE/'cpu_inputs/teacher_index_target7.json'
REFERENCE=HERE/'cpu_inputs/reference_index_target7.json'


def actual_gate():
    paths=prior.actual_gate()
    review_path=prior.FRESH/'analysis/results_v1/review.json'
    review=grid.read(review_path)
    assert review['verdict']=='PASS' and not review['findings']
    for mapping in (review['reviewed_sha256'],*[grid.read(review_path.parent/'verification.json')[k] for k in ('input_sha256','verified_input_sha256')]):
        assert mapping and all(Path(p).is_file() and grid.sha(p)==h for p,h in mapping.items());paths.update(map(Path,mapping))
    evidence=prior.FRESH/'runs/index/evaluation.json';value=grid.read(evidence)
    assert value['acceptance']['passed'] and len(value['episodes'])==4
    assert all(e['target_id']==A_ID for e in value['episodes'])
    return paths|{review_path,evidence,*prior.INPUTS['index']}


def geometry_derivation():
    import numpy as np
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.gpu.rigid_guitar import RigidGuitar
    from guitar_learning.gpu.press_surface import load_press_surface,project_press_strings
    from guitar_learning.core.geometry_v1 import fret_target
    rigid=RigidGuitar(load_prepared_reset_contract(),'cpu');manifest=rigid.manifest
    rows=dict(zip(manifest['logical_body_names'],np.array(manifest['logical_position_root_m'])))
    starts=np.array([rows['G:string%d'%i] for i in range(1,7)]);ends=np.array([rows['G:string%d_end'%i] for i in range(1,7)])
    frets=np.array([rows['G:nut']]+[rows['G:fret%d'%i] for i in range(1,23)])
    surface=load_press_surface([2,1],[4,5]);plane=np.array(surface['plane_G'])
    a,b=project_press_strings(torch.tensor(starts)[None],torch.tensor(ends)[None],torch.tensor(plane))
    snapshot=dict(starts_G_m=a[0].numpy(),ends_G_m=b[0].numpy(),fret_markers_G_m=frets)
    cells=[]
    for string,fret in ((3,4),(2,5)):
        center=fret_target(snapshot,string,fret)
        low,high=sorted(frets[fret-1:fret+1,1]);y=(low+high)/2
        start,end=starts[string-1],ends[string-1];fraction=(y-start[1])/(end[1]-start[1])
        independent=start+fraction*(end-start);independent[2]=-(independent[:2]@plane[:2]+plane[3])/plane[2]
        assert 0<=fraction<=1 and low+surface['inward_margin_m']<y<high-surface['inward_margin_m']
        np.testing.assert_allclose(center,independent,rtol=0,atol=1e-12)
        assert abs(center@plane[:3]+plane[3])<1e-12 and np.isfinite(center).all()
        cells.append(dict(physical_string=string,canonical_string=string-1,fret=fret,cell_y_bounds_m=[low,high],fraction=float(fraction),center_G_m=center.tolist()))
    delta=np.array(cells[1]['center_G_m'])-cells[0]['center_G_m']
    assert np.isfinite(delta).all() and delta[0]>0 and delta[1]<0 and abs(delta[2])<1e-12
    return dict(schema='diagnostic.target7_cell_translation.v1',cells=cells,delta_G_m=delta.tolist(),delta_norm_m=float(np.linalg.norm(delta)),
        coordinate_frame='guitar root local meters; +Gx physical6to1 strings, +Gy bridge to nut; Gz-only original press-plane projection',
        definition='Original project_press_strings then core.fret_target; independent NumPy midpoint/interpolation/plane calculation',
        helper_max_residual_tolerance_m=1e-12,press_surface=surface,
        scope='Source finite-cell geometry; not native cooked-surface, reachability, contact, pressure or B actual pose')


@contextmanager
def selected_inputs(state):
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    old=(prior.HERE,prior.INPUTS,runtime.ShortPool)
    class TaskPool(old[2]):
        def __init__(self,config,out):
            super().__init__(config,out)
            try:
                assert self.environment.contract==grid.read(HERE/'cpu_inputs/expected_environment.json')
                short=self.spec;assert short['teacher']['source_target_id']==B_ID and short['finger']==1
                assert short['view']==grid.read(HERE/'cpu_inputs/task_definition.json')['view']
                target=self.environment.task.targets[self.environment.selected_index]
                assert asdict(target)==short['view']['source_target'] and target.string==1 and target.fret==5 and target.finger==1
                grid.write(Path(out)/'target7_native_task.json',dict(expected_environment_exact=True,view=short['view'],source_target_id=B_ID,
                    scope='Original ShortEnvironment B task verified; no A-full-contract identity or B actual/source-pose claim'))
                state['task_verified']=True
            except BaseException:
                try:self.close()
                except BaseException as error:state['cleanup_errors'].append(dict(type=type(error).__name__,message=str(error)))
                raise
    prior.HERE=HERE;prior.INPUTS=dict(old[1],index=(TEACHER,REFERENCE));runtime.ShortPool=TaskPool
    try:yield
    finally:
        prior.HERE,prior.INPUTS,runtime.ShortPool=old
        state['aliases_restored']=(prior.HERE,prior.INPUTS,runtime.ShortPool)==old


def gate(require_review=True):
    paths=actual_gate();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        review=grid.read(HERE/'review.json')
        assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
    return seal,paths|{HERE/'preparation_seal.json'}


def postcheck(out):
    import numpy as np
    evaluation=grid.read(out/'evaluation.json');episodes=evaluation['episodes']
    assert evaluation['assigned_quotas']==[1]*4 and grid.complete(episodes,4) and evaluation['policy_performance'] is False
    assert all(e['target_id']==B_ID and e['steps']<=257 and len(e['reward_components'])==9 for e in episodes)
    config=grid.read(out/'settings.json');short=config['song']['short_learning']
    with np.load(out/'trace_env0_episode0.npz') as saved:trace=dict(saved)
    names=grid.read(out/'trace_metadata.json')['joint_names'];ids=[names.index(n) for n in short['learned_action_names']]
    target=trace['target'][:,ids];native=grid.read(out/'native_effort_readback.json')['actual_native_PD105']
    assert np.isfinite(target).all() and ((target>=np.array(native['lower'])[ids]-2e-6)&(target<=np.array(native['upper'])[ids]+2e-6)).all()
    rate=float(abs(np.diff(target,axis=0)).max()) if len(target)>1 else 0.;assert rate<=4/60+2e-6
    np.testing.assert_allclose(trace['source_time_s'],trace['time_s']+short['view']['score_offset_s'],rtol=0,atol=1e-8)
    hold=trace['time_s']>=2.;reference=grid.read(REFERENCE)
    np.testing.assert_allclose(target[hold],np.broadcast_to([reference['selected_targets_rad'][n] for n in short['learned_action_names']],target[hold].shape),rtol=0,atol=2e-6)
    pose=short['teacher']['wrist_position_G_m'];np.testing.assert_allclose(trace['wrist_goal_G_m'][hold],np.broadcast_to(pose,trace['wrist_goal_G_m'][hold].shape),rtol=0,atol=2e-6)
    q=np.array(short['teacher']['wrist_quaternion_G_xyzw']);dot=abs(trace['wrist_goal_G_xyzw'][hold]@q)
    np.testing.assert_allclose(dot,1.,rtol=0,atol=2e-6)
    return dict(acceptance=cap.repro.acceptance(episodes),source_target_id=B_ID,assigned_first_attempts=4,env0_endpoints=len(target),
        selected_max_endpoint_delta_rad=rate,rate_scope='Stored endpoint-to-endpoint only; t0 target not saved',score_clock_exact=True,
        post_ramp_endpoint_samples=int(hold.sum()),selected_targets_and_wrist_goal_match=True if hold.any() else None,scope='NoNN derived B7 hypothesis; original music predicate only, not AtoB transition/free-guitar success')


def launch():
    out=HERE/'runs/index';cap.reject_existing(out);seal,paths=gate()
    out.mkdir(parents=True,exist_ok=False);identity=(out.stat().st_dev,out.stat().st_ino)
    state=dict(task_verified=False,aliases_restored=False,cleanup_errors=[]);failure=None;completed=False
    try:
        import isaacgym
        with selected_inputs(state):prior.execute('index','reference',out,identity,seal,paths)
        result=postcheck(out);grid.write(out/'target7_reference_audit.json',result);completed=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
        if not (out/'report.json').exists():grid.write(out/'report.json',dict(completed=False,closed=False,failure=failure))
        raise
    finally:
        cap.owned(out,identity);ok=state['task_verified'] and state['aliases_restored'] and not state['cleanup_errors']
        grid.write(out/'target7_scope_report.json',dict(completed=completed and ok,failure=failure,**state))
        if failure is None and not ok:raise RuntimeError('Target7 task/scope audit failed; outputs preserved')


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    paths=actual_gate();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_teacher,read_reference,subset
    from guitar_learning.song.task import make_task
    from guitar_learning.tests.test_gpu_environment import fixture
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    declaration,old_checks=prior.cpu_checks()
    aconfig=prior.settings('index');a=read_teacher(prior.INPUTS['index'][0]);aref=read_reference(prior.INPUTS['index'][1],aconfig['song']['short_learning'])
    assert a['source_target_id']==aref['source_target_id']==A_ID
    derivation=geometry_derivation();task=make_task(aconfig['song_training']['bundle'],pre_roll_s=3.,tail_s=.5)
    _,_,view=subset(task,dict(source_target_id=B_ID,finger=1));target=view['source_target']
    assert target['string']==1 and target['fret']==5 and target['finger']==1 and view['duration_ticks']==257
    np.testing.assert_allclose([view['local_press_s'],view['local_onset_s'],view['local_end_s'],target['end_s']-target['onset_s']],[2.88,3.,3.7779,.7779],rtol=0,atol=1e-9)
    schedule=next(r for r in task.provenance['song']['schedule'] if r['target_id']==B_ID)
    assert schedule['source_press_s']==3.2817 and schedule['source_release_s']==5.1548 and schedule['source_end_s']==4.1796
    inputs=HERE/'cpu_inputs';inputs.mkdir();grid.write(inputs/'geometry_derivation.json',derivation)
    grid.write(inputs/'task_definition.json',dict(view=view,schedule=schedule,source_provenance=task.provenance['provenance'],scope='Original make_task/subset source7; shared release is not audible end'))
    evidence={str(p):grid.sha(p) for p in (*prior.INPUTS['index'],inputs/'geometry_derivation.json',inputs/'task_definition.json',prior.FRESH/'analysis/results_v1/review.json',prior.FRESH/'runs/index/evaluation.json')}
    teacher=dict(schema='short_finger_teacher.v2',condition='fixed_wrist_pose',source_target_id=B_ID,finger=1,finger_name='index',ramp_s=2.,
        arm_targets_rad=copy.deepcopy(a['arm_targets_rad']),wrist_quaternion_G_xyzw=copy.deepcopy(a['wrist_quaternion_G_xyzw']),
        wrist_position_G_m=(np.array(a['wrist_position_G_m'])+derivation['delta_G_m']).tolist(),source_evidence=evidence,
        borrowed_A_provenance=dict(source_target_id=A_ID,teacher=str(prior.INPUTS['index'][0]),reference=str(prior.INPUTS['index'][1]),delta_G_m=derivation['delta_G_m']),
        scope='Unverified derived B7 hypothesis: A arm12/quaternion/selected4 exact, wrist position translated by original cell-center delta; native B trials0')
    grid.write(TEACHER,teacher)
    reference=dict(schema='short_finger_reference.v2',source_target_id=B_ID,ramp_s=2.,selected_targets_rad=copy.deepcopy(aref['selected_targets_rad']),
        source_evidence={str(p):grid.sha(p) for p in (TEACHER,*prior.INPUTS['index'],inputs/'geometry_derivation.json',inputs/'task_definition.json')},
        scope='A112 exact selected4 angles under translated B7 wrist hypothesis; not B source actual pose or verified positive')
    grid.write(REFERENCE,reference);state=dict(cleanup_errors=[])
    with selected_inputs(state):
        config=prior.settings('index');assert read_reference(REFERENCE,config['song']['short_learning'])==reference
        assert read_teacher(TEACHER)['arm_targets_rad']==a['arm_targets_rad'] and teacher['wrist_quaternion_G_xyzw']==a['wrist_quaternion_G_xyzw']
    assert state['aliases_restored'] and config['song']['short_learning']['view']==view
    metadata,_=fixture(1);metadata['action_contract']=grid.read(prior.FRESH/'runs/index/training_contract.json')['action']['target_contract']
    env=runtime.ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    assert env.selected_index==view['source_index'] and asdict(env.task.targets[env.selected_index])==target
    grid.write(inputs/'expected_environment.json',env.contract);grid.write(inputs/'index_settings.json',config);grid.write(inputs/'settings.json',config)
    grid.write(inputs/'effort_declaration.json',declaration)
    grid.write(inputs/'commands.json',[dict(finger='index',control='reference',episodes=4,argv=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute'])])
    tests=importlib.util.spec_from_file_location('target7_cpu_checks',HERE/'cpu_checks.py');checks=importlib.util.module_from_spec(tests);tests.loader.exec_module(checks)
    extra=checks.check(sys.modules[__name__])
    grid.write(HERE/'cpu_verification.json',dict(CPU_only=True,GPU_executed=False,old_prelearning_CPU_regressions=old_checks,**extra))
    paths.update(inputs.glob('*.json'));paths.update((Path(__file__).resolve(),HERE/'PLAN.md',HERE/'cpu_checks.py',HERE/'cpu_verification.json'))
    paths.update(map(Path,derivation['press_surface']['source_sha256']));paths.update(Path(row['path']) for row in task.provenance['provenance'])
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),scope='One noNN B7 translated-wrist hypothesis; CPU prepared only; root-only native4'))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),native_trials=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','execute','gate-check','dry-plan'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare:prepare()
    elif args.execute:launch()
    elif args.dry_plan:print(json.dumps([dict(finger='index',source_target_id=B_ID,control='reference',episodes=4,out=str(HERE/'runs/index'))]))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:launch()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Unreviewed native admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym')) and not (HERE/'runs').exists()
        print(json.dumps(dict(stdlib_gate=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False,pending_native_rejected=True)))
