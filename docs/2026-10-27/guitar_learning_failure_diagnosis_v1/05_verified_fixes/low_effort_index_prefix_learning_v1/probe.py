"""New-schema prefix F4 experiment; root-only native128, original PPO runner."""
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
def module(name,path):
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v)
    return sys.modules[name]
guard=module('prefix_learning_guard_evidence',HERE.parent/'index_candidate_dip_guard_v1/probe.py')
release=module('prefix_learning_release_evidence',HERE.parent/'index_prefix_release_transfer_v1/probe.py')
B,base,grid,cap=guard.B,guard.B.base,guard.grid,guard.cap
RELEASE_REVIEW=release.HERE/'analysis/results_v1/review.json'
RELEASE_SHA='fde9560714e62c36d17433a59583f24cc79bc15c181f84ae86851577e45ee122'
GUARD_REVIEW=guard.HERE/'analysis/results_v1/review.json'
UPDATES=(0,50,100,150,200,250,300)
CONTROLS=('reference','zero','random')


def support():return module('prefix_learning_adapters',HERE/'learning.py')
def settings():return grid.read(HERE/'cpu_inputs/settings.json')
def output(phase,control=None,update=0):
    return HERE/'runs'/('precheck_'+control) if phase=='precheck' else HERE/'train' if phase=='train' else HERE/('evaluation_%06d'%update)
def checkpoint(update):return HERE/'train'/('initial.pt' if update==0 else 'final.pt' if update==300 else 'evaluation_%06d.pt'%update)


def acceptance(rows):
    assert grid.complete(rows,128) and all(r['selected_target_count']==len(r['notes'])==3 for r in rows)
    per_note=[]
    for i,index in enumerate((4,7,8)):
        notes=[r['notes'][i] for r in rows];assert all(n['source_index']==index for n in notes)
        achieved=sum(n['achieved'] for n in notes)/128;clean=sum(n['clean_fraction'] for n in notes)/128;wrong=sum(n['audible_wrong_fraction'] for n in notes)/128
        per_note.append(dict(source_index=index,achieved_fraction=achieved,mean_clean_fraction=clean,mean_wrong_fraction=wrong,passed=achieved>=.9 and clean>=.9 and wrong<=.1))
    all3=sum(r['achieved'] for r in rows)/128;physical=sum(r['termination']['physical_failure'] for r in rows);wrist=sum(r['termination']['wrist_failure'] for r in rows)
    music=all(n['passed'] for n in per_note) and all3>=.9 and physical==wrist==0
    released=sum(r['notes'][0]['released'] for r in rows)/128;release_passed=released>=.9
    return dict(attempts=128,note_opportunities=384,per_note=per_note,all3_achieved_fraction=all3,physical_failures=physical,wrist_failures=wrist,
        A_released_fraction=released,music_passed=music,release_passed=release_passed,stage_ready=music and release_passed,
        scope='Original music separate from original A native release latch; no full-skin/pressure/naturalness certification')


def evidence():
    _,paths=guard.gate()
    assert grid.sha(RELEASE_REVIEW)==RELEASE_SHA
    paths.update(base.reviewed(RELEASE_REVIEW));paths.update(base.reviewed(GUARD_REVIEW))
    return paths|{Path(__file__).resolve(),HERE/'PLAN.md',release.HERE/'probe.py',release.HERE/'schedule.py'}


def gate(phase='precheck',require_review=True):
    assert phase in ('precheck','train','evaluate')
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert r['verdict']=='PASS' and not r['findings'] and seal['independent_review']=='passed_no_findings'
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    if phase!='precheck':
        root=HERE/'precheck_analysis/results_v1';paths.update(base.reviewed(root/'review.json'))
        value=grid.read(root/'acceptance.json');assert value['reference']==acceptance(grid.read(output('precheck','reference')/'evaluation.json')['episodes'])
        assert value['reference']['stage_ready']
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


