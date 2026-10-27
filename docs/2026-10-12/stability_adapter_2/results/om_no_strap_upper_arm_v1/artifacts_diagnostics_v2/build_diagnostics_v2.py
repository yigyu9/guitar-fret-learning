#!/usr/bin/env python3
"""Exact-copy completed no-strap trials 5,6,7,9,10 and assemble native frame panel."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1')
V = Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1')
OUT = V / 'diagnostics_v2'
ART = P / 'artifacts_diagnostics_v2'
VERIFY8 = P / 'verification_v8.json'
VERIFY9 = P / 'effort_verification_v9_cases2.json'
CAPTURE = P / 'native_v10/three_support_relative_effort_microgap/media/capture.json'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FRAME_DIR = P / 'native_v10/three_support_relative_effort_microgap/media/frames/whole_body'
NATIVE8_ATTEMPT = P / 'native_v8/three_support_right_effort/attempt.json'
NATIVE8_SHORT = [P / 'native_v8/three_support_right_effort/media/whole_body.mp4', P / 'native_v8/three_support_right_effort/media/hands.mp4']
CASES = [
    (5, 'upper_arm_right_hold', '시험 5 · 오른상완 hold', 'native_v5/upper_arm_right_hold'),
    (6, 'upper_arm_relative_feedback', '시험 6 · 상대 피드백', 'native_v6/upper_arm_relative_feedback'),
    (7, 'three_support_lean12', '시험 7 · 3지점 지지·기울기 12', 'native_v7/three_support_lean12'),
    (9, 'three_support_right_effort', '시험 9 · 오른쪽 effort', 'native_v9/three_support_right_effort'),
    (10, 'three_support_relative_effort_microgap', '시험 10 · 상대 effort·microgap', 'native_v10/three_support_relative_effort_microgap'),
]
FRAME_INDICES = [(0, '0.0초'), (3, '0.1초'), (9, '0.3초'), (15, '0.5초'), (150, '5.0초')]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    v8 = json.loads(VERIFY8.read_text(encoding='utf-8'))
    v9 = json.loads(VERIFY9.read_text(encoding='utf-8'))
    capture = json.loads(CAPTURE.read_text(encoding='utf-8'))
    if not v8.get('passed') or not v9.get('passed'):
        raise RuntimeError('authoritative verification JSON did not pass')
    if len(capture['frames']) != 151 or capture.get('fps') != 30:
        raise RuntimeError('unexpected native capture frame count or fps')
    entries=[]
    inputs_before={str(p):sha(p) for p in [VERIFY8, VERIFY9, CAPTURE, FONT, NATIVE8_ATTEMPT, *NATIVE8_SHORT]}
    for trial,key,label,runrel in CASES:
        source_case=(v9['cases'][key] if key in v9['cases'] else v8['cases'][key])
        for view in ('whole_body','hands'):
            item=source_case['videos'][view]
            src=Path(item['path'])
            src_hash=sha(src)
            if src_hash != item['sha256']:
                raise RuntimeError(f'verification/source mismatch: {src}')
            dest=OUT/f'trial{trial:02d}_{Path(runrel).name}_{view}.mp4'
            # prevent accidental overwrite of any previously consumed result
            if dest.exists():
                raise RuntimeError(f'refusing to overwrite existing archive copy: {dest}')
            shutil.copyfile(src,dest)
            copy_hash=sha(dest)
            if copy_hash != src_hash:
                raise RuntimeError(f'copy mismatch: {dest}')
            entries.append({'source':str(src),'source_sha256':src_hash,'destination':str(dest),'copy_sha256':copy_hash,'label':label,'view':view})
            inputs_before[str(src)]=src_hash
    frames=[]
    for idx,label in FRAME_INDICES:
        p=FRAME_DIR/f'{idx:05d}.png'
        frame_meta=capture['frames'][idx]
        recorded=frame_meta['image_sha256'][str(p)]
        actual=sha(p)
        if actual!=recorded or frame_meta['time_s'] != float(label[:-1]):
            raise RuntimeError(f'frame does not match capture metadata: {p}')
        frames.append({'path':str(p),'sha256':actual,'time_s':frame_meta['time_s'],'physics_step':frame_meta['physics_step']})
        inputs_before[str(p)]=actual
    out=ART/'native_v10_whole_body_timeline.png'
    bg=(245,247,250)
    cell_w,cell_h=630,354
    gap=22
    top=126
    row_gap=30
    foot_h=112
    canvas=Image.new('RGB',(3*cell_w+4*gap,top+2*(cell_h+70)+row_gap+foot_h),bg)
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(str(FONT),26)
    titlefont=ImageFont.truetype(str(FONT),34)
    footerfont=ImageFont.truetype(str(FONT),21)
    draw.text((gap,22),'Native 10 · whole_body 캡처 시간 패널',font=titlefont,fill=(20,35,55))
    draw.text((gap,73),'0초 / 0.1초 / 0.3초 / 0.5초 / 5초',font=font,fill=(50,65,85))
    positions=[(gap,top),(2*gap+cell_w,top),(3*gap+2*cell_w,top),(gap+cell_w//2,top+cell_h+70+row_gap),(2*gap+cell_w+cell_w//2,top+cell_h+70+row_gap)]
    for (idx,label), (x,y) in zip(FRAME_INDICES,positions):
        im=Image.open(FRAME_DIR/f'{idx:05d}.png').convert('RGB').resize((cell_w,cell_h),Image.Resampling.LANCZOS)
        canvas.paste(im,(x,y))
        draw.rectangle((x,y+cell_h+8,x+cell_w,y+cell_h+54),fill=bg)
        draw.text((x+8,y+cell_h+10),f'{label} · frame {idx:05d}',font=font,fill=(20,35,55))
    foot_y=top+2*(cell_h+70)+row_gap
    draw.rectangle((gap,foot_y,canvas.width-gap,canvas.height-gap),fill=(230,235,241))
    draw.text((gap+12,foot_y+10),'실제 Isaac Gym native whole_body 캡처 프레임을 조합한 그림입니다.',font=footerfont,fill=(20,35,55))
    draw.text((gap+12,foot_y+42),'시간별 장면 참조용이며 힘 분포·접촉력·관통을 보여주거나 인증하지 않습니다.',font=footerfont,fill=(20,35,55))
    canvas.save(out,optimize=True)
    manifest={'videos':entries}
    manifest_path=V/'manifest_v2.json'
    if manifest_path.exists(): raise RuntimeError(f'refusing to overwrite manifest: {manifest_path}')
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    inputs_after={p:sha(Path(p)) for p in inputs_before}
    if inputs_before != inputs_after:
        raise RuntimeError('an input changed during processing')
    result={'inputs_before':inputs_before,'inputs_after':inputs_after,'frames':frames,'video_entries':entries,'outputs':{str(out):sha(out),str(manifest_path):sha(manifest_path)},'font':{'path':str(FONT),'sha256':sha(FONT)},'panel_size':list(canvas.size)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
