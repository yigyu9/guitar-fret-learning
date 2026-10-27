from pathlib import Path
import hashlib,json
A=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1')
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1')
inputs=[A/'README_V2.md',A/'provenance_v2.json',P/'search_v2/shoulder_forward10mm/candidate.json',P/'search_v2/shoulder_forward20mm/candidate.json',P/'result_summary_v2.json']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
before={str(p):snap(p) for p in inputs}
s=(A/'README_V2.md').read_text()
s=s.replace('오른쪽 어깨를 조금 앞으로 옮기려는 요청에 대해,','오른쪽 어깨 관절을 조정해 팔을 조금 앞으로 빼려는 요청에 대해,')
s=s.replace('두 조건 모두 초기 기타 81개 q, G position/quaternion, Chest/Torso/Spine 전체 초기 상태를 baseline과 정확히 같게 유지하고 오른쪽 Shoulder의 초기 3 scalar 각도만 바꿨습니다. gain, 중력, 10 N upper-effort cap, strap OFF, left grip OFF, root/lower 고정, 기타 자유·기타 직접힘 없음 조건은 같았습니다.','두 조건 모두 휴머노이드의 오른쪽 Shoulder 초기 3 scalar 각도만 바꾸고, 나머지 78개 초기 관절각과 기타 초기 전체 상태, Chest/Torso/Spine 초기 전체 상태는 baseline과 같게 유지했습니다. gain, 중력, 사람 상완 가상점의 force 요청 상한 10 N(사람 관절 토크로 변환되며 실제 접촉힘이나 토크의 상한이 아님), strap OFF, left grip OFF, root/lower 고정, 기타 자유·기타 직접힘 없음 조건은 같았습니다.')
assert s!=(A/'README_V2.md').read_text()
out=A/'README_V3.md';out.write_text(s)
after={str(p):snap(p) for p in inputs};assert before==after
producer=A/'build_archive_v3.py'
prov={'task':'README phrasing corrections only','physics_or_training_runs':0,'video_copies_or_reencodes':0,
 'corrections':['Clarify the request adjusts the right shoulder joint to bring the arm forward.','Clarify only three humanoid right-Shoulder initial scalar angles change; other 78 initial joint angles and the full guitar/Chest/Torso/Spine initial states match baseline.','Clarify 10 N is the virtual upper-arm point force-request cap converted to human joint torque, not a bound on actual contact force or torque.'],
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(producer),'sha256':sha(producer),'bytes':producer.stat().st_size},
 'outputs':{str(out):{'sha256':sha(out),'bytes':out.stat().st_size}},'README_V2_preserved':True,'media_and_manifests_unchanged':True}
(A/'provenance_v3.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
