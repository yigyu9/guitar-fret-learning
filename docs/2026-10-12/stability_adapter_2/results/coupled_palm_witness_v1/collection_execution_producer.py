from pathlib import Path
import hashlib,json,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1';s=R/'stability_adapter_2/collect_palm_witness_videos.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'collection_execution.json').exists()
before=sha(s);shutil.copy2(s,P/'collection_source.py');shutil.copy2(__file__,P/'collection_execution_producer.py');start=time.monotonic();cmd=['python','-m','stability_adapter_2.collect_palm_witness_videos']
with (P/'collection.log').open('wb') as f:r=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
(P/'collection_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(s),log_sha256=sha(P/'collection.log'),native_initializations=0,physics_steps=0),indent=2)+'\n')
print(r.returncode,(P/'collection.log').read_text());assert r.returncode==0 and sha(s)==before
