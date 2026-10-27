from pathlib import Path
import argparse,hashlib,json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image
ROOT=Path('/home/ajou/yigyu/3'); P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1'; OUT=P/'artifacts_v1/static_preview'
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CASES=[('margin_only','여유각 보정만','analysis_margin_only_static_v1.json','visual_margin_only_static_v1'),('roll_m2','Roll −2°','analysis_roll_m2_static_v1.json','visual_roll_m2_static_v1'),('roll_p2','Roll +2°','analysis_roll_p2_static_v1.json','visual_roll_p2_static_v1'),('torso_p2','Torso +2°','analysis_torso_p2_static_v1.json','visual_torso_p2_static_v1')]
EXPECTED={'margin_only':(3.286738679280705,0.8194552852290521,418),'roll_m2':(6.066885163887934,2.3525767903894104,46),'roll_p2':(20.857204167035686,4.727967924051142,93),'torso_p2':(3.9994683589343527,1.1593499089869337,113)}
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def expected_inputs():
 exp={}
 def add(path,digest=None):
  path=str(Path(path).resolve())
  if digest is not None and path in exp and exp[path] not in (None,digest):raise RuntimeError('conflicting SHA claims '+path)
  if digest is not None:exp[path]=digest
  else:exp.setdefault(path,None)
 add(OUT/'preview_producer_v1.py');add(FONT)
 for key,_,analysis,visual in CASES:
  ap=P/analysis;rp=P/visual/'report.json'
  add(ap);add(rp)
  ad=read(ap);rd=read(rp)
  for path,digest in ad.get('input_sha256',{}).items():add(path,digest)
  for path,digest in rd.get('input_sha256',{}).items():add(path,digest)
  if not rd.get('inputs_unchanged'):raise RuntimeError('visual input guard false: '+key)
  for snap in rd['snapshots']:add(snap['path'],snap['sha256'])
  front={x['path']:x['sha256'] for x in rd.get('annotated_frames',[]) if '/frames/front/' in x['path']}
  for frame in ('00000.png','00150.png'):
   path=P/visual/'frames/front'/frame
   if str(path) not in front:raise RuntimeError('requested annotated front frame absent '+str(path))
   add(path,front[str(path)])
 return exp
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--pin',action='store_true');args=parser.parse_args()
 OUT.mkdir(parents=True,exist_ok=True);exp=expected_inputs()
 if args.pin:
  before={'schema':'initial_pose_search_static_preview_before_v1','producer':{'path':str(OUT/'preview_producer_v1.py'),'sha256':sha(OUT/'preview_producer_v1.py')},'inputs':[{'path':p,'sha256':sha(p)} for p in sorted(exp)],'claims':'four completed static 5s comparisons; no interpretation of pending 16s stress runs'}
  (OUT/'preview_before_v1.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
  print('pinned',len(exp),'inputs');return
 before=read(OUT/'preview_before_v1.json')
 if before['producer']['sha256']!=sha(OUT/'preview_producer_v1.py') or before['producer']['path']!=str(OUT/'preview_producer_v1.py'):raise RuntimeError('producer pin mismatch')
 pinned={x['path']:x['sha256'] for x in before['inputs']}
 if set(pinned)!=set(exp):raise RuntimeError('input set differs from before pin')
 for path,digest in pinned.items():
  if sha(path)!=digest:raise RuntimeError('input changed after pin: '+path)
 frame_rows=[];records=[]
 for key,label,analysis,visual in CASES:
  ad=read(P/analysis);rd=read(P/visual/'report.json');m=ad['measured']['stages'][0]
  value=(m['motion']['maximum_body_mm'],m['motion']['maximum_SO3_deg'],m['contacts']['all_left_arm_hand_contact_free_samples'])
  ref=EXPECTED[key]
  if any(abs(float(a)-float(b))>1e-8 for a,b in zip(value,ref)):raise RuntimeError('approved metric mismatch '+key)
  if m['contacts']['samples']!=1200 or m['contacts']['right_wrist_hand_contact_samples']!=0:raise RuntimeError('unexpected static sampling/contact '+key)
  if rd['frame_count_per_view']!=151:raise RuntimeError('unexpected 30fps frame count '+key)
  row={'key':key,'label':label,'maximum_BB_mm':value[0],'maximum_SO3_deg':value[1],'left_free_samples':value[2],'samples':1200,'RH_wrist_hand_contacts':0}
  records.append(row)
  for time_s,frame in [(0.0,'00000.png'),(5.0,'00150.png')]:
   src=P/visual/'frames/front'/frame;dest=OUT/'front_frames'/f'{key}_t{int(time_s)}.png';dest.parent.mkdir(parents=True,exist_ok=True)
   want=next(x['sha256'] for x in rd['annotated_frames'] if x['path']==str(src))
   if sha(src)!=want:raise RuntimeError('front frame source hash mismatch '+str(src))
   shutil.copy2(src,dest)
   if sha(dest)!=want:raise RuntimeError('copied frame hash mismatch '+str(dest))
   im=Image.open(dest)
   if im.size!=(1280,940):raise RuntimeError(f'front image dimensions {im.size}: {dest}')
   frame_rows.append({'case':key,'time_s':time_s,'source':str(src),'copy':str(dest),'sha256':want,'width':im.width,'height':im.height})
 # 2x2 cases; each panel contains the native annotated front at t=0 and t=5, with labels outside each image.
 FP=FontProperties(fname=str(FONT));fig,axs=plt.subplots(2,2,figsize=(16,12))
 for ax,rec in zip(axs.flat,records):
  ax.axis('off');ax.set_title(rec['label'],fontproperties=FP,fontsize=15,pad=12)
  # Each row panel uses an inset horizontal pair with above-image labels.
  box=ax.get_position();pad=0.018;mid=(box.x0+box.x1)/2
  width=(box.width-pad)/2
  for idx,t in enumerate((0,5)):
   left=box.x0+idx*(width+pad)
   fig.text(left+width/2,box.y1-0.035,f'{rec["label"]} · t={t}s',ha='center',va='bottom',fontproperties=FP,fontsize=10)
   ia=fig.add_axes([left,box.y0,width,box.height-0.08]);ia.axis('off')
   ia.imshow(Image.open(OUT/'front_frames'/f'{rec["key"]}_t{t}.png'))
 fig.suptitle('네 조건의 정적 5초 비교 · 전면 · 시작/종료',fontproperties=FP,fontsize=18,y=.995)
 fig.savefig(OUT/'static_front_2x2.png',dpi=120,bbox_inches='tight');plt.close(fig)
 # Concise Korean evidence summary; use absolute local paths.
 table='\n'.join(f'| {r["label"]} | {r["maximum_BB_mm"]:.6f} mm | {r["maximum_SO3_deg"]:.6f}° | {r["left_free_samples"]}/1200 | 0 |' for r in records)
 doc=f'''# 정적 조건 미리보기 — 4개 후보

이 자료는 네 개의 완료된 정적 5초 실행을 비교하는 미리보기다. 진행 중인 16초 왼손 스트레스 시험은 포함하지 않으며, 이 표만으로 최종 후보를 고르지 않는다.

| 조건 | 기타 BB 중심 최대 변화 | 최대 SO(3) 회전 | 왼팔·손 무접촉 표본 | 오른손목·손 접촉 표본 |
|---|---:|---:|---:|---:|
{table}

네 실행 모두 1200개 240 Hz 표본의 정적 관측이다. 기타는 자유 상태, strap OFF, root·하체 고정, self-collision ON이며 유한한 인간 제어를 유지한다. 모든 조건에서 왼팔·손 접촉 없는 표본이 1200개 중 일부뿐이므로, 독립 지지 성공이나 최종 안정 자세로 부르지 않는다. 오른손목·손 접촉 표본은 각 조건 0이다. 최대 이동은 기타 BB 바디 중심 기준이며 SO(3) 회전은 정규화된 쿼터니언에서 계산됐다.

![각 후보의 시작·5초 전면 프레임. 각 case/time 표시는 영상 밖 제목에 있음.]({OUT/'static_front_2x2.png'})

프레임의 채운 원 표식은 양의 raw lambda 접촉, 빈 원은 lambda=0을 뜻하며 힘(N)이나 접촉 면적이 아니다. X-ray 표시는 가려진 접촉점도 항상 보이게 한다. 인체의 초록/분홍 영역은 모델 재질 색이며 접촉표식이 아니다. 네 시야는 동일 전면 축척의 native annotated frames에서 가져왔다.

| 조건 | t=0 전면 PNG | t=5 전면 PNG |
|---|---|---|
'''+ '\n'.join(f'| {r["label"]} | [PNG]({OUT/"front_frames"/(r["key"]+"_t0.png")}) | [PNG]({OUT/"front_frames"/(r["key"]+"_t5.png")}) |' for r in records)+f'''

분석 원자료: [margin only]({P/'analysis_margin_only_static_v1.json'}), [roll −2°]({P/'analysis_roll_m2_static_v1.json'}), [roll +2°]({P/'analysis_roll_p2_static_v1.json'}), [torso +2°]({P/'analysis_torso_p2_static_v1.json'}). Before pin: [preview_before_v1.json]({OUT/'preview_before_v1.json'}). Source/copy hashes: [preview_manifest_v1.json]({OUT/'preview_manifest_v1.json'}).
'''
 (OUT/'README.md').write_text(doc,encoding='utf-8')
 after={p:sha(p) for p in pinned}
 if any(after[p]!=digest for p,digest in pinned.items()):raise RuntimeError('input changed during production')
 for row in frame_rows:
  if sha(row['copy'])!=row['sha256']:raise RuntimeError('final copy hash mismatch')
 manifest={'schema':'initial_pose_search_static_preview_manifest_v1','producer':{'path':str(OUT/'preview_producer_v1.py'),'sha256':sha(OUT/'preview_producer_v1.py')},'before':str(OUT/'preview_before_v1.json'),'before_sha256':sha(OUT/'preview_before_v1.json'),'all_inputs_unchanged':True,'visual_reports_inputs_unchanged':True,'front_frame_copies_verified':True,'metrics_match_approved_values':True,'records':records,'frames':frame_rows,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [OUT/'README.md',OUT/'static_front_2x2.png']+[Path(x['copy']) for x in frame_rows]]}
 (OUT/'preview_manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'inputs':len(pinned),'frames':len(frame_rows),'cases':4,'verified':True},ensure_ascii=False))
if __name__=='__main__':main()
