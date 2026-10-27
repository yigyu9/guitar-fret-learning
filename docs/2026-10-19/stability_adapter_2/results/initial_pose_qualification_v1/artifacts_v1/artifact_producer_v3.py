from pathlib import Path
import hashlib,json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path('/home/ajou/yigyu/3'); P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1'; A=P/'artifacts_v1'; V=ROOT/'docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1'
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CASES=[('baseline','기준 자세','native_baseline_v2','visual_baseline_v1','analysis_baseline_v1.json'),('static','정적 분리','native_static_v3','visual_static_v1','analysis_static_v1.json'),('strike','EW6 타현','native_strike_v2','visual_strike_v1','analysis_strike_v1.json'),('left_cycle','왼손 사이클 (보호 중단)','native_left_cycle_v2','visual_left_cycle_v1','analysis_left_cycle_v1.json'),('z_plus3mm','초기 기타 world Z +3 mm','native_z_plus3mm_v2','visual_z_plus3mm_v1','analysis_z_plus3mm_v1.json')]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
# Build and verify closed current evidence pins before generating any output.
files=[P/'approved_artifact_brief_v1.md',P/'approved_artifact_addendum_v1.md',P/'left_station_comparison_v1.json',P/'qualification_summary_v1.json',P/'static_reproduction_v1.json',P/'strike_actual_windows_v1.json',P/'initial_arm_limit_margins_v1.json',P/'visual_baseline_v1/report.json',P/'visual_static_v1/report.json',P/'visual_strike_v1/report.json',P/'visual_left_cycle_v1/report.json',P/'visual_z_plus3mm_v1/report.json',P/'visual_baseline_v1/inputs_before.json',P/'visual_static_v1/inputs_before.json',P/'visual_strike_v1/inputs_before.json',P/'visual_left_cycle_v1/inputs_before.json',P/'visual_z_plus3mm_v1/inputs_before.json',P/'joint_240hz_audit_v1.json',P/'approved_artifact_addendum_v2.md']
files += [P/name for _,_,_,_,name in CASES]
files += [A/'README.md',A/'artifact_producer_v2.py',A/'artifact_producer_v3.py',A/'artifact_before_v2.json',A/'artifact_before_v2.json',A/'copy_manifest_v1.json',A/'maxima_comparison_v1.png',V/'README.md',FONT]
expected={}
def add(path,digest=None):
 p=str(Path(path).resolve())
 if digest is not None and p in expected and expected[p] not in (None,digest): raise RuntimeError('conflicting expected SHA: '+p)
 if digest is not None:expected[p]=digest
 else: expected.setdefault(p,None)
for f in files:add(f)
summary=read(P/'qualification_summary_v1.json')
for p,h in summary.get('input_sha256',{}).items():add(p,h)
for key,label,native,visual,analysis in CASES:
 an=read(P/analysis)
 for p,h in an.get('input_sha256',{}).items():add(p,h)
 rp=read(P/visual/'report.json')
 if not rp.get('inputs_unchanged'):raise RuntimeError('visual inputs changed: '+key)
 for p,h in rp.get('input_sha256',{}).items():add(p,h)
 for view,filename in [('front','front.mp4'),('right_side','right_side.mp4'),('top','top.mp4'),('combined','front_side_top.mp4')]:
  add(P/visual/filename,rp['videos'][view]['sha256'])
 for snap in rp['snapshots']:add(snap['path'],snap['sha256'])
# Pin current copied video/snapshot files reused by this new document pair.
for key,*_ in CASES:
 for p in list((V/key).glob('*.mp4'))+list((A/key).glob('*.png')):add(p)
