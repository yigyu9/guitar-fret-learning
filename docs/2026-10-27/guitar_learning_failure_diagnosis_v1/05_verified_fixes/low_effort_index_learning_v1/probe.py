"""Root-only index128 effort diagnostic: no-NN precheck, then gated original short PPO."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PRE = HERE.parent/'low_effort_finger_prelearning_v1'
spec = importlib.util.spec_from_file_location('index128_prelearning', PRE/'probe.py')
pre = importlib.util.module_from_spec(spec); sys.modules[spec.name] = pre; spec.loader.exec_module(pre)
cap, grid = pre.cap, pre.grid
PRECHECK_REVIEW = HERE/'precheck_analysis/results_v1/review.json'
RENDER = grid.DIAG/'03_short_learning/support/render_short_finger.py'
UPDATES = (0,50,100,150,200,250,300)


def reviewed(path):
    review = grid.read(path); assert review['verdict']=='PASS' and not review['findings']
    verification = path.parent/'verification.json'; assert str(verification) in review['reviewed_sha256']
    paths = {path}
    for mapping in (review['reviewed_sha256'], *[grid.read(verification)[k] for k in ('input_sha256','verified_input_sha256')]):
        assert mapping and all(Path(p).is_file() and grid.sha(p)==h for p,h in mapping.items())
        paths.update(map(Path,mapping))
    assert grid.read(verification)['completed']
    return paths


def actual_gate():
    paths = pre.actual_gate() | reviewed(PRE/'analysis/results_v1/review.json')
    launcher = PRE/'01_launcher.json'; value = grid.read(launcher)
    assert value['completed'] and value['returncode']==0 and len(value['children'])==10
    assert [(c['finger'],c['control']) for c in value['children']]==pre.JOBS and all(c['returncode']==0 for c in value['children'])
    return paths | {launcher}


def precheck_gate():
    paths = reviewed(PRECHECK_REVIEW); rows = {}
    launcher = HERE/'01_precheck_launcher.json'; launch = grid.read(launcher)
    assert launch['completed'] and launch['returncode']==0 and len(launch['children'])==3
    assert [c['control'] for c in launch['children']]==['reference','zero','random'] and all(c['returncode']==0 for c in launch['children'])
    for control in ('reference','zero','random'):
        folder = output('precheck',control,0)
        evaluation = grid.read(folder/'evaluation.json'); report = grid.read(folder/'diagnostic_report.json')
        assert evaluation['assigned_quotas']==[1]*128 and grid.complete(evaluation['episodes'],128)
        assert report['completed'] and report['scene_valid'] and report['aliases_restored'] and not report['failure']
        rows[control] = evaluation['episodes']; paths.update(folder/name for name in ('evaluation.json','diagnostic_report.json'))
    assert acceptance(rows)['passed']
    return paths | {launcher}


def acceptance(rows):
    assert set(rows)=={'reference','zero','random'} and all(grid.complete(v,128) for v in rows.values())
    ref,zero = rows['reference'],rows['zero']
    passed = (sum(r['achieved'] for r in ref)/128>=.9 and sum(r['clean_fraction'] for r in ref)/128>=.9
        and sum(r['audible_wrong_fraction'] for r in ref)/128<=.1
        and not any(r['termination']['physical_failure'] or r['termination']['wrist_failure'] for r in ref)
        and sum(r['achieved'] for r in zero)/128<=.1)
    return dict(passed=passed,scope='Original128 first attempts including failures; random disclosed, no random performance threshold')


def gate(phase, require_review=True):
    paths = actual_gate(); seal = grid.read(HERE/'preparation_seal.json')
    if require_review:
        review_path = HERE/'review.json'; review = grid.read(review_path)
        assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'].get(str(review_path))==grid.sha(review_path)
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if phase!='precheck': paths.update(precheck_gate())
    return seal, paths | {HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def train_args(out):
    return argparse.Namespace(command='train',teacher=str(pre.INPUTS['index'][0]),mode='incremental',initial_std=pre.STD,
        song='05_BN2-131-B_solo',size='large',seed=7,num_envs=128,horizon=32,updates=300,save_every=50,out=str(out))


def verify128(scene, source, declaration):
    """Explicit128 audit; never call/relax the old4/135/180 verifiers."""
    import numpy as np
    expected = cap.expected_properties(source,scene.pd_properties.dtype)
    expected['effort'][declaration['native_indices']] = cap.CAP
    assert scene.num_envs==len(scene.envs)==len(scene.actors)==scene._hand_collision_readback_count==128
    assert scene.physics_steps==0 and scene.hand_collision['enabled_distinct_finger_pairs']==90
    assert scene.names==source['initial']['joint_names'] and np.array_equal(scene.pd_properties,expected)
    for env,actors in zip(scene.envs,scene.actors):
        assert np.array_equal(scene.gym.get_actor_dof_properties(env,actors[0]),expected)
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted,source)
    baseline = cap.expected_properties(source,expected.dtype)
    changed = {k:np.flatnonzero(expected[k]!=baseline[k]).tolist() for k in expected.dtype.names}
    assert changed['effort']==declaration['native_indices'] and not any(v for k,v in changed.items() if k!='effort')
    return dict(**declaration,environment_count=128,explicit_DOF105_readback_environments=128,collision_readback_environments=128,
        changed_native_field_indices=changed,actual_native_PD105={k:expected[k].tolist() for k in expected.dtype.names},
        original_profile_native_PD105={k:baseline[k].tolist() for k in baseline.dtype.names},expected_readback_exact=True)


@contextmanager
def effort_scope(paths,state):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training import finger_skill_runner
    old = (runner.ShortPool,runtime.ShortPool,runner._pins,finger_skill_runner._pins)
    loader = prepared_reset_v1.load_prepared_reset_contract
    def pins(config,out,extra=()):
        if Path(out)==state['out']: state['identity']=(Path(out).stat().st_dev,Path(out).stat().st_ino)
        return old[3](config,out,[*extra,*paths])
    class EffortPool(old[1]):
        def _create_scene(self,config,out):
            calls = []; scene = None; state['scene_out']=Path(out)
            try:
                with cap.effort_loader(calls): scene = super()._create_scene(config,out)
                state['scene']=scene
                assert prepared_reset_v1.load_prepared_reset_contract is loader and len(calls)==1
                self.effort_readback=verify128(scene,*calls[0]); return scene
            except BaseException:
                if scene is not None:
                    try: scene.close()
                    except BaseException as e: state['cleanup_errors'].append(dict(type=type(e).__name__,message=str(e)))
                raise
        def __init__(self,config,out):
            assert config==grid.read(HERE/'cpu_inputs/settings.json')
            super().__init__(config,out)
            state['pool']=self
            try:
                assert np.array_equal(self.scene.effort_caps.cpu().numpy(),self.scene.pd_properties['effort'])
                assert torch.equal(self.controller.caps,self.scene.effort_caps)
                self.effort_readback['controller_caps_exact']=True
                assert self.effort_readback==grid.read(HERE/'cpu_inputs/effort_declaration128.json')
                self.contract['native_backend']['diagnostic_native_effort']=copy.deepcopy(self.effort_readback)
                runner.write(Path(out)/'native_effort_readback.json',self.effort_readback)
            except BaseException:
                self.close(); raise
        def close(self):
            try: super().close()
            except BaseException as e: state['cleanup_errors'].append(dict(type=type(e).__name__,message=str(e)))
    runner.ShortPool=runtime.ShortPool=EffortPool; runner._pins=finger_skill_runner._pins=pins
    try: yield runner
    finally:
        runner.ShortPool,runtime.ShortPool,runner._pins,finger_skill_runner._pins=old
        state['aliases_restored']=(runner.ShortPool,runtime.ShortPool,runner._pins,finger_skill_runner._pins)==old
        state['loader_restored']=prepared_reset_v1.load_prepared_reset_contract is loader


def precheck(runner,control,out):
    import numpy as np
    import torch
    config=runner.make_settings(train_args(out)); out.mkdir(parents=True,exist_ok=False)
    runner.write(out/'settings.json',config); runner.write(out/'inputs_before.json',runner._pins(config,out))
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32=False
    pool=runner.ShortPool(config,out); runner.write(out/'training_contract.json',pool.contract)
    runner.write(out/'action_provider.json',dict(NN=False,updates=0,seed=7,selected4_Gaussian_mean=0.,std=pre.STD,
        squash='tanh',scope='Reviewed noNN provider;128env not128seeds; ref uses original ramp/trajectory'))
    runner._evaluate(pool,pre.Actions(pool.spec['learned_action_indices'],control),pool.spec,
        argparse.Namespace(control=control,reference=str(pre.INPUTS['index'][1]),episodes=128),out)
    result=grid.read(out/'evaluation.json'); assert result['assigned_quotas']==[1]*128 and grid.complete(result['episodes'],128)
    assert pool.scene.physics_steps%4==0 and pool.scene.physics_steps//4<=pool.spec['view']['duration_ticks']
    assert not list(out.glob('*.pt'))


def output(phase,control,update):
    if phase=='precheck': return HERE/'runs'/('precheck_'+str(control))
    if phase=='train': return HERE/'train'
    return HERE/(('evaluation_' if phase=='evaluate' else 'native_video_')+('%06d'%update))


def checkpoint(update):
    return HERE/'train'/('initial.pt' if update==0 else 'final.pt' if update==300 else 'evaluation_%06d.pt'%update)


def launch(phase,control,update):
    out=output(phase,control,update); cap.reject_existing(out)
    assert (phase=='precheck' and control in ('reference','zero','random') and update==0) or (phase!='precheck' and control is None)
    assert phase!='train' or update==0
    assert update in UPDATES
    seal,paths=gate(phase)
    state=dict(out=out,cleanup_errors=[],pool=None,scene=None,aliases_restored=False,loader_restored=False)
    failure=None; completed=False; started=time.monotonic()
    try:
        import isaacgym  # The entire gate above is stdlib-only.
        from guitar_learning.training.recording import project_source_paths
        with effort_scope(paths,state) as runner:
            try:
                if phase=='precheck': precheck(runner,control,out)
                elif phase=='train': runner.run(train_args(out))
                elif phase=='evaluate': runner.run(argparse.Namespace(command='evaluate',checkpoint=str(checkpoint(update)),
                    control='policy',reference=None,episodes=128,out=str(out)))
                else:
                    module=importlib.util.spec_from_file_location('index128_short_video',RENDER)
                    render=importlib.util.module_from_spec(module); module.loader.exec_module(render)
                    render.render(checkpoint(update),out,num_envs=128,control='policy')
                completed=True
            finally:
                if state['pool'] is not None: state['pool'].close()
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error)); raise
    finally:
        if not out.exists(): out.mkdir(parents=True,exist_ok=False)
        if 'identity' in state: cap.owned(out,state['identity'])
        else: assert not out.is_symlink()
        pins=grid.read(out/'inputs_before.json') if (out/'inputs_before.json').is_file() else seal['input_pins']
        changed=[p for p,h in pins.items() if not Path(p).is_file() or grid.sha(p)!=h]
        missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins)) if 'project_source_paths' in locals() else []
        scene=state['scene']; audit=scene.diagnostics if scene is not None else {}
        valid=(audit.get('closed') is True and audit.get('environment_count')==128 and audit.get('diagnostic_guitar_mode')=='fixed'
            and audit.get('physx_use_gpu') is True and audit.get('use_gpu_pipeline') is True
            and audit.get('hand_collision',{}).get('enabled_distinct_finger_pairs')==90 and audit.get('hand_collision_native_readback_environments')==128)
        ok=completed and valid and state['aliases_restored'] and state['loader_restored'] and not changed and not missing and not state['cleanup_errors']
        grid.write(out/'diagnostic_inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
        grid.write(out/'diagnostic_report.json',dict(completed=ok,failure=failure,scene_valid=valid,closed=audit.get('closed') is True,
            aliases_restored=state['aliases_restored'],loader_restored=state['loader_restored'],cleanup_errors=state['cleanup_errors'],
            changed_inputs=changed,unpinned_project_sources=missing,phase=phase,control=control,update=update,native_environment_count=128,
            physics_steps=audit.get('physics_steps'),wall_s=time.monotonic()-started))
        if failure is None and not ok: raise RuntimeError('128cap source/alias/native/close audit failed; artifacts preserved')


def prepare():
    paths=actual_gate(); assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    test_spec=importlib.util.spec_from_file_location('index128_cpu_checks',HERE/'cpu_checks.py')
    tests=importlib.util.module_from_spec(test_spec); test_spec.loader.exec_module(tests)
    declaration,checks=tests.check(sys.modules[__name__])
    cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    inputs=HERE/'cpu_inputs'; inputs.mkdir(); config=runner.make_settings(train_args(HERE/'train'))
    reference=read_reference(pre.INPUTS['index'][1],config['song']['short_learning'])
    grid.write(inputs/'settings.json',config); grid.write(inputs/'effort_declaration128.json',declaration)
    commands=dict(precheck=[[grid.PYTHON,'-B',str(Path(__file__)),'--execute','precheck','--control',c] for c in ('reference','zero','random')],
        train=[grid.PYTHON,'-B',str(Path(__file__)),'--execute','train'],
        evaluate=[[grid.PYTHON,'-B',str(Path(__file__)),'--execute','evaluate','--update',str(u)] for u in UPDATES],
        render_template=[grid.PYTHON,'-B',str(Path(__file__)),'--execute','render','--update','CHOOSE_FROM_ACTUAL_FIXED_EVALUATIONS'])
    grid.write(inputs/'commands.json',commands); grid.write(HERE/'cpu_verification.json',checks)
    paths.update((Path(__file__),HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification.json',PRE/'probe.py',RENDER,
        *pre.INPUTS['index'],*map(Path,reference['source_evidence'])))
    paths.update(inputs.glob('*.json'))
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),
        precheck_review_required=str(PRECHECK_REVIEW),scope='CPU prepared only;128native/learning unverified;train blocked until independently reviewed128precheck'))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__)),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal=grid.read(HERE/'preparation_seal.json'); seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(result.stdout.strip())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true'); group.add_argument('--gate-check',action='store_true'); group.add_argument('--execute',choices=('precheck','train','evaluate','render'))
    parser.add_argument('--control',choices=('reference','zero','random')); parser.add_argument('--update',type=int,choices=UPDATES,default=0)
    args=parser.parse_args(); sys.path.insert(0,str(grid.ROOT))
    if args.prepare: prepare()
    elif args.gate_check:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        gate('precheck',require_review=False)
        try: gate('train',require_review=False)
        except (FileNotFoundError,AssertionError): pass
        else: raise AssertionError('Train admitted without reviewed128 precheck')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        print(json.dumps(dict(fresh_process=True,full_stdlib_gate=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False,unreviewed128_train_rejected=True)))
    else: launch(args.execute,args.control,args.update)
