"""Finalize after the first seal's redirected console log has closed."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    previous = json.loads((PHASE/'artifact_inventory.json').read_text())
    changed = [p for p,d in previous['files'].items() if sha(p)!=d['sha256']]
    assert changed == [str(PHASE/'final_seal.log')]
    assert json.loads((PHASE/'final_verification.json').read_text())['recording_5s_complete']
    assert sha(PHASE/'review.md') == previous['review_sha256']
    source = PHASE/'inventory_v2_source'; source.mkdir(exist_ok=False)
    shutil.copy2(Path(__file__).resolve(),source/Path(__file__).name)
    # This pass is not redirected into the phase: all listed files are already closed.
    files = {str(p): {'sha256':sha(p),'bytes':p.stat().st_size}
             for p in sorted(PHASE.rglob('*')) if p.is_file()}
    inventory = PHASE/'artifact_inventory_v2.json'
    inventory.write_text(json.dumps({'files':files,'excludes':['artifact_inventory_v2.json','final_verification_v2.json'],
        'supersedes':str(PHASE/'artifact_inventory.json'),'review_sha256':sha(PHASE/'review.md')},indent=2)+'\n')
    final = PHASE/'final_verification_v2.json'
    final.write_text(json.dumps({'preservation_pass':True,'artifact_files':len(files),
        'previous_inventory_only_live_log_changed':changed,
        'reason':'previous seal hashed redirected console log before its final print; v1 preserved',
        'inventory_sha256':sha(inventory),'native_verification':str(PHASE/'final_verification.json'),
        'review_sha256':sha(PHASE/'review.md'),'producer_sha256':sha(Path(__file__))},indent=2)+'\n')
    assert all(sha(p)==d['sha256'] for p,d in files.items())
    print(json.dumps({'artifact_files':len(files),'preservation_pass':True}))


if __name__ == '__main__': main()
