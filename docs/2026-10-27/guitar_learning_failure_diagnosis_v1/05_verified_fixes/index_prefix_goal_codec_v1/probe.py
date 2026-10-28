"""Root-only goal-codec reference128, gated fresh1000 fit, NN-only128 evaluation."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent

def module(name,path):
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return sys.modules[name]
source=module('goal_codec_original_recovery',HERE.parent/'index_prefix_imitation_warmstart_v1/recovery_v1/probe.py')
parent=source.source.parent;grid,cap=source.grid,source.cap
SCHEMA='diagnostic.index_prefix_goal_initialization.v1'
STAGES=('reference','fit','evaluate')
phase=source.source.phase

def output(stage):
    assert stage in STAGES
    return HERE/'runs'/stage

def support():return module('index_prefix_goal_codec_adapter',HERE/'codec.py')

def descriptor():
    return dict(schema=SCHEMA,seed=7,steps=1000,batch_size=192,per_phase=32,learning_rate=3e-4,gradient_norm=.5,
        loss='MSE tanh(mean) selected4 against full-native normalized planned desired(t+1/60)',train_envs=[0,1,2],heldout_envs=[3],
        label_source='original completed reference observations, planned schedule before inverse codec; not saturated requests or failed corrective models',
        initialization='new original fresh73 values; changed goal policy/control identity; no old identity strict-load bypass',PPO_updates=0,
        scope='deterministic same-scene goal-output diagnosis; no equivalent physical std/PPO/generalization/pressure/naturalness claim')

def evidence():
    _,paths=source.gate('fit')
    paths.update(parent.base.reviewed(source.HERE/'analysis/results_v1/review.json'))
    paths.update(parent.base.reviewed(HERE.parent/'index_prefix_corrective_imitation_v1/analysis/results_v1/review.json'))
    return paths|{Path(__file__).resolve(),HERE/'codec.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',parent.checkpoint(0)}

def gate(stage='reference',require_review=True):
    assert stage in STAGES
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    paths|={HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}
    if stage!='reference':
        folder=output('reference');r=grid.read(folder/'goal_codec_report.json');assert r['completed'] and r['stage']=='reference' and all(r['checks'].values()) and r['NN_constructors']==0
        native=grid.read(folder/'diagnostic_report.json');assert native['completed'] and native['scene_valid'] and native['closed'] and not native['failure']
        acceptance=parent.acceptance(grid.read(folder/'evaluation.json')['episodes']);assert acceptance==grid.read(folder/'prefix_acceptance.json') and acceptance['stage_ready']
        audit=HERE/'reference_analysis/results_v1';paths.update(parent.base.reviewed(audit/'review.json'))
        assert grid.read(audit/'acceptance.json')==acceptance
        after=grid.read(folder/'diagnostic_inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(grid.sha(p)==h for p,h in after['input_pins'].items());paths.update(map(Path,after['input_pins']))
        paths.update(folder/n for n in ('goal_codec_report.json','diagnostic_report.json','prefix_acceptance.json','evaluation.json','training_contract.json','observations4.npz','goal_codec_env0.npz','current_goal_DIP60.npz','diagnostic_inputs_after.json'))
    if stage=='evaluate':
        folder=output('fit');r=grid.read(folder/'goal_codec_report.json');assert r['completed'] and r['stage']=='fit' and all(r['checks'].values()) and r['procedure']==descriptor()
        assert grid.sha(folder/'initial.pt')==r['checkpoint_sha256']
        after=grid.read(folder/'inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(grid.sha(p)==h for p,h in after['input_pins'].items());paths.update(map(Path,after['input_pins']))
        paths.update(folder/n for n in ('goal_codec_report.json','initial.pt','inputs_after.json','offline_errors.json','parameter_invariants.json'))
    return seal,paths

def launch(stage):
    out=output(stage);cap.reject_existing(out);seal,paths=gate(stage)
    if stage=='fit':return support().fit(sys.modules[__name__],paths)
    observed={};completed=False;failure=None
    try:
        import isaacgym  # Output/source/review/actual gates precede all numerical/native imports.
        with support().execution_scope(sys.modules[__name__],stage,seal,paths,observed):
            parent.base.launch('precheck' if stage=='reference' else 'evaluate','reference' if stage=='reference' else None,0)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if out.is_dir():
            try:support().finish(sys.modules[__name__],stage,out,observed,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary goal adapter report error: '+repr(error),file=sys.stderr)

def commands():return {stage:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',stage] for stage in STAGES}

def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('index_prefix_goal_cpu',HERE/'cpu_checks.py').check(sys.modules[__name__])
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('commands.json',commands()),('settings.json',parent.settings()),('procedure.json',descriptor()),('policy_output_adapter.json',support().ADAPTER)):
        grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks);paths.update(inputs.glob('*.json'));paths.add(HERE/'cpu_verification.json')
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--execute',choices=STAGES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(module('index_prefix_goal_cpu',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.execute)
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending producer admitted')
        else:gate()
        for stage in ('fit','evaluate'):
            try:gate(stage)
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Premature fit/evaluation admitted')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,fit_blocked_before_reference=True,evaluate_blocked_before_fit=True)))
