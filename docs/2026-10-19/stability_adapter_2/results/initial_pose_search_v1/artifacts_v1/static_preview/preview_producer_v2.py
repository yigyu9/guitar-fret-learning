from pathlib import Path
import argparse,hashlib,json,shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1';OUT=P/'artifacts_v1/static_preview';FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CASES=[('margin_only','여유각 보정만','analysis_margin_only_static_v1.json','visual_margin_only_static_v1'),('roll_m2','Roll −2°','analysis_roll_m2_static_v1.json','visual_roll_m2_static_v1'),('roll_p2','Roll +2°','analysis_roll_p2_static_v1.json','visual_roll_p2_static_v1'),('torso_p2','Torso +2°','analysis_torso_p2_static_v1.json','visual_torso_p2_static_v1')]
EXPECTED={'margin_only':(3.286738679280705,0.8194552852290521,418),'roll_m2':(6.066885163887934,2.3525767903894104,46),'roll_p2':(20.857204167035686,4.727967924051142,93),'torso_p2':(3.9994683589343527,1.1593499089869337,113)}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def add(expected,p,digest=None):
 p=str(Path(p).resolve())
 if digest is not None and p in expected and expected[p] not in (None,digest):raise RuntimeError('conflicting digest '+p)
 if digest is not None:expected[p]=digest
 else:expected.setdefault(p,None)