@contextmanager
def execution_scope(phase,seal,paths,observed):
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    extra=support();config=settings()
    old=(base.HERE,base.gate,base.output,base.checkpoint,base.effort_scope,runner.SCHEMA,runner.make_settings,runner.compact_episode,runner._evaluate,
        runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,extra.prefix.transition_fraction,extra.LearningPool.record_first_controls)
    def make_settings(args):
        assert args.command=='train' and args.num_envs==128 and args.updates==300 and args.horizon==32 and args.seed==7 and args.size=='large' and args.mode=='incremental'
        assert Path(args.teacher).resolve()==Path(config['song']['short_learning']['teacher']['input_path']) and args.initial_std==config['initial_std']
        return copy.deepcopy(config)
    def policy(*,contract,size):
        value=extra.PrefixPolicy(contract=contract,size=size,fresh=phase=='train');observed['NN_constructors']=observed.get('NN_constructors',0)+1;return value
    @contextmanager
    def scoped_cap(evidence,state):
        observed['state']=state
        with old[4](evidence,state) as current:
            previous=(runner.ShortPool,runtime.ShortPool)
            class CheckedPool(previous[0]):
                def __init__(self,config,out):
                    super().__init__(config,out)
                    try:
                        import torch
                        env=self.environment;assert self.num_envs==128 and env.contract==grid.read(HERE/'cpu_inputs/expected_environment.json')
                        assert [asdict(t) for t in env.task.targets]==grid.read(HERE/'cpu_inputs/source_task.json')['targets']
                        expected=torch.zeros_like(env.focus_mask);expected[:,[4,7,8]]=True
                        assert env.M==67 and env.selected_indices==(4,7,8) and torch.equal(env.focus_mask,expected) and bool((env.duration_ticks==354).all())
                        state['prefix_task_verified']=True
                    except BaseException:
                        try:self.close()
                        except BaseException as error:state['cleanup_errors'].append(dict(type=type(error).__name__,message=str(error)))
                        raise
            runner.ShortPool=runtime.ShortPool=CheckedPool
            try:yield current
            finally:runner.ShortPool,runtime.ShortPool=previous
    base.HERE=HERE;base.gate=lambda requested:(seal,paths);base.output=output;base.checkpoint=checkpoint;base.effort_scope=scoped_cap
    runner.SCHEMA=extra.SCHEMA;runner.make_settings=make_settings;runner.compact_episode=extra.compact_episode;runner._evaluate=extra.evaluate
    runner.ShortPool=runtime.ShortPool=extra.LearningPool;runner.ShortPolicy=runtime.ShortPolicy=policy
    extra.prefix.transition_fraction=extra.timing.wrist_weight;extra.LearningPool.record_first_controls=phase!='train'
    try:yield
    finally:
        (base.HERE,base.gate,base.output,base.checkpoint,base.effort_scope,runner.SCHEMA,runner.make_settings,runner.compact_episode,runner._evaluate,
            runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,extra.prefix.transition_fraction,extra.LearningPool.record_first_controls)=old
        observed['aliases_restored']=(base.HERE,base.gate,base.output,base.checkpoint,base.effort_scope,runner.SCHEMA,runner.make_settings,runner.compact_episode,runner._evaluate,
            runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,extra.prefix.transition_fraction,extra.LearningPool.record_first_controls)==old


