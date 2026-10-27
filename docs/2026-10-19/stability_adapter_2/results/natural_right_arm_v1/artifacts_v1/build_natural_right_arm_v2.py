#!/usr/bin/env python3
"""Add a native2/native3 timeline comparison and preserve completed source videos."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path('/home/ajou/yigyu/3')
ART=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1'
VID=ROOT/'docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1'
P=ROOT/'docs/2026-10-19/stability_adapter_v1' # replaced below with actual P
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
V2=P/'native_v2/front160mm'; V3=P/'native_v3/front160mm_lift12mm'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')


def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):
 p=Path(p); st=p.stat()
 return {'sha256':sha(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
def fnt(n): return ImageFont.truetype(str(FONT),n)
def center(d,x,y,text,ft,fill):
 b=d.textbbox((0,0),text,font=ft);d.text((x-(b[2]-b[0])/2,y),text,font=ft,fill=fill)

def main():
 outputs=[ART/'native2_native3_timeline_comparison.png',ART/'README_V2.md',ART/'provenance_v2.json',
          VID/'front160mm_lift12mm_whole_body.mp4',VID/'front160mm_lift12mm_hands.mp4',VID/'manifest_v2.json',VID/'README_v2.md']
 if any(p.exists() for p in outputs):raise FileExistsError('refusing to overwrite any existing output')
 p1=json.loads((ART/'provenance_v1.json').read_text())
 old_outputs={x['path']:x for x in p1['outputs_sha256_bytes']}
 old_prov=ART/'provenance_v1.json'; old_video_manifest=VID/'manifest_v1.json'; old_video_manifest_sha=sha(old_video_manifest)
 old_v1_before={k:snap(Path(k)) for k in old_outputs}
 old_v1_before[str(old_prov)]=snap(old_prov); old_v1_before[str(old_video_manifest)]=snap(old_video_manifest)
 old_video_entries=json.loads(old_video_manifest.read_text())['videos']
 for v in old_video_entries:
  dst=Path(v['destination'])
  if sha(dst)!=v['copy_sha256'] or sha(v['source'])!=v['source_sha256_before']:
   raise RuntimeError(f'v1 source/copy mismatch: {dst}')
  old_v1_before[str(dst)]=snap(dst); old_v1_before[str(Path(v['source']))]=snap(Path(v['source']))

 verify2=P/'analysis_v1/verification.json'; verify3=P/'analysis_v2/verification.json'
 case2=json.loads(verify2.read_text())['cases']['front160mm']
 verification3=json.loads(verify3.read_text()); case3=verification3['cases']['front160mm_lift12mm']
 if not json.loads(verify2.read_text()).get('passed') or not verification3.get('passed'):
  raise RuntimeError('native verification is not passed')
 sources=[ROOT/'stability_adapter_2/AGENTS.md',ROOT/'stability_adapter_2/README.md',ROOT/'stability_adapter_2/EXPERIMENT_WORKFLOW.md',
   verify2,P/'analysis_v1/posture_shape_trace.json',P/'native_v2/front160mm/report.json',P/'native_v2/front160mm/initial_values.json',
   V2/'media/capture.json',V2/'media/videos.json',V2/'media/whole_body.mp4',V2/'media/hands.mp4',
   verify3,P/'analysis_v2/posture_shape_trace.json',V3/'report.json',V3/'initial_values.json',V3/'media/capture.json',V3/'media/videos.json',
   V3/'media/whole_body.mp4',V3/'media/hands.mp4',
   ART/'initial_pose_pair.png',ART/'native_v2_timeline_0_2_5s.png',ART/'README_V1.md',ART/'build_natural_right_arm_v1.py',ART/'provenance_v1.json',
   old_video_manifest,FONT]
 frame_paths=[]
 for base in (V2,V3):
  cap=json.loads((base/'media/capture.json').read_text())
  rows={x['physics_step']:x for x in cap['frames']}
  for step,idx,time_s in ((0,'00000',0.0),(480,'00060',2.0),(1200,'00150',5.0)):
   row=rows.get(step)
   if row is None or row['time_s']!=time_s:raise RuntimeError(f'missing expected capture time {base} step {step}')
   frame=base/f'media/frames/whole_body/{idx}.png'
   if row['image_sha256'].get(str(frame))!=sha(frame):raise RuntimeError(f'capture SHA mismatch for {frame}')
   sources.append(frame); frame_paths.append((base.name,frame,time_s))
 sources += [Path(v['source']) for v in old_video_entries]
 before={str(Path(x)):snap(Path(x)) for x in sources}
 helper=Path(__file__).resolve(); helper_before=snap(helper)

 # Compose a two-condition by three-time panel from recorded native frames.
 row_labels=['native 2 · front160mm','native 3 · front160mm_lift12mm (+12 mm target)']
 times=['0초','2초','5초']; names=['00000','00060','00150']
 imgs=[]
 for base in (V2,V3):
  imgs.append([Image.open(base/f'media/frames/whole_body/{n}.png').convert('RGB') for n in names])
 if len({im.size for row in imgs for im in row})!=1:raise RuntimeError('timeline image dimensions differ')
 iw,ih=imgs[0][0].size; cw=640; ch=round(ih*cw/iw); left=275; gap=18; outer=28; title_h=72; row_h=38; footer=120
 W=outer*2+left+3*cw+2*gap; H=outer+title_h+2*(row_h+ch+18)+footer
 canvas=Image.new('RGB',(W,H),(247,249,252)); d=ImageDraw.Draw(canvas)
 center(d,W//2,16,'실제 native 2 / native 3 whole_body 비교',fnt(34),(24,38,58))
 y=outer+title_h
 for r in range(2):
  d.text((outer+2,y+3),row_labels[r],font=fnt(24),fill=(34,49,67))
  y+=row_h
  for c in range(3):
   x=outer+left+c*(cw+gap)
   center(d,x+cw//2,y-3,times[c],fnt(21),(34,49,67))
   resized=imgs[r][c].resize((cw,ch),Image.Resampling.LANCZOS)
   canvas.paste(resized,(x,y+28))
  y+=ch+44
 fy=H-footer+12
 d.rounded_rectangle((outer,fy,W-outer,H-outer),radius=12,fill=(229,235,243))
 d.text((outer+16,fy+11),'각 프레임은 저장된 native 렌더입니다. 5초 시점에도 기타 위치·회전 및 접촉 상태를 함께 해석해야 합니다.',font=fnt(19),fill=(31,44,62))
 d.text((outer+16,fy+48),'native 3은 큰 초기 이탈 뒤 2→5초 변화가 작아졌지만, head 접촉과 큰 전체 회전으로 후보에서 거절됐습니다.',font=fnt(19),fill=(31,44,62))
 image=ART/'native2_native3_timeline_comparison.png'; canvas.save(image,optimize=True)

 # Preserve the earlier native2 exact copies and copy only the newly completed native3 MP4s.
 new_entries=[]
 for view in ('whole_body','hands'):
  entry=json.loads((V3/'media/videos.json').read_text())[view]
  src=Path(entry['path']); dst=VID/f'front160mm_lift12mm_{view}.mp4'
  sb=snap(src); shutil.copyfile(src,dst); sa=snap(src); cp=snap(dst)
  if sb!=sa or sb['sha256']!=cp['sha256'] or sb['bytes']!=cp['bytes']:
   raise RuntimeError(f'native3 exact copy/source immutability failed: {src}')
  new_entries.append({'source':str(src),'source_sha256_before':sb['sha256'],'source_sha256_after':sa['sha256'],
    'destination':str(dst),'copy_sha256':cp['sha256'],'bytes':cp['bytes'],'label':'native 3 · front160mm_lift12mm (+12 mm target)',
    'view':view,'fps':entry['stream']['avg_frame_rate'],'duration_seconds':entry['stream']['duration'],
    'frames':int(entry['stream']['nb_read_frames']),'physics_seconds':5.0,'mp4_copy':'byte-exact; no re-encoding'})
 old_entries=[]
 for v in old_video_entries:
  src=Path(v['source']); dst=Path(v['destination']); stats=json.loads((V2/'media/videos.json').read_text())[v['view']]['stream']
  old_entries.append({'source':str(src),'source_sha256_before':v['source_sha256_before'],'source_sha256_after':sha(src),
    'destination':str(dst),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'label':'native 2 · front160mm',
    'view':v['view'],'fps':stats['avg_frame_rate'],'duration_seconds':stats['duration'],
    'frames':int(stats['nb_read_frames']),'physics_seconds':5.0,'mp4_copy':'existing v1 exact copy; not recopied'})
 manifest={'schema_version':2,'videos':old_entries+new_entries,
   'description':'native 2/3 두 완료조건의 whole_body/hands 네 파일; v1 native2 사본은 유지, native3 두 MP4만 새 경로로 exact-copy'}
 if len({x['destination'] for x in manifest['videos']})!=4:raise RuntimeError('expected four unique output video paths')
 (VID/'manifest_v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

 readme=f'''# Natural right-arm · native 2/3 비교\n\n이 문서는 실제로 완료된 두 5초 조건을 함께 정리합니다. 사용자 사진은 정성 참고일 뿐 정확한 3D 재구성 기준이 아닙니다. 이전 native 11의 교차 팔 자세는 정지 유지 후보였으나 연주 자세로 자연스럽지 않아 채택하지 않았습니다. [초기 장면 비교]({ART/'initial_pose_pair.png'})와 native 2 원래 프레임은 [v1 문서]({ART/'README_V1.md'})에서 볼 수 있습니다.\n\n![native 2와 native 3의 실제 0·2·5초 whole_body 프레임 비교]({image})\n\n## 결과 비교\n\n두 실행 모두 root/하체 고정, 스트랩 OFF, 왼팔·왼손을 기타에서 떼고 왼손 grip 없이 기타를 자유롭게 둔 5초 정지 진단입니다. 음악 actor/policy는 0입니다. native 3은 front160mm의 상완 목표 위치를 +12 mm 올린 비교 조건입니다.\n\n| 관측값 | native 2 · front160mm | native 3 · front160mm_lift12mm |\n|---|---:|---:|\n| body bounding-box 중심 초기 대비 이동 | {case2['final_body_bbox_centre_change_mm']:.3f} mm | {case3['final_body_bbox_centre_change_mm']:.3f} mm |\n| actor-root 초기 대비 이동 | {case2['final_root_position_change_mm']:.3f} mm | {case3['final_root_position_change_mm']:.3f} mm |\n| 초기 대비 전체 SO(3) 회전 | {case2['final_rotation_change_deg']:.3f}° | {case3['final_rotation_change_deg']:.3f}° |\n| 2→5초 body 중심 이동 / 회전 변화 | {case2['body_centre_2_to_5s_mm']:.3f} mm / {case2['rotation_2_to_5s_deg']:.3f}° | {case3['body_centre_2_to_5s_mm']:.3f} mm / {case3['rotation_2_to_5s_deg']:.3f}° |\n| 오른 전완 접촉 표본 | {case2['endpoints']['right_forearm_presence']}/1200 | {case3['endpoints']['right_forearm_presence']}/1200 |\n| 오른상완 / 왼팔·왼손 접촉 표본 | {case2['endpoints']['right_upper_arm_presence']}/1200 / {case2['endpoints']['left_arm_hand_presence']}/1200 | {case3['endpoints']['right_upper_arm_presence']}/1200 / {case3['endpoints']['left_arm_hand_presence']}/1200 |\n| Head 접촉 표본 | {case2['endpoints']['head_presence']}/1200 | {case3['endpoints']['head_presence']}/1200 |\n\n표의 접촉 count는 240 Hz physics endpoint 1,200개 기준이며 접촉력·모멘트 기여를 나타내지 않습니다. native 3의 Head raw lambda count는 N 단위 힘이 아니므로 힘처럼 표시하지 않습니다. native 3은 2→5초 변화가 작아졌지만 그 전에 크게 이탈·회전한 자세에 머문 것이며, Head 접촉 812/1200과 전체 회전 76.809°로 거절된 조건입니다. native 2는 Head 접촉이 없고 전완 접촉이 더 자주 관측됐지만 기타 중심 이동 163.447 mm·회전 62.320°로 유지에 실패했습니다. 따라서 natural-arm shape reference는 native 2이며, 어느 조건도 기타 유지 성공으로 보지 않습니다.\n\n이미지의 각 칸은 저장된 actual native frame을 사용합니다. 화면상 겹침으로 실제 PhysX cooked 관통/여유를 보증하지 않습니다. 새 학습이나 물리 실행은 이 문서 작업에서 추가하지 않았습니다. native 진단은 5초 완료 2회와 Jacobian gate에서 약0.125초에 중단된 native 1회입니다.\n\n## 영상과 원자료\n\n![native 2 전신 영상]({VID/'front160mm_whole_body.mp4'})\n![native 2 손 영상]({VID/'front160mm_hands.mp4'})\n![native 3 전신 영상]({VID/'front160mm_lift12mm_whole_body.mp4'})\n![native 3 손 영상]({VID/'front160mm_lift12mm_hands.mp4'})\n\n- [네 영상 source/copy SHA manifest]({VID/'manifest_v2.json'}) · [video README v2]({VID/'README_v2.md'})\n- [native 2 verification]({verify2}) · [native 2 report]({V2/'report.json'})\n- [native 3 verification]({verify3}) · [native 3 report]({V3/'report.json'})\n- [사용자 reference.jpeg]({P/'reference.jpeg'})\n- [입력·출력 provenance v2]({ART/'provenance_v2.json'})\n'''
 (ART/'README_V2.md').write_text(readme,encoding='utf-8')
 video_readme=f'''# Native 2/3 whole_body·hands 영상\n\n각 native 조건의 물리 구간은 5.000초이고 MP4는 151 frame·30 fps·5.033333초 재생입니다. native 2 원본은 기존 v1 사본을 사용하고, native 3 두 영상만 exact-copy했습니다. 재인코딩하지 않았습니다. 자세 차이 및 해석은 [결과 README v2]({ART/'README_V2.md'})를 참고하세요.\n\n![native 2 전신]({VID/'front160mm_whole_body.mp4'})\n![native 2 손]({VID/'front160mm_hands.mp4'})\n![native 3 전신]({VID/'front160mm_lift12mm_whole_body.mp4'})\n![native 3 손]({VID/'front160mm_lift12mm_hands.mp4'})\n\n[네 파일의 source/copy SHA]({VID/'manifest_v2.json'})\n'''
 (VID/'README_v2.md').write_text(video_readme,encoding='utf-8')

 after={str(Path(x)):snap(Path(x)) for x in sources}
 helper_after=snap(Path(__file__).resolve())
 if before!=after or helper_before!=helper_after:raise RuntimeError('an input/helper changed during v2 artifact creation')
 old_v1_after={k:snap(Path(k)) for k in old_v1_before}
 if old_v1_before!=old_v1_after:raise RuntimeError('an existing v1 output changed')
 # Include all input/copy and output evidence except provenance self-hash.
 generated=[image,ART/'README_V2.md',VID/'manifest_v2.json',VID/'README_v2.md',
            VID/'front160mm_lift12mm_whole_body.mp4',VID/'front160mm_lift12mm_hands.mp4',helper]
 prov={'schema_version':2,'scope':'native2/3 자료 후처리; native/physics/training 0회',
   'inputs_before':before,'inputs_after':after,'producer_sha256_before':helper_before['sha256'],'producer_sha256_after':helper_after['sha256'],
   'existing_v1_outputs_before_after':{k:{'sha256_before':v['sha256'],'sha256_after':old_v1_after[k]['sha256'],'unchanged':v==old_v1_after[k]} for k,v in old_v1_before.items()},
   'existing_v1_preservation_verified':old_v1_before==old_v1_after,
   'native3_video_copies':new_entries,'native2_video_recopy_count':0,'new_video_reencoding_count':0,
   'selected_frame_sources':[{'path':str(base/f'media/frames/whole_body/{idx}.png'),'time_s':time_s,'sha256':sha(base/f'media/frames/whole_body/{idx}.png')} for base in (V2,V3) for idx,time_s in zip(names,[0,2,5])],
   'outputs_sha256_bytes':[{'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size} for p in generated],
   'self_hash_note':'provenance_v2는 자기 SHA를 포함하지 않으며 root 독립 보존 감사에서 해시한다.'}
 (ART/'provenance_v2.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'video_count':len(manifest['videos']),'new_video_copies':len(new_entries),'unique_destinations':len({x['destination'] for x in manifest['videos']}),
   'old_v1_preserved':True,'producer_sha256':helper_after['sha256'],'provenance_sha256':sha(ART/'provenance_v2.json')},ensure_ascii=False))

if __name__=='__main__': main()
