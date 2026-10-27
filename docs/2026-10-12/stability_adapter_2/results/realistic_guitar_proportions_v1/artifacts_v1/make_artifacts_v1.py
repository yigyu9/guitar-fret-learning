#!/usr/bin/env python3
"""기존 native 결과를 읽어 비교패널과 바이트 보존 영상 보관본을 만든다."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
P = ROOT / 'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
A = P / 'artifacts_v1'
V = ROOT / 'docs/2026-10-12/video/realistic_guitar_proportions_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def load(path): return json.loads(Path(path).read_text())
def font(size): return ImageFont.truetype(str(FONT),size)
def fit(im, box):
    im=im.copy(); im.thumbnail(box,Image.Resampling.LANCZOS); return im

def titled_canvas(title, w=1800, h=1100):
    im=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(im); d.text((50,25),title,font=font(34),fill='#17212b'); return im,d

v3=load(P/'verification_v3.json'); audit=load(P/'body_center_audit_v2.json'); geo=load(P/'geometry_build_v1.json')
assert v3['passed'] and len(v3['checks'])==25 and all(v3['checks'].values())
# Pin and verify the upstream closure before any generated output.
input_paths={}
for p,h in v3['input_sha256'].items():
    q=Path(p) if Path(p).is_absolute() else ROOT/p
    assert q.is_file() and sha(q)==h, f'입력 SHA 불일치: {q}'
    input_paths[str(q)]=h
for q in [P/'verification_v3.json',P/'geometry_build_v1.json',P/'body_center_audit_v2.json']:
    input_paths[str(q)]=sha(q)
input_paths[str(FONT)]=sha(FONT)
# capture frames and collision panels are direct inputs; verify via capture map.
source_names={'old':'native_baseline_v2','new':'native_realistic_v2'}
captures={k:load(P/n/'media/capture.json') for k,n in source_names.items()}
for k,c in captures.items():
    for fr in [c['frames'][0],c['frames'][60],c['frames'][150]]:
        for q,h in fr['image_sha256'].items():
            assert sha(q)==h, f'프레임 SHA 불일치: {q}'
            input_paths[q]=h
for n in source_names.values():
    q=P/n/'initial_collision.png'; input_paths[str(q)]=sha(q)

# Exact byte copies of only the four completed native videos.
video_records=[]
for label,n in source_names.items():
    for kind,srcname in [('전신','whole_body'),('손','hands')]:
        src=P/n/'media'/f'{srcname}.mp4'
        dst=V/f'{label}_{srcname}.mp4'
        s0=sha(src)
        if dst.exists():
            assert sha(dst)==s0, f'기존 복사본 불일치: {dst}'
        else:
            shutil.copyfile(src,dst)
        s1=sha(dst); assert s0==s1
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
        assert probe['avg_frame_rate']=='30/1' and probe['nb_read_frames']=='151'
        video_records.append({'label':label,'view':kind,'source':str(src),'destination':str(dst),'bytes':dst.stat().st_size,'source_sha256':s0,'copy_sha256':s1,'ffprobe':probe})

# Actual Isaac Gym image panels: own native frames at 0, 2, 5 s.
for kind,folder,outname in [('전신','whole_body','native_whole_body_panel.png'),('손','hands','native_hands_panel.png')]:
    cw,ch=640,390; pad=20
    canvas=Image.new('RGB',(3*cw+4*pad,2*(ch+60)+3*pad),'white'); d=ImageDraw.Draw(canvas)
    for ri,label in enumerate(['old','new']):
        cap=captures[label]
        for ci,fi in enumerate([0,60,150]):
            fr=cap['frames'][fi]; key=next(k for k in fr['image_sha256'] if f'/{folder}/' in k)
            im=Image.open(key).convert('RGB'); im=fit(im,(cw,ch))
            x=pad+ci*(cw+pad); y=pad+ri*(ch+60+pad)
            canvas.paste(im,(x,y+36)); d.text((x,y),f"{'원본' if label=='old' else '현실 비율'} · {fr['time_s']:.0f}초",font=font(24),fill='#17212b')
    canvas.save(A/outname)

# Native initial render/collision images side by side, preserving source pixels.
canvas=Image.new('RGB',(1660,900),'white'); d=ImageDraw.Draw(canvas)
for ri,(label,n) in enumerate(source_names.items()):
    q=P/n/'initial_collision.png'; im=Image.open(q).convert('RGB'); im=fit(im,(800,820)); x=20+ri*820
    d.text((x,10),'원본 native t0' if label=='old' else '현실 비율 native t0',font=font(25),fill='#17212b'); canvas.paste(im,(x,55))
canvas.save(A/'native_visual_collision_t0.png')

# Dimension comparison schematic; explicit not a scan.
im,d=titled_canvas('치수 비교 — 설계 도식(실물 스캔 아님)')
# side outlines scaled to consistent 700px guitar body height
for x,label,length,width,total,color in [(500,'원본',34.0,30.0,None,'#637381'),(1300,'현실 비율',48.7896,37.3039,100.2298,'#148a9c')]:
    body_h=540; body_w=int(body_h*width/length)
    top=180; left=x-body_w//2
    d.rounded_rectangle((left,top,left+body_w,top+body_h),radius=body_w//2,outline=color,width=8)
    d.line((x,top-90,x,top),fill=color,width=20); d.rectangle((x-25,top-155,x+25,top-90),fill=color)
    d.text((left,top+body_h+25),f'{label}: 몸체 길이 {length:.2f} cm · 최대폭 {width:.2f} cm',font=font(25),fill='#17212b')
    d.text((left,top+body_h+65),f'전체 길이 {total:.2f} cm' if total is not None else '전체 길이: 이 자료에 값 없음',font=font(25),fill='#17212b')
d.text((70,1000),'중립 원본 소스 높이 172.05 cm 기준 스케일링; 사람 실측 키가 아님. Yamaha FS800 수치에 맞춘 근사 비율이며 정밀 복제품이 아님.',font=font(24),fill='#38434d')
im.save(A/'dimensions_comparison.png')

# Outline from the actual new half-width profile; old body is its declared rectangular bounds.
im,d=titled_canvas('평면 윤곽 비교 — 새 윤곽은 빌드된 두 볼록부 프로파일')
# draw old rectangle scaled to comparable width/length
for x,label,color in [(420,'원본 경계','#637381'),(1280,'새 half-width profile','#148a9c')]:
    if label.startswith('원본'):
        x0,x1=x-220,x+220; y0,y1=230,820
        d.rectangle((x0,y0,x1,y1),outline=color,width=7)
        d.text((x0,y1+25),'34 × 30 cm 경계',font=font(24),fill='#17212b')
    else:
        prof=geo['half_width_profile_t_m']; pts=[]
        for t,half in prof: pts.append((x+half*1150,220+t*600))
        left=[(2*x-px,py) for px,py in pts]
        d.polygon(pts+list(reversed(left)),outline=color,fill='#d8f1f2')
        d.line(pts,fill=color,width=5); d.line(left,fill=color,width=5)
        d.text((x-250,845),'새 윤곽: upper/lower 볼록 메시, 허리 포함',font=font(24),fill='#17212b')
d.text((65,990),'넥·프렛·현 좌표와 body frame/name/order는 보존됨. 오른쪽은 half_width_profile_t_m을 그대로 그린 평면 도식.',font=font(23),fill='#38434d')
im.save(A/'outline_comparison.png')

# Depth range comparison.
im,d=titled_canvas('두께 범위 비교 — 몸체 두께 (cm)')
old=(4.0,4.0); new=(8.8351399,10.7985043)
for y,label,lo,hi,col in [(310,'원본',*old,'#637381'),(650,'현실 비율',*new,'#148a9c')]:
    x0=300+(lo/12)*1200; x1=300+(hi/12)*1200
    d.text((65,y-10),label,font=font(30),fill='#17212b'); d.line((x0,y,x1,y),fill=col,width=30)
    d.text((x0,y+45),f'{lo:.2f}–{hi:.2f} cm',font=font(28),fill='#17212b')
for cm in range(0,13,2):
    x=300+(cm/12)*1200; d.line((x,780,x,800),fill='#52606d',width=2); d.text((x-12,810),str(cm),font=font(19),fill='#52606d')
d.text((300,870),'공통 축 (cm)',font=font(22),fill='#38434d'); d.text((65,1000),'기존 몸체 두께 4 cm; 새 메쉬 bounds 두께 8.8351–10.7985 cm.',font=font(24),fill='#38434d')
im.save(A/'thickness_comparison.png')

# Records of exact copies and input closure.
(V/'manifest.json').write_text(json.dumps({'schema':'video-archive-manifest-v1','video_count':len(video_records),'videos':video_records},ensure_ascii=False,indent=2)+'\n')
# report summaries and correct center coordinates.
prov={'schema':'realistic-guitar-artifacts-provenance-v1','verification_source':str(P/'verification_v3.json'),'verification_passed':v3['passed'],'verification_checks':len(v3['checks']),'inputs_sha256_before_after':{k:{'before':h,'after':sha(k)} for k,h in input_paths.items()},'font':{'path':str(FONT),'sha256':sha(FONT)},'body_center_audit':{'actual_envelope_center_G_m':audit['actual_envelope_center_G_m'],'body_mid_length_depth_reference_G_m':audit['body_mid_length_depth_reference_G_m'],'native_G_body_COM_G_m':audit['native_G_body_COM_G_m']},'summary_metrics':[{k:x[k] for k in ['label','final_actor_root_change_mm','final_SO3_change_deg','geometric_envelope_center_change_mm','contact_sample_counts_of_300']} for x in v3['summaries']],'video_copies':video_records,'outputs_sha256':{str(q):sha(q) for q in sorted(A.glob('*.png'))},'producer_sha256':sha(Path(__file__))}
(A/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':video_records,'producer_sha256':prov['producer_sha256'],'outputs_sha256':prov['outputs_sha256']},ensure_ascii=False,indent=2))
