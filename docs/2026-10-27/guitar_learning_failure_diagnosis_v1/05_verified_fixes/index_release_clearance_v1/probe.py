"""Root-only original128 noNN reference runs with bounded distal128 observation."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('clearance_original_noise',HERE.parent/'index_prefix_reference_noise_v1/probe.py')
noise=importlib.util.module_from_spec(s);sys.modules[s.name]=noise;s.loader.exec_module(noise)
goal,parent,grid,cap=noise.goal,noise.parent,noise.grid,noise.cap
MODES=('reference','noisy_reference')
SCHEMA='diagnostic.index_release_distal_samples.v1'

def output(mode):assert mode in MODES;return HERE/'runs'/mode

def support():return noise.on.module('clearance_source_samples',HERE/'surface.py')

def evidence():
    _,paths=noise.gate()
    paths.update(parent.base.reviewed(noise.HERE/'analysis/results_v1/review.json'))
    return paths|{HERE/n for n in ('probe.py','surface.py','cpu_checks.py','PLAN.md','README.md')}

def gate(require_review=True):
    paths=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}

@contextmanager
def execution_scope(mode,approved,audit):
    # Only entered after original native import order; numerical callback imports stay here.
    old=(goal.output,goal.gate,noise.output,noise.gate)
    if mode=='reference':goal.output=lambda stage:output(mode) if stage=='reference' else old[0](stage);goal.gate=lambda stage:approved
    else:noise.output=lambda:output(mode);noise.gate=lambda:approved
    try:
        with support().observer(sys.modules[__name__],audit):yield
    finally:
        goal.output,goal.gate,noise.output,noise.gate=old
        audit['producer_aliases_restored']=(goal.output,goal.gate,noise.output,noise.gate)==old

def finish(mode,audit,completed,failure):
    import numpy as np
    out=output(mode);first=None
    try:
        if audit['rows']:
            with (out/'release_clearance4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in audit['rows']]) for k in audit['rows'][0]})
        if 'static' in audit:
            with (out/'surface_static.npz').open('xb') as f:np.savez_compressed(f,**audit['static'])
            grid.write(out/'surface_metadata.json',dict(schema=SCHEMA,pad_contract=audit['pad_contract'],source_sha256={str(HERE/'surface.py'):grid.sha(HERE/'surface.py')},
                sample_order='original index3 slot0 local source sample0..127; no subsampling or reselection',A_source_index=4,A_target_id='event-000004/string-3/note-4',
                physical_string=3,fret=4,frame='point/normal and starts/ends/frets/plane in current guitar-local; body/guitar poses world position+xyzw quaternion',
                source_valid='original4x128 allTrue current asset, no time-varying facing-mask substitution',clock_window=[692,920],clock_hz=240,endpoint_stride=4,
                window='A original press2.88s through first60Hz endpoint at/after B7 shared press3.832s; inclusive saved endpoints2.883333..3.833333',
                load_scope='original index3 net-body loaded bit and resultant force, shared by all points; no sample/contact-partner force decomposition',
                geometry_scope='original finite inset cell3D distance; separate signed press-plane height/cos/lateral/in-cell. P1 zero velocity is unused, no velocity output saved; nearest and any same-sample witness distinct',
                reset_scope='copied precontrol first mask retains failure endpoint; reset snapshots explicitly invalid and perpoint geometry NaN/false; no new clearance predicate'))
    except BaseException as error:first=error
    try:
        original=grid.read(out/'goal_codec_report.json') if (out/'goal_codec_report.json').is_file() else {}
        native=grid.read(out/'diagnostic_report.json') if (out/'diagnostic_report.json').is_file() else {}
        checks=dict(original_goal_complete=original.get('completed') is True,original_native_closed=native.get('completed') is True and native.get('closed') is True,
            NN_constructors_zero=original.get('NN_constructors')==0,aliases_restored=audit.get('observer_alias_restored',False) and audit.get('producer_aliases_restored',False),
            after_delegated=audit['after_calls']>0 and audit['after_calls']==original.get('reference_calls'),typed_saved=first is None and all((out/n).is_file() for n in ('release_clearance4.npz','surface_static.npz','surface_metadata.json')),
            bounded_rows=0<len(audit['rows'])<=232,no_checkpoint_written=not list(out.glob('*.pt')))
        grid.write(out/'clearance_report.json',dict(schema=SCHEMA,mode=mode,completed=completed and all(checks.values()),failure=failure,checks=checks,
            rows=len(audit['rows']),after_calls=audit['after_calls'],clock_window=[692,920],env_ids=[0,1,2,3],model_loads=0,NN_constructors=0,PPO_updates=0,fit_steps=0,
            scope='Read-only60Hz index3 original128 source samples on first attempts in fixed window; original128 evaluator/ledger/9rewards unchanged. No whole skin, continuous240Hz clearance, contact pair or pressure claim. Original reference RNG/model-frozen fields are not a new sampling audit.'))
    except BaseException as error:
        if first is not None:print('Secondary clearance report error: '+repr(error),file=sys.stderr);raise first from None
        raise
    if first is not None:raise first
    if failure is None and not all(checks.values()):raise RuntimeError('Clearance observation audit failed')

def launch(mode):
    cap.reject_existing(output(mode));approved=gate();audit=dict(rows=[],after_calls=0);failure=None;completed=False
    try:
        import isaacgym  # Reviewed stdlib gate precedes numerical/native imports.
        with execution_scope(mode,approved,audit):
            if mode=='reference':goal.launch('reference')
            else:noise.launch()
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if output(mode).is_dir():
            try:finish(mode,audit,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary clearance audit error: '+repr(error),file=sys.stderr)

def commands():return {mode:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',mode] for mode in MODES}

def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths=evidence();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=noise.on.module('clearance_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]);inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('commands.json',commands()),('settings.json',parent.settings())):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks);paths|={HERE/'cpu_verification.json',*inputs.glob('*.json')}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+name,action='store_true')
    g.add_argument('--execute',choices=MODES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:print(json.dumps(noise.on.module('clearance_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__]),indent=2))
    elif a.execute:launch(a.execute)
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending execution admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,modes=MODES)))
