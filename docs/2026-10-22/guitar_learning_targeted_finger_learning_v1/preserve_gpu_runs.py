"""Preserve short-run source bytes and verify every compressed archive member."""
import hashlib
import json
import lzma
import os
from pathlib import Path
import shutil
import tarfile

PHASE=Path(__file__).resolve().parent
RUNS=Path('/dev/shm/guitar_learning_targeted_finger_v8_20261022')

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

files={str(p.relative_to(RUNS)):dict(sha256=digest(p),bytes=p.stat().st_size)
       for p in sorted(RUNS.rglob('*')) if p.is_file()}
assert files and all((RUNS/name).is_file() for name in ('gpu_smoke8/final.pt','gpu_resume1/final.pt'))
archive=PHASE/'gpu_runs.tar.xz'
assert not archive.exists()
with lzma.open(archive,'wb',filters=[dict(id=lzma.FILTER_LZMA2,preset=1,dict_size=128*1024*1024)]) as compressed:
    with tarfile.open(fileobj=compressed,mode='w|') as tar:
        for name in files:tar.add(RUNS/name,arcname=name,recursive=False)
with archive.open('rb') as stream:os.fsync(stream.fileno())
seen=set()
with tarfile.open(archive,'r|xz') as tar:
    for member in tar:
        assert member.isfile() and member.name in files and member.name not in seen
        h=hashlib.sha256();stream=tar.extractfile(member)
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        assert member.size==files[member.name]['bytes'] and h.hexdigest()==files[member.name]['sha256']
        seen.add(member.name)
assert seen==set(files)
for name in files:
    if not name.endswith('.pt'):
        destination=PHASE/name;destination.parent.mkdir(parents=True,exist_ok=True)
        assert not destination.exists();shutil.copy2(RUNS/name,destination)
result=dict(completed=True,source_root=str(RUNS),archive=str(archive),archive_sha256=digest(archive),
            archive_bytes=archive.stat().st_size,uncompressed_bytes=sum(v['bytes'] for v in files.values()),
            verified_members=len(seen),files=files,scope='Exact source-byte preservation; no performance claim')
(PHASE/'gpu_runs_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
fd=os.open(str(PHASE),os.O_RDONLY);os.fsync(fd);os.close(fd)
print('PASS:',len(seen),'archive members verified;',archive.stat().st_size,'compressed bytes',flush=True)
