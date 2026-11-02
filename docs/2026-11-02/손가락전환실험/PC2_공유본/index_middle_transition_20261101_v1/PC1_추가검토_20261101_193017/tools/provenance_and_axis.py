"""공유된 봉인과 현재 PC1 입력의 확인 가능 범위를 읽기 전용으로 구분한다."""
from pathlib import Path
import gzip,hashlib,json,math
ROOT=Path('/home/ajou/yigyu/3')
OUT=Path(__file__).resolve().parents[1];BASE=OUT.parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
manifest=read(BASE/'공유파일목록.json');seal=read(BASE/'보존/study_seal.json');project_study='docs/2026-11-02/손가락전환실험/'
covered=[];not_supplied=[];bad=[]
for name,expected in seal['files'].items():
 if name in manifest['reference_project_files']:p=BASE/'읽기용코드'/name
 elif name.startswith(project_study) and name[len(project_study):] in manifest['study_files']:p=BASE/name[len(project_study):]
 else:not_supplied.append(name);continue
 actual=sha(p);covered.append(name)
 if actual!=expected:bad.append(name)
reference=read(ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/geometry/initial_catalog.json')
index=reference['joint_names'].index('L_Thorax_y');action=reference['action_indices'].index(index)
goal=next(row for row in reference['goals'] if row['song']=='virtual_finger_v9_middle_s3_f6')
axis=dict(joint='L_Thorax_y',joint_index=index,action_index=action,
 reference_deg=math.degrees(reference['reference105'][index]),hold_deg=math.degrees(goal['hold_target105'][index]),upper_deg=math.degrees(reference['action_upper'][action]),existing_evaluations=[])
for label in ('seed7_u800_mean128','seed7_u1000_mean128'):
 folder=ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/analysis/review_20261101'/label
 values=[]
 with gzip.open(folder/'finger_control_trace.jsonl.gz','rt') as f:
  for line in f:
   x=json.loads(line)['natural_preparation']['transition'];t=x['all_env_episode_time_s'][0]
   if 5.25<=t<6.75:values.append(math.degrees(x['arm_requested_rad'][action]))
 metrics=read(folder/'analysis.json')
 axis['existing_evaluations'].append(dict(label=label,env=0,scope='B audible 240Hz endpoint requests, representative env only',sample_count=len(values),requested_deg_min=min(values),requested_deg_max=max(values),all_env_AB=metrics['AB'],all_env_N=metrics['episodes']))
state_path=ROOT/'docs/2026-11-02/압현실험/자율개선_20261101/runs_recovery/progress.json';state=read(state_path)
source_actual={};mismatched=[]
for name,expected in state['source_seal'].items():
 actual=sha(ROOT/name);source_actual[name]=actual
 if actual!=expected:mismatched.append(name)
output_actual={}
for job in state['jobs'].values():
 for name,expected in job.get('evidence',{}).items():
  actual=sha(Path(name));output_actual[name]=actual
  if actual!=expected:mismatched.append(name)
result=dict(shared_original_seal_entries=len(seal['files']),original_seal_entries_independently_covered=len(covered),
 original_seal_entries_not_in_share=len(not_supplied),covered_mismatches=bad,
 original_seal_scope_limit='Not all original PC2 project inputs/assets/native runtime are supplied. No full original load/identity rerun claimed; no PC1 substitution or checkpoint unpickling performed.',
 pc1_axis_comparison=axis,pc1_source_checked=len(source_actual),pc1_output_evidence_checked=len(output_actual),pc1_expected_mismatches=mismatched,
 pc1_protected_before=dict(source=source_actual,outputs=output_actual),
 shared_seal_sha256=sha(BASE/'보존/study_seal.json'))
(OUT/'provenance_and_pc1_axis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='pc1_protected_before'},ensure_ascii=False,indent=2))
assert not bad and not mismatched
