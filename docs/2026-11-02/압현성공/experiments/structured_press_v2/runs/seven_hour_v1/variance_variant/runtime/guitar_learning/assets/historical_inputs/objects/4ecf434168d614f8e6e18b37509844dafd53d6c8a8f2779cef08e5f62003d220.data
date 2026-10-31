"""Snapshot all direct/reused analysis inputs before importing the analyzer."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import sys


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=Path,required=True)
    parser.add_argument('--version',choices=('arm','support'),required=True)
    args=parser.parse_args();phase=args.phase.resolve();root=Path(__file__).resolve().parents[1]
    audit=phase/'analysis_verified_audit';audit.mkdir(exist_ok=False)
    A=root/'stability_adapter_2';results=root/'docs/2026-10-12/stability_adapter_2/results'
    paths={p for p in A.rglob('*') if p.is_file() and p.suffix in ('.py','.md','.xml','.json')}
    runs=[phase/'ON/data',phase/'OFF/data' if args.version=='arm' else results/'fret_current_guitar_arm_v1/OFF/data']
    for directory in runs:
        paths.update(p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.json','.png'))
    paths.update([results/'initial_middle3_alignment_v1/native/initial_values.json',
        results/'fret_fingers_arm_hold_v1/native/data/controls.json',results/'fret_fingers_arm_hold_v1/native/data/trace.json',
        root/'tab2body/fret_v2_contract.py',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')])
    hashes={str(p):sha(p) for p in sorted(paths)}
    (audit/'inputs_before.json').write_text(json.dumps(hashes,indent=2)+'\n')
    source=audit/'source_before'
    for p in sorted(paths):
        if A in p.parents or p==root/'tab2body/fret_v2_contract.py':
            target=source/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    module='stability_adapter_2.analyze_fret_current_guitar_'+('arm_verified' if args.version=='arm' else 'support_v2_verified')
    previous=sys.argv
    try:
        sys.argv=[module,'--phase',str(phase),'--out',str(phase/'analysis_verified')]
        runpy.run_module(module,run_name='__main__')
    finally:
        sys.argv=previous
        changed=[p for p,h in hashes.items() if sha(Path(p))!=h]
        (audit/'inputs_after.json').write_text(json.dumps(dict(input_count=len(hashes),inputs_unchanged=not changed,changed=changed),indent=2)+'\n')
        if changed:raise RuntimeError('analysis consumed input changed')


if __name__=='__main__':main()
