from pathlib import Path
import hashlib, json, subprocess
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1')
ART=ROOT/'artifacts_v1'; VID=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1')
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
PRODUCER=ART/'build_archive_v2.py'
README1=ART/'README_V1.md'; README2=ART/'README_V2.md'; PROV1=ART/'provenance_v1.json'; PROV2=ART/'provenance_v2.json'
CHART=ART/'elbow_5deg_response_and_body_delta_v2.png'
SUPPORT=ART/'native5deg_initial_support_detail.png'
CROP=ART/'native5deg_upperbody_samecrop_0_5s.png'

sources={
 'initial_support':ROOT/'native_v4/elbow_motion5/media/initial_native.png',
 'whole_0':ROOT/'native_v4/elbow_motion5/media/frames/whole_body/00000.png',
 'whole_5':ROOT/'native_v4/elbow_motion5/media/frames/whole_body/00150.png',
 'trace':ROOT/'elbow_comparison_trace_v2.json',
 'comparison':ROOT/'elbow_comparison_v2.json',
 'verify_static':ROOT/'analysis_v3/static_cradle/verification.json',
 'verify_2deg':ROOT/'analysis_v4/elbow_motion/verification.json',
 'verify_5deg':ROOT/'analysis_v5/elbow_motion5/verification.json',
 'contact_region':ROOT/'contact_region_v3.json',
}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''): h.update(block)
 return h.hexdigest()
def snap(path):
 path=Path(path); s=path.stat()
 return {'sha256':sha(path),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}

# Include every consumed V1 artifact/copy plus all direct source media and the executing helper.
v1=json.loads(PROV1.read_text(encoding='utf-8'))
inputs={Path(p) for p in v1['outputs']}
inputs.update(sources.values())
inputs.update([README1,PROV1,ART/'build_archive_v1.py',ART/'native_whole_body_timeline.png',ART/'native_hands_timeline.png',ART/'elbow_5deg_response_and_body_delta.png',ART/'static_vs_elbow_motion5_side_by_side.mp4',VID/'manifest_v1.json',VID/'INDEX_V1.md',ROOT/'compare_elbow_motion_v2.py',FONT,PRODUCER])
inputs={p for p in inputs if p.exists()}
before={str(p):snap(p) for p in sorted(inputs)}

# Rebuild chart from authoritative trace with a figure-level legend outside the plot.
data=json.loads(sources['trace'].read_text(encoding='utf-8'))
plt.rcParams['font.family']='NanumGothic'; plt.rcParams['axes.unicode_minus']=False
matplotlib.font_manager.fontManager.addfont(str(FONT))
fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True,constrained_layout=False)
t=data['time_s']; pt=data['physics_time_s']
l1,=axs[0].plot(pt,data['elbow_command_delta_deg'],label='명령 변화',linewidth=2)
l2,=axs[0].plot(pt,data['elbow_actual_moving_minus_static_deg'],label='실제 R_Elbow_y 변화',linewidth=1.5)
axs[0].set_ylabel('각도 변화 (°)'); axs[0].grid(alpha=.25)
axs[1].plot(t,data['same_time_body_centre_delta_mm'],color='#c44e52',linewidth=1.8)
axs[1].set_ylabel('동시점 body-bbox\n중심 차이 (mm)'); axs[1].grid(alpha=.25)
axs[2].plot(t,data['same_time_rotation_delta_deg'],color='#4c72b0',linewidth=1.8)
axs[2].set_ylabel('동시점 전체 SO(3)\n차이 (°)'); axs[2].set_xlabel('물리 시간 (초)'); axs[2].grid(alpha=.25)
axs[-1].set_xlim(2.5,5)
fig.suptitle('5° 명령의 native 응답과 같은 시각의 자세 차이 · 2.5–5초',fontsize=15,y=.99)
fig.legend([l1,l2],[l1.get_label(),l2.get_label()],loc='upper center',bbox_to_anchor=(.5,.955),ncol=2,frameon=True)
fig.subplots_adjust(top=.90,hspace=.18,left=.12,right=.98,bottom=.08)
fig.savefig(CHART,dpi=170); plt.close(fig)

