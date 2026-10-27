"""Inspect native video encoding, endpoint integrity and finite captured poses."""
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_large_until0900_v1')
VIDEO=ROOT/'analysis/video_final_framed'
metadata=json.loads((VIDEO/'capture_metadata.json').read_text())
report=json.loads((VIDEO/'report.json').read_text())
pose=np.load(VIDEO/'poses_env0000.npz')
finite={key:bool(np.isfinite(pose[key]).all()) for key in pose.files}
physics=pose['physics_step'].reshape(-1)
endpoint_ok=bool(np.array_equal(physics,np.arange(1,len(physics)+1)*4))
checks={}
for name in ('hand','fullbody'):
    path=VIDEO/(name+'.mp4')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-count_frames','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration',
        '-of','json',str(path)]))['streams'][0]
    duration=float(probe['duration'])
    for label,t in (('mid',duration/2),('last',max(0,duration-.1))):
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-ss',str(t),'-i',str(path),
            '-frames:v','1','-threads','1',str(VIDEO/(name+'_'+label+'.png'))],check=True)
    checks[name]=dict(probe=probe,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
checks.update(native_report_completed=report['completed'],policy_unchanged=report['policy_unchanged'],
    source_pins_unchanged=report['source_pins_unchanged'],source_checkpoint_pins_validated=report['source_checkpoint_pins_validated'],
    scene_closed=report['scene_closed'],lifecycle_verified=report['lifecycle_verified'],
    encoding_exit_codes=report['encoding_exit_codes'],cleanup_errors=report['cleanup_errors'],
    finite_pose_arrays=finite,physics_endpoints_in_sequence=endpoint_ok,captured_control_endpoints=len(physics),
    frame_count_matches=all(int(checks[name]['probe']['nb_read_frames'])==metadata['frames'] for name in ('hand','fullbody')),
    recorded_environment=metadata['environment'],selection=metadata['selection'],
    actual_achieved_notes=metadata['actual_achieved_notes'],actual_target_count=metadata['actual_target_count'],
    captured_duration_s=metadata['captured_control_duration_s'],video_duration_s=metadata['video_duration_s'],
    visual_inspection='pending native mid/last frame inspection')
(ROOT/'support/final_framed_video_verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(checks,ensure_ascii=False,indent=2))
