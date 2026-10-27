"""Seal the closed audit log without editing the consumed first inventory."""
from pathlib import Path
import hashlib
import json

P = Path(__file__).resolve().parent


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    target = P/'artifact_inventory_v2.json'
    assert not target.exists()
    original = json.loads((P/'artifact_inventory.json').read_text())
    changed = [p for p,v in original.items() if Path(p).stat().st_size != v['size'] or sha(p) != v['sha256']]
    assert changed == [str(P/'root_audit.log')], changed
    previous = json.loads((P/'final_verification.json').read_text())
    assert len(previous['checks']) == 27 and all(previous['checks'].values())
    notes = dict(original_verification=str(P/'final_verification.json'),original_inventory=str(P/'artifact_inventory.json'),
        checks=dict(original27_checks_pass=True,only_closed_stdout_log_differs=True),
        correction='First audit inventory included its still-open stdout log before the final print. Original metadata preserved; v2 records the closed log and supplements. No source/search/artifact/physics rerun.',
        native_initializations=0,physical_steps=0)
    (P/'final_verification_v2.json').write_text(json.dumps(notes,indent=2)+'\n')
    paths = set(Path(p) for p in original)
    paths.update(p for p in P.rglob('*') if p.is_file() and p != target)
    inventory = {str(p):dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(paths,key=str)}
    target.write_text(json.dumps(inventory,indent=2)+'\n')
    assert all(Path(p).stat().st_size == v['size'] and sha(p) == v['sha256'] for p,v in inventory.items())
    print(json.dumps(dict(correction='closed stdout log sealed',files=len(inventory),checks27=True)))


if __name__ == '__main__': main()
