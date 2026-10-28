"""CPU migration checks with legacy file access and imports forcibly disabled."""
import argparse
import ast
import importlib.util
import importlib.abc
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PHASE = Path(__file__).resolve().parent
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


def run(*, renderer=False):
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
    from guitar_learning.runtime.prepared_reset_v1 import BASELINE_CONFIG, load_prepared_reset_contract, prepared_input_paths
    from guitar_learning.native import paths as common
    from guitar_learning.native.paths import ASSETS, original_input_path, verify_provenance
    from guitar_learning.core.dependency_inputs import parity_errors
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

    asset_paths = {path for path in prepared_paths if ASSETS in path.parents}
    assert asset_paths and all(path.is_file() for path in asset_paths)
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
                  baseline_parity_files=len(checked), prepared_asset_inputs=len(asset_paths),
                  fk_max_position_error_m=position_error, renderer_asset_inputs=len(visual_paths),
                  provenance=verify_provenance())
    if renderer:
        model, data, mapping, _ = static_visual_v7.build_model(initial)
        result['renderer'] = static_visual_v7.set_body_poses(model, data, mapping, state)
    assert not any(name.split('.')[0] in ('tab2body', 'stability_adapter_2') for name in sys.modules)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(renderer=args.renderer), sort_keys=True))
