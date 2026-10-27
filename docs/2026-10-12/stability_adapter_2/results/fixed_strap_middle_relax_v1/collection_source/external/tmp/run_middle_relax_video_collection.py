from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
r=Path('/home/ajou/yigyu/3');a=r/'stability_adapter_2';d=r/'docs/2026-10-12/stability_adapter_2';p=d/'results/fixed_strap_middle_relax_v1'
assert not (p/'collection_execution.json').exists()
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
source=a/'collect_middle_relax_videos.py';ast.parse(source.read_text(),feature_version=(3,8))
paths=[source,Path(__file__).resolve(),d/'VIDEO_INDEX_v7.md',p/'native/report.json',p/'native/videos.json']+list((d/'videos').glob('*.mp4'))+[p/'native/whole_body.mp4',p/'native/hands.mp4']
before={str(f):sha(f) for f in paths};manifest={}
for f in paths[:5]:
 rel=f.relative_to(r) if f.is_relative_to(r) else Path('external')/f.relative_to('/')
 dst=p/'collection_source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);assert sha(dst)==before[str(f)];manifest[str(f)]={'snapshot':str(dst),'sha256':sha(dst)}
(p/'collection_source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
cmd=[sys.executable,str(source)]
result=subprocess.run(cmd,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(p/'collection.log').write_text(result.stdout)
after={str(f):sha(f) for f in paths}
(p/'collection_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(p/'collection.log')),indent=2)+'\n')
print(result.stdout);assert result.returncode==0 and before==after
