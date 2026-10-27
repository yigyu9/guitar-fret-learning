"""Verify saved 5s recording, raw coverage, encoded videos and controlled stop."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    out=PHASE/'verification.json'
    if out.exists():raise FileExistsError('preserve earlier verification')
    p=PHASE/'baseline/report.json';hashes={str(p):sha(p)};report=read(p)
    p=PHASE/'baseline/capture.json';hashes[str(p)]=sha(p);capture=read(p)
    paths=[Path(p) for p in report['input_sha256']]+[Path(__file__).resolve(),PHASE/'execution.json',PHASE/'stop_execution.json',PHASE/'baseline/initial_values.json',PHASE/'baseline/videos.json',PHASE/'stop_check/report.json',PHASE/'stop_check/capture.json']
    paths += [PHASE/'baseline'/(n+'.jsonl') for n in ('states','trace','tasks','contacts','controls')]
    paths += [Path(p) for f in capture['frames'] for p in f['image_sha256']]+[Path(v['path']) for v in report['videos'].values()]
    hashes.update({str(p):sha(p) for p in paths})
    initial=read(PHASE/'baseline/initial_values.json');raw={n:[json.loads(s) for s in (PHASE/'baseline'/(n+'.jsonl')).read_text().splitlines()] for n in ('states','trace','tasks','contacts','controls')}
    if len(raw['states'])!=1201 or any(len(raw[n])!=1201 for n in ('trace','tasks')) or any(len(raw[n])!=1200 for n in ('contacts','controls')):raise AssertionError('raw coverage')
    if raw['states'][0]!=initial['native_initial_state'] or initial['actual_initial_angles_rad']!={n:d['pos'] for n,d in zip(initial['human_joint_names'],raw['states'][0]['human_dof_states'])}:raise AssertionError('initial values')
    if any(s['physics_step']!=i for i,s in enumerate(raw['states'])) or any(abs(t['time_s']-i/240)>1e-9 for i,t in enumerate(raw['trace'])):raise AssertionError('raw time')
    if len(capture['frames'])!=151 or any(f['physics_step']!=i*8 or abs(f['time_s']-i/30)>1e-9 or not f['render_preserves_states'] for i,f in enumerate(capture['frames'])):raise AssertionError('capture coverage')
    if any(sha(p)!=h for f in capture['frames'] for p,h in f['image_sha256'].items()):raise AssertionError('native frame hash')
    videos={}
    for view,v in report['videos'].items():
        proc=subprocess.run(v['ffprobe_command'],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError('ffprobe failed')
        stream=json.loads(proc.stdout)['streams'][0]
        if stream!=v['stream'] or int(stream['nb_read_frames'])!=151 or stream['avg_frame_rate']!='30/1' or abs(float(stream['duration'])-151/30)>.002 or sha(v['path'])!=v['sha256']:raise AssertionError('encoded coverage/hash')
        videos[view]=stream
    reference=PHASE.parent/'palm_hold_pd_v2/scale_1/native'
    if any(raw[n][:25 if n in ('states','trace','tasks') else 24]!=read(reference/(n+'.json')) for n in raw):raise AssertionError('old prefix exact')
    stop=read(PHASE/'stop_execution.json');partial=read(PHASE/'stop_check/report.json');partial_capture=read(PHASE/'stop_check/capture.json')
    checks={'initial_values_and_continuous_raw':True,'actual151_frames0_to5_seconds':True,'two_encoded_videos_151_frames_30fps':len(videos)==2,
        'first24_five_arrays_exact':True,'native_completion_and_exit_zero':report['completed'] and all(report['checks'].values()) and read(PHASE/'execution.json')['exit_code']==0,
        'controlled_stop_partial_and_expected_exit':all(stop['checks'].values()) and not partial['completed'] and len(partial_capture['frames'])==partial['frame_count'],
        'native_inputs_unchanged':all(sha(p)==h for p,h in report['input_sha256'].items()),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    trace=raw['trace'];result={'checks':checks,'input_sha256':hashes,'counts':{'full_native_initializations':1,'full_physics_steps':1200,'stop_check_initializations':partial['native_initializations'],'stop_check_physics_steps':partial['physics_steps']},
        'summary':{'max_guitar_position_error_mm':max(t['position_error_m'] for t in trace)*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in trace),
            'end_guitar_position_error_mm':trace[-1]['position_error_m']*1000,'end_guitar_rotation_error_deg':trace[-1]['rotation_error_deg'],
            'end_point_error_mm':math.sqrt(sum(v*v for v in raw['tasks'][-1][:3]))*1000,'palm_up_proxy_violations':len(report['constraint_violations'])},
        'videos':videos,'scope':'saved-data verification; 5s recording complete is not guitar/pose stability success; stop check is separate partial initialization; native_initializations means completed constructors, attempts recorded separately'}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'counts':result['counts'],'summary':result['summary']},indent=2))


if __name__=='__main__':main()
