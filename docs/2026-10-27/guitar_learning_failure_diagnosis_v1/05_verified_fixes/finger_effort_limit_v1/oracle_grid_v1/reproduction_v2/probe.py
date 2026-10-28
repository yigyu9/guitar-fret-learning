"""Fresh4 reproduction of the independently reviewed low-effort grid selections."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location('fresh_low_effort_grid', BASE/'probe.py')
acquisition = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = acquisition
spec.loader.exec_module(acquisition)
cap = acquisition.cap
grid = acquisition.grid
REVIEW = BASE/'analysis/results_v1/review.json'
EXECUTE_FINGERS = ('index',)  # Middle114 already has reviewed4/4 under this exact cap.


def grid_gate():
    paths = acquisition.actual_gate()
    review = grid.read(REVIEW)
    assert review['verdict'] == 'PASS' and not review['findings']
    mapping = review['reviewed_sha256']
    assert mapping and all(Path(p).is_file() and grid.sha(p) == h for p, h in mapping.items())
    paths.update(map(Path, mapping)); paths.add(REVIEW)
    verification_path = REVIEW.parent/'verification.json'
    assert str(verification_path) in mapping
    verification = grid.read(verification_path)
    assert verification['completed']
    for name in ('input_sha256', 'verified_input_sha256'):
        values = verification[name]
        assert values and all(Path(p).is_file() and grid.sha(p) == h for p, h in values.items())
        paths.update(map(Path, values))
    assert grid.read(BASE/'01_launcher.json')['completed'] and grid.read(BASE/'01_launcher.json')['returncode'] == 0
    paths.add(BASE/'01_launcher.json')
    selected = {}
    for finger in acquisition.COUNTS:
        folder = BASE/'runs'/finger
        document = grid.read(grid.HERE/'cpu_inputs'/(finger+'_grid.json'))
        evaluation = grid.read(folder/'evaluation.json')
        assert grid.complete(evaluation['episodes'], acquisition.COUNTS[finger])
        choice = grid.choose(evaluation['episodes'], document)
        assert choice == grid.read(folder/'selection.json') and choice['selected_grid_index'] is not None
        assert grid.read(folder/'report.json')['completed']
        assert grid.read(folder/'effort_grid_lifecycle.json')['scene_valid']
        selected[finger] = choice['selected_grid_index']
        paths.update(folder/name for name in ('evaluation.json', 'selection.json', 'report.json', 'effort_grid_lifecycle.json'))
    middle = acquisition.CAP_ROOT/'runs/middle/evaluation.json'
    assert grid.read(middle)['acceptance']['passed']
    stored = grid.read(acquisition.CAP_ROOT/'cpu_inputs/middle_targets.json')
    assert stored['selected_grid_index'] == selected['middle']
    assert grid.read(cap.REPRO/'cpu_inputs/middle_settings.json') == grid.read(acquisition.CAP_ROOT/'cpu_inputs/middle_settings.json')
    paths.update((middle, acquisition.CAP_ROOT/'cpu_inputs/middle_targets.json',
                  acquisition.CAP_ROOT/'cpu_inputs/middle_settings.json'))
    return paths, selected


@contextmanager
def selected_inputs(selected):
    original_here = cap.HERE; original_selected = cap.repro.SELECTED
    cap.HERE = HERE; cap.repro.SELECTED = copy.deepcopy(selected)
    try:
        yield
    finally:
        cap.HERE = original_here; cap.repro.SELECTED = original_selected


def prepare():
    assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
    paths, selected = grid_gate()
    assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.tool.experiments.short_finger_learning import runner
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    seal = grid.read(BASE/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    paths.update(map(Path, seal['input_pins'])); paths.add(BASE/'preparation_seal.json')
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    _, declaration = cap.private_contract(load_prepared_reset_contract())
    grid.write(inputs/'effort_declaration.json', declaration)
    saved_here = cap.HERE; saved_selected = cap.repro.SELECTED
    with selected_inputs(selected):
        for finger in EXECUTE_FINGERS:
            index = selected[finger]
            original = grid.read(grid.HERE/'cpu_inputs'/(finger+'_grid.json'))
            document = cap.repro.document_for(finger, original)
            assert document['selected_grid_index'] == index and document['selected_target_rad'] == original['rows'][index]['target_rad']
            assert len(document['rows']) == 4 and [r['env_id'] for r in document['rows']] == list(range(4))
            assert len({r['attempt_id'] for r in document['rows']}) == 4
            grid.write(inputs/(finger+'_targets.json'), document)
            grid.write(inputs/(finger+'_settings.json'), grid.settings(finger, 4))
    try:
        with selected_inputs(selected):
            raise RuntimeError('CPU injected selected-input error')
    except RuntimeError as error:
        assert str(error) == 'CPU injected selected-input error'
    assert cap.HERE is saved_here and cap.repro.SELECTED is saved_selected
    grid.write(inputs/'settings.json', grid.settings('index', 4))
    grid.write(HERE/'cpu_verification.json', dict(CPU_only=True, GPU_executed=False, selected_grid_indices=selected,
        assigned_quotas_each=[1]*4, native_cap_Nm=cap.CAP, original_cap_execute_reused=True,
        original_4env_verifier_and_acceptance_reused=True, aliases_restored_after_injected_error=True,
        pre_native_gate_import_order_checked=True,
        original_grid_source_targets_unchanged=True, no_NN_checkpoint=True,
        GPU_fingers=list(EXECUTE_FINGERS), middle_reuses_reviewed_cap4of4=True))
    paths.update(inputs.glob('*.json'))
    paths.update((Path(__file__), HERE/'PLAN.md', HERE/'cpu_verification.json'))
    pins = runner._pins(grid.settings('index', 4), inputs, paths)
    grid.write(HERE/'preparation_seal.json', dict(independent_review='pending', input_pins=pins,
        selected_grid_indices=selected, GPU_fingers=list(EXECUTE_FINGERS),
        scope='Fresh index4; reuse reviewed unchanged middle4; not learned/free/fullsong performance'))
    print(dict(CPU_only=True, pins=len(pins), selected_grid_indices=selected))


def launch(finger):
    out = HERE/'runs'/finger; cap.reject_existing(out)
    seal = grid.read(HERE/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    paths, selected = grid_gate()
    assert selected == seal['selected_grid_indices']
    out.mkdir(parents=True, exist_ok=False); identity = (out.stat().st_dev, out.stat().st_ino)
    grid.write(out/'selection_provenance.json', dict(grid_selection=str(BASE/'runs'/finger/'selection.json'),
        grid_analysis_review=str(REVIEW), selected_grid_index=selected[finger], original_acceptance_unchanged=True))
    saved_here = cap.HERE; saved_selected = cap.repro.SELECTED
    try:
        import isaacgym
        with selected_inputs(selected):
            cap.execute(finger, out, identity, seal, paths)
    finally:
        cap.owned(out, identity)
        restored = cap.HERE is saved_here and cap.repro.SELECTED is saved_selected
        grid.write(out/'selected_input_aliases.json', dict(restored=restored, selected_grid_indices=selected))
        assert restored


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true'); group.add_argument('--execute', action='store_true')
    parser.add_argument('--finger', choices=EXECUTE_FINGERS); args = parser.parse_args()
    sys.path.insert(0, str(grid.ROOT))
    if args.prepare: prepare()
    elif args.finger is None: raise ValueError('Predeclared finger required')
    else: launch(args.finger)