def expected_inputs():
 e={};add(e,OUT/'preview_producer_v2.py');add(e,FONT);add(e,OUT/'preview_producer_v1.py');add(e,OUT/'preview_before_v1.json');add(e,OUT/'preview_manifest_v1.json');add(e,OUT/'README.md');add(e,OUT/'static_front_2x2.png')
 for p in sorted((OUT/'front_frames').glob('*.png')):add(e,p)
 for key,_,a,v in CASES:
  adp=P/a;rp=P/v/'report.json';add(e,adp);add(e,rp)
  ad=read(adp);rd=read(rp)
  for p,h in ad.get('input_sha256',{}).items():add(e,p,h)
  for p,h in rd.get('input_sha256',{}).items():add(e,p,h)
  if rd.get('inputs_unchanged') is not True:raise RuntimeError('visual report guard false '+key)
  ann={x['path']:x['sha256'] for x in rd['annotated_frames']}
  for t,name in [(0,'00000.png'),(5,'00150.png')]:
   src=P/v/'frames/front'/name
   if str(src) not in ann:raise RuntimeError('frame missing '+str(src))
   add(e,src,ann[str(src)])
 return e
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pin',action='store_true');args=ap.parse_args();exp=expected_inputs()
 if args.pin:
  before={'schema':'initial_pose_search_static_preview_before_v2','producer':{'path':str(OUT/'preview_producer_v2.py'),'sha256':sha(OUT/'preview_producer_v2.py')},'inputs':[{'path':p,'sha256':sha(p)} for p in sorted(exp)],'note':'v1 composite retained; v2 presents four cases in 2x2 panels with time labels outside image geometry'}
  (OUT/'preview_before_v2.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n');print('pinned',len(exp));return
 before=read(OUT/'preview_before_v2.json');pins={x['path']:x['sha256'] for x in before['inputs']}
 if before['producer']['path']!=str(OUT/'preview_producer_v2.py') or before['producer']['sha256']!=sha(OUT/'preview_producer_v2.py'):raise RuntimeError('producer pin mismatch')
 if set(exp)!=set(pins):raise RuntimeError('input set changed')
 for p,h in pins.items():
  if sha(p)!=h:raise RuntimeError('input changed: '+p)
 rows=[];copylist=[]
 for key,label,an,vis in CASES:
  analysis=read(P/an)['measured']['stages'][0];contact=analysis['contacts'];motion=analysis['motion'];want=EXPECTED[key]
  vals=(motion['maximum_body_mm'],motion['maximum_SO3_deg'],contact['all_left_arm_hand_contact_free_samples'])
  if any(abs(float(x)-float(y))>1e-8 for x,y in zip(vals,want)):raise RuntimeError('metric mismatch '+key)
  if contact['samples']!=1200 or contact['right_wrist_hand_contact_samples']!=0:raise RuntimeError('contact sample mismatch '+key)
  rows.append({'key':key,'label':label,'BB':vals[0],'SO3':vals[1],'LHfree':vals[2]})
  report=read(P/vis/'report.json');ann={x['path']:x['sha256'] for x in report['annotated_frames']}
  for t,name in [(0,'00000.png'),(5,'00150.png')]:
   src=P/vis/'frames/front'/name;dst=OUT/'front_frames'/f'{key}_t{t}.png';wantsha=ann[str(src)]
   if sha(src)!=wantsha:raise RuntimeError('source mismatch '+str(src))
   shutil.copy2(src,dst)
   if sha(dst)!=wantsha:raise RuntimeError('copy mismatch '+str(dst))
   with Image.open(dst) as im:
    if im.size!=(1280,940):raise RuntimeError('unexpected frame dimensions '+str(im.size))
   copylist.append({'case':key,'time_s':t,'source':str(src),'copy':str(dst),'sha256':wantsha})
 # Compact 2x2 outer grid; each cell shows its native front t0/t5 pair. Headings are in a separate band.
 fw,fh=640,470;label_band=48;case_band=42;gap=16;cell_w=fw*2;cell_h=case_band+label_band+fh
 canvas=Image.new('RGB',(cell_w*2+gap*3,cell_h*2+gap*3),'white');draw=ImageDraw.Draw(canvas)
 font_case=ImageFont.truetype(str(FONT),24,index=0);font_time=ImageFont.truetype(str(FONT),18,index=0)
 for i,row in enumerate(rows):
  col=i%2;rr=i//2;x0=gap+col*(cell_w+gap);y0=gap+rr*(cell_h+gap)
  draw.text((x0+cell_w//2,y0+5),row['label'],font=font_case,fill='black',anchor='mt')
  for j,t in enumerate((0,5)):
   xx=x0+j*fw;draw.text((xx+fw//2,y0+case_band+5),f'{row["label"]} · t={t}s',font=font_time,fill='black',anchor='mt')
   img=Image.open(OUT/'front_frames'/f'{row["key"]}_t{t}.png').convert('RGB').resize((fw,fh),Image.Resampling.LANCZOS)
   canvas.paste(img,(xx,y0+case_band+label_band))
 canvas.save(OUT/'static_front_2x2_v2.png',quality=95)
 table='\n'.join(f'| {r["label"]} | {r["BB"]:.6f} mm | {r["SO3"]:.6f}° | {r["LHfree"]}/1200 | 0 |' for r in rows)
 pth=lambda p:f'[{p.name}]({p})'
 doc=f'''# 정적 조건 미리보기 — 4개 후보

네 개의 완료된 정적 5초 실행을 나란히 보는 미리보기다. 진행 중인 16초 왼손 스트레스 시험은 포함하지 않으며, 여기서 최종 후보를 선택하지 않는다.

| 조건 | 기타 BB 중심 최대 변화 | 최대 SO(3) 회전 | 왼팔·손 무접촉 표본 | 오른손목·손 접촉 표본 |
|---|---:|---:|---:|---:|
{table}

각 조건은 240 Hz에서 1200개 표본으로 관측했다. 기타는 자유 상태, strap OFF, root·하체 고정, self-collision ON이며 유한한 인간 제어를 유지한다. 네 조건 모두 일부 표본에서 왼팔·손 접촉이 있으므로 독립 지지 성공으로 해석하지 않는다. 오른손목·손 접촉은 네 조건에서 각각 0/1200이다. BB 값은 기타 바디 중심 변위이며 회전은 SO(3) geodesic이다.

![2×2 조건 배치, 각 칸에 t=0초와 t=5초의 동일 축척 native 전면 프레임을 표시. 조건·시간 캡션은 영상 바깥에 있음.]({OUT/'static_front_2x2_v2.png'})

영상의 채운 원 표식은 양의 raw lambda, 빈 원은 lambda=0이며 힘(N)이나 면적이 아니다. X-ray 표시는 가려진 접촉점도 보이게 한다. 사람 모델의 초록/분홍 영역은 재질 색이고 접촉표식이 아니다.

| 조건 | t=0 전면 | t=5 전면 |
|---|---|---|
'''+ '\n'.join(f'| {r["label"]} | [PNG]({OUT/"front_frames"/(r["key"]+"_t0.png")}) | [PNG]({OUT/"front_frames"/(r["key"]+"_t5.png")}) |' for r in rows)+f'''

[before pin]({OUT/'preview_before_v2.json'}) · [manifest]({OUT/'preview_manifest_v2.json'})
'''
 (OUT/'README_v2.md').write_text(doc,encoding='utf-8')
 for p,h in pins.items():
  if sha(p)!=h:raise RuntimeError('post-production input changed '+p)
 manifest={'schema':'initial_pose_search_static_preview_manifest_v2','producer':{'path':str(OUT/'preview_producer_v2.py'),'sha256':sha(OUT/'preview_producer_v2.py')},'before':str(OUT/'preview_before_v2.json'),'before_sha256':sha(OUT/'preview_before_v2.json'),'inputs_unchanged':True,'all_visual_reports_guarded':True,'all_frame_copies_match_sha':True,'metrics_match_parent_brief':True,'records':rows,'frames':copylist,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [OUT/'README_v2.md',OUT/'static_front_2x2_v2.png']+[Path(x['copy']) for x in copylist]]}
 (OUT/'preview_manifest_v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'pinned_inputs':len(pins),'frames':len(copylist),'verified':True},ensure_ascii=False))
if __name__=='__main__':main()
