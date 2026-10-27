#!/usr/bin/env python3
"""Byte-exact packaging of approved native elbow/wrist ready-pose outputs."""
import hashlib, json, shutil, subprocess
from pathlib import Path

P = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1')
A = P / 'artifacts_v1'
V = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1')
PIN = A / 'preflight_pin_v1.json'
CASES = ('native_static_v1', 'native_strike_v1', 'native_velocity_v1')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def ffprobe(path):
    r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)],check=True,capture_output=True,text=True)
    d=json.loads(r.stdout)
    if len(d.get('streams',[])) != 1: raise RuntimeError(f'expected one video stream: {path}')
    return d['streams'][0]

if not A.is_dir() or not V.is_dir(): raise RuntimeError('owned destination directories missing')
if not PIN.is_file(): raise RuntimeError('preflight pin missing; refuse unpinned execution')
pin=json.loads(PIN.read_text())
self_path=Path(__file__).resolve()
if pin['producer_path'] != str(self_path) or pin['producer_sha256_before'] != sha(self_path): raise RuntimeError('producer pre-pin mismatch')
for p,h in pin['inputs_before'].items():
    if sha(p) != h: raise RuntimeError(f'input changed since preflight: {p}')

records=[]
for case in CASES:
    srcdir=P/case
    report=json.loads((srcdir/'report.json').read_text())
    cap=json.loads((srcdir/'media/capture.json').read_text())
    if not report.get('completed') or report.get('physics_steps') != 1200 or report.get('control_steps') != 300 or report.get('physics_seconds') != 5.0:
        raise RuntimeError(f'run is not a complete 5s native run: {case}')
    frames={int(f['physics_step']):f for f in cap['frames']}
    for step in (0,480,1200):
        if step not in frames or frames[step]['time_s'] != {0:0.0,480:2.0,1200:5.0}[step]:
            raise RuntimeError(f'capture time mapping mismatch {case} step {step}')
    for media_kind in ('whole_body','hands'):
        source=srcdir/'media'/f'{media_kind}.mp4'
        expected=report['videos'][media_kind]['sha256']
        if sha(source) != expected: raise RuntimeError(f'report video SHA mismatch: {source}')
        stream=ffprobe(source)
        if stream.get('nb_read_frames') != '151' or stream.get('avg_frame_rate') != '30/1': raise RuntimeError(f'unexpected native video timing: {source}')
        dest=V/f'{case}_{media_kind}.mp4'
        with dest.open('xb') as out, source.open('rb') as inp: shutil.copyfileobj(inp,out)
        if sha(dest) != expected or dest.stat().st_size != source.stat().st_size: raise RuntimeError(f'byte-copy verification failed: {dest}')
        out_stream=ffprobe(dest)
        if out_stream != stream: raise RuntimeError(f'ffprobe mismatch after copy: {dest}')
        records.append({'kind':'video','case':case,'media':media_kind,'source':str(source),'destination':str(dest),'sha256':expected,'size_bytes':dest.stat().st_size,'ffprobe':out_stream})
    for step in (0,480,1200):
        frame=frames[step]
        for view in ('whole_body','hands'):
            src=Path(next((p for p in frame['image_sha256'] if f'/frames/{view}/' in p)))
            expected=frame['image_sha256'][str(src)]
            if sha(src) != expected: raise RuntimeError(f'capture frame SHA mismatch: {src}')
            dest=A/f'{case}_t{int(frame["time_s"]):02d}_{view}.png'
            with dest.open('xb') as out, src.open('rb') as inp: shutil.copyfileobj(inp,out)
            if sha(dest) != expected or dest.stat().st_size != src.stat().st_size: raise RuntimeError(f'frame copy verification failed: {dest}')
            records.append({'kind':'frame','case':case,'physics_step':step,'time_s':frame['time_s'],'view':view,'source':str(src),'destination':str(dest),'sha256':expected,'size_bytes':dest.stat().st_size})

for p,h in pin['inputs_before'].items():
    if sha(p) != h: raise RuntimeError(f'input changed during packaging: {p}')
producer_after=sha(self_path)
if producer_after != pin['producer_sha256_before']: raise RuntimeError('producer changed during execution')
result={'schema':'native_artifact_provenance_v1','producer':str(self_path),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':producer_after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'outputs':records,'scope_note':'Three approved complete native runs only; no pending/in-progress run was read or packaged. PNGs and MP4s are byte-exact copies; no image or video transformation was performed.'}
with (A/'provenance_v1.json').open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v1.json')},ensure_ascii=False))
