from pathlib import Path
import hashlib,json
A=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1')
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1')
inputs=[A/'README_V1.md',A/'provenance_v1.json',P/'result_summary_v2.json',P/'contact_region_v2.json',P/'contact_region_v1.json']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
before={str(p):snap(p) for p in inputs}
s=(A/'README_V1.md').read_text()
old='두 조건은 각각 5초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초로 완료했습니다. 10 mm의 late upper contact는 120/120, total upper 1173/1200, R_Hip1194/1200; head/left/right distal은0입니다. strict 35%+upper-rim contact는1062/1200입니다. 20 mm의 late upper 120/120, total upper1178/1200, R_Hip1195/1200; head/left/distal0, strict region1102/1200입니다. 접촉 표본·raw lambda는 힘 크기나 해부학적 지지의 인증이 아닙니다. 이는 움직임이 없는 5초 native 진단이며 별도 elbow motion, 학습, 음악 평가는 하지 않았습니다.'
new='두 새 조건은 각각 5초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초로 완료했습니다. 접촉 존재와 양의 raw lambda 표본은 별도 계수이며, strict 35%+upper-rim은 지정영역 분류입니다.\n\n| 조건 | 상완 전체 presence / positive raw lambda | 지정영역 presence / positive raw lambda | 후기 상완 presence |\n|---|---:|---:|---:|\n| baseline 19° | — | 1117 / 1113 | — |\n| shoulder target 10 mm | 1173 / 1162 | 1062 / 237 | 120/120 |\n| shoulder target 20 mm | 1178 / 1171 | 1102 / 122 | 120/120 |\n\nR_Hip 표본은 10 mm 1194/1200, 20 mm 1195/1200이며, 두 조건 모두 head/left/right distal 0입니다. 양의 raw lambda는 힘(N) 측정이나 지지력 분담이 아니며, 지정영역 분류도 해부학적 겨드랑이 지지 인증이 아닙니다. 10 mm는 상완 전방 target 및 최종 전체 정지 gate를 통과한 후보로 정리했지만, 실제 겨드랑이 힘 지지는 인증되지 않았습니다. 이들은 움직임 없는 5초 native 진단이며 별도 elbow-motion trial, 학습, 음악 평가는 하지 않았습니다.'
assert old in s
out=A/'README_V2.md';out.write_text(s.replace(old,new))
after={str(p):snap(p) for p in inputs};assert before==after
producer=A/'build_archive_v2.py'
prov={'task':'separate contact-presence and positive-raw-lambda counts in README only','physics_or_training_runs':0,'video_copies_or_reencodes':0,
 'correction':'README_V1 collapsed strict region presence and positive raw lambda into a single count. V2 separates upper-arm any-contact and strict 35%+upper-rim region counts, and explicitly states lambda is not force in newtons or force share.',
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(producer),'sha256':sha(producer),'bytes':producer.stat().st_size},
 'outputs':{str(out):{'sha256':sha(out),'bytes':out.stat().st_size}},'README_V1_preserved':True}
(A/'provenance_v2.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
