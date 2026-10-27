from pathlib import Path
import hashlib,json,re
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1';A=P/'artifacts_v1';V=ROOT/'docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())
# Compose expected hashes from immutable evidence records and reused media manifests.
expected={}
def add(p,h=None):
 p=str(Path(p).resolve())
 if h is not None and p in expected and expected[p] not in (None,h):raise RuntimeError('conflicting pin '+p)
 if h is not None:expected[p]=h
 else:expected.setdefault(p,None)
for f in [P/'approved_artifact_brief_v1.md',P/'approved_artifact_addendum_v1.md',P/'approved_artifact_addendum_v2.md',P/'left_station_comparison_v1.json',P/'qualification_summary_v1.json',P/'joint_240hz_audit_v1.json',P/'static_reproduction_v1.json',P/'strike_actual_windows_v1.json',P/'initial_arm_limit_margins_v1.json',A/'README.md',A/'README_v3.md',A/'artifact_before_v4.json',A/'artifact_producer_v3.py',A/'artifact_producer_v4.py',A/'copy_manifest_v1.json',A/'copy_manifest_v3.json',A/'maxima_comparison_v1.png',A/'maxima_comparison_v3.png',A/'artifact_producer_v5.py',V/'README.md',V/'README_v3.md']:
 add(f)
for f in [P/'analysis_baseline_v1.json',P/'analysis_static_v1.json',P/'analysis_strike_v1.json',P/'analysis_left_cycle_v1.json',P/'analysis_z_plus3mm_v1.json',P/'visual_baseline_v1/report.json',P/'visual_static_v1/report.json',P/'visual_strike_v1/report.json',P/'visual_left_cycle_v1/report.json',P/'visual_z_plus3mm_v1/report.json',P/'visual_baseline_v1/inputs_before.json',P/'visual_static_v1/inputs_before.json',P/'visual_strike_v1/inputs_before.json',P/'visual_left_cycle_v1/inputs_before.json',P/'visual_z_plus3mm_v1/inputs_before.json']:
 add(f)
for f in [P/'qualification_summary_v1.json',P/'joint_240hz_audit_v1.json']:
 for p,h in j(f).get('input_sha256',{}).items():add(p,h)
for key in ['baseline','static','strike','left_cycle','z_plus3mm']:
 for suffix in ['analysis_'+key+'_v1.json','visual_'+key+'_v1/report.json']:
  q=j(P/suffix)
  for p,h in q.get('input_sha256',{}).items():add(p,h)
for manifest in [A/'copy_manifest_v1.json',A/'copy_manifest_v3.json']:
 for row in j(manifest).get('copies',[]):
  add(row.get('source'),row.get('sha256'));add(row.get('path'),row.get('sha256'))
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');add(FONT)
# Verify all pinned evidence at production time.
before=j(A/'artifact_before_v5.json')
if before['producer']['path']!=str(A/'artifact_producer_v5.py') or before['producer']['sha256']!=sha(A/'artifact_producer_v5.py'):raise RuntimeError('producer pin mismatch')
if {x['path'] for x in before['inputs']}!=set(expected):raise RuntimeError('input list mismatch')
for item in before['inputs']:
 if sha(item['path'])!=item['sha256']:raise RuntimeError('input changed '+item['path'])
# Correct only the newly generated copy; all consumed docs remain unchanged.
text=(A/'README_v3.md').read_text()
old='''보호 중단 실행의 실제 joint bound overshoot 최대는 0.19815°이며 목표는 모델 한계와 변화율 안이었다.'''
new='''기존 analysis의 실제 joint 한계 초과 최대 0.19815°는 60 Hz·81개 관절각 표본 기준이다. 별도의 240 Hz 재계산에서 active33(body9+양팔24) 위치의 보호 중단 실행 최대 초과는 L_Wrist_y 0.220198°(5.541667초)였다. 나머지48 관절의 240 Hz 위치 최댓값은 기록 범위에 포함되지 않는다. 240 Hz로 기록한 81개 속도 최대는 EW6 타현의 3.203110 rad/s이며 모두 50 rad/s 미만이다. 이는 목표 변화율 3 rad/s와 별도인 실제 속도다.'''
if old not in text:raise RuntimeError('expected inherited phrase absent')
text=text.replace(old,new).replace('문서 v2','문서 v4').replace('영상 색인 v2','영상 색인 v4').replace('README_v3.md','README_v4.md').replace('copy_manifest_v3.json','copy_manifest_v4.json').replace('artifact_before_v4.json','artifact_before_v5.json').replace('maxima_comparison_v3.png','maxima_comparison_v3.png')
text+='\n\n상위 결과 안내는 [README v2]('+str(P/'README_v2.md')+')를 따른다. 본 요약은 [영상 색인 v4]('+str(V/'README_v4.md')+')와 짝이며, 이 정정 전 버전은 보존했다.\n'
(A/'README_v4.md').write_text(text)
idx=(V/'README_v3.md').read_text().replace('README_v3.md','README_v4.md').replace('copy_manifest_v3.json','copy_manifest_v4.json').replace('artifact_before_v4.json','artifact_before_v5.json').replace('index v2','index v4').replace('색인 v2','색인 v4')
idx+='\n\n상위 결과 안내는 [README v2]('+str(P/'README_v2.md')+')를 따른다. 이 영상 색인은 [요약 v4]('+str(A/'README_v4.md')+')와 짝이다.\n'
(V/'README_v4.md').write_text(idx)
# Input pin remains unchanged, and every Markdown target in the new pair exists.
for doc in [A/'README_v4.md',V/'README_v4.md']:
 for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
  if target.endswith('copy_manifest_v4.json'):continue
  if not Path(target).exists():raise RuntimeError('broken link '+target)
if str(V/'README_v4.md') not in (A/'README_v4.md').read_text() or str(A/'README_v4.md') not in (V/'README_v4.md').read_text():raise RuntimeError('doc pair mismatch')
if '60 Hz·81개 관절각 표본 기준' not in (A/'README_v4.md').read_text() or '0.220198°' not in (A/'README_v4.md').read_text():raise RuntimeError('scope correction absent')
for row in before['inputs']:
 if sha(row['path'])!=row['sha256']:raise RuntimeError('post-production input changed '+row['path'])
outputs=[A/'README_v4.md',V/'README_v4.md']
manifest={'schema':'initial_pose_qualification_artifact_manifest_v4','producer':{'path':str(A/'artifact_producer_v5.py'),'sha256':sha(A/'artifact_producer_v5.py')},'before_record':str(A/'artifact_before_v5.json'),'before_sha256':sha(A/'artifact_before_v5.json'),'inputs_unchanged':True,'previous_versions_preserved':True,'inherited_joint_metric_sampling_scope_corrected':True,'reused_media_hashes_verified_in_prior_manifest':True,'preferred_docs_crosslink':True,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
(A/'copy_manifest_v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Verify new manifest link now exists.
for doc in [A/'README_v4.md',V/'README_v4.md']:
 for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
  if not Path(target).exists():raise RuntimeError('final broken link '+target)
print(json.dumps({'inputs':len(expected),'docs': [str(p) for p in outputs], 'inputs_unchanged':True,'links_verified':True}))