def launch(phase,control=None,update=0):
    assert phase in ('precheck','train','evaluate') and update in UPDATES
    assert (phase=='precheck' and control in CONTROLS and update==0) or (phase!='precheck' and control is None)
    assert phase!='train' or update==0
    out=output(phase,control,update);cap.reject_existing(out);seal,paths=gate(phase);observed={};failure=None;completed=False
    try:
        import isaacgym  # Full stdlib gates above; original cap verifier below before policy.
        with execution_scope(phase,seal,paths,observed):base.launch(phase,control,update)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if out.is_dir():
            try:
                import numpy as np
                state=observed.get('state',{});pool=state.get('pool');ctor=observed.get('NN_constructors',0)
                if 'identity' in state:cap.owned(out,state['identity'])
                if pool is not None and getattr(pool,'guard_rows',None):
                    with (out/'current_goal_DIP60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
                if phase!='train' and (out/'evaluation.json').is_file():grid.write(out/'prefix_acceptance.json',acceptance(grid.read(out/'evaluation.json')['episodes']))
                checks=dict(prefix_task_verified=state.get('prefix_task_verified',False),aliases_restored=observed.get('aliases_restored',False),
                    NN_constructor_count_exact=ctor==(0 if phase=='precheck' else 1))
                grid.write(out/'prefix_learning_report.json',dict(completed=completed and all(checks.values()),failure=failure,checks=checks,phase=phase,control=control,update=update,
                    NN_constructors=ctor,fresh_cost_initialization=phase=='train',reference_N_injected=phase=='precheck' and control=='reference',
                    guard_counts_by_goal=pool.guard_counts.cpu().tolist() if pool is not None and hasattr(pool,'guard_counts') else None,
                    guard_count_columns=['all_current_episode_controls','blocked_positive_DIP','negative_DIP'],guard_goal_order=[4,7,8,None],
                    scope='New-schema conditional3note F4/stagedwrist/currentgoalDIP/cost0; not pure cost-only intervention or free-guitar J33'))
                if failure is None and not all(checks.values()):raise RuntimeError('Prefix task/alias/NN count audit failed')
            except BaseException as error:
                if failure is None:raise
                print('Secondary prefix cleanup error: '+repr(error),file=sys.stderr)


def commands():
    prefix=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']
    return dict(precheck=[prefix+['precheck','--control',c] for c in CONTROLS],train=prefix+['train'],
        evaluate=[prefix+['evaluate','--update',str(u)] for u in UPDATES],
        render_status='Future own3note adapter after completed training/selection; old single-note renderer CLI forbidden')


def prepare():
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    extra=support()
    from guitar_learning.tool.experiments.short_finger_learning import runner
    config=runner.make_settings(base.train_args(HERE/'train'))
    config['song']['short_learning']=copy.deepcopy(release.settings()['song']['short_learning']);short=config['song']['short_learning']
    schedule=short.pop('release_transfer');short.update(schema=extra.SCHEMA,ablation=B.variants.descriptor('B_zero_cost_head'),candidate_dip_guard=extra.guard_descriptor(),
        reference_release_schedule=schedule,policy_scope='Selected4 NN from first tick; N injected only by separate noNN reference evaluator',
        result_scope='Conditional fixed-guitar3note F4/staged finite wrist/currentgoalDIP/Bcost0; no free-guitar/J33/naturalness inheritance')
    from guitar_learning.tests.test_gpu_environment import fixture
    metadata,_=fixture(128);metadata['action_contract']=grid.read(B.output('evaluate',update=300)/'training_contract.json')['action']['target_contract']
    env=extra.PrefixLearningEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    checks=module('prefix_learning_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__],config,metadata,env)
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    for n,v in (('settings.json',config),('expected_environment.json',env.contract),('source_task.json',dict(targets=[asdict(t) for t in env.task.targets])),
        ('commands.json',commands()),('effort_declaration128.json',grid.read(B.BASE/'cpu_inputs/effort_declaration128.json'))):grid.write(inputs/n,v)
    grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json'));paths.update((HERE/'learning.py',HERE/'cpu_checks.py',HERE/'README.md',HERE/'cpu_verification.json',base.HERE/'probe.py'))
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths)))
    value=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(value.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),precheck_scenes=3,train_started=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','gate-check','dry-plan'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--execute',choices=('precheck','train','evaluate'));p.add_argument('--control',choices=CONTROLS);p.add_argument('--update',type=int,choices=UPDATES,default=0)
    a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.execute,a.control,a.update)
    else:
        assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending native admitted')
        else:gate()
        try:gate('train',require_review=False)
        except (FileNotFoundError,AssertionError):pass
        else:raise AssertionError('Train admitted before own128 precheck actual PASS')
        assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'));print(json.dumps(dict(stdlib_only=True,train_blocked_before_precheck=True,GPU_executed=False)))
