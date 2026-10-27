#!/usr/bin/env python3
"""Build Korean-labelled panels and exact video copies from completed OM native captures."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3/docs/2026-10-12')
P = ROOT / 'stability_adapter_2/results/om_body_geometry_v1'
A = P / 'artifacts_v1'
V = ROOT / 'video/om_body_geometry_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def pin(paths): return {str(p): {'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
def font(size): return ImageFont.truetype(str(FONT), size)

def panel(kind, out):
    cap=json.loads((P/'native_v2/media/capture.json').read_text())
    rows=[next(x for x in cap['frames'] if x['time_s']==t) for t in (0.0,2.0,5.0)]
    imgs=[]
    for row in rows:
        p=Path(next(k for k in row['image_sha256'] if f'/{kind}/' in k))
        assert sha(p)==row['image_sha256'][str(p)]
        imgs.append(Image.open(p).convert('RGB'))
    w=max(i.width for i in imgs); h=max(i.height for i in imgs); band=58; gap=14
    canvas=Image.new('RGB',(w*3+gap*4,h+band+gap*2),(245,245,245)); d=ImageDraw.Draw(canvas)
    for i,(im,row) in enumerate(zip(imgs,rows)):
        x=gap+i*(w+gap); y=band
        canvas.paste(im,(x,y))
        d.text((x+8,12),f"{kind} · {row['time_s']:.0f}초 · 물리 {row['physics_step']} step",font=font(24),fill=(20,20,20))
    canvas.save(out)

def caption_image(src,dst):
    im=Image.open(src).convert('RGB'); band=68
    out=Image.new('RGB',(im.width,im.height+band),(245,245,245)); out.paste(im,(0,band))
    ImageDraw.Draw(out).text((16,16),'native_v2 초기 외관 · Isaac Gym 화면 · 넥 시각화 포함',font=font(25),fill=(15,15,15))
    out.save(dst)

# Pin all direct evidence and reusable source-stage artifacts before reading/producing.
inputs=[P/'depth_v1.json',P/'build_v2.json',P/'native_v1/report.json',P/'native_v1/initial_values.json',P/'native_v1/media/capture.json',P/'native_v1/media/raw/capture.json',P/'native_v1/media/videos.json',P/'native_v2/report.json',P/'native_v2/initial_values.json',P/'native_v2/media/capture.json',P/'native_v2/media/raw/capture.json',P/'native_v2/media/videos.json',P/'native_v2/initial_OM_appearance.png',A/'make_source_views_v1.py',A/'source_provenance_v1.json',A/'source_mesh_three_views.png',A/'local_depth_samples.png']
for version in ('native_v1','native_v2'):
    for name in ('whole_body.mp4','hands.mp4'):
        inputs.append(P/version/'media'/name)
for t in (0,2,5):
    row=next(x for x in json.loads((P/'native_v2/media/capture.json').read_text())['frames'] if x['time_s']==float(t))
    for k in row['image_sha256']: inputs.append(Path(k))
inputs.append(FONT)
before=pin(inputs)
assert all(json.loads((P/f'{v}/report.json').read_text())['completed'] for v in ('native_v1','native_v2'))
assert FONT.exists()
A.mkdir(parents=True,exist_ok=True); V.mkdir(parents=True,exist_ok=True)
for kind in ('whole_body','hands'): panel(kind,A/f'native_v2_{kind}_0_2_5s.png')
caption_image(P/'native_v2/initial_OM_appearance.png',A/'native_v2_initial_appearance_captioned.png')
manifest={'title':'OM native 영상 exact-copy 보관','videos':[]}
for v in ('native_v1','native_v2'):
    for kind in ('whole_body','hands'):
        src=P/v/'media'/f'{kind}.mp4'; dst=V/f'{v}_{kind}.mp4'
        shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        q=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
        manifest['videos'].append({'source':str(src),'destination':str(dst),'sha256_source':sha(src),'sha256_copy':sha(dst),'bytes':dst.stat().st_size,'ffprobe':q})
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
after=pin(inputs)
assert before==after, 'an input changed during processing'
outputs=[A/'make_native_media_v1.py',A/'native_v2_whole_body_0_2_5s.png',A/'native_v2_hands_0_2_5s.png',A/'native_v2_initial_appearance_captioned.png',V/'manifest_v1.json']+[V/f'{v}_{k}.mp4' for v in ('native_v1','native_v2') for k in ('whole_body','hands')]
prov={'inputs_before':before,'inputs_after':after,'producer_sha256':sha(A/'make_native_media_v1.py'),'outputs':pin(outputs),'native_reruns':0,'notes':['native_v1 영상은 넥 시각화가 빠진 화면이며 원본 그대로 보관했다.','native_v2 영상은 visual-only 넥 표시를 포함한다.','영상은 원본 bytes exact-copy이며 물리 재실행 없음.']}
(A/'native_media_provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':len(manifest['videos']),'input_count':len(inputs),'pngs':[str(x) for x in outputs if x.suffix=='.png'],'provenance':str(A/'native_media_provenance_v1.json')},ensure_ascii=False))
