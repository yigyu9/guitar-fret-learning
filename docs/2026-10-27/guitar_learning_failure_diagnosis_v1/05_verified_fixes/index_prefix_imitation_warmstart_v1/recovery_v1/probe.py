"""Reuse one completed reference capture after one frozen reporting defect; no recapture CLI."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('imitation_recovery_original',HERE.parent/'probe.py')
source=importlib.util.module_from_spec(s);sys.modules[s.name]=source;s.loader.exec_module(source)
grid,cap=source.grid,source.cap
SCHEMA='diagnostic.index_prefix_imitation_initialization.recovery.v1'
DATA_SHA='00bfe7dc68acaddb9a783e55b36db1155249b0b63fa45daa19339185131f4954'
ORIGINAL_SEAL='9f1ba34da06db02883441485cae384cd3a53d383b8f4acf36c9c5e0ef20dfa86'
COLLECT=source.HERE/'runs/collect'
PROCEDURE=source.descriptor()


def output(stage):
    assert stage in ('collect','fit','evaluate')
    return COLLECT if stage=='collect' else HERE/'runs'/stage


def descriptor():
    return dict(PROCEDURE,schema=SCHEMA,collection_recovery=dict(path=str(HERE/'collection_recovery.json'),sha256=grid.sha(HERE/'collection_recovery.json'),
        original_launcher_returncode=1,original_imitation_completed=False,original_native_completed=True,
        reason='Only missing NN constructor counter default in completed noNN collection; original artifacts unchanged'))


def single_defect(launcher,report,native,provider,acceptance):
    assert launcher['stage']=='collect' and launcher['returncode']==1 and launcher['completed'] is False
    assert report['stage']=='collect' and report['completed'] is False and report['failure'] is None
    assert set(report['checks'])=={'aliases_restored','observer_aliases_restored','original_native_closed','prefix_task_verified','NN_constructors_exact',
        'selected4_request_not_replaced','model_RNG_updates_frozen','no_secondary_errors','reference_only_in_collection'}
    assert [k for k,v in report['checks'].items() if not v]==['NN_constructors_exact']
    assert report['dataset_sha256']==DATA_SHA and report['reference_calls']==354 and report['reference_N_injected'] is True
    assert native['completed'] and native['closed'] and native['scene_valid'] and native['failure'] is None
    assert native['aliases_restored'] and native['loader_restored'] and native['native_environment_count']==128 and native['physics_steps']==1416
    assert not any(native[k] for k in ('cleanup_errors','changed_inputs','unpinned_project_sources'))
    assert provider['NN'] is False and provider['updates']==0 and acceptance['stage_ready'] and acceptance['attempts']==128


def evidence():
    assert grid.sha(source.HERE/'preparation_seal.json')==ORIGINAL_SEAL
    seal,paths=source.gate('collect')  # Original complete1882 source/review gate; do not weaken the frozen function.
    launcher=grid.read(source.HERE/'01_launcher.json');report=grid.read(COLLECT/'imitation_report.json')
    a=source.parent.acceptance(grid.read(COLLECT/'evaluation.json')['episodes']);assert a==grid.read(COLLECT/'prefix_acceptance.json')
    single_defect(launcher,report,grid.read(COLLECT/'diagnostic_report.json'),grid.read(COLLECT/'action_provider.json'),a)
    assert launcher['argv']==source.commands()['collect'] and grid.sha(COLLECT/'observations4.npz')==DATA_SHA
    assert grid.read(COLLECT/'settings.json')==source.parent.settings()
    assert grid.read(COLLECT/'native_effort_readback.json')==grid.read(source.parent.HERE/'cpu_inputs/effort_declaration128.json')
    scene=grid.read(COLLECT/'gpu_scene_final.json')
    assert scene['closed'] and scene['environment_count']==128 and scene['physics_steps']==1416 and scene['diagnostic_guitar_mode']=='fixed'
    assert scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['hand_collision']['enabled_distinct_finger_pairs']==90
    assert scene['hand_collision_native_readback_environments']==128
    assert grid.read(COLLECT/'training_contract.json')==grid.read(source.parent.HERE/'train/training_contract.json')
    after=grid.read(COLLECT/'diagnostic_inputs_after.json');before=grid.read(COLLECT/'inputs_before.json')
    assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    assert all(grid.sha(p)==h for p,h in before.items());paths.update(map(Path,before))
    paths.update(COLLECT/n for n in ('imitation_report.json','diagnostic_report.json','action_provider.json','evaluation.json','prefix_acceptance.json',
        'observations4.npz','trace_env0_episode0.npz','trace_metadata.json','current_goal_DIP60.npz','training_contract.json','settings.json',
        'native_effort_readback.json','gpu_scene_final.json','inputs_before.json','diagnostic_inputs_after.json'))
    return paths|{source.HERE/'01_launcher.json',source.HERE/'01_collect.log',Path(__file__).resolve(),HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_checks.py'}


def gate(stage='fit',require_review=True):
    assert stage in ('fit','evaluate');paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(grid.sha(p)==h for p,h in seal['input_pins'].items())
    recovery=grid.read(HERE/'collection_recovery.json')
    assert recovery['accepted_for_continuation'] and recovery['dataset_sha256']==DATA_SHA
    assert recovery['original_parent_returncode']==1 and recovery['original_imitation_completed'] is False and recovery['original_native_completed'] is True
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'].get(str(HERE/'review.json'))==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    paths|={HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}
    if stage=='evaluate':
        folder=output('fit');r=grid.read(folder/'imitation_report.json');assert r['completed'] and all(r['checks'].values()) and r['procedure']==descriptor()
        assert grid.sha(folder/'initial.pt')==r['checkpoint_sha256']
        after=grid.read(folder/'inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(grid.sha(p)==h for p,h in after['input_pins'].items())
        paths.update(folder/n for n in ('imitation_report.json','initial.pt','inputs_after.json','offline_errors.json'))
    return seal,paths


@contextmanager
def scope(seal,paths):
    old=(source.gate,source.output,source.SCHEMA,source.descriptor)
    source.gate=lambda stage:(seal,paths);source.output=output;source.SCHEMA=SCHEMA;source.descriptor=descriptor
    try:yield
    finally:source.gate,source.output,source.SCHEMA,source.descriptor=old


def launch(stage):
    out=output(stage);assert stage in ('fit','evaluate');cap.reject_existing(out);seal,paths=gate(stage)
    old=(source.gate,source.output,source.SCHEMA,source.descriptor);failure=None;completed=False
    try:
        with scope(seal,paths):source.launch(stage)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        restored=(source.gate,source.output,source.SCHEMA,source.descriptor)==old
        try:
            print(json.dumps(dict(continuation_completed=completed and restored,failure=failure,aliases_restored=restored,
                original_collection_returncode=1,recovery_sha256=grid.sha(HERE/'collection_recovery.json'),schema=SCHEMA)),flush=True)
            if failure is None and not restored:raise RuntimeError('Continuation aliases not restored')
        except BaseException as error:
            if failure is None:raise
            print('Secondary continuation audit error: '+repr(error),file=sys.stderr)


def commands():return {s:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',s] for s in ('fit','evaluate')}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence()
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json');cap.reject_existing(HERE/'collection_recovery.json')
    check=source.module('imitation_recovery_cpu_checks',HERE/'cpu_checks.py');recovery,verification=check.check(sys.modules[__name__])
    grid.write(HERE/'collection_recovery.json',recovery);grid.write(HERE/'cpu_verification.json',verification)
    inputs=HERE/'cpu_inputs';inputs.mkdir();grid.write(inputs/'commands.json',commands());grid.write(inputs/'procedure.json',descriptor())
    paths.update(inputs.glob('*.json'));paths|={HERE/'collection_recovery.json',HERE/'cpu_verification.json'}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(source.parent.settings(),source.HERE/'cpu_inputs',paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=('fit','evaluate'));a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    elif a.execute:launch(a.execute)
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));s,_=gate(require_review=False)
        try:gate()
        except (AssertionError,FileNotFoundError):assert s['independent_review']=='pending'
        else:assert s['independent_review']=='passed_no_findings'
        try:gate('evaluate')
        except (AssertionError,FileNotFoundError):pass
        else:raise AssertionError('NN evaluation admitted before new fit')
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,recapture_command=False)))
