from pathlib import Path
import ast,hashlib,json,os,shutil,subprocess,time
r=Path('/home/ajou/yigyu/3');a=r/'stability_adapter_2';p=r/'docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2'
assert not (p/'analysis_execution.json').exists() and not (p/'analysis.json').exists()
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
sources=[a/n for n in ['analyze_fixed_strap_middle_relax_v2.py','analyze_natural_envelope.py','analyze_small_wrist_motion.py','analyze_body9_strap_minus4mm.py','strap.py','warmstart_targets.py','build_fixed_lower_asset.py','environment.py','FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md']]+[Path(__file__).resolve()]
ast.parse(sources[0].read_text(),feature_version=(3,8))
paths=sources+[p/n for n in ['native_execution.json','proposal.json','preparation.json']]+[p.parent/'fixed_strap_middle_relax_v1/preparation.json']
for folder in [p/'native',p.parent/'joint_only_fixed_strap_v1/native',p.parent/'fixed_strap_middle_relax_v1/native']:
 paths += [folder/n for n in ['initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json','initial_grip_audit.json']]
before={str(f):sha(f) for f in paths};manifest={}
for f in sources:
 rel=f.relative_to(r) if f.is_relative_to(r) else Path('external')/f.relative_to('/')
 dst=p/'analysis_source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);assert sha(dst)==before[str(f)];manifest[str(f)]={'snapshot':str(dst),'sha256':sha(dst)}
(p/'analysis_source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_fixed_strap_middle_relax_v2'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',PYTHONPATH=str(r/'isaacgym/python')+':'+str(r),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (p/'analysis.log').open('xb') as log:result=subprocess.run(cmd,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
after={str(f):sha(f) for f in paths}
(p/'analysis_execution.json').write_text(json.dumps(dict(command=cmd,environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','PYTHONPATH','LD_LIBRARY_PATH']},exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(p/'analysis.log')),indent=2)+'\n')
print((p/'analysis.log').read_text()[-7000:]);assert result.returncode==0 and before==after
