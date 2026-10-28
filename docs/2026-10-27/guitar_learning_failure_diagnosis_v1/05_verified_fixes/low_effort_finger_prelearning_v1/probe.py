"""CPU preparation; root-only ten no-NN four-attempt low-effort controls."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
FRESH = HERE.parent/'finger_effort_limit_v1/oracle_grid_v1/reproduction_v2'
module = importlib.util.spec_from_file_location('prelearning_fresh_evidence', FRESH/'probe.py')
fresh = importlib.util.module_from_spec(module); sys.modules[module.name] = fresh
module.loader.exec_module(fresh)
cap, grid = fresh.cap, fresh.cap.parent
ROOT = grid.ROOT
INPUTS = dict(grid.INPUTS, **{f: tuple(grid.DIAG/'03_short_learning/other_finger_precheck_v3'/
    (kind+'_'+f+'_row'+row+'.json') for kind in ('teacher', 'reference')) for f, row in (('ring','16'),('pinky','23'))})
JOBS = [(f,c) for f in INPUTS for c in (('zero','random') if f in ('index','middle') else ('reference','zero','random'))]
STD = .1711710544767014
SCHEMA = 'diagnostic.low_effort_finger_prelearning.v1'


def actual_gate():
    # All called helpers are stdlib-only; no settings()/runtime import here.
    paths, selected = fresh.grid_gate()
    assert selected == dict(index=112, middle=114)
    review_path = FRESH/'analysis/results_v1/review.json'
    review = grid.read(review_path)
    assert review['verdict'] == 'PASS' and not review['findings']
    paths.add(review_path)
    verification_path = review_path.parent/'verification.json'
    assert str(verification_path) in review['reviewed_sha256']
    for mapping in (review['reviewed_sha256'], *[grid.read(verification_path)[k] for k in ('input_sha256','verified_input_sha256')]):
        assert mapping and all(Path(p).is_file() and grid.sha(p) == h for p,h in mapping.items())
        paths.update(map(Path, mapping))
    for folder in (FRESH/'runs/index', cap.HERE/'runs/middle'):
        evaluation, report = (grid.read(folder/name) for name in ('evaluation.json','report.json'))
        assert evaluation['assigned_quotas'] == [1]*4 and grid.complete(evaluation['episodes'],4)
        assert cap.repro.acceptance(evaluation['episodes'])['passed'] and report['completed'] and report['closed']
        paths.update(folder/name for name in ('evaluation.json','report.json','settings.json'))
    launcher = FRESH/'01_launcher.json'
    assert grid.read(launcher)['completed'] and grid.read(launcher)['returncode'] == 0
    return paths | {launcher, FRESH/'probe.py', cap.HERE/'probe.py'}


def gate(require_review=True):
    paths = actual_gate(); seal = grid.read(HERE/'preparation_seal.json')
    assert not require_review or seal['independent_review'] == 'passed_no_findings'
    if require_review:
        review_path = HERE/'review.json'; review = grid.read(review_path)
        assert review['verdict'] == 'PASS' and not review['findings']
        assert seal['input_pins'].get(str(review_path)) == grid.sha(review_path)
    assert all(Path(p).is_file() and grid.sha(p) == h for p,h in seal['input_pins'].items())
    return seal, paths


def settings(finger):
    from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
    return make_settings(argparse.Namespace(teacher=str(INPUTS[finger][0]),mode='incremental',initial_std=STD,
        song='05_BN2-131-B_solo',size='large',seed=7,num_envs=4,horizon=32,updates=1,save_every=50))


class Actions:
    """Not a network: fresh zero or selected-four independent Gaussian→tanh commands."""
    def __init__(self, selected, control):
        self.selected, self.control, self.generator = selected, control, None

    def act(self, state, *unused, deterministic=True):
        import torch
        action = state.new_zeros((len(state),39))
        if self.control == 'random':
            if self.generator is None: self.generator = torch.Generator(device=state.device).manual_seed(7)
            action[:,self.selected] = (torch.randn((len(state),4),device=state.device,dtype=state.dtype,
                generator=self.generator)*STD).tanh()
        return dict(action=action)


def cpu_checks():
    import tempfile
    import torch
    from types import SimpleNamespace
    from guitar_learning.tests.test_short_finger_learning import setup
    from guitar_learning.tool.experiments.short_finger_learning import runner
    declaration, checks = cap.cpu_checks()
    checks['original_cap_helper_old_reference_regression'] = checks.pop('checks')
    assert len(JOBS) == 10 and len(set(JOBS)) == 10
    for finger in INPUTS:
        spec = settings(finger)['song']['short_learning']; ids = spec['learned_action_indices']
        state = torch.zeros(4,561); a,b = Actions(ids,'random'),Actions(ids,'random')
        first, second = a.act(state)['action'],a.act(state)['action']
        assert torch.equal(first,b.act(state)['action']) and torch.equal(second,b.act(state)['action'])
        assert not torch.equal(first,second) and torch.isfinite(first).all() and (first.abs()<1).all()
        assert not first[:,[i for i in range(39) if i not in ids]].any()
        assert not Actions(ids,'zero').act(state)['action'].any()
    # Original evaluator: early failed env0, then env0 retry + other first attempts.
    env,snapshot,observation,metadata,_,_ = setup(count=4)
    feedback = dict(active=torch.zeros(4,dtype=torch.bool),pose_error_world=torch.zeros(4,6),
        requested_delta_rad=torch.zeros(4,12),requested_arm_rad=torch.zeros(4,12),candidate_arm_rad=torch.zeros(4,12),
        position_goal_G_m=torch.zeros(4,3),quaternion_goal_G_xyzw=torch.tensor([[0.,0.,0.,1.]]*4))
    scene = SimpleNamespace(q=snapshot['q'],target=snapshot['target'],body_state=snapshot['body_state'],
        snapshot=lambda:snapshot,names=metadata['joint_names'],metadata=metadata)
    pool = SimpleNamespace(num_envs=4,observation=observation,environment=env,scene=scene,
        last_policy_action=torch.zeros(4,39),last_executed_action=torch.zeros(4,39),last_wrist_feedback=feedback)
    calls = []; resets = []
    def step(action):
        calls.append(action.clone()); env.clock[:] += 4
        ids = [0] if len(calls)==1 else list(range(4))
        return observation,None,None,torch.tensor([True,False,False,False]),torch.zeros(4,dtype=torch.bool),[env._episode(i,i==0) for i in ids]
    pool.step = step
    pool.reset = lambda ids:(resets.append(ids.tolist()) or observation,None)
    with tempfile.TemporaryDirectory() as temp:
        runner._evaluate(pool,Actions(env.contract['task']['short_learning']['learned_action_indices'],'zero'),
            env.contract['task']['short_learning'],SimpleNamespace(episodes=4,control='zero'),Path(temp))
        evaluation = grid.read(Path(temp)/'evaluation.json')
        assert grid.complete(evaluation['episodes'],4) and evaluation['assigned_quotas']==[1]*4
        assert evaluation['episodes'][0]['reason']=='terminal_failure' and len(calls)==2 and resets==[[0]]
    with tempfile.TemporaryDirectory() as temp:
        for path in (Path(temp),Path(temp)/'link'):
            if path.name == 'link': path.symlink_to(Path(temp)/'absent')
            try: launch('index','zero',path)
            except (FileExistsError,ValueError): pass
            else: raise AssertionError('Existing/symlink output accepted')
    return declaration, dict(checks, ten_scenes_40_first_attempts=True, no_NN_or_training=True,
        selected4_only_Gaussian_tanh_seed7_reproducible=True, random_consecutive_draws_differ=True,
        original_evaluator_four_quotas_early_failure_and_retry_exclusion=True)


def prepare():
    paths = actual_gate()
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    declaration, checks = cpu_checks(); inputs = HERE/'cpu_inputs'; inputs.mkdir()
    for finger,(teacher,reference) in INPUTS.items():
        config = settings(finger); short = config['song']['short_learning']
        ref = read_reference(reference,short)
        paths.update((teacher,reference,*map(Path,short['teacher']['source_evidence']),*map(Path,ref['source_evidence'])))
        grid.write(inputs/(finger+'_settings.json'),config)
        if finger in ('index','middle'):
            baseline = FRESH/'runs/index' if finger == 'index' else cap.HERE/'runs/middle'
            assert config == grid.read(baseline/'settings.json')
    grid.write(inputs/'settings.json',settings('index')); grid.write(inputs/'effort_declaration.json',declaration)
    grid.write(inputs/'jobs.json',[dict(finger=f,control=c,assigned_quotas=[1]*4,
        argv=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute','--finger',f,'--control',c]) for f,c in JOBS])
    grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json')); paths.update((Path(__file__),HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification.json'))
    grid.write(HERE/'preparation_seal.json',dict(schema=SCHEMA,independent_review='pending',
        input_pins=runner._pins(settings('index'),inputs,paths),scope='CPU prepared only; root GPU after independent review; no NN/checkpoints/training'))
    result = subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal_path = HERE/'preparation_seal.json'; seal = grid.read(seal_path)
    seal['input_pins'][str(HERE/'fresh_process_gate.json')] = grid.sha(HERE/'fresh_process_gate.json')
    seal_path.write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,jobs=len(JOBS),fresh_process_gate=json.loads(result.stdout))))


def execute(finger, control, out, identity, seal, paths):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    from guitar_learning.training.recording import project_source_paths
    cleanup = []; original = prepared_reset_v1.load_prepared_reset_contract

    class EffortPool(ShortPool):
        def _create_scene(self, config, target_out):
            calls = []; scene = None
            try:
                with cap.effort_loader(calls): scene = super()._create_scene(config,target_out)
                assert prepared_reset_v1.load_prepared_reset_contract is original and len(calls) == 1
                self.effort_readback = cap.verify_native(scene,*calls[0]); return scene
            except BaseException:
                if scene is not None:
                    try: scene.close()
                    except BaseException as error: cleanup.append(dict(type=type(error).__name__,message=str(error)))
                raise

    config = settings(finger); assert config == grid.read(HERE/'cpu_inputs'/(finger+'_settings.json'))
    runner.write(out/'settings.json',config)
    pins = runner._pins(config,out,[HERE/'preparation_seal.json',*map(Path,seal['input_pins']),*paths])
    runner.write(out/'inputs_before.json',pins)
    runner.write(out/'action_provider.json',dict(control=control,selected_indices=config['song']['short_learning']['learned_action_indices'],
        seed=7,Gaussian_mean=0.,Gaussian_std=STD,squash='tanh',NN=False,training_updates=0,
        scope='Selected4 independent scripted commands; reference uses original evaluator ramp/trajectory. Not untrained-NN exact; 4env not4seeds.'))
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    pool = None; completed = False; failure = None; resources = {}; started = time.monotonic()
    try:
        pool = EffortPool(config,out)
        assert np.array_equal(pool.scene.effort_caps.cpu().numpy(),pool.scene.pd_properties['effort'])
        assert torch.equal(pool.controller.caps,pool.scene.effort_caps)
        pool.contract['native_backend']['diagnostic_native_effort'] = pool.effort_readback
        runner.write(out/'native_effort_readback.json',pool.effort_readback); runner.write(out/'training_contract.json',pool.contract)
        runner._evaluate(pool,Actions(pool.spec['learned_action_indices'],control),pool.spec,
            argparse.Namespace(control=control,reference=str(INPUTS[finger][1]),episodes=4),out)
        evaluation = grid.read(out/'evaluation.json')
        assert grid.complete(evaluation['episodes'],4) and evaluation['assigned_quotas'] == [1]*4
        steps = pool.scene.physics_steps
        assert steps % 4 == 0 and steps//4 <= pool.spec['view']['duration_ticks']
        resources = dict(physics_steps=steps,control_ticks=steps//4)
        assert not list(out.glob('*.pt')); completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error)); raise
    finally:
        try:
            if pool is not None: pool.close()
        except BaseException as error: cleanup.append(dict(type=type(error).__name__,message=str(error)))
        cap.owned(out,identity)
        changed = [p for p,h in pins.items() if not Path(p).is_file() or grid.sha(p) != h]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        scene = grid.read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
        restored = prepared_reset_v1.load_prepared_reset_contract is original
        valid = (scene.get('closed') is True and scene.get('environment_count') == 4 and scene.get('diagnostic_guitar_mode') == 'fixed'
            and scene.get('hand_collision',{}).get('enabled_distinct_finger_pairs') == 90 and scene.get('hand_collision_native_readback_environments') == 4
            and scene.get('physx_use_gpu') is True and scene.get('use_gpu_pipeline') is True and scene.get('physics_steps') == resources.get('physics_steps'))
        runner.write(out/'inputs_after.json',dict(verified=not changed and not missing,changed_paths=changed,unpinned_project_sources=missing,input_pins=pins))
        runner.write(out/'report.json',dict(completed=completed and valid and restored and not changed and not missing and not cleanup,
            closed=scene.get('closed') is True,scene_valid=valid,loader_restored=restored,failure=failure,close_errors=cleanup,
            changed_inputs=changed,unpinned_project_sources=missing,resources=resources,assigned_first_attempts=4,
            cap_Nm=cap.CAP,no_NN_checkpoint_training=True,wall_s=time.monotonic()-started))
        if failure is None and (not valid or not restored or changed or missing or cleanup): raise RuntimeError('Source/scene/close verification failed; outputs preserved')


def launch(finger, control, out):
    cap.reject_existing(out); assert (finger,control) in JOBS
    seal, paths = gate()
    out.mkdir(parents=True,exist_ok=False); identity = (out.stat().st_dev,out.stat().st_ino)
    try:
        import isaacgym  # Must precede runtime/Torch/NumPy; gates above are stdlib-only.
        execute(finger,control,out,identity,seal,paths)
    except BaseException as error:
        if not (out/'report.json').exists(): grid.write(out/'report.json',dict(completed=False,closed=False,failure=dict(type=type(error).__name__,message=str(error))))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','self-test','gate-check','dry-plan','execute'): group.add_argument('--'+name,action='store_true')
    parser.add_argument('--finger',choices=tuple(INPUTS)); parser.add_argument('--control',choices=('reference','zero','random'))
    args = parser.parse_args(); sys.path.insert(0,str(ROOT))
    if args.prepare: prepare()
    elif args.self_test: print(json.dumps(cpu_checks()[1],indent=2))
    elif args.gate_check:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        seal,_ = gate(require_review=False)
        if seal['independent_review'] == 'pending':
            import tempfile
            with tempfile.TemporaryDirectory() as temp:
                out = Path(temp)/'denied'
                try: launch('index','zero',out)
                except AssertionError: pass
                else: raise AssertionError('Unreviewed execute admitted')
                assert not out.exists()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        print(json.dumps(dict(fresh_process=True,full_actual_and_own_seal_gate=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False)))
    elif args.dry_plan: print(json.dumps([dict(finger=f,control=c,out=str(HERE/'runs'/(f+'_'+c))) for f,c in JOBS],indent=2))
    else: launch(args.finger,args.control,HERE/'runs'/(str(args.finger)+'_'+str(args.control)))
