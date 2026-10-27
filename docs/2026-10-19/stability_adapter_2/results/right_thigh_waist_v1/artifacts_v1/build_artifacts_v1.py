#!/usr/bin/env python3
"""Create evidence panels, waist projection, and exact-copy video archive for approved brief."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, math, shutil, subprocess

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1')
ART = BASE / 'artifacts_v1'
VIDEO = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1')
PREV = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close')
DATA = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/geometry_v3_manifest.json')
BRIEF = BASE / 'artifact_brief_v1.json'
ANALYSIS = BASE / 'analysis_final_v1/analysis.json'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
OLD = PREV
STATIC = BASE / 'native_static_v2'
WAVE = BASE / 'native_elbow5_v1'
PARTIAL = BASE / 'native_static_v1'
RUNS = [(PARTIAL,'partial_static_v1'),(STATIC,'static_v2'),(WAVE,'elbow5_v1')]
VIDEO_ROWS=[]
INPUTS={}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def rec(path):
    p=Path(path); s=p.stat()
    return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}

def add_input(path, expected=None):
    p=Path(path)
    if p not in INPUTS:
        INPUTS[p]=rec(p)
    if expected is not None and INPUTS[p]['sha256'] != expected:
        raise RuntimeError(f'입력 SHA 불일치: {p}')
    return INPUTS[p]

def font(size): return ImageFont.truetype(str(FONT),size)

def centered(draw, xy, text, fnt, fill):
    x,y=xy
    box=draw.textbbox((0,0),text,font=fnt)
    draw.text((x-(box[2]-box[0])/2,y),text,font=fnt,fill=fill)

def panel(sources, labels, out, title, thumb_w=560):
    imgs=[Image.open(p).convert('RGB') for p in sources]
    size=imgs[0].size
    if any(im.size != size for im in imgs): raise RuntimeError('패널 프레임 크기가 다릅니다.')
    thumb_h=round(thumb_w*size[1]/size[0]); gap=24; margin=36; title_h=70; caption_h=55
    canvas=Image.new('RGB',(margin*2+len(imgs)*thumb_w+(len(imgs)-1)*gap,title_h+thumb_h+caption_h+margin*2),(248,248,248))
    d=ImageDraw.Draw(canvas)
    centered(d,(canvas.width//2,18),title,font(29),(20,20,20))
    for i,(im,label) in enumerate(zip(imgs,labels)):
        x=margin+i*(thumb_w+gap); y=title_h
        canvas.paste(im.resize((thumb_w,thumb_h),Image.Resampling.LANCZOS),(x,y))
        d.rectangle((x,y,x+thumb_w-1,y+thumb_h-1),outline=(70,70,70),width=2)
        centered(d,(x+thumb_w//2,y+thumb_h+12),label,font(22),(25,25,25))
    canvas.save(out)
    return [str(p) for p in sources]

def pair_panel(left,right,out,title,leftlabel,rightlabel,thumb_w=620):
    imgs=[Image.open(left).convert('RGB'),Image.open(right).convert('RGB')]
    if imgs[0].size!=imgs[1].size: raise RuntimeError('비교 이미지 크기가 다릅니다.')
    tw=thumb_w; th=round(tw*imgs[0].height/imgs[0].width); gap=28; margin=34; titleh=66; caph=50
    c=Image.new('RGB',(margin*2+2*tw+gap,titleh+th+caph+margin*2),(248,248,248)); d=ImageDraw.Draw(c)
    centered(d,(c.width//2,16),title,font(27),(20,20,20))
    for i,(im,label) in enumerate(zip(imgs,[leftlabel,rightlabel])):
        x=margin+i*(tw+gap); y=titleh
        c.paste(im.resize((tw,th),Image.Resampling.LANCZOS),(x,y)); d.rectangle((x,y,x+tw-1,y+th-1),outline=(70,70,70),width=2)
        centered(d,(x+tw//2,y+th+10),label,font(21),(25,25,25))
    c.save(out)
    return [str(left),str(right)]

def waist_plot(out, profile, waist, case_name):
    W,H=1700,1270
    im=Image.new('RGB',(W,H),(250,250,250)); d=ImageDraw.Draw(im)
    title='기타 G 프레임: 원본 평면 윤곽과 실제 contact point의 XY 투영'
    centered(d,(W//2,24),title,font(30),(15,15,15))
    centered(d,(W//2,68),f'{case_name} · Z 성분은 표시하지 않음 · 렌더 영상이 아닌 원자료 좌표 도식',font(21),(60,60,60))
    # G_Y spans body-length offset -0.4 m; G_X is symmetric about guitar centerline.
    length=0.49195743100000017; y0=-0.4
    xmin,xmax=-0.205,0.205; ymin,ymax=-0.415,0.12
    left,right=180,1510; top,bottom=150,1040
    def xy(x,y):
        return (left+(x-xmin)/(xmax-xmin)*(right-left), bottom-(y-ymin)/(ymax-ymin)*(bottom-top))
    # grid/ticks
    for x in [-.2,-.15,-.1,-.05,0,.05,.1,.15,.2]:
        px,py=xy(x,ymin); d.line((px,top,px,bottom),fill=(225,225,225),width=1)
        centered(d,(px,bottom+11),f'{x:.2f}',font(16),(60,60,60))
    for y in [-.4,-.35,-.3,-.25,-.2,-.15,-.1,-.05,0,.05,.1]:
        px,py=xy(xmin,y); d.line((left,py,right,py),fill=(225,225,225),width=1)
        d.text((left-82,py-11),f'{y:.2f}',font=font(16),fill=(60,60,60))
    d.rectangle((left,top,right,bottom),outline=(35,35,35),width=2)
    # Profile is t in [0,1] and half-width in metres; its body-length origin is G_y=-0.4m.
    profile_xy=[(float(t),float(hw)) for t,hw in profile]
    outer=[]; inner=[]
    for t,hw in profile_xy:
        y=y0+t*length
        outer.append((hw,y)); inner.append((-hw,y))
    silhouette=outer+list(reversed(inner))
    d.polygon([xy(*pt) for pt in silhouette],fill=(211,216,222),outline=(42,52,62))
    # Margins outside the source half-width: inner core +5 mm and flank band to +15 mm.
    core=[]; flank=[]
    for t,hw in profile_xy:
        y=y0+t*length
        core.extend([(hw,y),(hw+.005,y)])
        flank.extend([(hw+.005,y),(hw+.015,y)])
    # Use polygons by side, each sampled along the longitudinal axis.
    for sign in [1,-1]:
        p5=[(sign*hw,y0+t*length) for t,hw in profile_xy]
        p5out=[(sign*(hw+.005),y0+t*length) for t,hw in profile_xy]
        p15=[(sign*(hw+.015),y0+t*length) for t,hw in profile_xy]
        d.polygon([xy(*p) for p in p5+list(reversed(p5out))],fill=(248,190,93))
        d.polygon([xy(*p) for p in p5out+list(reversed(p15))],fill=(247,224,170))
        d.line([xy(*p) for p in p5],fill=(42,52,62),width=2)
    # waist interval from canonical analysis.
    ylo,yhi=waist['waist_G_y_interval_m']
    ylow=xy(xmin,ylo)[1]; yhigh=xy(xmin,yhi)[1]
    d.rectangle((left,yhigh,right,ylow),outline=(28,120,90),width=3)
    points=waist['contact_points_G_m']
    # Include only the requested early and late half-second sets, both from recorded native samples.
    for row in points:
        step=row['physics_step']; t=step/240.0
        if step<=120:
            col=(30,103,190) if row['positive_raw_lambda'] else (135,175,225)
            marker='early'
        elif step>=1080:
            col=(194,53,116) if row['positive_raw_lambda'] else (225,150,185)
            marker='late'
        else: continue
        gx,gy=row['point_G_m'][0],row['point_G_m'][1]
        px,py=xy(gx,gy); r=3
        if marker=='early': d.ellipse((px-r,py-r,px+r,py+r),fill=col,outline=(20,45,85))
        else: d.polygon([(px,py-r-1),(px-r-1,py+r),(px+r+1,py+r)],fill=col,outline=(90,25,60))
    centered(d,((left+right)//2,H-174),'G_X (m) · 양의 G_X는 기타의 아래쪽 edge 방향',font(20),(25,25,25))
    centered(d,(75,(top+bottom)//2),'G_Y (m)',font(20),(25,25,25))
    # legend remains in footer, away from plotted data.
    ly=H-115
    d.rectangle((210,ly+8,230,ly+28),fill=(211,216,222),outline=(42,52,62));d.text((240,ly+4),'source 윤곽',font=font(18),fill=(20,20,20))
    d.rectangle((390,ly+8,410,ly+28),fill=(248,190,93));d.text((420,ly+4),'윤곽에서 바깥 +5 mm core',font=font(18),fill=(20,20,20))
    d.rectangle((735,ly+8,755,ly+28),fill=(247,224,170));d.text((765,ly+4),'core 바깥부터 +15 mm flank 범위',font=font(18),fill=(20,20,20))
    d.ellipse((1120,ly+10,1134,ly+24),fill=(30,103,190));d.text((1142,ly+4),'초기 0–0.5 s',font=font(18),fill=(20,20,20))
    d.polygon([(1340,ly+8),(1332,ly+24),(1348,ly+24)],fill=(194,53,116));d.text((1357,ly+4),'후기 4.5–5 s',font=font(18),fill=(20,20,20))
    d.text((205,H-62),f'실제 waist interval: G_Y [{ylo:.6f}, {yhi:.6f}] m  |  윤곽 mapping: G_Y = -0.4 + t × {length:.9f} m',font=font(17),fill=(45,45,45))
    d.text((205,H-35),'기호 채움색은 raw lambda 양수 여부를 뜻함. 점은 높이를 버린 XY 투영이며 cooked 형상/힘/연속 접촉 인증이 아님.',font=font(17),fill=(45,45,45))
    im.save(out)

# Track direct inputs: brief closure, canonical inputs, media, images, geometry, font, previous case.
brief=json.loads(BRIEF.read_text())
analysis=json.loads(ANALYSIS.read_text())
for p,expected in brief['input_sha256'].items(): add_input(p,expected)
for p,expected in analysis['input_sha256'].items():
    # The canonical analysis itself contains the native input closure. Pin each file for provenance.
    add_input(p,expected)
for p in [BRIEF,ANALYSIS,DATA,FONT,PREV/'media/capture.json',PREV/'media/frames/whole_body/00000.png',PREV/'media/initial_support_side.png',
          WAVE/'media/capture.json',WAVE/'media/initial_support_side.png',STATIC/'media/initial_support_side.png']:
    add_input(p)
# exact output and comparison frame sources
FRAME_INPUTS=[]
for case,slug in RUNS:
    for f in ['report.json','initial_values.json','trace.json','media/capture.json','media/videos.json','media/whole_body.mp4','media/hands.mp4']:
        add_input(case/f)
for view in ['whole_body','hands']:
    for idx in [0,90,150]:
        p=WAVE/f'media/frames/{view}/{idx:05d}.png'; add_input(p); FRAME_INPUTS.append((p,view,idx,idx*8))
OLD_FRAME=PREV/'media/frames/whole_body/00000.png'; NEW_FRAME=WAVE/'media/frames/whole_body/00000.png'
add_input(OLD_FRAME); add_input(NEW_FRAME)
# Verify comparison camera matrices before composing.
oldcap=json.loads((PREV/'media/capture.json').read_text())['frames'][0]['cameras']['whole_body']
newcap=json.loads((WAVE/'media/capture.json').read_text())['frames'][0]['cameras']['whole_body']
if oldcap['view_matrix'] != newcap['view_matrix'] or oldcap['projection_matrix'] != newcap['projection_matrix']:
    raise RuntimeError('이전/새 전신 카메라 행렬이 달라 비교패널을 만들지 않습니다.')

# Save input snapshot before output generation.
inputs_before={str(p):r.copy() for p,r in INPUTS.items()}
# Generate native frame panels (captions outside the frame pixels).
whole_sources=[WAVE/f'media/frames/whole_body/{i:05d}.png' for i in [0,90,150]]
hands_sources=[WAVE/f'media/frames/hands/{i:05d}.png' for i in [0,90,150]]
panel(whole_sources,['0초 · step 0','3초 · step 720','5초 · step 1200'],ART/'elbow5_whole_0_3_5_v1.png','새 waist 조건 · 전신 실제 native 캡처')
panel(hands_sources,['0초 · step 0','3초 · step 720','5초 · step 1200'],ART/'elbow5_hands_0_3_5_v1.png','새 waist 조건 · 손 실제 native 캡처')
pair_panel(OLD_FRAME,NEW_FRAME,ART/'initial_whole_comparison_v1.png','초기 기타 위치 비교 · 전신 camera matrices exact match','이전 elbow5_close','새 right_thigh_waist elbow5')
pair_panel(PREV/'media/initial_support_side.png',WAVE/'media/initial_support_side.png',ART/'initial_side_comparison_v1.png','초기 측면 native 캡처 · 시각 비교','이전 elbow5_close','새 right_thigh_waist elbow5')
geom=json.loads(DATA.read_text())
waist=analysis['waist_regions']['native_elbow5_v1']
waist_plot(ART/'waist_profile_contacts_v1.png',geom['half_width_profile_t_m'],waist,'native_elbow5_v1')
# Save PNG input hashes used for frame composition in provenance.
for p,*_ in FRAME_INPUTS: add_input(p)

# Copy the six original MP4 byte-for-byte and create the requested manifest.
VIDEO.mkdir(parents=True,exist_ok=True)
for case,slug in RUNS:
    report=json.loads((case/'report.json').read_text())
    for view in ['whole_body','hands']:
        src=case/'media'/f'{view}.mp4'
        destdir=VIDEO/slug; destdir.mkdir(parents=True,exist_ok=True)
        dst=destdir/f'{view}.mp4'
        shutil.copyfile(src,dst)
        if sha(src)!=sha(dst): raise RuntimeError(f'복사 SHA 불일치: {src}')
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(src)],text=True))['streams'][0]
        VIDEO_ROWS.append({'case':case.name,'view':view,'source':str(src),'destination':str(dst),'source_sha256':sha(src),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':{k:probe[k] for k in ['width','height','nb_read_frames','avg_frame_rate','duration']},'completed':report['completed'],'physics_steps':report['physics_steps'],'physics_seconds':report['physics_seconds']})

# Collect post-generation input states; refuse to proceed if any source changed.
inputs_after={str(p):rec(p) for p in INPUTS}
unchanged=all(inputs_before[k]['sha256']==inputs_after[k]['sha256'] and inputs_before[k]['bytes']==inputs_after[k]['bytes'] and inputs_before[k]['mtime_ns']==inputs_after[k]['mtime_ns'] for k in inputs_before)
if not unchanged: raise RuntimeError('원자료가 생성 중 변경되었습니다.')
# Pixel-source frame provenance (frame hash/time/view/case). Native PNGs themselves remain untouched.
frame_sources=[]
for p,view,idx,step in FRAME_INPUTS:
    frame_sources.append({'source':str(p),'sha256':sha(p),'case':WAVE.name,'view':view,'frame_index':idx,'physics_step':step,'physics_time_s':step/240.0})
# Copy source hashes and output hashes are recorded separately; no re-encoding.
outputs=[]
for p in sorted(ART.iterdir()):
    if p.is_file() and p.name!='provenance_v1.json': outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
for p in sorted(VIDEO.rglob('*')):
    if p.is_file() and p.name not in ['manifest_v1.json','INDEX_V1.md','README_V1.md']:
        outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'videos':VIDEO_ROWS}
(VIDEO/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
index=['# right_thigh_waist_v1 영상 색인','', '원본 MP4를 재인코딩 없이 복사했습니다. `manifest_v1.json`에 원본/사본 SHA-256과 ffprobe 정보를 기록했습니다.','']
for case,slug in RUNS:
    for row in [r for r in VIDEO_ROWS if r['case']==case.name]:
        index.append(f"- `{case.name}` · `{row['view']}` · 완료 `{row['completed']}` · 물리 {row['physics_seconds']}초 · {row['ffprobe']['nb_read_frames']} frames/{row['ffprobe']['avg_frame_rate']} · [영상]({row['destination']})")
(VIDEO/'INDEX_V1.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
readme=f'''# 오른쪽 허벅지·waist 배치 native 보관

이 문서는 승인된 세 native 시도의 이미지와 원본 MP4를 정리합니다. 새 물리 실행·학습은 하지 않았으며, 기존 결과를 재인코딩하지 않았습니다. 원본/사본 여섯 영상의 해시와 ffprobe 정보는 [manifest]({VIDEO/'manifest_v1.json'})에 있습니다.

## 초기 위치 비교

![이전과 새 조건의 초기 전신 native 캡처. 전신 카메라 view/projection matrices가 일치함]({ART/'initial_whole_comparison_v1.png'})

![이전과 새 조건의 초기 측면 native 캡처 비교. 시각 비교이며 측면 카메라 행렬 메타데이터는 제공되지 않음]({ART/'initial_side_comparison_v1.png'})

새 후보 초기 기타 위치는 이전 기준 대비 world delta `[94.929004, 33.672083, -48.5815375] mm`, local G Y 회전 `-5°`입니다. 넥의 world 방향은 유지됐습니다. 이전/새 전신 캡처의 카메라 행렬은 exact match이며, 측면 이미지는 각 native 원본의 나란한 시각 비교입니다.

## 새 waist 조건의 native 프레임

![새 elbow5 조건의 실제 native 전신 프레임: 0, 3, 5초]({ART/'elbow5_whole_0_3_5_v1.png'})

![새 elbow5 조건의 실제 native 손 프레임: 0, 3, 5초]({ART/'elbow5_hands_0_3_5_v1.png'})

각 패널은 native 캡처 프레임을 그대로 배치했고, 캡션은 프레임 밖에 있습니다. wave의 실제 `R_Elbow_y` 이동 범위는 2.5–4.5초에 `10.09574359°`입니다. 실행 길이는 5초이며, wave 분석 구간과 혼동하지 않습니다.

## 기타 프레임의 윤곽과 waist contact 좌표

![기타 G 프레임에서 원본 윤곽과 native contact 좌표 XY 투영]({ART/'waist_profile_contacts_v1.png'})

윤곽은 [geometry manifest]({DATA})의 `half_width_profile_t_m`을 이용해 `G_Y = -0.4 + t × 0.491957431 m`로 배치했습니다. 양의 `G_X`는 기타의 아래쪽 edge 방향입니다. 그림의 core `+5 mm`와 flank `+15 mm` 구간 및 실제 native 접촉좌표는 서로 다른 근거로 표시했습니다. 점은 z를 버린 XY 투영이며, 초기 0–0.5초와 후기 4.5–5초 표본만 색을 달리합니다. 이 도식은 native 렌더 이미지가 아니며, cooked 형상·힘·연속 접촉을 인증하지 않습니다.

## 결과와 범위

| 조건 | 완료 | 물리 step | 물리 시간 | 영상 프레임/재생시간 | 결과 요약 |
|---|---:|---:|---:|---:|---|
| `native_static_v1` | 아니오 | 1148 | 4.783333초 | 145 / 4.833333초 | 부분 실행, abort로 분리 보관 |
| `native_static_v2` | 예 | 1200 | 5초 | 151 / 5.033333초 | 정지 조건 |
| `native_elbow5_v1` | 예 | 1200 | 5초 | 151 / 5.033333초 | elbow 1주기 조건 |

승인 분석에서 새 조건은 waist region presence `1198/1200` step, positive raw lambda `1198/1200` step이며, 마지막 120 step은 각각 `120/120`입니다. 이전 튜닝보다 waist 목표 영역 접촉은 개선됐지만 이는 접촉 표본이지 힘(N)이나 지지력 분담을 뜻하지 않습니다. 오른 허벅지 접촉도 `1198/1200` step으로 오목한 측면(flank)을 받치므로 독립된 허리 지지로 볼 수 없습니다. Thorax는 `72/1200` presence, `33/1200` positive이며 마지막 120 step은 presence `0`입니다. 상완과 왼손 손가락 접촉은 계속 남습니다. 왼손 접촉은 엄지가 아니라 `middle2/fret6`, `index2/fret5/root`, `pinky3/root`입니다.

새 elbow 조건의 초기 대비 기타 body-centre 최종/최대 변위는 `11.66041149/11.72524298 mm`, SO(3) 최종/최대 변화는 `5.2166087°/6.09468586°`입니다. 정지 기준 대비 추가 최대 변화는 `0.1547542294 mm`, `0.148811516°`입니다. body9 scalar 최대 변화는 `2.23482765°`입니다. raw positive lambda는 힘 단위가 아니며, contact presence와 구별합니다.

이 단계는 3 native 시도 중 2회 5초 완료, 1회 부분 중단입니다. CPU 후보 검사는 9개 완료(7 거절, 2 수락)됐습니다. 고정 strap/기타 부착/직접 기타 힘/자세 덮어쓰기/학습 checkpoint 연결은 없었고, root와 하체는 고정, strap은 OFF입니다. full 81개 목표는 body 9개와 arm 24개 effort, head 6개와 finger 42개 position으로 구성되며, body 설정은 K=150, D=1, target=40, cap=10입니다. 두 완료 시험은 초기 상태와 첫 2.5초 trace가 exact match입니다. source1의 입력 목록에는 사전 SHA가 없는 손 STL 35개가 누락된 한계가 있으며, source2 이후에는 human mesh 37개를 pin했습니다. source3/helper1의 shape 검수 prototype은 fitting에 실행하지 않았습니다. 한 번의 정지와 한 번의 단일 elbow 주기이므로 임의 동작, 반복성, 음악 성공을 인증하지 않습니다.

## 원자료와 파일

- [승인 brief]({BRIEF})
- [canonical analysis]({ANALYSIS})
- [이전 기준 native 영상/프레임]({PREV/'media/whole_body.mp4'})
- [영상 색인]({VIDEO/'INDEX_V1.md'}) · [manifest]({VIDEO/'manifest_v1.json'})
- [생성 입력·출력 SHA provenance]({ART/'provenance_v1.json'})
- [producer]({ART/'build_artifacts_v1.py'})
'''
(ART/'README_V1.md').write_text(readme,encoding='utf-8')
(VIDEO/'README_V1.md').write_text(f'''# right_thigh_waist_v1 영상 보관\n\n세 native 시도의 전신·손 영상 6개를 원본 bytes 그대로 복사했습니다. 재인코딩은 없습니다. 상세 결과는 [한국어 산출물 설명]({ART/'README_V1.md'}), 영상 항목은 [INDEX_V1]({VIDEO/'INDEX_V1.md'}), 복사 SHA와 ffprobe는 [manifest_v1]({VIDEO/'manifest_v1.json'})를 확인하세요.\n''',encoding='utf-8')
# Refresh output inventory now that docs/manifest/index exist.
outputs=[]
for p in sorted(ART.iterdir()):
    if p.is_file() and p.name!='provenance_v1.json': outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
for p in sorted(VIDEO.rglob('*')):
    if p.is_file() and p.name!='provenance_v1.json': outputs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
provenance={
 'task':'승인된 right_thigh_waist_v1 결과의 이미지·문서 작성 및 원본 영상 복사',
 'physics_runs':0,'training_updates':0,'video_reencodes':0,'copied_videos':len(VIDEO_ROWS),
 'direct_inputs_before_after':{k:{'before':inputs_before[k],'after':inputs_after[k],'unchanged':inputs_before[k]==inputs_after[k]} for k in sorted(inputs_before)},
 'camera_comparison':{'previous_whole_body_view_projection_exact_match':True,'side_capture_matrix_metadata_available':False},
 'frame_sources':frame_sources,
 'video_rows':VIDEO_ROWS,
 'outputs':outputs,
 'producer':{'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size},
 'font':{'path':str(FONT),'sha256':sha(FONT),'bytes':FONT.stat().st_size},
}
(ART/'provenance_v1.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'videos':len(VIDEO_ROWS),'video_bytes':sum(r['bytes'] for r in VIDEO_ROWS),'inputs':len(inputs_before),'unchanged':unchanged,'outputs':len(outputs)},ensure_ascii=False))
