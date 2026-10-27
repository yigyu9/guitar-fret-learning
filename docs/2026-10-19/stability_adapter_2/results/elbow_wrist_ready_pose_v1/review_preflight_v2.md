# V3 wrapper hard gate와 경로 전체 형상 표본 보완 검수

요약 판정: 문제없음. [앞선 V1 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/review_preflight_v1.md:1)의 실행 전 ball norm Critical은 새 wrapper V3에서 해소됐다. 이전 V1/V2는 보존하며 native에는 V3를 사용한다.

Critical: 0

## 확인 근거

- [run_elbow_wrist_ready_v3.py:42](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v3.py:42): IK 요청6의 finite/위치오차≤2mm/모델범위/준비 기준±1rad/두 ball norm<160°를 확인하고 실패 시 원 물리 step 전에 중단한다. helper의 soft penalty를 hard 인증으로 대체하지 않는다.
- [V3:47](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v3.py:47): 원 contract.targets(action,previous)로 rate 적용 최종81을 미리 계산하고 최종6 finite/norm<160°를 원 step 전 검사한다. 원 step 후 실제 논리 최종81이 예상과 정확히 같은지 확인한다. contract.targets는 여기서 상태를 변경하지 않는다. 모델 clipping/rate/PD/gain/cap/한 actuator 합성/4patch/LEFT OFF 및75 목표 보존 경로는 기존과 동일하다. 추가 힘·state setter는 없다.
- [CONTROL_PLAN_V3](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_CONTROL_PLAN_V3.md:1)의 요청/최종 목표 범위와 실제 상태·속도 guard 구분이 코드와 일치한다. norm 검사는 명령에 대한 것이며 실제75 상태를 고정한다는 주장이 아니다.
- [경로 감사:22](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_path_v1.py:22): 준비 후보의5점과 crossing/하강 중점2점, 총7점에서 fresh 손·손가락/기타/비인접 인체 whole-source audit를 수행한다. 모든 표본 source_clear이며 최대 IK 오차 .000212463mm다. `accepted_for_native`의 위치/형상 표본 조건도 일치한다. 저장 norm도 모두160° 미만이다.
- 경로 감사 입력1022개 현재 SHA가 모두 일치하고 새 wrapper V2/V3·audit AST를 확인했다. source/helper/물리 실행을 재수행하지 않았다. 이전 source/계획/결과를 변경하지 않았다.

## Warning

- [경로 감사 scope:27](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_path_v1.py:27): 7점 source clear는 연속 경로·현재 움직이는 기타·PhysX cooking/native 충돌 인증이 아니다. 실제 정지/타현 완료 여부, 손 접촉, marker 추종 및 원 detector60Hz RELEASE는 후속 실제 원자료에서 판정한다.
- [요청 기록:54](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v3.py:54): IK 오차는 요청 목표에 대한 값이다. rate 적용 목표 및 실제 marker 추종오차와 구분하며, disabled/첫2초의 error=0을 실제 오차0으로 해석하지 않는다.

## Suggestion

없음. 현 preflight 범위에서 V3 정지/타현 비교를 막는 구현 오류를 발견하지 못했다.
