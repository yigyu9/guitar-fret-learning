"""Same-budget reference-only versus counterfactual-label supervised continuation."""
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
base=module('corrective_original_recovery',HERE.parent/'index_prefix_imitation_warmstart_v1/recovery_v1/probe.py')
source=base.source;grid,cap=base.grid,base.cap
CONDITIONS=('reference_only','corrective_mixed')
SCHEMA='diagnostic.index_prefix_corrective_initialization.v1'
START=base.output('fit')/'initial.pt'
START_SHA='162c617a28e548757bea8b0721c13c740d452fc430ae1601f01ed8411e2e480a'
ACTUAL=base.HERE/'analysis/results_v1/review.json'
ACTUAL_SHA='2c7445ce886db063a39d08e4fb88a0f4953af9e3a5df9dcebb616a6008c837c6'
PROCEDURE=source.descriptor()


def support():return module('corrective_original_fit_adapter',HERE/'fit.py')
def output(condition,stage):
    assert condition in CONDITIONS and stage in ('fit','evaluate')
    return HERE/'runs'/(condition+'_'+stage)


def descriptor(condition):
    assert condition in CONDITIONS
    return dict(PROCEDURE,schema=SCHEMA,condition=condition,additional_steps=1000,total_supervised_steps=2000,
        starting_checkpoint=str(START),starting_checkpoint_sha256=START_SHA,
        source_mix='16 native reference +16 native reference per phase' if condition==CONDITIONS[0] else '16 native reference +16 saved NN observation counterfactual request per phase',
        sampling='same seed7/6phases/two16-with-replacement draws; env0..2 only; env3 heldout same-scene',
        label_manifest_sha256=grid.sha(HERE/'cpu_inputs/label_manifest.json'),label_arrays_sha256=grid.sha(HERE/'cpu_inputs/labels.npz'),
        origin_scope='NN actual/requested/executed remains original; shadow reference request is computed offline and never certified as executed')


def evidence():
    _,paths=base.gate('evaluate');assert grid.sha(ACTUAL)==ACTUAL_SHA and grid.sha(START)==START_SHA
    paths.update(source.parent.base.reviewed(ACTUAL))
    return paths|{ACTUAL,START,Path(__file__).resolve(),HERE/'PLAN.md',HERE/'README.md',HERE/'fit.py',HERE/'cpu_checks.py'}


def fitted(condition,report,path):
    assert Path(path)==output(condition,'fit')/'initial.pt'
    assert report['completed'] and report['condition']==condition and report['procedure']==descriptor(condition)
    assert report['checkpoint_path']==str(path) and report['checkpoint_sha256']==grid.sha(path) and all(report['checks'].values())


def gate(condition,stage='fit',require_review=True):
    assert condition in CONDITIONS and stage in ('fit','evaluate');paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    paths|={HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}
    if stage=='evaluate':
        folder=output(condition,'fit');fitted(condition,grid.read(folder/'corrective_fit_report.json'),folder/'initial.pt')
        after=grid.read(folder/'inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(grid.sha(p)==h for p,h in after['input_pins'].items())
        paths.update(folder/n for n in ('corrective_fit_report.json','initial.pt','inputs_after.json','offline_errors.json'))
    return seal,paths


def check_metadata(value,condition):
    assert value['schema']==SCHEMA and value['actual_initialization']==descriptor(condition)
    assert value['settings']==source.parent.settings() and value['starting_checkpoint_sha256']==START_SHA
    assert value['settings_scope']=='Unchanged source configuration; actual_initialization declares additional supervised continuation'


@contextmanager
def evaluation_scope(condition,seal,paths):
    from guitar_learning.tool.experiments.short_finger_learning import runner
    old=(source.gate,source.output,source.SCHEMA,source.descriptor,runner.DecisionPPOTrainer)
    class Trainer(old[4]):
        def load(self,path):
            assert Path(path)==output(condition,'fit')/'initial.pt'
            value=super().load(path);check_metadata(value,condition);return value
    source.gate=lambda stage:(seal,paths);source.output=lambda stage:output(condition,stage)
    source.SCHEMA=SCHEMA;source.descriptor=lambda:descriptor(condition);runner.DecisionPPOTrainer=Trainer
    try:yield
    finally:source.gate,source.output,source.SCHEMA,source.descriptor,runner.DecisionPPOTrainer=old


def launch(condition,stage):
    out=output(condition,stage);cap.reject_existing(out);seal,paths=gate(condition,stage)
    if stage=='fit':return support().fit(sys.modules[__name__],condition,paths)
    failure=None
    try:
        import isaacgym  # Full stdlib gate precedes native/Torch imports.
        with evaluation_scope(condition,seal,paths):source.launch('evaluate')
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:print(json.dumps(dict(condition=condition,stage=stage,failure=failure,scope='NN-only original guard/evaluator; no reference injection')),flush=True)


def commands():
    prefix=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']
    return {c:{s:prefix+[s,'--condition',c] for s in ('fit','evaluate')} for c in CONDITIONS}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    inputs=HERE/'cpu_inputs';inputs.mkdir()
    support().make_labels(sys.modules[__name__],inputs)
    checks=module('corrective_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]);grid.write(HERE/'cpu_verification.json',checks)
    grid.write(inputs/'commands.json',commands());grid.write(inputs/'settings.json',source.parent.settings());grid.write(inputs/'procedures.json',[descriptor(c) for c in CONDITIONS])
    paths.update(inputs.iterdir());paths.add(HERE/'cpu_verification.json')
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(source.parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=('fit','evaluate'));p.add_argument('--condition',choices=CONDITIONS);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.condition,a.execute)
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        for c in CONDITIONS:
            s,_=gate(c,require_review=False)
            try:gate(c)
            except (AssertionError,FileNotFoundError):assert s['independent_review']=='pending'
            else:assert s['independent_review']=='passed_no_findings'
            try:gate(c,'evaluate')
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('NN admitted before matching fit')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,new_capture=False)))
