"""Snapshot native/search inputs before import; keep each attempt immutable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('search','settle','fret'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--native',type=Path)
    parser.add_argument('--support',choices=('OFF','ON'),default='OFF')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]; out = args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    A = root/'stability_adapter_2'; D = root/'docs/2026-10-12/stability_adapter_2/results'
    paths = {p for p in A.rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json','.xml')}
    paths.update(p for p in (root/'tab2body').rglob('*.py') if p.is_file())
    paths.update(p for p in (root/'tab2body/assets').rglob('*') if p.is_file())
    paths.update(p for p in (root/'isaacgym/python/isaacgym').rglob('*') if p.is_file() and p.suffix in ('.py','.so'))
    paths.update(p for directory in ('initial_middle3_alignment_v1/native','multi_face_grip_v3',
                                    'underneck_initial_pose_v1/refine')
                 for p in (D/directory).rglob('*.json'))
    paths.add(args.candidate.resolve())
    paths.add(Path(os.environ['TORCH_EXTENSIONS_DIR'])/'gymtorch/gymtorch.so')
    paths.update(root/p for p in ('tab2body/_gen/mjcf_gains.json',
        'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt',
        'data/song_bundles/02_Jazz1-200-B_solo/training/fret_training.json',
        'data/song_bundles/02_Jazz1-200-B_solo/training/hand_position_targets.json'))
    if args.native: paths.update(p for p in args.native.resolve().glob('*.json') if p.is_file())
    hashes = {str(p):sha(p) for p in sorted(paths)}
    for p in sorted(paths):
        if A in p.parents:
            target = out/'source_before'/p.relative_to(root); target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
    (out/'inputs_before.json').write_text(json.dumps(dict(sha256=hashes,python=sys.executable,
        environment={k:os.environ.get(k) for k in ('PYTHONPATH','LD_LIBRARY_PATH','TORCH_EXTENSIONS_DIR',
        'VK_ICD_FILENAMES','MUJOCO_GL','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','PYTHONDONTWRITEBYTECODE')},
        mode=args.mode),indent=2)+'\n')
    modules = dict(search='palm_thumb_support_search_v2',settle='run_palm_thumb_posture_support_v1',fret='run_palm_thumb_fret_v1')
    module = 'stability_adapter_2.'+modules[args.mode]; error = None; returncode = None
    try:
        command = [sys.executable,'-X','faulthandler','-m',module,'--out',str(out/'data'),'--candidate',str(args.candidate.resolve())]
        if args.mode=='search':
            if args.native is None: raise ValueError('search needs --native')
            command += ['--native',str(args.native.resolve())]
        else: command += ['--support',args.support]
        with (out/'process.log').open('x') as log:
            process = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        returncode = process.returncode
        if returncode: raise RuntimeError('child exit code '+str(returncode))
    except BaseException as exc:
        error = str(exc); raise
    finally:
        changed = [p for p,h in hashes.items() if not Path(p).is_file() or sha(Path(p))!=h]
        (out/'inputs_after.json').write_text(json.dumps(dict(input_count=len(hashes),inputs_unchanged=not changed,
            changed=changed,task_error=error,returncode=returncode),indent=2)+'\n')
        if changed: raise RuntimeError('consumed inputs changed '+str(changed))


if __name__=='__main__': main()
