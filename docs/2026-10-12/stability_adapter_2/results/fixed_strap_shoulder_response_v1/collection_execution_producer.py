from pathlib import Path
import hashlib,json,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';P=D/'results/fixed_strap_shoulder_response_v1';source=A/'collect_fixed_strap_shoulder_videos.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'collection_execution.json').exists()
inputs=[source,D/'VIDEO_INDEX_v6.md']+[P/l/'report.json' for l in ['minus008','plus008']]
for label in ['minus008','plus008']:
 inputs += [Path(v['path']) for v in json.loads((P/label/'report.json').read_text())['videos'].values()]
before={str(p):sha(p) for p in inputs};shutil.copy2(source,P/'collection_source.py');shutil.copy2(__file__,P/'collection_execution_producer.py');assert sha(source)==sha(P/'collection_source.py')
cmd=['python','-m','stability_adapter_2.collect_fixed_strap_shoulder_videos'];start=time.monotonic()
with (P/'collection.log').open('xb') as log:result=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
after={str(p):sha(p) for p in inputs}
(P/'collection_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,source_sha256_before=before[str(source)],source_sha256_after=sha(source),log_sha256=sha(P/'collection.log')),indent=2)+'\n')
assert result.returncode==0 and before==after
print((P/'collection.log').read_text())
