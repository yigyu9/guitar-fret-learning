from pathlib import Path
import hashlib,json,math,shutil
import numpy as np
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';S=D/'results/torso_hold_native_collision_v1/native';P=D/'results/practical_stability_assessment_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(S/n):sha(S/n) for n in ('trace.jsonl','report.json','initial_values.json')}
rows=[json.loads(l) for l in (S/'trace.jsonl').read_text().splitlines()];late=rows[480:];p=np.array([r['guitar_position_m'] for r in late]);q=np.array([r['guitar_quaternion_xyzw'] for r in late]);metrics=dict(observed_interval_s=[2.,5.],max_displacement_from_interval_start_mm=float(np.linalg.norm(p-p[0],axis=1).max()*1000),max_rotation_from_interval_start_deg=float((2*np.arccos(np.clip(abs(q@q[0]),0,1))*180/math.pi).max()),end_initial_position_error_mm=rows[-1]['position_error_m']*1000,end_initial_rotation_error_deg=rows[-1]['rotation_error_deg'])
assert all(sha(path)==value for path,value in inputs.items());P.mkdir(exist_ok=False)
(P/'assessment.json').write_text(json.dumps(dict(input_sha256=inputs,metrics=metrics,assessment='Practical quiet-hold subgoal substantially satisfied on this recorded5s trial; microscopic pose jitter accepted by user; initial displacement and moving-hand robustness remain separate evaluations',native_initializations=0,physics_steps=0),indent=2)+'\n')
plan=A/'QUIET_HOLD_BASELINE_DECISION.md';assert not plan.exists()
plan.write_text('''# 미세 떨림을 허용한 정지 유지 기준 채택

사용자는2026-10-08에 “미세한 떨림은 무시해도 괜찮을 정도”라고 판단했다. 따라서 완전한 정적 평형/속도0을 정지 유지 서브목표의 필수 조건으로 두지 않는다. 영상과 저장 pose에서 확인되는 실용적인 자세 유지를 평가한다. 기존 기록의 report를 소급 수정하지 않는다.

현재 torso_hold_native_collision_v1의2~5초는2초 시작점 대비 기타 위치 최대0.001899241mm·회전 최대0.001245157° 변화로 매우 작다. 이 관측 범위의 정지 유지 목표는 상당 부분 만족했다. 해당 body9PD×2·기존81목표·같은 초기81/G p/q/절대LA1.1018469719600776m를 후속 시험의 유지 기준으로 채택한다. Root·하체 물리 고정, 자유 기타/passive strap은 같다.

초기 과도 구간의 이탈과 이후 유지는 분리한다. 종료 초기오차14.050564mm/2.856298°가 허용 범위라고 사용자가 승인한 것으로 해석하지 않는다. 초기배치/strap을 개선해 이탈을 더 줄이는 목표는 유지한다. 손바닥 옆면/엄지 후면/나머지 손가락 전면 배치도 후속 연주 자세의 개선 항목이며 그 미완성이 현재 정지 유지를 전부 실패로 바꾸지는 않는다.

다음 작은 단위는 기준 설정에서 작은 손·팔 목표 움직임을 가했을 때의 실제5초 유지 성능 확인이다. 구체적 관절/진폭/주기/최종target경계는 별도 실행 계획에 먼저 적는다. 기준 PD목표+움직임/안정화 residual 관계와 최종 양쪽66권한을 유지한다. 별도 필수2초 대기 상태를 만들지 않으며2초는 이번 관측의 분석 구간일 뿐이다. 원본·영상 보존과 실제 스트랩 표시도 유지한다.

- [x] 사용자 미세 떨림 허용을 정지 유지 평가에 반영
- [x] 기존 실제2~5초 pose 변화 재계산 및 유지 기준 채택
- [ ] 작은 손·팔 동작 시험의 입력/target범위와 실제5초 기록
- [ ] 초기 이탈 추가 감소와 움직임 중 p/q 복원·유지

새 물리 실행은0이며 전체 연주 안정화 완료 선언은 아니다.
''')
(P/'README.md').write_text('''# 정지 유지 목표의 실용적 평가

사용자의 미세 떨림 허용을 반영하면 현재 결과는 **초기 움직임 이후 정지 자세를 유지하는 서브목표를 상당 부분 만족**한다. 완전한 정적 평형 여부를 필수 조건으로 강조한 이전 답변은 실용적 목적에 비해 엄격했다.

| 기존 실제 기록에서 측정한 항목 | 값 |
|---|---:|
| 분석 구간 |2~5초|
|2초 시작점 대비 최대 위치 차이 |0.001899241mm (약1.90µm)|
|2초 시작점 대비 최대 회전 차이 |0.001245157°|
|5초 종료의 초기 목표 위치 오차 |14.050564mm|
|5초 종료의 초기 목표 회전 오차 |2.856298°|

정지 유지와 초기 이탈량을 분리해 평가한다. 미세 pose 떨림/속도 field 비영 자체를 근거로 정지 유지 실패로 분류하지 않는다. 초기14mm/2.86°가 허용된 것으로 확대 해석하지 않는다. 이번 설정을 유지 성능의 기준으로 삼고 초기 이탈 감소와 작은 손·팔 동작 중 유지 성능을 후속 검증한다.

![평가 대상인 기존 실제 Isaac Gym 스트랩 영상]('''+str(S/'hands.mp4')+''')

[주요 제어·유지 기준 결정]('''+str(plan)+''':1), [재계산 원자료]('''+str(P/'assessment.json')+''':1)에 남긴다. 원본 실행과 기존 실패 기록은 수정하지 않았다. 추가 native/physics0이다.
''')
progress='\n\n## 미세 떨림 허용 — 정지 유지 기준 채택\n\n사용자 판단을 반영해 현재 실제 body9PD×2 기록의2~5초 정지 유지는 실용적으로 상당 부분 만족한 것으로 평가한다. 해당 구간 위치차이 최대0.001899241mm/회전차이0.001245157°다. 완전한 평형/속도0을 필수 조건으로 두지 않는다. 초기이탈14.050564mm/2.856298°와 손·팔 움직임 중 유지는 별도 평가한다. [결정]('+str(plan)+':1), [수치·기존영상]('+str(P/'README.md')+':1)을 기록했다. 원본 report 변경/새물리 실행은0이며 다음 단계는 이 설정에서 작은 손·팔 움직임의 실제 유지성 확인이다.\n'
for name in ('README.md','PLAN.md'):
 with (A/name).open('a') as f:f.write(progress)
changed='# 변경 파일과 실제 줄\n\n'
for file,key in ((plan,'# '),(A/'README.md','## 미세 떨림 허용'),(A/'PLAN.md','## 미세 떨림 허용'),(P/'README.md','# ')):
 line=next(i for i,l in enumerate(file.read_text().splitlines(),1) if l.startswith(key));changed+='- ['+file.name+']('+str(file)+':'+str(line)+')\n'
(P/'CHANGED_FILES.md').write_text(changed);shutil.copyfile(__file__,P/'source.py');(P/'artifact_inventory.json').write_text(json.dumps({str(f):dict(size=f.stat().st_size,sha256=sha(f)) for f in sorted(P.iterdir()) if f.is_file()},indent=2)+'\n');print(json.dumps(metrics,indent=2))
