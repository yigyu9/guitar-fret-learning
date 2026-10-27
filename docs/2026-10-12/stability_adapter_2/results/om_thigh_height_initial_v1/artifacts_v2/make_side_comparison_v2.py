#!/usr/bin/env python3
"""Fix cropped follow-camera note and clarify source-gap side-view labels."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1')
A=P/'artifacts_v2';A1=P/'artifacts_v1';FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
SIDE=[Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png'),P/'native_v1/thigh_gap8mm/media/initial_thigh_side.png',P/'native_v1/thigh_gap3mm/media/initial_thigh_side.png']
LABELS=['이전 높은 기준 · 초기 측면','양 Hip 최소 source gap 8 mm · 초기 측면','양 Hip 최소 source gap 3 mm · 초기 측면']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(ps):return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in ps}
# These v1 files are consumed references: assert their stored hashes before reusing them.
v1prov=json.loads((A1/'provenance_v1.json').read_text())
assert v1prov['inputs_before']==v1prov['inputs_after']
for rel in ('whole_body_0_2_5s_comparison.png','initial_strings_3conditions.png','initial_side_comparison.png'):
 p=A1/rel;assert v1prov['outputs'][str(p)]['sha256']==sha(p)
assert v1prov['outputs'][str(Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/manifest_v1.json'))]['sha256']==sha(Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/manifest_v1.json'))
inputs=SIDE+[Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30/initial_values.json'),Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/initial_values.json'),A1/'README.md',A1/'make_archive_v1.py',P/'native_v1/thigh_gap8mm/initial_values.json',P/'native_v1/thigh_gap3mm/initial_values.json',P/'search_v2/search.json',P/'verification_v1.json',P/'native_v1/thigh_gap8mm/media/capture.json',P/'native_v1/thigh_gap3mm/media/capture.json',Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/capture.json'),A1/'provenance_v1.json',A1/'whole_body_0_2_5s_comparison.png',A1/'initial_strings_3conditions.png',A1/'initial_side_comparison.png',Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/manifest_v1.json'),FONT]
before=pin(inputs)
assert SIDE[0].is_file()
assert Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30/initial_values.json').read_bytes()==Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/initial_values.json').read_bytes()
ims=[Image.open(p).convert('RGB') for p in SIDE];w=max(i.width for i in ims);h=max(i.height for i in ims);gap=12;head=66;foot=64
out=Image.new('RGB',(3*w+4*gap,h+head+foot+gap),(248,248,248));d=ImageDraw.Draw(out);title=ImageFont.truetype(str(FONT),18);note=ImageFont.truetype(str(FONT),16)
for j,(im,label) in enumerate(zip(ims,LABELS)):
 x=gap+j*(w+gap);out.paste(im,(x,head));d.text((x+5,12),label,font=title,fill=(15,15,15))
d.text((gap,head+h+10),'각 native 측면 카메라는 기타를 따라가는 follow view입니다. 화면 픽셀 높이 차이는 world z 하강량을 뜻하지 않습니다.',font=note,fill=(20,20,20))
target=A/'initial_side_comparison_v2.png';out.save(target)
after=pin(inputs);assert before==after
outputs=[A/'make_side_comparison_v2.py',target,A/'README_V2.md',A/'CHANGED_FILES_V2.md']
(A/'provenance_v2.json').write_text(json.dumps({'inputs_before':before,'inputs_after':after,'outputs':pin(outputs),'producer_sha256':sha(outputs[0]),'source_v1_provenance_verified':True,'notes':['v1 lower follow-camera caption was cropped; v2 adds a 64px bottom band','low condition labels explicitly say minimum source gap over both Hip capsules','old high ON side image initial_values is byte-identical to high OFF reference','native reruns 0; video recopy 0; existing V files unmodified']},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'inputs':len(inputs),'before_after_equal':before==after,'output_sha256':sha(target),'size':Image.open(target).size},ensure_ascii=False))
