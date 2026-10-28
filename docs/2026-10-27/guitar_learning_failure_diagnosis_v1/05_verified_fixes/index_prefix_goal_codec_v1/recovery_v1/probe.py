"""Evaluate-only explicit recovery of one saved goal model after one post-fit audit defect."""
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
        spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return sys.modules[name]
source=module('goal_fit_recovery_original',HERE.parent/'probe.py');grid,cap=source.grid,source.cap
CHECKPOINT=source.output('fit')/'initial.pt'
MODEL_SHA='70e40d1cb80a90a2636fd7d1babb4870bd82333d900c667fa136bac233ef9327'
SOURCE_SEAL='c255ad4f565ef70efe0e776d4a6e6530797d0ca5c6f8f8459a6b70933af35a14'
CODE_SHA='b007618dc5428e40f1e2fcff73d78affa470acf49d46f44702ca0097b012d532'
SCHEMA='diagnostic.index_prefix_goal_fit_recovery.v1'


def output(stage):
    assert stage in source.STAGES
    return HERE/'runs/evaluate' if stage=='evaluate' else source.HERE/'runs'/stage


def single_defect(parent,log,names):
    assert parent['completed'] is False and parent['returncode']==1 and len(parent['children'])==1
    child=parent['children'][0];assert child['job']=='fit' and child['returncode']==1 and child['argv']==source.commands()['fit']
    assert child['wall_s']>0 and parent['wall_s']>=child['wall_s']
    assert log.count('Traceback (most recent call last):')==1 and log.rstrip().endswith("NameError: name 'sys' is not defined")
    assert 'codec.py", line 221, in fit' in log and 'During handling' not in log
    assert 'runner.project_source_paths(list(sys.modules.items()))' in log
    assert sorted(names)==sorted(('settings.json','inputs_before.json','offline_errors.json','parameter_invariants.json','initial.pt'))


def evidence():
    assert grid.sha(source.HERE/'preparation_seal.json')==SOURCE_SEAL and grid.sha(source.HERE/'codec.py')==CODE_SHA
    _,paths=source.gate('fit')  # Keep original own2023 + actual reference128/review/readiness gate intact.
    parent=grid.read(source.HERE/'02_launcher.json');log=(source.HERE/'02_fit.log').read_text()
    single_defect(parent,log,[p.name for p in source.output('fit').iterdir()])
    assert grid.sha(CHECKPOINT)==MODEL_SHA
    paths.update(source.output('fit')/n for n in ('settings.json','inputs_before.json','offline_errors.json','parameter_invariants.json','initial.pt'))
    paths|={source.HERE/'02_launcher.json',source.HERE/'02_fit.log',Path(__file__).resolve(),HERE/'audit.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md'}
    return paths


def gate(require_review=True):
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    audit=grid.read(HERE/'fit_recovery.json');assert audit['accepted_for_evaluate_only'] and audit['original_parent_completed'] is False and audit['original_returncode']==1
    assert audit['checkpoint_sha256']==MODEL_SHA and audit['unchanged_original_missing_reports']==['inputs_after.json','goal_codec_report.json']
    assert audit['original_checkpoint_schema']==source.SCHEMA and audit['PPO_updates']==0 and audit['supervised_steps']==1000
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


@contextmanager
def scope(seal,paths):
    old=(source.gate,source.output)
    def evaluate_only(stage):
        if stage!='evaluate':raise ValueError('Recovery permits evaluate only; no refit/reference')
        return seal,paths
    source.gate=evaluate_only;source.output=output
    try:yield
    finally:source.gate,source.output=old


def launch():
    out=output('evaluate');cap.reject_existing(out);seal,paths=gate();completed=False;failure=None;old=(source.gate,source.output)
    try:
        with scope(seal,paths):source.launch('evaluate')  # Original metadata/GoalPolicy/original full trainer.load, no model rewrite.
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if out.is_dir():
            try:
                restored=(source.gate,source.output)==old;original=grid.read(out/'goal_codec_report.json') if (out/'goal_codec_report.json').is_file() else {}
                checks=dict(aliases_restored=restored,original_evaluator_completed=original.get('completed') is True,checkpoint_unchanged=grid.sha(CHECKPOINT)==MODEL_SHA)
                grid.write(out/'fit_recovery_report.json',dict(schema=SCHEMA,completed=completed and all(checks.values()),failure=failure,checks=checks,
                    original_parent_completed=False,original_returncode=1,original_missing_reports_preserved=True,checkpoint=str(CHECKPOINT),checkpoint_sha256=MODEL_SHA,
                    original_checkpoint_schema=source.SCHEMA,metadata_rewritten=False,PPO_updates=0,supervised_steps=1000,
                    scope='Single known post-fit audit failure accepted explicitly; original failure retained; no refit or reference injection'))
                if failure is None and not all(checks.values()):raise RuntimeError('Recovery evaluator audit failed')
            except BaseException as error:
                if failure is None:raise
                print('Secondary recovery audit error: '+repr(error),file=sys.stderr)


def commands():return dict(evaluate=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute','evaluate'],checkpoint=str(CHECKPOINT),PPO_updates=0,supervised_steps=1000)


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    audit,checks=module('goal_postfit_recovery_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__])
    grid.write(HERE/'fit_recovery.json',audit);grid.write(HERE/'cpu_verification.json',checks)
    inputs=HERE/'cpu_inputs';inputs.mkdir();grid.write(inputs/'commands.json',commands());grid.write(inputs/'settings.json',source.parent.settings())
    paths|={HERE/'fit_recovery.json',HERE/'cpu_verification.json',*inputs.glob('*.json')}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(source.parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json');(HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=('evaluate',));a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(module('goal_postfit_recovery_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__])[1],indent=2))
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch()
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('Pending recovery admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,evaluate_only=True,original_failed_parent_preserved=True)))