# Keep the actual 1280x960 initial native support view byte-identical.
SUPPORT.write_bytes(sources['initial_support'].read_bytes())
# Same-coordinate 2D crop from the actual native whole-body camera, not a new camera or projection.
font=ImageFont.truetype(str(FONT),24)
frames=[]
for key,label in [('whole_0','0.0 s · 초기 native 캡처'),('whole_5','5.0 s · native 종료 캡처')]:
 im=Image.open(sources[key]).convert('RGB')
 crop=im.crop((420,80,910,470)).resize((735,585),Image.Resampling.LANCZOS)
 frames.append((crop,label))
canvas=Image.new('RGB',(1500,700),(246,247,249)); draw=ImageDraw.Draw(canvas)
draw.text((24,14),'native 전신 카메라의 동일 좌표 상체 crop · 화면 표시용 2D 확대',font=font,fill=(25,35,50))
for i,(im,label) in enumerate(frames):
 x=12+i*750; y=58; canvas.paste(im,(x,y)); draw.rectangle((x,y,x+im.width,y+im.height),outline=(120,130,145),width=2); draw.text((x+8,y+im.height+8),label,font=font,fill=(25,35,50))
canvas.save(CROP)

text=README1.read_text(encoding='utf-8')
old='/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/elbow_5deg_response_and_body_delta.png'
if text.count(old)!=1: raise RuntimeError('V1 chart embed/link occurrence not unique')
text=text.replace(old,str(CHART))
insert='''

## 오른쪽 상완 시점 보완

![5° 조건의 실제 native 초기 support view]('''+str(SUPPORT)+''')

위 support view는 native_v4/elbow_motion5의 실제 초기 native 렌더입니다. 아래 두 장은 같은 native whole-body 카메라 프레임의 같은 픽셀 좌표를 잘라 확대한 2D crop이며, 별도의 native camera나 접촉 측정이 아닙니다.

![동일 전신 카메라의 0초·5초 상체 2D crop]('''+str(CROP)+''')

앞의 hands timeline은 기타 넥/왼손 쪽을 보는 카메라입니다. 이 시점으로 오른쪽 상완 contact 여부를 판정하지 않습니다.
'''
text += insert
text=text.replace('# 겨드랑이 지지 자세: 팔꿈치 영향 격리 진단', '# 겨드랑이 지지 자세: 팔꿈치 영향 격리 진단\n\n> V2 보완본: 그래프 범례를 plotting area 밖에 두고, 실제 초기 support view 및 동일 전신 카메라 상체 crop을 추가했습니다. V1과 기존 원본 미디어는 변경하지 않았습니다.')
README2.write_text(text,encoding='utf-8')

after={str(p):snap(p) for p in sorted(inputs)}
if before!=after: raise RuntimeError('a consumed V1/source input changed')
outputs={}
for p in [CHART,SUPPORT,CROP,README2]: outputs[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
prov={'scope':'metadata/visual supplement only; no native or training run, no original video copy/re-encode', 'inputs_before':before,'inputs_after':after,'input_unchanged':True,'producer':{str(PRODUCER):snap(PRODUCER)},'font':{str(FONT):snap(FONT)},'outputs':outputs,'support_image_source':{'path':str(sources['initial_support']),'source_sha256':sha(sources['initial_support']),'copy_sha256':sha(SUPPORT)},'same_camera_crop_sources':{str(sources[k]):snap(sources[k]) for k in ('whole_0','whole_5')},'chart_trace_source':{str(sources['trace']):snap(sources['trace'])},'note':'V1 files, manifests, copied native videos, and source captures remain unchanged.'}
PROV2.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'outputs':outputs,'provenance':str(PROV2),'input_count':len(inputs)},ensure_ascii=False))
