"""Retain the rejected native attempt and distinguish root/centre displacement."""
from pathlib import Path
import json
import hashlib
import subprocess
import numpy as np
from scipy.spatial.transform import Rotation

P=Path(__file__).resolve().parent
N=P/'native_static_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    inputs={str(f):sha(f) for f in N.rglob('*') if f.is_file()}
    inputs[str(Path(__file__).resolve())]=sha(__file__);inputs.update(read(N/'attempt.json')['input_sha256'])
    report=read(N/'report.json');trace=read(N/'trace.json');rows=read(N/'media/physics_endpoint_contacts.json')['rows']
    assert not report['completed'] and report['physics_steps']==1148 and report['control_steps']==287 and not report['forbidden_calls']
    pos=np.array([r['position_W_m'] for r in trace]);rot=Rotation.from_quat([r['quaternion_xyzw'] for r in trace])
    # This physical-body bbox centre is fixed in the unchanged OM3 asset.
    centre=np.array([0,-.4,-.055937985]);body=pos+rot.apply(np.repeat(centre[None],len(trace),axis=0))
    videos=[]
    for view in ('whole_body','hands'):
        f=N/'media'/(view+'.mp4');stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,avg_frame_rate,duration','-of','json',str(f)]))['streams'][0]
        videos.append({'path':str(f),'sha256':sha(f),'stream':stream})
    result={'input_sha256':inputs,'case':str(N),'completed':False,'physics_steps':1148,'control_steps':287,'physics_seconds':report['physics_seconds'],
        'failure':report['failure'],'root_max_displacement_mm':float(np.linalg.norm(pos-pos[0],axis=1).max()*1000),'body_bbox_centre_max_displacement_mm':float(np.linalg.norm(body-body[0],axis=1).max()*1000),
        'final_SO3_deg':float(np.rad2deg((rot[0].inv()*rot[-1]).magnitude())),
        'contacts':{key:{'presence_steps':sum(bool(r[key]) for r in rows),'last120_presence_steps':sum(bool(r[key]) for r in rows[-120:])} for key in ('right_thorax_body_contacts','right_upper_arm_body_contacts','right_hip_body_contacts','left_arm_hand_guitar_contacts')},
        'videos':videos,'scope':'initial scene passed but free guitar drifted; root translation20cm guard, not35deg guard; partial retained, not five-second success'}
    assert all(sha(p)==h for p,h in inputs.items())
    with (P/'partial_analysis_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)

if __name__=='__main__':main()
