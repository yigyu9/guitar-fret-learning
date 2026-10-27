"""CPU migration checks with legacy file access and imports forcibly disabled."""
import argparse
import ast
import importlib.util
import importlib.abc
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
PHASE = Path(__file__).resolve().parent
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
LEGACY = tuple(str(ROOT / name) + os.sep for name in ('tab2body', 'stability_adapter_2'))


class NoLegacyImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('tab2body', 'stability_adapter_2'):
            raise RuntimeError('Forbidden legacy import: ' + fullname)


def forbid_legacy_open(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.abspath(os.fsdecode(args[0]))
        if path.startswith(LEGACY):
            raise RuntimeError('Forbidden legacy file access: ' + path)



def runtime_sources():
    pending = ['guitar_learning.native.front_facing_ready_v1.runtime_v15',
               'guitar_learning.native.front_facing_ready_v1.runtime_v12']
    seen, paths = set(), set()
    while pending:
        module = pending.pop()
        if module in seen or not module.startswith('guitar_learning.native'):
            continue
        seen.add(module)
        path = ROOT/(module.replace('.', '/')+'.py')
        if not path.is_file():
            path = ROOT/module.replace('.', '/')/'__init__.py'
        paths.add(str(path))
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                base = importlib.util.resolve_name('.'*node.level+(node.module or ''), module.rpartition('.')[0]) if node.level else node.module
                pending.append(base)
                if node.module is None:
                    pending.extend(base+'.'+alias.name for alias in node.names)
            elif isinstance(node, ast.Import):
                pending.extend(alias.name for alias in node.names)
    return paths


def run(*, gates=False, renderer=False):
    if any(name.split('.')[0] in ('tab2body', 'stability_adapter_2') for name in sys.modules):
        raise RuntimeError('Isolation requires a fresh interpreter')
    sys.meta_path.insert(0, NoLegacyImports())
    sys.addaudithook(forbid_legacy_open)
    # Prove that both guards are active before running the actual checks.
    for operation in (lambda: __import__('tab2body'), lambda: open(ROOT/'stability_adapter_2/config.json')):
        try:
            operation()
        except RuntimeError:
            pass
        else:
            raise AssertionError('Legacy access guard did not fire')

    import numpy as np
    from guitar_learning.prepared_reset_v1 import BASELINE_CONFIG, load_prepared_reset_contract, prepared_input_paths
    from guitar_learning.native.lower_body_release_v1 import common
    from guitar_learning.native.paths import ASSETS, original_input_path, verify_provenance
    from guitar_learning.dependency_inputs import parity_errors
    from guitar_learning.transition import solver
    from guitar_learning.native.upper_arm_static_geometry_v1 import calibrated_upper_fk
    from guitar_learning.native.initial_pose_video60_v1 import static_visual_v7

    contract = load_prepared_reset_contract()
    prepared_paths = prepared_input_paths()
    sources = {path for path in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in path.parts}
    pins = common.pin(BASELINE_CONFIG, extra=sources | prepared_paths)
    assert common.verify(pins)
    expected = {}
    baseline = ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_baseline_v14'
    for name in ('attempt.json', 'support_wrapper.json'):
        for path, digest in json.loads((baseline/name).read_text())['input_sha256'].items():
            path = str(Path(path).resolve())
            assert path not in expected or expected[path] == digest
            expected[path] = digest
    models = [path for path in pins if Path(path).suffix.lower() in ('.xml', '.obj', '.stl', '.ply', '.dae')]
    checked = models + [str(BASELINE_CONFIG)] + list(runtime_sources())
    errors = parity_errors(checked, expected)
    assert not errors, errors

    paths = solver.input_paths()
    assert all(ASSETS in Path(path).parents and Path(path).is_file() for path in paths)
    solver._check_fk_axes(solver.DEFAULT_ASSET)
    initial, state = contract['initial'], contract['state']
    q = np.array([row['pos'] for row in state['human_dof_states']])
    fk, _ = calibrated_upper_fk(initial['joint_names'], initial['human_body_names'], state, q)
    poses = fk(q)
    position_error = max(float(np.max(abs(poses[name][0] - np.array([body['pose']['p'][axis] for axis in 'xyz']))))
                         for name, body in zip(initial['human_body_names'], state['human_body_states']))
    assert position_error < 1e-12
    visual_paths = set()
    for asset in initial['loaded_assets']:
        visual_paths.update(static_visual_v7.asset_paths(asset['path']))
        # Old recorded paths must also resolve without reading either old folder.
        visual_paths.update(static_visual_v7.asset_paths(original_input_path(asset['path'])))
    assert all(ASSETS in path.parents for path in visual_paths)
    result = dict(legacy_open_and_import_guards=True, prepared_inputs=len(prepared_paths), pins=len(pins),
                  baseline_parity_files=len(checked), solver_inputs=len(paths),
                  fk_max_position_error_m=position_error, renderer_asset_inputs=len(visual_paths),
                  provenance=verify_provenance())
    if renderer:
        model, data, mapping, _ = static_visual_v7.build_model(initial)
        result['renderer'] = static_visual_v7.set_body_poses(model, data, mapping, state)
    if gates:
        import torch
        torch.set_num_threads(1)
        from guitar_learning.local_skills.learning import settings_document as local_settings
        from guitar_learning.local_skills.train import validate_gate
        from guitar_learning.joint.proofs import validate_preflight
        from guitar_learning.song.transfer import validate_experts as song_experts
        from guitar_learning.song_reward_v2.transfer import validate_experts as reward_experts
        from guitar_learning.transition.transfer import validate_source
        proof_counts = {}
        for role in ('left', 'right'):
            settings = local_settings(json.loads((RESULTS/f'guitar_learning_local_skills_v1/{role}_bc_ppo_ready_settings_v1.json').read_text()))
            proof_counts['local_'+role] = len(validate_gate(settings))
        settings = json.loads((RESULTS/'guitar_learning_joint_v1/joint_training_settings_v1.json').read_text())
        proof_counts['joint_preflight'] = len(validate_preflight(settings)['pins'])
        settings = json.loads((RESULTS/'guitar_learning_full_song_v1/training_settings_v1.json').read_text())
        proof_counts['full_song'] = len(song_experts(settings)['source_pins'])
        settings = json.loads((RESULTS/'guitar_learning_reward_v2/training_settings_v1.json').read_text())
        proof_counts['reward_v2'] = len(reward_experts(settings)['source_pins'])
        proof_counts['transition_source'] = len(validate_source(RESULTS/'guitar_learning_reward_v2/training_v1/final.pt')['source_pins'])
        result['actual_evidence_preflight'] = proof_counts
    assert not any(name.split('.')[0] in ('tab2body', 'stability_adapter_2') for name in sys.modules)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gates', action='store_true')
    parser.add_argument('--renderer', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(gates=args.gates, renderer=args.renderer), sort_keys=True))
