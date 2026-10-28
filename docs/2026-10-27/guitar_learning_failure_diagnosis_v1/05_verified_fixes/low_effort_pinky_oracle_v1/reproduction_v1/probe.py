"""Fresh four scripted attempts of reviewed pinky grid121; root alone runs native."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location('pinky_reproduction_grid', BASE/'probe.py')
acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquisition)
prior, grid, cap = acquisition.prior, acquisition.grid, acquisition.cap
REVIEW = BASE/'analysis/results_v1/review.json'
REFERENCE = HERE/'cpu_inputs/reference_pinky_grid121.json'


def actual_gate():
    paths = acquisition.actual_gate()
    review = grid.read(REVIEW)
    assert review['verdict'] == 'PASS' and not review['findings']
    verification_path = REVIEW.parent/'verification.json'
    assert str(verification_path) in review['reviewed_sha256']
    verification = grid.read(verification_path)
    assert verification['completed'] and verification['total_valid_first_attempts'] == 72
    for values in (review['reviewed_sha256'],verification['input_sha256'],verification['verified_input_sha256']):
        assert values and all(Path(p).is_file() and grid.sha(p) == h for p,h in values.items())
        paths.update(map(Path, values))
    document = grid.read(BASE/'cpu_inputs/pinky_grid.json')
    evaluation = grid.read(BASE/'runs/pinky/evaluation.json')
    selection = grid.choose(evaluation['episodes'],document)
    assert grid.complete(evaluation['episodes'],72) and selection == grid.read(BASE/'runs/pinky/selection.json')
    assert selection['selected_grid_index'] == 121 and document['rows'][121]['valid']
    launcher = grid.read(BASE/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode'] == 0 and len(launcher['children']) == 1
    assert launcher['children'][0]['finger'] == 'pinky' and launcher['children'][0]['returncode'] == 0
    paths.update((REVIEW,verification_path,BASE/'01_launcher.json',BASE/'cpu_inputs/pinky_grid.json',BASE/'runs/pinky/selection.json',BASE/'runs/pinky/evaluation.json'))
    return paths


@contextmanager
def selected_inputs():
    original_here, original_inputs = prior.HERE, prior.INPUTS
    prior.HERE = HERE
    prior.INPUTS = dict(original_inputs,pinky=(original_inputs['pinky'][0],REFERENCE))
    try: yield
    finally: prior.HERE, prior.INPUTS = original_here, original_inputs


def gate(require_review=True):
    paths = actual_gate(); seal = grid.read(HERE/'preparation_seal.json')
    assert not require_review or seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and grid.sha(p) == h for p,h in seal['input_pins'].items())
    if require_review:
        review = grid.read(HERE/'review.json')
        assert review['verdict'] == 'PASS' and not review['findings']
        assert seal['input_pins'].get(str(HERE/'review.json')) == grid.sha(HERE/'review.json')
    return seal, paths


def launch():
    out = HERE/'runs/pinky'; cap.reject_existing(out)
    seal, paths = gate()
    out.mkdir(parents=True,exist_ok=False); identity = (out.stat().st_dev,out.stat().st_ino)
    saved_here, saved_inputs = prior.HERE, prior.INPUTS
    try:
        import isaacgym  # Original native import must precede Torch/NumPy.
        with selected_inputs(): prior.execute('pinky','reference',out,identity,seal,paths)
        evaluation = grid.read(out/'evaluation.json')
        acceptance = cap.repro.acceptance(evaluation['episodes'])
        grid.write(out/'reproduction_acceptance.json',dict(selected_grid_index=121,acceptance=acceptance,
            scope='Original four-attempt acceptance; scripted finite target, not NN/free guitar performance'))
    except BaseException as error:
        if not (out/'report.json').exists(): grid.write(out/'report.json',dict(completed=False,closed=False,failure=dict(type=type(error).__name__,message=str(error))))
        raise
    finally:
        cap.owned(out,identity)
        restored = prior.HERE is saved_here and prior.INPUTS is saved_inputs
        grid.write(out/'selected_input_aliases.json',dict(restored=restored,selected_grid_index=121,reference=str(REFERENCE)))
        assert restored


def cpu_checks():
    import tempfile
    import torch
    from unittest.mock import patch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runtime,runner
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    declaration, checks = prior.cpu_checks()
    saved_here, saved_inputs = prior.HERE, prior.INPUTS
    try:
        with selected_inputs(): raise RuntimeError('injected execute failure')
    except RuntimeError as error: assert str(error) == 'injected execute failure'
    assert prior.HERE is saved_here and prior.INPUTS is saved_inputs
    with tempfile.TemporaryDirectory() as temp:
        old = Path(temp)/'runs/pinky'; old.mkdir(parents=True); sentinel = old/'sentinel'; sentinel.write_bytes(b'unchanged')
        def denied(): raise AssertionError('gate must not run')
        with patch.dict(globals(),HERE=Path(temp),gate=denied):
            try: launch()
            except FileExistsError: pass
            else: raise AssertionError('Existing output accepted')
            assert sentinel.read_bytes() == b'unchanged' and not list(old.glob('*.json'))
            sentinel.unlink(); old.rmdir(); old.symlink_to(Path(temp)/'absent')
            try: launch()
            except (FileExistsError,ValueError): pass
            else: raise AssertionError('Dangling output accepted')
    # Execute the unchanged parent's local EffortPool failure path with CPU stubs.
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp); identity = (out.stat().st_dev,out.stat().st_ino); closed = []
        class Scene:
            def close(self): closed.append(True); raise RuntimeError('injected close failure')
        class Pool:
            def __init__(self,config,target_out): self._create_scene(config,target_out)
            def _create_scene(self,config,target_out):
                prepared_reset_v1.load_prepared_reset_contract(); return Scene()
        original_loader = prepared_reset_v1.load_prepared_reset_contract
        config = prior.settings('pinky')
        with selected_inputs(),patch.object(runtime,'ShortPool',Pool),patch.object(runner,'_pins',return_value={}),patch.object(prior.cap,'verify_native',side_effect=AssertionError('injected native mismatch')),patch.object(grid,'read',wraps=grid.read) as reading:
            # No own prepared files are required for this isolated constructor failure fixture.
            original_read = reading._mock_wraps
            reading.side_effect = lambda path: config if Path(path) == HERE/'cpu_inputs/pinky_settings.json' else original_read(path)
            try: prior.execute('pinky','reference',out,identity,dict(input_pins={}),set())
            except AssertionError as error: assert str(error) == 'injected native mismatch'
            else: raise AssertionError('Constructor failure swallowed')
        assert len(closed) == 1 and prior.HERE is saved_here and prior.INPUTS is saved_inputs
        assert prepared_reset_v1.load_prepared_reset_contract is original_loader
        report = grid.read(out/'report.json')
        assert report['failure']['message'] == 'injected native mismatch' and report['close_errors'][0]['message'] == 'injected close failure'
    return declaration,dict(CPU_only=True,GPU_executed=False,CUDA_initialized=False,
        original_prelearning_CPU_regressions=checks,new_native_jobs=1,new_first_attempts=4,
        selected_input_objects_restored=True,constructor_primary_and_close_error_preserved=True,
        scope='Original cap/evaluator CPU fixtures reused; no native execution')


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    paths = actual_gate()
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
    cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    declaration, checks = cpu_checks()
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    document = grid.read(BASE/'cpu_inputs/pinky_grid.json'); row = document['rows'][121]
    reference = copy.deepcopy(grid.read(prior.INPUTS['pinky'][1]))
    reference['selected_targets_rad'] = dict(zip(document['joint_names'],row['target_rad']))
    reference['source_evidence'].update({str(path):grid.sha(path) for path in (BASE/'cpu_inputs/pinky_grid.json',BASE/'runs/pinky/selection.json',REVIEW)})
    reference['scope'] = 'Finite grid-selected121 target [0,+5,0,0]deg; not source actual pose, policy or free-guitar performance'
    inputs = HERE/'cpu_inputs'; inputs.mkdir(); grid.write(REFERENCE,reference)
    with selected_inputs():
        config = prior.settings('pinky'); assert config == grid.read(acquisition.PRELEARNING/'runs/pinky_reference/settings.json')
        assert read_reference(REFERENCE,config['song']['short_learning']) == reference
    grid.write(inputs/'pinky_settings.json',config); grid.write(inputs/'settings.json',config)
    grid.write(inputs/'effort_declaration.json',declaration)
    grid.write(inputs/'jobs.json',[dict(finger='pinky',control='reference',assigned_quotas=[1]*4,
        argv=[grid.PYTHON,'-B',str(Path(__file__)),'--execute'])])
    grid.write(HERE/'cpu_verification.json',dict(checks,selected_grid_index=121,offset_deg=row['offset_deg'],
        selected_target_rad=row['target_rad'],original_settings_exact=True,original_read_reference_passed=True))
    paths.update(inputs.glob('*.json'));paths.update((Path(__file__),HERE/'PLAN.md',HERE/'cpu_verification.json'))
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),
        scope='Fresh4 scripted pinky121; original prelearning evaluator/cap verifier unchanged; root-only native'))
    result = subprocess.run([grid.PYTHON,'-B',str(Path(__file__)),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout))
    seal = grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')] = grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,pins=len(seal['input_pins']),GPU_executed=False)))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','execute','self-test','gate-check','dry-plan'): group.add_argument('--'+name,action='store_true')
    args=parser.parse_args();sys.path.insert(0,str(grid.ROOT))
    if args.prepare: prepare()
    elif args.execute: launch()
    elif args.self_test: print(json.dumps(cpu_checks()[1],indent=2))
    elif args.gate_check:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym')); gate(require_review=False)
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))
        print(json.dumps(dict(fresh_process=True,stdlib_gate=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False)))
    else: print(json.dumps([dict(finger='pinky',control='reference',selected_grid_index=121,episodes=4,out=str(HERE/'runs/pinky'))]))
