from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1';s=A/'collect_joint_only_fixed_strap_videos.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'collection_execution.json').exists();before=sha(s);shutil.copy2(s,P/'collection_source.py');shutil.copy2(__file__,P/'collection_execution_producer.py')
cmd=['/home/ajou/miniconda3/bin/python','-u',str(s)];t=time.monotonic()
with (P/'collection.log').open('xb') as log:r=subprocess.run(cmd,cwd=R,env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT)
(P/'collection_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,wall_seconds=time.monotonic()-t,source_sha256_before=before,source_sha256_after=sha(s),log_sha256=sha(P/'collection.log')),indent=2)+'\n')
assert r.returncode==0 and sha(s)==before;print((P/'collection.log').read_text())
