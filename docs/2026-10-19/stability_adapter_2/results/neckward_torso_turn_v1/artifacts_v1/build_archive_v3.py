from pathlib import Path
import hashlib,json
A=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1')
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1')
producer=A/'build_archive_v3.py'; readme=A/'README_V3.md'; provenance=A/'provenance_v3.json'
inputs=[A/'README_V2.md',A/'provenance_v2.json',P/'result_summary_v1.json',P/'contact_region_v1.json']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def state(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
before={str(p):state(p) for p in inputs}
s=(A/'README_V2.md').read_text()
old='Hands 영상은 왼손/넥 방향 카메라라 오른쪽 상완 접촉의 증거가 아닙니다. 세 native 모두 5초/1200 physics step 완료. 상완 접촉은 1169/1200, R_Hip 1193/1200, Head/왼팔/오른쪽 distal arm 0/1200; 선언된 support-region은 0/1200입니다. Source geometry 간격은 PhysX cooked clearance 인증이 아니며 raw lambda는 힘 측정이 아닙니다. 안정성·연주 성공 주장은 하지 않습니다.'
new='Hands 영상은 왼손/넥 방향 카메라라 오른쪽 상완 접촉의 증거가 아닙니다. 세 native 모두 5초/1200 physics step을 완료했습니다. 아래 접촉 수치는 새 두 실행(static_neckyaw12 및 elbow_neckyaw12)에 해당합니다: 상완 any-contact 1169/1200, R_Hip 1193/1200, Head/왼팔/오른쪽 distal arm 0/1200, declared support-region 0/1200. 이전 static_cradle 기준은 상완 1187/1200, R_Hip 1196/1200, proximal-35% 분류 1171/1200입니다. Source geometry 간격은 PhysX cooked clearance 인증이 아니며 raw lambda는 힘 측정이 아닙니다. 이는 각 조건의 단일 5초 진단이며 자연스러운 연주, 음악 성공, 반복성을 보증하지 않습니다.'
assert old in s
readme.write_text(s.replace(old,new))
# Capture script SHA after file has been written. Inputs must remain byte-identical.
after={str(p):state(p) for p in inputs}
assert before==after
prov={
 'task':'V2 contact-count attribution correction; text/documentation only',
 'physical_or_training_runs':0,'video_copies_or_reencodes':0,
 'correction':'V2 grouped all-three completion with contact counts that apply only to the two new runs. V3 scopes those counts to the two new runs and explicitly reports the distinct old static_cradle counts.',
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(producer),'sha256':sha(producer),'bytes':producer.stat().st_size},
 'outputs':{str(readme):{'sha256':sha(readme),'bytes':readme.stat().st_size}},
 'source_output_files_preserved':True}
provenance.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
