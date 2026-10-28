"""One reference collection, fixed supervised initialization, strict NN-only evaluation."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def module(name,path):
    if name not in sys.modules:
        s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v)
    return sys.modules[name]
parent=module('imitation_original_prefix',HERE.parent/'low_effort_index_prefix_learning_v1/probe.py')
grid,cap=parent.grid,parent.cap
SCHEMA='diagnostic.index_prefix_imitation_initialization.v1'
STAGES=('collect','fit','evaluate')
PHASES=('A_approach','A_hold','release','move','close','B_hold')


def descriptor():
    return dict(schema=SCHEMA,seed=7,steps=1000,batch_size=192,per_phase=32,learning_rate=3e-4,gradient_norm=.5,
        loss='mean square of original tanh(mean) selected4 minus requested reference action; no atanh/clipping',
        train_envs=[0,1,2],heldout_envs=[3],phases=list(PHASES),
        trainable_prefixes=['finger_encoder.','finger_heads.index.'],
        unchanged='original PrefixPolicy architecture/environment/currentgoal guard/std/reward; other parameter values exact',
        checkpoint='new initialization metadata schema; new original PPO optimizers empty/updates0; no supervised optimizer inheritance',
        scope='same-scene heldout observation check, not independent seeds/generalization/RL-only/free guitar')


def phase(endpoint_s,short):
    import bisect
    bounds=[short['teacher']['ramp_s'],*module('imitation_phase_schedule',parent.release.HERE/'schedule.py').boundaries(short['view'])]
    return bisect.bisect_right(bounds,endpoint_s)


def output(stage):return HERE/'runs'/stage
def support():return module('prefix_imitation_runtime',HERE/'imitation.py')


def evidence():
    _,paths=parent.gate('evaluate')
    paths.update(parent.base.reviewed(HERE.parent/'index_acquired_contact_guard_v1/analysis/results_v1/review.json'))
    p=grid.DIAG/'04_ablation/prefix_release_objective_v1/review.json';review=grid.read(p)
    assert grid.sha(p)=='d1f3c8395eddc1eb8b0b5a7c0c18741670d9b9d66038c4dc310ea3b540dbbe05'
    assert review['verdict']=='PASS' and not review['findings'];paths.add(p)
    historical_docs={grid.DIAG/'README.md',grid.DIAG/'status.json',grid.ROOT/'docs/plans/guitar_learning_failure_diagnosis_20261027.md'}
    audit=p.parent;actual_audit={audit/n for n in ('audit.py','results.json','README.md','PLAN.md')}
    assert set(map(Path,review['reviewed_sha256']))==historical_docs|actual_audit
    # Exactly these three mutable progress documents are historical review scope, not execution inputs.
    mappings=({name:h for name,h in review['reviewed_sha256'].items() if Path(name) not in historical_docs},
        review['evidence_sha256'],grid.read(audit/'results.json')['input_sha256'])
    assert len(mappings[-1])==19
    for mapping in mappings:
        assert all(grid.sha(name)==h for name,h in mapping.items());paths.update(map(Path,mapping))
    assert not paths&historical_docs
    return paths|{Path(__file__).resolve(),HERE/'PLAN.md',HERE/'imitation.py',HERE/'cpu_checks.py',HERE/'README.md',parent.checkpoint(0)}


def gate(stage='collect',require_review=True):
    assert stage in STAGES
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        review=grid.read(HERE/'review.json')
        assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in review['reviewed_sha256'].items())
    paths|={HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}
    if stage!='collect':
        folder=output('collect');report=grid.read(folder/'imitation_report.json')
        assert report['completed'] and report['stage']=='collect' and all(report['checks'].values())
        assert grid.read(folder/'prefix_acceptance.json')==parent.acceptance(grid.read(folder/'evaluation.json')['episodes'])
        assert grid.read(folder/'prefix_acceptance.json')['stage_ready']
        for p,h in grid.read(folder/'diagnostic_inputs_after.json')['input_pins'].items():assert grid.sha(p)==h
        assert grid.sha(folder/'observations4.npz')==report['dataset_sha256']
        paths.update(folder/n for n in ('imitation_report.json','prefix_acceptance.json','evaluation.json','observations4.npz','training_contract.json','diagnostic_inputs_after.json'))
    if stage=='evaluate':
        folder=output('fit');report=grid.read(folder/'imitation_report.json')
        assert report['completed'] and all(report['checks'].values()) and report['procedure']==descriptor()
        assert grid.sha(folder/'initial.pt')==report['checkpoint_sha256']
        for p,h in grid.read(folder/'inputs_after.json')['input_pins'].items():assert grid.sha(p)==h
        paths.update(folder/n for n in ('imitation_report.json','initial.pt','inputs_after.json','offline_errors.json'))
    return seal,paths


@contextmanager
def execution_scope(stage,seal,paths,observed):
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    old=(parent.base.output,parent.base.checkpoint)
    try:
        with parent.execution_scope('precheck' if stage=='collect' else 'evaluate',seal,paths,observed):
            original=parent.base.effort_scope
            @contextmanager
            def scope(evidence,state):
                with original(evidence,state) as current:
                    with support().observer_scope(sys.modules[__name__],current,stage,observed):yield current
            parent.base.output=lambda *args,**kwargs:output(stage)
            parent.base.checkpoint=lambda update:output('fit')/'initial.pt'
            parent.base.effort_scope=scope
            try:yield
            finally:parent.base.effort_scope=original
    finally:parent.base.output,parent.base.checkpoint=old


def launch(stage):
    out=output(stage);cap.reject_existing(out);seal,paths=gate(stage)
    if stage=='fit':
        return support().fit(sys.modules[__name__],paths)
    observed={};failure=None;completed=False
    # Direct aliases must restore even when the original evaluator or constructor fails.
    old=(parent.base.output,parent.base.checkpoint)
    try:
        import isaacgym  # stdlib source/review and existing-output gates precede native import.
        with execution_scope(stage,seal,paths,observed):
            parent.base.launch('precheck' if stage=='collect' else 'evaluate','reference' if stage=='collect' else None,0)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        parent.base.output,parent.base.checkpoint=old
        if out.is_dir():
            try:
                state=observed.get('state',{});cap.owned(out,state['identity'])
                support().finish(sys.modules[__name__],stage,out,observed,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary imitation cleanup error: '+repr(error),file=sys.stderr)


def commands():
    p=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']
    return {s:p+[s] for s in STAGES}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('prefix_imitation_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__])
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    for n,v in (('settings.json',parent.settings()),('procedure.json',descriptor()),('commands.json',commands())):grid.write(inputs/n,v)
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
    for n in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=STAGES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(module('prefix_imitation_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.execute)
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));gate(require_review=False)
        for stage in STAGES:
            try:gate(stage)
            except (AssertionError,FileNotFoundError):pass
            else:assert grid.read(HERE/'preparation_seal.json')['independent_review']=='passed_no_findings' and stage=='collect'
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        print(json.dumps(dict(stdlib_only=True,checkpoint_deserialized=False,GPU_executed=False)))
