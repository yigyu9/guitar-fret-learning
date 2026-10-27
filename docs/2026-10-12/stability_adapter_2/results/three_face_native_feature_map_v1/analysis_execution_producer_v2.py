import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1';S=R/'stability_adapter_2/analyze_three_face_native_features_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'analysis_execution_v2.json').exists()
expected=json.loads((P/'input_manifest_v2.json').read_text())['input_sha256'][str(S)];assert sha(S)==expected
shutil.copyfile(S,P/'analysis_source_v2.py');shutil.copyfile(__file__,P/'analysis_execution_producer_v2.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_three_face_native_features_v2'];t=time.monotonic()
with (P/'analysis_v2.log').open('w') as log:res=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
metadata={'command':cmd,'exit_code':res.returncode,'wall_seconds':time.monotonic()-t,'producer_sha256_before':expected,'producer_sha256_after':sha(S),'log_sha256':sha(P/'analysis_v2.log'),'native_calls':0}
(P/'analysis_execution_v2.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'analysis_v2.log').read_text()[-3500:]);raise SystemExit(res.returncode)
