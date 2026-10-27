#!/usr/bin/env python3
"""Create native-frame comparison panels and byte-exact video archive for right_body_approach_v1."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

P = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1')
BASE = P.parent / 'right_thigh_waist_v1'
A = P / 'artifacts_v1'
V = P.parents[1] / 'video' / 'right_body_approach_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
BRIEF = P / 'artifact_brief_v1.json'
ANALYSIS = P / 'analysis_static_v2/analysis.json'
PARTIAL = P / 'partial_analysis_v2.json'
PREV_ANALYSIS = BASE / 'analysis_final_v1/analysis.json'
PREV_VALUES = BASE / 'native_static_v2/initial_values.json'

cases = [
    ('이전 기준 · waist inset 0 mm', BASE / 'native_static_v2', None),
    ('새 조건 · inset 3 mm', P / 'native_inset3_static', P / 'search_v1/inset3mm/candidate.json'),
    ('새 조건 · inset 6 mm', P / 'native_inset6_static', P / 'search_v1/inset6mm/candidate.json'),
    ('새 조건 · inset 10 mm', P / 'native_inset10_static', P / 'search_v1/inset10mm/candidate.json'),
    ('부분 중단 · inset 20 mm', P / 'native_inset20_static', P / 'search_v2/inset20mm/candidate.json'),
    ('부분 중단 · inset 30 mm', P / 'native_inset30_static', P / 'search_v2/inset30mm/candidate.json'),
]


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load(path):
    return json.loads(Path(path).read_text())
def dump(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def font(size): return ImageFont.truetype(str(FONT),size)
def probe(path):
    raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)],text=True)
    s=json.loads(raw)['streams'][0]
    return {k:s.get(k) for k in ('width','height','avg_frame_rate','nb_read_frames','duration')}

def frame(native, view, idx):
    return native/'media'/'frames'/view/f'{idx:05d}.png'

def make_panel(items, out, title, crop=None, cols=2, thumb=(576,324)):
    margin=28; cap_h=92; gap=20; rows=(len(items)+cols-1)//cols
    W=margin*2+cols*thumb[0]+(cols-1)*gap
    H=margin*2+rows*(thumb[1]+cap_h)+(rows-1)*gap+54
    im=Image.new('RGB',(W,H),'#f5f5f5'); dr=ImageDraw.Draw(im)
    dr.text((margin,14),title,font=font(28),fill='#111111')
    for i,(path,caption) in enumerate(items):
        x=margin+(i%cols)*(thumb[0]+gap); y=64+(i//cols)*(thumb[1]+cap_h+gap)
        src=Image.open(path).convert('RGB')
        if crop: src=src.crop(crop)
        src.thumbnail(thumb,Image.Resampling.LANCZOS)
        cell=Image.new('RGB',thumb,'#202020'); cell.paste(src,((thumb[0]-src.width)//2,(thumb[1]-src.height)//2))
        im.paste(cell,(x,y)); dr.rectangle((x,y,x+thumb[0]-1,y+thumb[1]-1),outline='#555555',width=2)
        yy=y+thumb[1]+7
        for line in caption.split('\n'):
            dr.text((x+4,yy),line,font=font(20),fill='#111111'); yy+=26
    im.save(out)

# Hash all directly read sources before production.
inputs=set([BRIEF,ANALYSIS,PARTIAL,PREV_ANALYSIS,PREV_VALUES,FONT,Path(__file__)])
inputs.add(BASE/'native_static_v2/report.json')
inputs.add(BASE/'native_static_v2/media/capture.json')
inputs.add(BASE/'native_static_v2/media/whole_body.mp4')
inputs.add(BASE/'native_static_v2/media/hands.mp4')
inputs.add(BASE/'native_static_v2/media/frames/whole_body/00000.png')
for label,native,candidate in cases:
    cap=native/'media/capture.json'; inputs.add(cap)
    report=native/'report.json'; inputs.add(report)
    if candidate:
        inputs.add(candidate)
        inputs.add(candidate.parent/'config.json')
    inputs.add(native/'media/whole_body.mp4')
    inputs.add(native/'media/hands.mp4')
    inputs.add(native/'initial_values.json')
    for idx in ([0,60,150] if native.name=='native_inset6_static' else [0]):
        for view in ('whole_body','hands'):
            f=frame(native,view,idx)
            if f.exists(): inputs.add(f)
input_before={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(inputs)}

# Verify all whole-body camera matrices match before comparing initial frames.
cam=[]
for _,native,_ in cases:
    c=load(native/'media/capture.json')['frames'][0]['cameras']['whole_body']
    cam.append((c['view_matrix'],c['projection_matrix']))
if any(x != cam[0] for x in cam[1:]):
    raise SystemExit('whole-body camera matrices differ; comparison panels not produced')

# Parse selected candidates for maximum scalar-q difference from the previous waist baseline.
old=load(PREV_VALUES); q0=old['q_ref_rad']; names=old['joint_names']
max_delta={}
for label,native,candidate in cases:
    if candidate:
        q=load(candidate)['joint_angles_rad']
        max_delta[native.name]=max(abs((a-b)*180/3.141592653589793) for a,b in zip(q,q0))
    else: max_delta[native.name]=0.0

# Initial six-condition full-view comparison and identical pixel crop around the right-side guitar/body support area.
initial=[]; crop_items=[]
for label,native,candidate in cases:
    f=frame(native,'whole_body',0)
    corr='기준 q' if candidate is None else f"baseline 대비 최대 scalar 관절각 차이 {max_delta[native.name]:.1f}°"
    text=f'{label}\n초기 배치 · {corr}'
    initial.append((f,text)); crop_items.append((f,text))
make_panel(initial,A/'initial_six_whole_body.png','초기 전신 비교 — native Isaac Gym frame 0',cols=2)
# Fixed crop coordinates, identical across all six inputs/cameras.
make_panel(crop_items,A/'initial_six_right_blocks_crop.png','오른쪽 기타·몸통 접점 주변 동일 픽셀 crop — frame 0',crop=(430,270,850,530),cols=2,thumb=(520,322))

# 6 mm selected timeline, native frames: 0,60,150 map to recorded 0,2,5 seconds at 30fps.
selected=P/'native_inset6_static'
for view in ('whole_body','hands'):
    items=[]
    for idx,t in [(0,'0초'),(60,'2초'),(150,'5초')]:
        items.append((frame(selected,view,idx),f'inset 6 mm · {t} · native Isaac Gym'))
    make_panel(items,A/f'inset6_{view}_timeline.png',f'inset 6 mm 실제 native {"전신" if view=="whole_body" else "손"} 프레임',cols=3,thumb=(400,225))

# Byte-exact MP4 archive, retaining both completed and partial clips.
manifest={'schema':'right_body_approach_video_manifest_v1','videos':[]}
for label,native,_ in cases:
    if native.parent == BASE:  # baseline is used only for the comparison panels, not among the 10 new source videos
        continue
    for view in ('whole_body','hands'):
        src=native/'media'/f'{view}.mp4'
        dest_dir=V/native.name; dest_dir.mkdir(parents=True,exist_ok=True)
        dest=dest_dir/f'{view}.mp4'
        shutil.copyfile(src,dest)
        srcsha=sha(src); dstsha=sha(dest)
        if srcsha != dstsha or src.stat().st_size != dest.stat().st_size:
            raise RuntimeError(f'copy mismatch: {src}')
        metadata=probe(dest)
        report=load(native/'report.json')
        manifest['videos'].append({'case':native.name,'condition':label,'view':view,'source':str(src),'destination':str(dest),'source_sha256':srcsha,'copy_sha256':dstsha,'bytes':dest.stat().st_size,'completed':report['completed'],'physics_steps':report['physics_steps'],'control_steps':report['control_steps'],'physics_seconds':report['physics_seconds'],'ffprobe':metadata})
dump(V/'manifest_v1.json',manifest)

# Input after-hashes; ensure source materials remained unchanged during production.
input_after={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(inputs)}
if input_before != input_after: raise RuntimeError('read-only source changed during artifact production')

# Provenance includes source data, native frames, originals, copied outputs, producer and font.
outputs=[]
for p in sorted(A.iterdir()):
    if p.is_file() and p.name not in ('provenance_v1.json',):
        outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
for row in manifest['videos']:
    outputs.append({'path':row['destination'],'sha256':row['copy_sha256'],'bytes':row['bytes']})
prov={'created_utc':'2026-10-13','scope':'자료 비교 패널 및 원본 MP4 byte-exact 복사; 물리/학습 재실행 없음','input_before':input_before,'input_after':input_after,'outputs':outputs,'camera_matrix_comparison':'6개 whole_body view/projection matrix exact-equal','source_copy_count':len(manifest['videos']),'source_copy_bytes':sum(x['bytes'] for x in manifest['videos'])}
dump(A/'provenance_v1.json',prov)
