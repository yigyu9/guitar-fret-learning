"""Close the inventory after the previous sealer's stdout log has finished."""
from pathlib import Path
import hashlib
import json
P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1')
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def read(f):return json.loads(Path(f).read_text())
def save(n,d):
    f=P/n;assert not f.exists();f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
old=read(P/'final_verification_v1.json')
assert old['passed']
assert sha(P/'artifact_inventory_v1.json')==old['inventory_sha256']
assert sha(P/'source_final_v1.json')==old['source_final_sha256']
entries=read(P/'artifact_inventory_v1.json')['files']
bad=[e['path'] for e in entries if sha(e['path'])!=e['sha256']]
assert bad==[str(P/'seal_v2.log')],bad
# This file was open for stdout when v1 inventoried it, then received the completion line.
assert read(P/'seal_v2.log')['passed']
files={Path(e['path']) for e in entries}|{f for f in P.rglob('*') if f.is_file()}
manifest={'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(files)]}
save('artifact_inventory_v2.json',manifest)
save('final_verification_v2.json',{**old,'inventory_sha256':sha(P/'artifact_inventory_v2.json'),'inventory_path':str(P/'artifact_inventory_v2.json'),'prior_seal_preserved':True,'prior_seal_log_open_file_correction':str(P/'seal_v2.log'),'other_v1_inventory_entries_unchanged':len(entries)-1,'closure_source_sha256':sha(__file__),'closure_note':'v1 inventory was captured before its stdout log closed; v2 pins the closed log and preserves v1 records; no source/native changes'})
for e in manifest['files']:assert sha(e['path'])==e['sha256']
print(json.dumps({'passed':True,'sealed_files':len(manifest['files']),'all_hashes_exact_after_write':True}))
