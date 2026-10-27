"""Preserve prepared-pose Strike connection inputs before native import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('trial',), required=True)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--torque',type=int,choices=(0,1),required=True)
    args = parser.parse_args()
    if args.mode=='trial' and args.candidate is None: parser.error('--candidate required for trial')
    root = Path(__file__).resolve().parents[1]
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    paths = set()
    for directory, patterns in ((root/'stability_adapter_2', ('*.py', '*.md', '*.json', '*.xml')),
                                (root/'tab2body', ('*.py',)),
                                (root/'tab2body/assets', ('*',)),
                                (root/'isaacgym/python/isaacgym', ('*.py', '*.so'))):
        for pattern in patterns:
            paths.update(p for p in directory.rglob(pattern) if p.is_file())
    result_root = root/'docs/2026-10-12/stability_adapter_2/results'
    paths.update(root/p for p in (
        'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt',
        'data/song_bundles/02_Jazz1-200-B_solo/training/strike_plan.json',
        'strike/02_physical_control/pick-grip-reference.json', 'tab2body/_gen/mjcf_gains.json'))
    paths.update(result_root/p for p in (
        'underneck_initial_pose_v1/refine/candidate_w10000.json',
        'initial_middle3_alignment_v1/native/initial_values.json', 'multi_face_grip_v3/search.json'))
    cache = Path(os.environ['TORCH_EXTENSIONS_DIR'])/'gymtorch/gymtorch.so'
    paths.add(cache)
    if args.candidate is not None: paths.add(args.candidate.resolve())
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    source = out/'source_before'; source.mkdir()
    for p in sorted(paths):
        if p.suffix in ('.py', '.md', '.xml') and root/'stability_adapter_2' in p.parents:
            target = source/p.relative_to(root); target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
    (out/'inputs_before.json').write_text(json.dumps({'sha256': hashes, 'python': sys.executable,
        'environment': {k: os.environ.get(k) for k in ('PATH', 'TORCH_EXTENSIONS_DIR', 'PYTHONPATH', 'LD_LIBRARY_PATH',
            'VK_ICD_FILENAMES', 'MUJOCO_GL', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'PYTHONDONTWRITEBYTECODE')},
        'scope': 'conservative source/data superset; source snapshots before task import; no checkpoint copy'}, indent=2)+'\n')
    original_argv = sys.argv
    error = None
    try:
        module = 'run_human_pd_actuation_probe_v2'
        sys.argv = [module, '--out', str(out/'data')]
        if args.candidate is not None: sys.argv += ['--candidate',str(args.candidate.resolve())]
        sys.argv += ['--torque',str(args.torque)]
        runpy.run_module('stability_adapter_2.'+module, run_name='__main__')
    except BaseException as exc:
        error = str(exc)
        raise
    finally:
        sys.argv = original_argv
        changed = [p for p, h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
        (out/'inputs_after.json').write_text(json.dumps({'inputs_unchanged': not changed, 'changed': changed,
            'input_count': len(hashes), 'task_error': error}, indent=2)+'\n')
        if changed: raise RuntimeError('consumed input changed: '+str(changed))


if __name__ == '__main__': main()
