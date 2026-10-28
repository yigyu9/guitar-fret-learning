"""Thin native video adapter for truthful supervised initialization metadata/PPO0."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
def module(name,path):
    if name not in sys.modules:
        s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v)
    return sys.modules[name]
recovery=module('warmstart_video_recovery',HERE.parent/'probe.py')
parent=recovery.source.parent;grid,cap=recovery.grid,recovery.cap
HELPER=parent.HERE/'native_video_v1/render.py'
CHECKPOINT=recovery.output('fit')/'initial.pt'
SHA='162c617a28e548757bea8b0721c13c740d452fc430ae1601f01ed8411e2e480a'
OUT=HERE/'runs/initial'
VIDEO_SCHEMA='diagnostic.index_prefix_imitation_video.recovery.v1'


def header(payload,update,settings,schema):
    m=payload.get('metadata',{})
    if (update!=0 or payload.get('updates')!=0 or m.get('schema')!=recovery.SCHEMA or m.get('settings')!=settings or not m.get('input_pins') or
        settings['num_envs']!=128 or settings['song']['short_learning']['schema']!=schema or m.get('actual_initialization')!=recovery.descriptor() or
        m.get('collection_sha256')!=recovery.DATA_SHA or m.get('original_initial_sha256')!=grid.sha(parent.checkpoint(0))):
        raise ValueError('Original recovery initialization/PPO0/source/schema128 required')
    return m  # Original payload and policy/environment contract are never rewritten.


def evidence():
    for name,stage in (('02_launcher.json','fit'),('03_launcher.json','evaluate')):
        value=grid.read(recovery.HERE/name);assert value['completed'] and value['returncode']==0 and value['stage']==stage
    _,paths=recovery.gate('evaluate')
    report=grid.read(recovery.output('evaluate')/'imitation_report.json')
    assert report['completed'] and all(report['checks'].values()) and report['reference_calls']==0 and report['reference_N_injected'] is False
    assert grid.sha(CHECKPOINT)==SHA
    paths.update(parent.base.reviewed(recovery.HERE/'analysis/results_v1/review.json'))
    return paths|{HELPER,recovery.HERE/'02_launcher.json',recovery.HERE/'03_launcher.json',recovery.output('evaluate')/'imitation_report.json'}


def gate(require_review=True):
    cap.reject_existing(OUT);paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items()) and seal['input_pins'][str(CHECKPOINT)]==SHA
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


@contextmanager
def adapter(helper,state):
    old=(helper.producer,helper.header,helper.grid)
    extra=parent.support();reference=extra.reference_action
    def forbidden(*args,**kwargs):
        state['reference_calls']+=1;raise RuntimeError('No reference/N allowed in warmstart NN video')
    def write(path,value):
        if Path(path) in (OUT/'capture_metadata.json',OUT/'report.json'):
            value=dict(value,schema=VIDEO_SCHEMA,checkpoint_metadata_schema=recovery.SCHEMA,actual_initialization=recovery.descriptor(),
                supervised_steps=1000,PPO_updates=0,selection='one predeclared supervised initialization, not best/latest or RL checkpoint',
                initialization_scope='Original configuration initialization text is source provenance; checkpoint actual_initialization is supervised recovery',
                policy_performance_scope='conditional fixed-guitar/F4/finite stagedwrist/NN-only supervised warmstart; not RL-only/fullJ33/naturalness/pressure')
            state['metadata_outputs'].append(Path(path).name)
        grid.write(path,value)
    helper.producer=parent;helper.header=header;helper.grid=SimpleNamespace(sha=grid.sha,write=write);extra.reference_action=forbidden
    try:yield
    finally:
        helper.producer,helper.header,helper.grid=old;extra.reference_action=reference
        state['aliases_restored']=(helper.producer,helper.header,helper.grid)==old and extra.reference_action is reference


def execute():
    seal,paths=gate()
    import isaacgym  # Original native import order: gates, Isaac, then policy/Torch.
    helper=module('warmstart_native_prefix_renderer',HELPER)
    state=dict(reference_calls=0,metadata_outputs=[],aliases_restored=False);failure=None;completed=False
    try:
        with adapter(helper,state):helper.render_native(CHECKPOINT,OUT,0,seal,paths)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if OUT.is_dir():
            try:
                checks=dict(aliases_restored=state['aliases_restored'],reference_calls_zero=state['reference_calls']==0,checkpoint_unchanged=grid.sha(CHECKPOINT)==SHA,
                    actual_metadata_recorded=set(state['metadata_outputs'])=={'capture_metadata.json','report.json'})
                grid.write(OUT/'initialization_video_report.json',dict(completed=completed and all(checks.values()),failure=failure,checks=checks,reference_calls=state['reference_calls'],
                    checkpoint=str(CHECKPOINT),checkpoint_sha256=SHA,checkpoint_metadata_schema=recovery.SCHEMA,PPO_updates=0,supervised_steps=1000,
                    evaluator_fingerprint_callback_used=False,scope='Renderer original strict full load/identity; no evaluator fingerprint observer used'))
                if failure is None and not all(checks.values()):raise RuntimeError('Warmstart video adapter audit failed')
            except BaseException as error:
                if failure is None:raise
                print('Secondary video adapter error: '+repr(error),file=sys.stderr)


def commands():return dict(render=[[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']],checkpoint=str(CHECKPOINT),PPO_updates=0,supervised_steps=1000)


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('warmstart_video_CPU_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]);inputs=HERE/'cpu_inputs';inputs.mkdir()
    grid.write(inputs/'commands.json',commands());grid.write(inputs/'settings.json',parent.settings());grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json'));paths|={Path(__file__).resolve(),HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification.json',CHECKPOINT,
        HELPER.parent/'qa/results_v1/review.json',HELPER.parent/'qa/results_v1/verification.json'}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    value=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(value.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),command=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('self-test','prepare','gate-check','dry-plan','execute'):g.add_argument('--'+n,action='store_true')
    a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.self_test:print(json.dumps(module('warmstart_video_CPU_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.prepare:prepare()
    elif a.execute:execute()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        try:gate()
        except (AssertionError,FileNotFoundError):assert seal['independent_review']=='pending'
        else:assert seal['independent_review']=='passed_no_findings'
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,PPO_updates=0)))
