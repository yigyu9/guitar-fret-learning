from pathlib import Path
import ast,hashlib,json,os,shutil,subprocess,sys,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'configuration_execution.json').exists()
source=A/'verify_finger_map_configuration.py';ast.parse(source.read_text(),feature_version=(3,8))
files=[source,A/'FINGER_CONTACT_MAP_PLAN.md',A/'analyze_three_face_native_features_v2.py',A/'native_contacts.py',R/'isaacgym/docs/api/python/struct_py.html',A/'environment.py',A/'physics_presets.py',A/'fixed_lower_environment.py',A/'self_collision_environment.py',A/'capture_isaac_gym_initial.py',Path(__file__)]
manifest={}
for p in files:
 relative=p.relative_to(R) if p.is_relative_to(R) else Path('invocation')/p.name
 dest=P/'configuration_source_before'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);manifest[str(p)]=dict(snapshot=str(dest),sha256=sha(p))
(P/'configuration_source_before_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');before={str(p):sha(p) for p in files};cmd=[sys.executable,'-m','stability_adapter_2.verify_finger_map_configuration'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');started=time.monotonic()
with (P/'configuration.log').open('xb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
after={str(p):sha(p) for p in files};(P/'configuration_execution.json').write_text(json.dumps(dict(command=cmd,environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},exit_code=result.returncode,wall_seconds=time.monotonic()-started,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/'configuration.log')),indent=2)+'\n');print((P/'configuration.log').read_text());assert result.returncode==0 and before==after
