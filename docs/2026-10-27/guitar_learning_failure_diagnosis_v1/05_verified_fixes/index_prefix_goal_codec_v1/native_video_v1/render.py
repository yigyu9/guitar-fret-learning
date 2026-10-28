"""Native goal-policy video adapter; original renderer/GoalPool/strict loader unchanged."""
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
        spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return sys.modules[name]
recovery=module('goal_video_recovery',HERE.parent/'recovery_v1/probe.py');source=recovery.source
parent=source.parent;grid,cap=recovery.grid,recovery.cap
CHECKPOINT=recovery.CHECKPOINT;SHA=recovery.MODEL_SHA
HELPER=parent.HERE/'native_video_v1/render.py'
OUT=HERE/'runs/initial'
VIDEO_SCHEMA='diagnostic.index_prefix_goal_video.v1'
ACTUAL_REVIEW=source.HERE/'analysis/results_recovery_v1/review.json'


def header(payload,update,settings,schema):
    metadata=payload.get('metadata',{});codec=source.support()
    contract=payload.get('identity',{}).get('architecture',{}).get('contract',{})
    if (update!=0 or payload.get('updates')!=0 or metadata.get('schema')!=source.SCHEMA or metadata.get('settings')!=settings or not metadata.get('input_pins') or
        settings['num_envs']!=128 or settings['song']['short_learning']['schema']!=schema or metadata.get('actual_initialization')!=source.descriptor() or
        metadata.get('policy_output_adapter')!=codec.ADAPTER or payload['identity']['architecture'].get('schema')!='diagnostic.index_prefix_goal_policy.v1' or
        contract.get('action',{}).get('policy_output_adapter')!=codec.ADAPTER or contract.get('task',{}).get('short_learning',{}).get('policy_output_adapter')!=codec.ADAPTER or
        metadata.get('collection_sha256')!=source.source.DATA_SHA or metadata.get('original_initial_sha256')!=grid.sha(parent.checkpoint(0))):
        raise ValueError('Original goal schema/layered identity/PPO0/supervised1000 required')
    return metadata


def evidence():
    _,paths=recovery.gate()
    value=grid.read(recovery.HERE/'01_launcher.json');assert value['completed'] and value['returncode']==0 and len(value['children'])==1 and value['children'][0]['job']=='evaluate' and value['children'][0]['returncode']==0
    assert value['children'][0]['argv']==recovery.commands()['evaluate']
    report=grid.read(recovery.output('evaluate')/'fit_recovery_report.json');assert report['completed'] and all(report['checks'].values()) and report['metadata_rewritten'] is False
    assert report['original_parent_completed'] is False and report['original_returncode']==1 and report['checkpoint_sha256']==grid.sha(CHECKPOINT)==SHA
    paths.update(parent.base.reviewed(ACTUAL_REVIEW))
    return paths|{CHECKPOINT,HELPER,recovery.HERE/'01_launcher.json',recovery.output('evaluate')/'fit_recovery_report.json'}


