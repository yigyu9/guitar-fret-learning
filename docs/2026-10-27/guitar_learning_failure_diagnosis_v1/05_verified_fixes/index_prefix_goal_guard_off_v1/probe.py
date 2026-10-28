"""Guard-off execution override; original strict goal model/std/mode evaluator reused."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('goal_guard_off_original',HERE.parent/'index_prefix_goal_exploration_precheck_v1/probe.py')
on=importlib.util.module_from_spec(s);sys.modules[s.name]=on;s.loader.exec_module(on)
grid,cap=on.grid,on.cap
MODES=on.MODES
SCHEMA='diagnostic.index_prefix_goal_guard_off.execution.v1'
ORIGINAL_GATE=on.gate


def output(mode):
    if mode not in MODES:raise ValueError('Only deterministic/stochastic guard-off evaluations')
    return HERE/'runs'/mode


def evidence():
    seal,paths,sigma=ORIGINAL_GATE()
    paths.update(on.parent.base.reviewed(on.HERE/'analysis/results_v1/review.json'))
    return paths|{HERE/'probe.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md'},sigma


def gate(mode='deterministic',require_review=True):
    output(mode);paths,sigma=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])},sigma


def passthrough(original,*args):
    assert args[-1] is True  # The frozen LearningPool requests its original guard-on contract.
    target,row=original(*args[:-1],False)
    row['would_block']=row['eligible'] & (row['raw_target_rad']>row['old_target_rad'])
    row['actual_blocked']=row['blocked'].clone()
    assert not bool(row['blocked'].any()) and bool((row['raw_target_rad']==row['final_target_rad']).all())
    return target,row


@contextmanager
def execution_scope(mode,audit,approved):
    old=(on.output,on.gate,on.adapter)
    @contextmanager
    def adapter(*args):
        with old[2](*args):
            extra=on.parent.support();original_filter=extra.guard.target_filter
            extra.guard.target_filter=lambda *a:passthrough(original_filter,*a)
            try:yield
            finally:extra.guard.target_filter=original_filter;audit['filter_alias_restored']=extra.guard.target_filter is original_filter
    on.output=output;on.gate=lambda requested:approved;on.adapter=adapter
    try:yield
    finally:
        on.output,on.gate,on.adapter=old
        audit['producer_aliases_restored']=(on.output,on.gate,on.adapter)==old


def finish(mode,audit,completed,failure):
    import numpy as np
    out=output(mode);checks=dict(filter_alias_restored=audit.get('filter_alias_restored',False),producer_aliases_restored=audit.get('producer_aliases_restored',False))
    counts=None
    p=out/'current_goal_DIP60.npz'
    if p.is_file():
        with np.load(p,allow_pickle=False) as raw:
            mask=raw['first_attempt'];actual=raw['actual_blocked'];would=raw['would_block']
            checks.update(actual_blocked_zero=not bool(actual[mask].any()),blocked_means_actual=np.array_equal(actual,raw['blocked']),
                would_block_definition=np.array_equal(would[mask],(raw['eligible']&(raw['raw_target_rad']>raw['old_target_rad']))[mask]),
                raw_final_exact=np.array_equal(raw['raw_target_rad'][mask],raw['final_target_rad'][mask]),other104_exact=bool((raw['other104_error_rad'][mask]==0).all()),
                memory_submit_observation_exact=all(bool((raw[k][mask]==0).all()) for k in ('memory_error_rad','submit_error_rad','observation_error')),
                original_rate_bounds=bool((raw['box_rate_excess_rad'][mask]<=raw['numerical_tolerance_rad'][mask]).all()))
            counts=dict(first_attempt_controls=int(mask.sum()),would_block_controls=int((would&mask).sum()),actual_blocked_controls=int((actual&mask).sum()))
    else:checks['first_attempt_sidecar_saved']=False
    report=out/'execution_override.json';checks['original_std_mode_execution_completed']=report.is_file() and grid.read(report)['completed'] is True
    checks['checkpoint_unchanged']=grid.sha(on.CHECKPOINT)==on.recovery.MODEL_SHA
    grid.write(out/'guard_execution_override.json',dict(schema=SCHEMA,completed=completed and all(checks.values()),failure=failure,checks=checks,mode=mode,first_attempt_counts=counts,
        guard_enabled=False,checkpoint=str(on.CHECKPOINT),checkpoint_sha256=on.recovery.MODEL_SHA,checkpoint_metadata_rewritten=False,
        original_control_contract_preserved=True,original_std_mode_report='execution_override.json',
        scope='Only original DIP positive-increment filter bypassed; would_block is counterfactual eligibility, blocked/actual_blocked are actual false. Original model contract describes guard-on; this separate execution override declares off. Closed-loop128 first attempts, not fixed-action physics or a new learned controller.'))
    if failure is None and not all(checks.values()):raise RuntimeError('Guard-off execution audit failed')


def launch(mode):
    out=output(mode);cap.reject_existing(out);approved=gate(mode);audit={};completed=False;failure=None
    try:
        with execution_scope(mode,audit,approved):on.launch(mode)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if out.is_dir():
            try:finish(mode,audit,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary guard-off report error: '+repr(error),file=sys.stderr)


def commands():return {mode:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',mode] for mode in MODES}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths,sigma=evidence();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=on.module('goal_guard_off_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]);inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('commands.json',commands()),('settings.json',on.parent.settings()),('execution_override.json',dict(schema=SCHEMA,guard_enabled=False,sigma4=sigma,checkpoint=str(on.CHECKPOINT),seed=7))):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks);paths|={HERE/'cpu_verification.json',*inputs.glob('*.json')}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(on.parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--execute',choices=MODES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(on.module('goal_guard_off_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.execute:launch(a.execute)
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending execution admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,modes=list(MODES))))
