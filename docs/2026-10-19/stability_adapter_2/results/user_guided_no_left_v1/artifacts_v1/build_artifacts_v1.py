#!/usr/bin/env python3
"""Byte-copy source native media with SHA/ffprobe provenance; no image or video transform."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1'
ART=P/'artifacts_v1'
VIDEO=ROOT/'docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1'
SCRIPT=ART/'build_artifacts_v1.py'
PIN=ART/'preflight_pin_v1.json'
CASES=('native_upper50_static','native_upper50_v12_static','native_upper50_v13_static','native_upper50_v14_elbow5','native_upper50_v4_static','native_upper50_v5_static','native_upper50_v6_static','native_upper50_v8_static','native_upper65_v6_static')
FRAME_CASES=('native_upper50_v13_static','native_upper50_v14_elbow5')
FRAME_INDEX_TO_STEP={0:0,60:480,150:1200}


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def ffprobe(path:Path)->dict:
    command=['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)]
    result=subprocess.run(command,check=True,capture_output=True,text=True)
    data=json.loads(result.stdout)
    if len(data.get('streams',[]))!=1:raise ValueError(f'expected one video stream: {path}')
    return {'command':command,'exit_code':result.returncode,'stream':data['streams'][0]}


def copy_exclusive(source:Path,dest:Path)->None:
    with source.open('rb') as src, dest.open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024)


def main()->None:
    pin=json.loads(PIN.read_text(encoding='utf-8'))
    if pin.get('schema')!='user_guided_no_left_preflight_v1' or pin.get('producer',{}).get('path')!=str(SCRIPT):
        raise ValueError('preflight pin schema/producer mismatch')
    input_rows=pin['inputs']
    for row in input_rows:
        path=Path(row['path'])
        if not path.is_file() or sha(path)!=row['sha256_before']:
            raise ValueError(f'input missing or differs from saved before pin: {path}')
    if sha(SCRIPT)!=pin['producer']['sha256_before']:
        raise ValueError('producer differs from saved before pin')

    reports={}
    source_videos=[]
    capture_paths=[]
    for case in CASES:
        run=P/case
        report_path=run/'report.json'
        report=json.loads(report_path.read_text(encoding='utf-8'))
        reports[case]=report
        vids=report.get('videos') or {}
        if not vids:
            continue
        videos_json=json.loads((run/'media/videos.json').read_text(encoding='utf-8'))
        for view in ('whole_body','hands'):
            record=vids[view]
            media_record=videos_json[view]
            if media_record['path']!=record['path'] or media_record['sha256']!=record['sha256']:
                raise ValueError(f'report/videos.json source provenance differs: {case} {view}')
            source=Path(record['path'])
            if not source.is_file() or sha(source)!=record['sha256']:
                raise ValueError(f'report MP4 source/hash mismatch: {source}')
            source_videos.append((case,view,source,record))
        cap=run/'media/capture.json'
        if not cap.is_file():raise FileNotFoundError(cap)
        capture_paths.append(cap)

    copied_videos=[]
    for case,view,source,record in source_videos:
        dest=VIDEO/f'{case}_{view}.mp4'
        if dest.exists():raise FileExistsError(dest)
        copy_exclusive(source,dest)
        source_hash=sha(source);copy_hash=sha(dest)
        if source_hash!=copy_hash or source.stat().st_size!=dest.stat().st_size:
            raise ValueError(f'copy not byte-identical: {dest}')
        source_probe=ffprobe(source);copy_probe=ffprobe(dest)
        if source_probe['stream']!=copy_probe['stream']:
            raise ValueError(f'ffprobe stream differs after copy: {dest}')
        copied_videos.append({'case':case,'view':view,'source_path':str(source),'source_sha256':source_hash,'source_bytes':source.stat().st_size,'copy_path':str(dest),'copy_sha256':copy_hash,'copy_bytes':dest.stat().st_size,'byte_exact':True,'ffprobe_source':source_probe,'ffprobe_copy':copy_probe,'reported_stream':record.get('stream')})

    copied_frames=[]
    for case in FRAME_CASES:
        run=P/case
        capture=json.loads((run/'media/capture.json').read_text(encoding='utf-8'))
        for view in ('whole_body','hands'):
            for frame_index,physics_step in FRAME_INDEX_TO_STEP.items():
                frame=run/'media/frames'/view/f'{frame_index:05d}.png'
                if not frame.is_file():raise FileNotFoundError(frame)
                row=capture['frames'][frame_index]
                if row['physics_step']!=physics_step or row['time_s']!=physics_step/240:
                    raise ValueError(f'capture timeline mismatch: {case} {view} frame {frame_index}')
                if row['image_sha256'].get(str(frame))!=sha(frame):
                    raise ValueError(f'capture PNG SHA mismatch: {frame}')
                dest=ART/f'{case}_{view}_frame_{frame_index:05d}_step_{physics_step:04d}.png'
                if dest.exists():raise FileExistsError(dest)
                copy_exclusive(frame,dest)
                copied_frames.append({'case':case,'view':view,'frame_index':frame_index,'physics_step':physics_step,'time_s':row['time_s'],'source_path':str(frame),'source_sha256':sha(frame),'copy_path':str(dest),'copy_sha256':sha(dest),'byte_exact':True,'width_px':1280,'height_px':720})

    after={row['path']:sha(Path(row['path'])) for row in input_rows}
    changed=[path for path,value in after.items() if value!=next(row['sha256_before'] for row in input_rows if row['path']==path)]
    producer_after=sha(SCRIPT)
    if changed or producer_after!=pin['producer']['sha256_before']:
        raise RuntimeError(f'input/producer changed during artifact build: {changed}')
    report_summary=[]
    for case in CASES:
        d=reports[case]
        report_summary.append({'case':case,'report_path':str(P/case/'report.json'),'physics_steps':d.get('physics_steps'),'control_steps':d.get('control_steps'),'physics_seconds':d.get('physics_seconds'),'completed':d.get('completed'),'video_views':sorted((d.get('videos') or {}).keys())})
    provenance={
      'schema':'user_guided_no_left_artifact_provenance_v1',
      'method':'copy original native MP4/PNG bytes only; no crop, montage, annotation, decode/re-encode, frame extension, or physics rerun',
      'producer':{'path':str(SCRIPT),'sha256_before':pin['producer']['sha256_before'],'sha256_after':producer_after,'unchanged':producer_after==pin['producer']['sha256_before']},
      'inputs':[{'path':row['path'],'sha256_before':row['sha256_before'],'sha256_after':after[row['path']],'unchanged':after[row['path']]==row['sha256_before']} for row in input_rows],
      'reports':report_summary,
      'videos':copied_videos,
      'native_png_copies':copied_frames,
    }
    target=ART/'provenance_v1.json'
    with target.open('x',encoding='utf-8') as f:json.dump(provenance,f,ensure_ascii=False,indent=2);f.write('\n')

if __name__=='__main__':main()
