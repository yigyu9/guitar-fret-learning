"""Independently verify the original snapshot and each mirrored video copy."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


inventory = ROOT/'root_source_inventory_before_v1.json'
expected = json.loads(inventory.read_text())
failures = []
verified = []
for source, record in expected['files'].items():
    destination = ROOT/'archive_v1'/record['relative_path']
    if not destination.is_file():
        failures.append({'source': source, 'reason': 'copy missing'})
        continue
    source_hash, copy_hash = sha(source), sha(destination)
    if source_hash != record['sha256'] or copy_hash != record['sha256']:
        failures.append({'source': source, 'destination': str(destination),
                         'reason': 'snapshot/source/copy SHA mismatch'})
    else:
        verified.append({'source': source, 'destination': str(destination),
                         'sha256': copy_hash, 'bytes': destination.stat().st_size})
result = {'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'videos in the independent pre-copy inventory; original encoded files only',
    'snapshot_count': len(expected['files']), 'verified_count': len(verified),
    'unique_content_count': len({item['sha256'] for item in verified}),
    'copied_bytes': sum(item['bytes'] for item in verified),
    'originals_and_copies_match_snapshot': not failures, 'failures': failures,
    'source_inventory_sha256': sha(inventory), 'producer_sha256': sha(__file__),
    'verified': verified}
(ROOT/'root_final_verification_v1.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: result[key] for key in ('snapshot_count', 'verified_count',
    'unique_content_count', 'copied_bytes', 'originals_and_copies_match_snapshot')}))
if failures:
    raise SystemExit('Archive verification failed; inspect preserved failure details.')
