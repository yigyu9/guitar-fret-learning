from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re

meeting = Path(__file__).resolve().parents[1]
manifest = json.loads((meeting / 'MATERIAL_MANIFEST.json').read_text())
shortlist = json.loads((meeting / 'SHORTLIST_MANIFEST.json').read_text())
records = manifest['records']
errors = []
ids = {}
for record in records:
    rid = record['id']
    if rid in ids:
        errors.append(f'duplicate ID: {rid}')
    ids[rid] = record
    path = Path(record['destination'])
    if not path.is_relative_to(meeting):
        errors.append(f'outside Meeting: {rid}')
        continue
    if not path.is_file():
        errors.append(f'missing file: {rid}')
        continue
    if path.stat().st_size != record['bytes']:
        errors.append(f'size mismatch: {rid}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != record['sha256']:
        errors.append(f'hash mismatch: {rid}')
counts = dict(Counter(record['kind'] for record in records))
if counts != manifest['counts']:
    errors.append('manifest count mismatch')
if sum(record['bytes'] for record in records) != manifest['total_bytes']:
    errors.append('manifest total bytes mismatch')
for kind, key in [('video', 'videos'), ('image', 'images')]:
    for entry in shortlist[key]:
        record = ids.get(entry['id'])
        if not record or record['kind'] != kind:
            errors.append(f'invalid shortlist entry: {entry}')
if shortlist['missing_requested_source_paths']:
    errors.append('unresolved shortlist source paths')
checked_links = 0
for document in sorted(meeting.glob('*.md')):
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', document.read_text()):
        target = target.strip('<>')
        if target.startswith(('http:', 'https:')):
            continue
        path = Path(re.sub(r':\d+$', '', target.split('#')[0]))
        if not path.is_absolute():
            path = document.parent / path
        checked_links += 1
        if not path.exists():
            errors.append(f'broken link in {document.name}: {target}')
result = {
    'checked_utc': datetime.now(timezone.utc).isoformat(),
    'passed': not errors,
    'counts': counts,
    'checked_file_hashes': len(records),
    'checked_top_level_markdown_links': checked_links,
    'shortlist_videos': len(shortlist['videos']),
    'shortlist_images': len(shortlist['images']),
    'errors': errors,
    'notes': [
        'Copied files match hashes recorded during collection.',
        'Original copied documents retain their text and may contain links relative to their original location.',
        'Running main-thread work was not changed; this collection is a snapshot.'
    ],
}
(meeting / 'COLLECTION_VERIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['passed'] else 1)
