"""Preserve failed native run and incomplete analysis without treating either as a pass."""
from pathlib import Path
import hashlib
import json
import subprocess

P = Path(__file__).resolve().parent
N = P/'native_static_body9_effort'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    partial = P/'native_analysis_low_v1.json'
    suffix = partial.read_text().split('"input_sha256":', 1)[1].lstrip()
    recovered, _ = json.JSONDecoder().raw_decode(suffix)
    inputs = {str(p):sha(p) for p in N.rglob('*') if p.is_file()}
    inputs.update({str(p):sha(p) for p in [Path(__file__).resolve(),partial,P/'native_analysis_low_v2.json']})
    inputs.update(recovered); inputs.update(read(N/'attempt.json')['input_sha256'])
    assert all(sha(p) == h for p,h in inputs.items())
    report, state = read(N/'report.json'), read(N/'final_state.json')
    assert not report['completed'] and report['physics_steps'] == 5 and not report['forbidden_calls']
    videos = []
    for view in ['whole_body','hands']:
        f = N/'media'/(view+'.mp4')
        stream = read_stream = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
            '-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',str(f)]))['streams'][0]
        assert stream['nb_read_frames'] == '2' and stream['r_frame_rate'] == '30/1'
        videos.append({'path':str(f),'sha256':sha(f),'stream':stream})
    result = {'input_sha256':inputs,'native_failure':{'case':str(N),'physics_steps':5,'control_ticks':1,
        'physics_s':report['physics_seconds'],'reason':report['failure']['message'],
        'maximum_final_qdot_rad_s':max(abs(s['vel']) for s in state['human_dof_states']),
        'input_SHA_preserved':True,'forbidden_calls':[],'videos':videos},
        'analysis_failure':{'file':str(partial),'sha256':sha(partial),
            'reason':'NumPy bool serialization; incomplete file preserved; native_analysis_low_v2.json is the complete retry',
            'complete_result':False,'recovered_complete_input_sha256':recovered}}
    assert all(sha(p) == h for p,h in inputs.items())
    with (P/'failure_audit_v2.json').open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)


if __name__ == '__main__': main()