def gate(require_review=True):
    cap.reject_existing(OUT);paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items()) and seal['input_pins'][str(CHECKPOINT)]==SHA
    if require_review:
        review=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and review['verdict']=='PASS' and not review['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in review['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


@contextmanager
def adapter(helper,state):
    codec=source.support();old=(helper.producer,helper.header,helper.grid,codec.convert)
    def convert(pool,raw):
        state['conversion_calls']+=1
        return old[3](pool,raw)
    @contextmanager
    def execution(phase,seal,paths,observed):
        if phase!='evaluate':raise ValueError('Goal video evaluate scope only')
        state['observed']=observed
        with codec.execution_scope(source,'evaluate',seal,paths,observed):yield
    def write(path,value):
        tagged=Path(path) in (OUT/'capture_metadata.json',OUT/'report.json')
        if tagged:
            value=dict(value,schema=VIDEO_SCHEMA,checkpoint_metadata_schema=source.SCHEMA,actual_initialization=source.descriptor(),policy_output_adapter=codec.ADAPTER,
                PPO_updates=0,supervised_steps=1000,selection='predeclared env0 first attempt; one goal initialization, not selected successful environment',
                original_fit_returncode=1,recovery_record=str(recovery.HERE/'fit_recovery.json'),goal_conversion_calls=state['conversion_calls'],
                action_scope='original pose policy_action/executed_action are physical requests; goal_codec_env0 holds raw normalized goal and decoded absolute goal',
                policy_performance_scope='fixed-guitar/F4/finite stagedwrist/NN goal initialization; not RL-only/fullJ33/naturalness/pressure')
        grid.write(path,value)
        if tagged:state['metadata_outputs'].append(Path(path).name)
    helper.producer=SimpleNamespace(support=parent.support,settings=parent.settings,execution_scope=execution,base=parent.base)
    helper.header=header;helper.grid=SimpleNamespace(sha=grid.sha,write=write);codec.convert=convert
    try:yield
    finally:
        helper.producer,helper.header,helper.grid,codec.convert=old
        state['aliases_restored']=(helper.producer,helper.header,helper.grid,codec.convert)==old


def save_goals(state):
    rows=state.get('observed',{}).get('records',[])
    if not rows:return False
    import numpy as np
    with (OUT/'observations4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
    env0=[r for r in rows if r['env_id']==0]
    keys=('start_clock','clock','raw_goal_normalized','decoded_goal_rad','requested_NN_action','old_target_rad','final_target_rad','raw_DIP_target_rad','final_DIP_target_rad','current_goal')
    with (OUT/'goal_codec_env0.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in env0]) for k in keys})
    return bool(env0)


def execute():
    seal,paths=gate()
    import isaacgym  # All stdlib gates before native or policy/Torch import.
    helper=module('goal_original_native_renderer',HELPER)
    state=dict(conversion_calls=0,metadata_outputs=[],aliases_restored=False);completed=False;failure=None;secondary=None;saved=False
    try:
        with adapter(helper,state):helper.render_native(CHECKPOINT,OUT,0,seal,paths)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if OUT.is_dir():
            try:saved=save_goals(state)
            except BaseException as error:secondary=error
            try:
                report=grid.read(OUT/'report.json') if (OUT/'report.json').is_file() else {};observed=state.get('observed',{})
                steps=(report.get('episode_summary') or {}).get('steps')
                checks=dict(aliases_restored=state['aliases_restored'],goal_aliases_restored=observed.get('goal_aliases_restored',False),
                    reference_calls_zero=observed.get('reference_calls')==0,checkpoint_unchanged=grid.sha(CHECKPOINT)==SHA,
                    metadata_recorded=set(state['metadata_outputs'])=={'capture_metadata.json','report.json'},goal_conversion_once=state['conversion_calls']==steps,
                    typed_goal_records_saved=saved,original_renderer_completed=report.get('completed') is True,no_secondary_error=secondary is None)
                grid.write(OUT/'goal_video_report.json',dict(schema=VIDEO_SCHEMA,completed=completed and all(checks.values()),failure=failure,
                    secondary_failure=dict(type=type(secondary).__name__,message=str(secondary)) if secondary else None,checks=checks,conversion_calls=state['conversion_calls'],
                    reference_calls=observed.get('reference_calls'),checkpoint_sha256=SHA,PPO_updates=0,supervised_steps=1000,evaluator_fingerprint_callback_used=False,
                    scope='Original GoalPool step conversion once; original renderer full strict load/model/scene audit; evaluator callback unused; original fit exit1 retained'))
                if failure is None:
                    if secondary is not None:raise secondary
                    if not all(checks.values()):raise RuntimeError('Goal video scope/counter/metadata audit failed')
            except BaseException as error:
                if failure is None:
                    if secondary is not None and error is not secondary:
                        print('Secondary goal video audit error: '+repr(error),file=sys.stderr)
                        raise secondary from None
                    raise
                print('Secondary goal video error: '+repr(error),file=sys.stderr)
                if secondary is not None and error is not secondary:print('Secondary typed goal raw error: '+repr(secondary),file=sys.stderr)


def commands():return dict(render=[[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']],checkpoint=str(CHECKPOINT),PPO_updates=0,supervised_steps=1000)


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('goal_native_video_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]);inputs=HERE/'cpu_inputs';inputs.mkdir()
    grid.write(inputs/'commands.json',commands());grid.write(inputs/'settings.json',parent.settings());grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json'));paths|={Path(__file__).resolve(),HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification.json',HELPER.parent/'qa/results_v1/review.json',HELPER.parent/'qa/results_v1/verification.json'}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('self-test','prepare','gate-check','dry-plan','execute'):g.add_argument('--'+n,action='store_true')
    a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.self_test:print(json.dumps(module('goal_native_video_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.prepare:prepare()
    elif a.execute:execute()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending video admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,PPO_updates=0)))
