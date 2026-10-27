#!/usr/bin/env python3
"""Build captioned contact sheets from CP241's saved native Isaac Gym frames."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3')
OUT=ROOT/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v1'
EP=ROOT/'docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/long_on_v2/evaluations/update_000241/native/episode_0001'
MEDIA=EP/'media';CAPTURE=MEDIA/'capture.json'
PROBE=ROOT/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/reset_probe_v2'
FRAME_IDS=(0,60,491)
CAPTIONS=('0초 · physics step 0','2초 · physics step 480','최종 16.3667초 · physics step 3928')
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def entry(p):p=Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 cap=json.loads(CAPTURE.read_text())
 if cap['renderer']!='Isaac Gym native camera + actual strap-route overlay':raise RuntimeError('unexpected frame renderer')
 if len(cap['frames'])!=492 or cap['frames'][-1]['time_s']!=16.366666666666667:raise RuntimeError('unexpected CP241 capture horizon')
 sources=[CAPTURE,ROOT/'stability_adapter_2/capture_isaac_gym_initial.py',PROBE/'report.json',PROBE/'comparison.json',FONT]
 selected={}
 for view in ('whole_body','hands'):
  for i in FRAME_IDS:
   rec=cap['frames'][i];p=MEDIA/'frames'/view/f'{i:05d}.png'
   if not p.exists():raise FileNotFoundError(p)
   expected=rec['image_sha256'][str(p)]
   if sha(p)!=expected:raise RuntimeError(f'frame differs from capture provenance: {p}')
   selected[(view,i)]=p;sources.append(p)
 before=[entry(p) for p in sources]
 font=ImageFont.truetype(str(FONT),28);small=ImageFont.truetype(str(FONT),20)
 for view,filename,title in [('whole_body','cp241_strap_full_scene_v1.png','CP241 · Isaac Gym native 전체 장면 · 스트랩 표시'),('hands','cp241_strap_hands_v1.png','CP241 · Isaac Gym native 손 장면 · 스트랩 표시')]:
  images=[Image.open(selected[(view,i)]).convert('RGB') for i in FRAME_IDS]
  panel_w=960;panel_h=540;gap=20;band=76;top=90
  canvas=Image.new('RGB',(3*panel_w+2*gap,top+panel_h+band),(248,248,248));draw=ImageDraw.Draw(canvas)
  draw.text((28,20),title,font=font,fill=(20,20,20))
  for col,(im,caption) in enumerate(zip(images,CAPTIONS)):
   im.thumbnail((panel_w,panel_h),Image.Resampling.LANCZOS)
   x=col*(panel_w+gap);y=top
   canvas.paste(im,(x,y))
   draw.text((x+8,y+panel_h+12),caption,font=small,fill=(20,20,20))
   im.close()
  canvas.save(OUT/filename,optimize=True)
 after=[entry(p) for p in sources]
 if before!=after:raise RuntimeError('source changed while making contact sheets')
 report=json.loads((PROBE/'report.json').read_text());comparison=json.loads((PROBE/'comparison.json').read_text())
 if not report['completed'] or report['resets_completed']!=60 or not comparison['trace_exact'] or not comparison['controls_exact']:
  raise RuntimeError('reset probe facts do not match requested scope')
 prov={'scope':'Preparation only from completed CP241 native capture. No new physics or training run.',
       'producer':entry(Path(__file__).resolve()),'inputs_before':before,'inputs_after':after,'inputs_unchanged':True,
       'capture_summary':{'renderer':cap['renderer'],'camera_config_source':cap['camera_config_source'],'fps':cap['fps'],'frame_count':len(cap['frames']),'times':[cap['frames'][i]['time_s'] for i in FRAME_IDS],
                          'strap_overlay_scope':cap['strap_visualization']['scope'],'strap_rest_length_m':cap['frames'][0]['strap_rest_length_m']},
       'reset_probe_summary':{'completed':report['completed'],'resets_completed':report['resets_completed'],'trace_exact':comparison['trace_exact'],'controls_exact':comparison['controls_exact'],'trace_lengths':comparison['trace_lengths'],'controls_lengths':comparison['controls_lengths'],'max_absolute_difference':comparison['max_absolute_difference']},
       'outputs':[entry(OUT/'cp241_strap_full_scene_v1.png'),entry(OUT/'cp241_strap_hands_v1.png')]}
 (OUT/'cp241_preparation_provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'inputs':len(before),'outputs':prov['outputs'],'producer_sha256':prov['producer']['sha256']},ensure_ascii=False))
if __name__=='__main__':main()