missing=[p for p in expected if not Path(p).is_file()]
if missing:raise RuntimeError('missing pin inputs: '+repr(missing[:10]))
bad=[p for p,h in expected.items() if h and sha(p)!=h]
if bad:raise RuntimeError('input SHA mismatch: '+repr(bad[:10]))
# Immutable pre-production record, new version only.
before={'schema':'initial_pose_qualification_artifact_before_v3','purpose':'새 문서·그래프 버전 생성 전 현재 읽기 입력과 재사용 기존 산출물 SHA를 기록','inputs':[{'path':p,'sha256':sha(p)} for p in sorted(expected)],'evidence_status':{'all_five_visual_reports_inputs_unchanged':True,'addendum_included':True,'old_artifact_set_preserved':True}}
(A/'artifact_before_v3.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
# Corrected comparison chart; Korean font applied to every text artist.
FP=FontProperties(fname=str(FONT)); colors=['#0072B2','#009E73','#D55E00','#CC79A7','#56B4E9']; labels=[c[1] for c in CASES]
rows=[next(x for x in summary['cases'] if x['case']==c[0]) for c in CASES]
fig,axs=plt.subplots(1,2,figsize=(13.4,5.6)); x=list(range(5))
for ax,field,title,ylabel in [(axs[0],'maximum_BB_mm','최대 기타 BB 중심 변위','변위 (mm)'),(axs[1],'maximum_SO3_deg','최대 기타 SO(3) 회전','회전 (도)')]:
 vals=[r[field] for r in rows]; bars=ax.bar(x,vals,color=colors,edgecolor='black',linewidth=.4)
 bars[3].set_hatch('///');bars[3].set_edgecolor('#7A1F5C')
 ax.set_xticks(x);ax.set_xticklabels(labels,rotation=22,ha='right',fontproperties=FP,fontsize=9)
 ax.set_title(title,fontproperties=FP);ax.set_ylabel(ylabel,fontproperties=FP);ax.grid(axis='y',alpha=.25);ax.set_axisbelow(True)
 for i,(bar,val) in enumerate(zip(bars,vals)):
  ax.text(bar.get_x()+bar.get_width()/2,bar.get_height(),f'{val:.3f}'+('*' if i==3 else ''),ha='center',va='bottom',fontsize=8,fontproperties=FP)
 for tick in ax.get_yticklabels():tick.set_fontproperties(FP)
fig.suptitle('관측 구간 최대값 — 두 패널은 서로 다른 물리량',fontproperties=FP,fontsize=12)
fig.tight_layout(rect=(0,0,1,.94)); chart=A/'maxima_comparison_v2.png';fig.savefig(chart,dpi=180);plt.close(fig)
# Derive new documents from consumed docs without editing those originals.
old=(A/'README.md').read_text(); old=old.replace('maxima_comparison_v1.png','maxima_comparison_v2.png').replace("/video/initial_pose_qualification_v1/README.md)","/video/initial_pose_qualification_v1/README_v2.md)").replace("/artifacts_v1/copy_manifest_v1.json)","/artifacts_v1/copy_manifest_v2.json)")
needle='Strike는 5초 실행에서 EW6 타현 목표만 변경하고 다른 75개 목표는 유지했다(실제 상태는 움직일 수 있음).'
addition='''### 왼손 사이클 비교 범위와 접촉 보충

이 보호 중단 실행에서 오른손 엄지3/중지3 접촉은 181 physics step 동안 6.345833–7.095833초 관측됐다. 이는 EW6 타현 5초 실행의 오른손 접촉 0과 구분한다. actor-root가 20 cm 한계를 처음 넘은 시각은 240 Hz 기준 7.279167초이며, 60 Hz 보호 표본에서 7.283333초에 중단했다.

이전 16초 cycle과 이번 실패를 몸통 자세만의 비교로 볼 수 없다. 이번 실행은 초기 관절값, 기타 초기 위치, 제어 참조와 손목 station을 함께 재기준화했다. 새 A 손목 목표는 이전 A보다 기타 좌표에서 (-1.170, 42.048, -0.034) mm 이동해 이전 B 분리 위치에 가까워졌으며, 이전 실행이 이전 B 분리 자세에서 시작했다. 따라서 실패 원인을 몸통 자세로 단정하지 않는다. [station 비교 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/left_station_comparison_v1.json).

'''
if needle not in old:raise RuntimeError('README insertion point missing')
old=old.replace(needle,addition+needle)
old=old.replace('# 초기 자세 적격성 비교','# 초기 자세 적격성 비교 — 문서 v2')
old+='\n\n이 문서는 [영상 색인 v2]('+str(V/'README_v2.md')+')와 짝을 이룬다. 입력 SHA는 [새 before 기록]('+str(A/'artifact_before_v3.json')+')에, 생성 파일 SHA와 검증 결과는 [새 manifest]('+str(A/'copy_manifest_v2.json')+')에 기록했다. 이전 README와 그래프는 보존했다.\n'
(A/'README_v2.md').write_text(old,encoding='utf-8')
idx=(V/'README.md').read_text().replace(str(A/'README.md'),str(A/'README_v2.md')).replace('# 초기 자세 적격성 — annotated video index','# 초기 자세 적격성 — annotated video index v2')
idx='문서와 영상 색인 v2는 서로 짝을 이룹니다.\n\n'+idx+'\n\n이 색인은 [새 before 기록]('+str(A/'artifact_before_v3.json')+')과 [새 copy manifest]('+str(A/'copy_manifest_v2.json')+')에 연결됩니다.\n'
(V/'README_v2.md').write_text(idx,encoding='utf-8')
# Verify pins remained unchanged and all media reused still matches their source reports.
after={p:sha(p) for p in expected}
changed=[p for p,h in after.items() if h!=next(x['sha256'] for x in before['inputs'] if x['path']==p)]
if changed:raise RuntimeError('input changed while producing: '+repr(changed[:10]))
# All Markdown links must target existing absolute paths; pair must be bidirectional.
import re
for doc in [A/'README_v2.md',V/'README_v2.md']:
 text=doc.read_text()
 for target in re.findall(r'\]\((/[^)]+)\)',text):
  if not Path(target).exists():raise RuntimeError('broken markdown link '+target)
 if not text.startswith('#') and doc==A/'README_v2.md':raise RuntimeError('unexpected summary format')
if str(A/'README_v2.md') not in (V/'README_v2.md').read_text() or str(V/'README_v2.md') not in (A/'README_v2.md').read_text():raise RuntimeError('preferred docs pair mismatch')
outputs=[A/'README_v2.md',V/'README_v2.md',chart]
copylist=[]
for key,_,_,visual,_ in CASES:
 rp=read(P/visual/'report.json')
 for view,filename in [('front','front.mp4'),('right_side','right_side.mp4'),('top','top.mp4'),('combined','front_side_top.mp4')]:
  src=P/visual/filename; dst=V/key/filename; want=rp['videos'][view]['sha256']
  if sha(src)!=want or sha(dst)!=want:raise RuntimeError('reused video hash mismatch '+key+'/'+filename)
  copylist.append({'kind':'reused_byte_preserved_video','case':key,'view':view,'source':str(src),'path':str(dst),'sha256':want})
 for snap in rp['snapshots']:
  src=Path(snap['path']);dst=A/key/src.name;want=snap['sha256']
  if sha(src)!=want or sha(dst)!=want:raise RuntimeError('reused snapshot hash mismatch '+key+'/'+src.name)
  copylist.append({'kind':'reused_byte_preserved_snapshot','case':key,'source':str(src),'path':str(dst),'sha256':want})
outputs += [p for key,*_ in CASES for p in list((V/key).glob('*.mp4'))+list((A/key).glob('*.png'))]
manifest={'schema':'initial_pose_qualification_artifact_manifest_v2','producer':{'path':str(A/'artifact_producer_v3.py'),'sha256':sha(A/'artifact_producer_v3.py')},'before_record':str(A/'artifact_before_v3.json'),'before_sha256':sha(A/'artifact_before_v3.json'),'after_inputs_unchanged':True,'copies_reused_without_reencoding':True,'media_sources_match_visual_report_sha256':True,'markdown_absolute_links_exist':True,'preferred_docs_crosslink':True,'copies':copylist,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
(A/'copy_manifest_v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pinned_inputs':len(expected),'reused_media':len(copylist),'outputs':[str(x) for x in outputs[:3]],'verified':True},ensure_ascii=False))
