"""Thin strict B300 native renderer with the reviewed single-DIP guard."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard_video_parent',HERE.parent/'probe.py')
guard=importlib.util.module_from_spec(spec);sys.modules[spec.name]=guard;spec.loader.exec_module(guard)
B,grid,cap=guard.B,guard.grid,guard.cap
ACTUAL=HERE.parent/'analysis/results_v1/review.json'
ACTUAL_SHA='f5427fe9954112854621425b4844a40b8926c80205caf2ebcce429d3ce34c541'
OLD_QA=guard.BPATH/'native_video_qa/results_v1'


def gate(require_review=True):
    _,paths=guard.gate();assert grid.sha(ACTUAL)==ACTUAL_SHA
    paths.update(B.base.reviewed(ACTUAL));paths.update(B.base.reviewed(OLD_QA/'review.json'))
    seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert r['verdict']=='PASS' and not r['findings'] and seal['independent_review']=='passed_no_findings'
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json')
        assert all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def finish(out,audit,state,failure):
    cleanup=list(audit.get('cleanup_errors',[]))
    if not out.is_dir():return
    if 'identity' in state:cap.owned(out,state['identity'])
    try:
        import numpy as np
        for name,values in (('dip_aborted_control.npz',audit.get('aborted_control')),('dip_control60.npz',
            {k:np.stack([r[k] for r in audit['rows']]) for k in audit['rows'][0]} if audit['rows'] else None)):
            if values:
                with (out/name).open('xb') as f:np.savez_compressed(f,**values)
    except BaseException as error:cleanup.append(dict(type=type(error).__name__,message=str(error)))
    report=grid.read(out/'report.json') if (out/'report.json').is_file() else {}
    meta=grid.read(out/'capture_metadata.json') if (out/'capture_metadata.json').is_file() else {}
    checks=dict(all128_finished=len(audit.get('completed_envs',set()))==128,observer_aliases_restored=audit.get('observer_aliases_restored',False),
        B_initialization_aliases_restored=state.get('initialization_aliases_restored',False),B_contract_tagged=state.get('initialization_contract_tagged',False),
        original_render_complete=report.get('completed',False),original_policy_unchanged=report.get('policy_unchanged',False),original_checkpoint_unchanged=report.get('checkpoint_unchanged',False),
        original_scene_closed=report.get('scene_closed',False),updates300=meta.get('checkpoint_training_updates')==300,
        strict_checkpoint_identity=report.get('checkpoint')==str(B.checkpoint(300)) and report.get('checkpoint_sha256')==grid.sha(B.checkpoint(300)) and report.get('checkpoint_pins_validated',False),
        training_updates_zero=report.get('training_updates')==0,
        evaluation_callback_not_used='policy_before' not in audit and 'policy_after' not in audit)
    grid.write(out/'execution_override.json',dict(mode=guard.MODES[1],fresh=False,closed_loop=True,enabled=True,
        model_checkpoint=str(B.checkpoint(300)),scope='Native env0 first attempt with reviewed DIP guard; not unmodified policy performance, fixed-tape effect or training',
        evaluator_fingerprint_callback_used=False,identity_scope='Original renderer strict load/model unchanged/checkpoint SHA/updates300; no evaluator RNG fingerprint claim'))
    grid.write(out/'guard_video_report.json',dict(completed=failure is None and not cleanup and all(checks.values()),failure=failure,cleanup_errors=cleanup,checks=checks,
        first_attempts=128,completed_first_attempts=len(audit.get('completed_envs',set())),control_rows=len(audit['rows']),
        scope='Whole128 first-attempt scalar DIP60 sidecar incl failure endpoint/retry masked; native pixels and full body raw only env0'))
    if failure is None and (cleanup or not all(checks.values())):raise RuntimeError('Guard renderer audit failed; original outputs retained')


def launch():
    out=HERE/'runs/guard';cap.reject_existing(out);seal,paths=gate();observed={};audit=dict(rows=[]);failure=None
    old=(B.base.output,B.base.checkpoint)
    try:
        import isaacgym  # All output/review/source gates precede numerical/native imports.
        with B.execution_scope('render',seal,paths,observed):
            original=B.base.effort_scope
            @contextmanager
            def scope(evidence,state):
                with original(evidence,state) as runner:
                    with guard.observer_scope(runner,guard.MODES[1],audit):yield runner
            B.base.effort_scope=scope;B.base.output=lambda *args,**kwargs:out;B.base.checkpoint=lambda update:B.checkpoint(update)
            try:B.base.launch('render',None,300)
            finally:B.base.effort_scope=original
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        B.base.output,B.base.checkpoint=old
        try:finish(out,audit,observed.get('state',{}),failure)
        except BaseException as error:
            if failure is None:raise
            print('Secondary guard-video cleanup error: '+repr(error),file=sys.stderr)


def command():return [grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute']


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    _,paths=guard.gate();assert grid.sha(ACTUAL)==ACTUAL_SHA
    paths.update(B.base.reviewed(ACTUAL));paths.update(B.base.reviewed(OLD_QA/'review.json'))
    cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    test=B.module('guard_video_cpu_checks',HERE/'cpu_checks.py');checks=test.check(sys.modules[__name__])
    inputs=HERE/'cpu_inputs';inputs.mkdir();grid.write(inputs/'command.json',command())
    config=grid.read(guard.BPATH/'cpu_inputs/settings.json');grid.write(inputs/'settings.json',config)
    grid.write(inputs/'reuse.json',dict(old_hand=str(guard.BPATH/'native_video_000300/hand.mp4'),old_fullbody=str(guard.BPATH/'native_video_000300/fullbody.mp4'),
        guard_evaluation=str(HERE.parent/'runs'/guard.MODES[1]),renderer=str(B.base.RENDER),checkpoint=str(B.checkpoint(300)),num_envs=128,guard_mode=guard.MODES[1]))
    grid.write(HERE/'cpu_verification.json',checks)
    paths.update(inputs.glob('*.json'));paths.update((Path(__file__),HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md',HERE/'cpu_verification.json',B.base.RENDER))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),command=command())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','execute','self-test','gate-check'):g.add_argument('--'+name,action='store_true')
    args=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare:prepare()
    elif args.execute:launch()
    elif args.self_test:print(json.dumps(B.module('guard_video_cpu_checks',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (AssertionError,FileNotFoundError):pass
            else:raise AssertionError('Pending renderer admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False)))
