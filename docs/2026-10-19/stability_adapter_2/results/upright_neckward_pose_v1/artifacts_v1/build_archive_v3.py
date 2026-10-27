from pathlib import Path
import hashlib,json
A=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1')
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1')
inputs=[A/'README_V1.md',A/'provenance_v2.json',P/'analysis_v6/static_neckyaw19/verification.json',P/'analysis_v7/elbow_neckyaw19/verification.json',P/'native_v6/static_neckyaw19/initial_values.json',P/'native_v7/elbow_neckyaw19/initial_values.json']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
before={str(p):snap(p) for p in inputs}
s=(A/'README_V1.md').read_text()
s=s.replace('기타 quaternion은 초기값을 유지했습니다.','기타의 초기 quaternion은 이전 후보와 같게 설정했으며 이후 물리에서 자유롭게 회전했습니다.')
s=s.replace('최대치는 body 중심 10.380810 mm, 전체 회전 3.313974°로 회전 gate를 작은 여유로 통과했습니다.','최종값을 검사하는 3° 미만 gate는 2.995398°로 0.004602° 여유를 두고 통과했습니다. 실행 중 최대치는 중심 10.380810 mm/회전 3.313974°였고 최종값 gate와 별도입니다.')
assert s!= (A/'README_V1.md').read_text()
out=A/'README_V2.md';out.write_text(s)
after={str(p):snap(p) for p in inputs};assert before==after
producer=A/'build_archive_v3.py'
prov={'task':'README V2 wording corrections only','physical_or_training_runs':0,'video_copies_or_reencodes':0,
 'corrections':['Clarify the initial guitar quaternion was configured to match the previous candidate, then remained physically free to rotate.','Separate the final-value <3° gate result (2.995398°, margin 0.004602°) from the run-wide maximum rotation (3.313974°).'],
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(producer),'sha256':sha(producer),'bytes':producer.stat().st_size},
 'outputs':{str(out):{'sha256':sha(out),'bytes':out.stat().st_size}},'README_V1_preserved':True}
(A/'provenance_v3.json').write_text(json.dumps(prov,indent=2,ensure_ascii=False)+'\n')
