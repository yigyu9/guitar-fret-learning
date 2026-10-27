"""Audit historical closure preservation with explicitly appended main documents."""
import hashlib,json
from pathlib import Path
R=Path('/home/ajou/yigyu/3');G=R/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((G/'old_training_stop_snapshot_v1.json').read_text())['input_sha256']
main=json.loads((G/'main_append_resume_v1.json').read_text())
checks={};exceptions={}
for path,expected in old.items():
    actual=sha(path)
    if actual==expected:checks[path]=True
    elif path in main:
        n=list(main).index(path);before=(G/'main_before_v1'/('%d_%s'%(n,Path(path).name))).read_bytes()
        checks[path]=hashlib.sha256(before).hexdigest()==expected and Path(path).read_bytes().startswith(before)
        exceptions[path]='main document appended after old native completion; original prefix snapshot matches old input SHA'
    else:checks[path]=False
for n,path in enumerate(main):
    before=(G/'main_before_resume_v1'/('%d_%s'%(n,Path(path).name))).read_bytes()
    checks['second_prefix:'+path]=Path(path).read_bytes().startswith(before) and sha(path)==main[path]['after_sha256']
result={'passed':all(checks.values()),'old_input_count':len(old),'checks':checks,'explicit_append_exceptions':exceptions,
    'scope':'all old native input closure hashes preserved except approved main append with exact prefix; no deletion/source/asset edit'}
with (G/'preservation_verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'passed':result['passed'],'old_input_count':len(old),'append_exceptions':list(exceptions)},ensure_ascii=False))
assert result['passed']
