"""Same fresh1000 goal initialization, only decoded-angle rad^2 loss changed."""
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
source=module('angle_loss_original_goal',HERE.parent/'index_prefix_goal_codec_v1/probe.py')
parent=source.parent;grid,cap=source.grid,source.cap
SCHEMA='diagnostic.index_prefix_goal_angle_loss_initialization.v1'
ACTUAL=source.HERE/'analysis/results_recovery_v1/review.json'
ACTUAL_SHA='9070c12f160a63a666a6373801ee7573aaa4026f34215772e3edde693244488f'

def support():return module('angle_loss_fit',HERE/'fit.py')
def output(stage):
    assert stage in ('fit','evaluate')
    return HERE/'runs'/stage
def descriptor():
    return dict(source.descriptor(),schema=SCHEMA,loss='mean((original_decode(tanh(mean_selected4))-original_planned_desired_selected4_rad)^2)',
        comparison='only loss units changed; original fresh73; no70e40d transfer/additional steps',
        unchanged='GoalPolicy/environment/codec/105/.25Nm/90pairs/currentgoalguard/9RLrewards/std/clock/1000x192/6phase/seed7/split')


def evidence():
    _,paths=source.gate('fit')  # Original2023/reference128/readiness/strict inputs unchanged.
    assert grid.sha(ACTUAL)==ACTUAL_SHA
    paths.update(parent.base.reviewed(ACTUAL))
    return paths|{ACTUAL,Path(__file__).resolve(),HERE/'fit.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md'}


def fitted(report,path):
    assert Path(path)==output('fit')/'initial.pt' and report['completed'] and report['failure'] is None and all(report['checks'].values())
    assert report['procedure']==descriptor() and report['checkpoint_sha256']==grid.sha(path)


def check_metadata(metadata):
    assert metadata['schema']==SCHEMA and metadata['actual_initialization']==descriptor()
    assert metadata['settings']==parent.settings() and metadata['policy_output_adapter']==source.support().ADAPTER
    assert metadata['settings_scope']=='source environment configuration; new decoded-angle supervised loss declared separately'


def gate(stage='fit',require_review=True):
    assert stage in ('fit','evaluate');paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        review=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in review['reviewed_sha256'].items())
    paths|={HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}
    if stage=='evaluate':
        folder=output('fit');fitted(grid.read(folder/'angle_loss_fit_report.json'),folder/'initial.pt')
        after=grid.read(folder/'inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(grid.sha(p)==h for p,h in after['input_pins'].items());paths.update(folder/n for n in ('initial.pt','angle_loss_fit_report.json','inputs_after.json','offline_errors.json','parameter_invariants.json'))
    return seal,paths


@contextmanager
def evaluation_scope(seal,paths):
    from guitar_learning.tool.experiments.short_finger_learning import runner
    old=(source.gate,source.output,source.SCHEMA,runner.DecisionPPOTrainer)
    class Trainer(old[3]):
        def load(self,path):
            assert Path(path)==output('fit')/'initial.pt'
            metadata=super().load(path);check_metadata(metadata);return metadata
    source.gate=lambda stage:(seal,paths);source.output=lambda stage:output(stage);source.SCHEMA=SCHEMA;runner.DecisionPPOTrainer=Trainer
    try:yield
    finally:source.gate,source.output,source.SCHEMA,runner.DecisionPPOTrainer=old


def launch(stage):
    out=output(stage);cap.reject_existing(out);seal,paths=gate(stage)
    if stage=='fit':return support().fit(sys.modules[__name__],paths)
    failure=None;completed=False;old=(source.gate,source.output,source.SCHEMA)
    try:
        import isaacgym  # Full original and own stdlib gates precede native/Torch.
        with evaluation_scope(seal,paths):source.launch('evaluate')
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        try:
            if out.is_dir():
                identity=(out.stat().st_dev,out.stat().st_ino);cap.owned(out,identity)
                original=grid.read(out/'goal_codec_report.json');checks=dict(original_evaluator_completed=original['completed'],aliases_restored=(source.gate,source.output,source.SCHEMA)==old,
                    checkpoint_unchanged=grid.sha(output('fit')/'initial.pt')==grid.read(output('fit')/'angle_loss_fit_report.json')['checkpoint_sha256'])
                grid.write(out/'angle_loss_execution.json',dict(completed=completed and all(checks.values()),failure=failure,checks=checks,procedure=descriptor(),scope='Original GoalPool/guard/evaluator; no reference or N injection; loss-only initialization'))
                if failure is None and not all(checks.values()):raise RuntimeError('Angle-loss execution audit failed')
        except BaseException as error:
            if failure is None:raise
            print('Secondary angle-loss evaluation audit error: '+repr(error),file=sys.stderr)


def commands():return {s:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',s] for s in ('fit','evaluate')}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    inputs=HERE/'cpu_inputs';inputs.mkdir();checks=module('angle_loss_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]);grid.write(HERE/'cpu_verification.json',checks)
    grid.write(inputs/'settings.json',parent.settings());grid.write(inputs/'procedure.json',descriptor());grid.write(inputs/'commands.json',commands())
    paths.update(inputs.iterdir());paths.add(HERE/'cpu_verification.json')
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    process=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(process.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=('fit','evaluate'));a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.execute)
    else:
        assert not (HERE/'runs').exists() and not any(n in sys.modules for n in ('torch','numpy','isaacgym'));s,_=gate(require_review=False)
        if s['independent_review']=='pending':
            try:gate()
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('Unreviewed execution admitted')
        else:gate()
        try:gate('evaluate')
        except (AssertionError,FileNotFoundError):pass
        else:raise AssertionError('Evaluation admitted before own fit')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,reference_reused=True)))
