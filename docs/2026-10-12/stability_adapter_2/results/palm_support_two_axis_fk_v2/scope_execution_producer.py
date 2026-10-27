import json,hashlib,shutil,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2';source=R/'stability_adapter_2/assess_palm_runtime_fk_scope.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
shutil.copyfile(source,P/'scope_source.py');shutil.copyfile(__file__,P/'scope_execution_producer.py');before=sha(source);cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.assess_palm_runtime_fk_scope'];start=time.monotonic()
with (P/'scope.log').open('wb') as log:r=subprocess.run(cmd,cwd=str(R),stdout=log,stderr=subprocess.STDOUT)
e=dict(command=cmd,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/'scope.log'),native_calls=0);(P/'scope_execution.json').write_text(json.dumps(e,indent=2)+'\n');print(r.returncode,(P/'scope.log').read_text());assert r.returncode==0 and e['source_sha256_before']==e['source_sha256_after']
