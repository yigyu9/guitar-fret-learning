import ast,hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'strap_video_v1';old=B/'three_face_near_contact_diagnostic_v1';runner=R/'stability_adapter_2/run_strap_recorded_diagnostic.py';helper=R/'stability_adapter_2/strap_trial_recording.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def node(source,kind):
 tree=ast.parse(source)
 return next(n for n in ast.walk(tree) if (kind=='observe' and isinstance(n,ast.FunctionDef) and n.name=='observe') or (kind=='loop' and isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step' and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='range' and ast.literal_eval(n.iter.args[0])==1200))
checks={k+'_AST_unchanged':ast.dump(node(runner.read_text(),k),include_attributes=False)==ast.dump(node((P/'previous_native_runner_source.py').read_text(),k),include_attributes=False) for k in ('observe','loop')}
import sys
sys.path.insert(0,str(R))
from stability_adapter_2.strap_trial_recording import project,draw_route
import numpy as np
view=np.eye(4);proj=np.zeros((4,4));proj[0,0]=proj[1,1]=1.;proj[2,3]=-1.
uv,z,valid=project(np.array([[0,0,-1],[.5,0,-1],[0,.5,-1],[0,0,1]]),view,proj,1280,720)
checks['pinhole_center_right_up_behind']=np.array_equal(uv[:3],[[640,360],[960,360],[640,180]]) and valid.tolist()==[True,True,True,False]
from PIL import Image
raw=P/'numeric_source.png';Image.new('RGB',(1280,720),(60,60,60)).save(raw);points=np.column_stack((np.linspace(-.3,.3,13),np.zeros(13),np.full(13,-1.)))
v=draw_route(raw,P/'numeric_visible.png',points,view,proj,np.full((720,1280),-2.),1.1);o=draw_route(raw,P/'numeric_occluded.png',points,view,proj,np.full((720,1280),-.5),1.1)
checks['negative_depth_visible_vs_occluded']=v['visible_samples']>0 and v['occluded_samples']==0 and o['visible_samples']==0 and o['occluded_samples']>0
assert all(checks.values());before={str(p):sha(p) for p in [runner,helper,R/'stability_adapter_2/STRAP_VIDEO_VISUALIZATION_PLAN.md',R/'stability_adapter_2/gym_trial_recording.py',R/'stability_adapter_2/capture_isaac_gym_initial.py',old/'original_targets_proposal.json',R/'stability_adapter_2/trials/three_face_near_contact_diagnostic_v1/original_targets.json',Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]}
(P/'root_preflight.json').write_text(json.dumps(dict(checks=checks,input_sha256=before,numeric_visible=v,numeric_occluded=o,independent_review=False,scope='root projection/depth branches and unchanged real1200 control/observe loop; no added physics'),indent=2)+'\n');shutil.copyfile(runner,P/'native_runner_source.py');shutil.copyfile(helper,P/'recording_helper_source.py');shutil.copyfile(__file__,P/'execution_producer.py')
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_strap_recorded_diagnostic','--trial',str(R/'stability_adapter_2/trials/three_face_near_contact_diagnostic_v1/original_targets.json'),'--proposal',str(old/'original_targets_proposal.json'),'--out',str(P/'native')]
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (P/'native.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'native.log'))
(P/'execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(dict(exit_code=result.returncode,wall_seconds=metadata['wall_seconds'],checks=checks),indent=2));print((P/'native.log').read_text()[-3000:]);assert result.returncode==0 and metadata['input_sha256_before']==metadata['input_sha256_after']
