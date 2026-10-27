# 왼손 두 지점 잡기·놓기 결과

현재 오른쪽+10mm 초기 배치를 유지한 실제 Isaac Gym16초 진단을2회 실행했다. 손은 넥 방향으로 약36.7mm 이동해 다시 잡고 놓았다. 두 잡기 유지 구간에는 엄지+다른 손가락 접촉이 있었고, 놓은 뒤 왼팔·왼손의 기타 접촉이 없는 상태에서도 기타가 떨어지지 않았다. 그러나 잡고 놓는 전체 과정에서 기타 자세가 변했으므로 초기 자세가 계속 그대로 유지된 결과는 아니다.

## 조건 및 단계

- 자유 기타, 스트랩OFF, 휴머노이드 Root/하체 고정, 자기 충돌ON. 기타 고정·손 강제 부착·지속 pose 덮어쓰기·기타 외부 힘은 사용하지 않았다.
- 기존 오른팔 유한 지지 제어와 준비 목표는 유지하며 실제 관절은 물리적으로 움직인다. 이번에는 오른손 타현 궤적을OFF로 해 왼손 변화만 진단했다. 학습/체크포인트 연결은0회다.
- 왼팔12 IK 목표 + 유한 손목 임피던스(사람 관절 토크만), 왼손21 POSITION 목표를 사용한다. 몸통/머리/오른팔·손48 목표는 유지한다. 원래 arm3rad/s·finger1.5rad/s와 모델/토크 한계를 검증했다.
- 0–2초 준비 →2–4.5초 A 접근·잡기 →4.5–7초 놓기 →7–8.5초 물린 상태로 B 이동 →8.5–11.5초 B 접근·잡기 →11.5–16초 놓기·관찰. “펴기”는 추가 굽힘을 풀어 기존 손가락 형태로 되돌리는 것이며 완전히 곧은 손가락을 강제하지 않는다.

## 실제 측정

| 구간 | 접촉 확인 | 기타 바디 BB 중심 이동 / SO3 회전 |
|---|---|---|
|A 잡기 유지3–4.5초|엄지+다른 손가락 양의 raw lambda360/360|구간 시작 대비 최대1.064mm /1.031°|
|A 놓은 뒤6–7초|왼팔·왼손 접촉 없음240/240|최대0.415mm /0.136°|
|손 물린 상태 이동7–8.5초|접촉 없음360/360|최대0.123mm /0.076°|
|B 잡기 유지10–11.5초|엄지+다른 손가락360/360|최대1.773mm /0.640°|
|B 놓기 과정11.5–13초|접촉이 사라지는 전환|최대12.885mm /5.275°|
|B 놓은 뒤13–16초|접촉 없음720/720|최대0.0187mm /0.00662°|

위 변화는 각 구간 시작 상태를 기준으로 한다. 전체 사이클의2초 준비 상태 대비 최대는22.264mm/9.796°다. 초기0초부터 포함하면41.255mm/10.455°이며 초기 정착 이동도 포함한다. 왼손이 없는 마지막3초는 조용하지만, 두 번째 놓기 과정의 이동/회전은 개선 여지가 있다. 힘 폐쇄·압현 정확도·타현·연주 성공·무작위 조건 강건성은 이 시험으로 판정하지 않는다. 오른쪽 위팔과 오른쪽 허벅지(R_Hip) 지지 접촉이 계속 존재하며 유한 관절 제어가 유지되므로 수동 평형을 뜻하지 않는다.

## 영상과 자료

두 실행 모두16초/3840physics step, 각 영상481프레임/30fps(초기·끝 장면 포함16.033초)다. V1/V2의 초기 상태와 기타 위치·쿼터니언 trace가 정확히 같았다. 카메라 렌더는 상태를 바꾸지 않았으며, 화면의6개 줄 선분은 비물리적 표시다.

[장면별 이미지·설명 정정본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/README_v2.md:1), [전체 영상 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/INDEX_v2.md:1), [V2 원시 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/analysis_v2.json:1), [반복 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/repeat_comparison_v1.json:1)을 확인한다.

V1 소스·원자료·영상은 보존했다. V1의 L_Hip 접촉 오분류와 상속 로그 scope는 정정 메타데이터에 구분했고, 직접 기본 config의 실행 전SHA가 누락된 한계를 소급 인증하지 않는다. V2는 정확한 왼팔·손 body 목록, 상속 실제 encode scope, config 사전/사후SHA를 보완했다. 산출물 초기 README/INDEX의 몸통고정 조건·기타 바디 중심 표기는 README_v2/INDEX_v2에서 정정하고 이전 문서는 보존했다.

## 계획 → 구현 → 검증 → 검토

- [x] 기존 초기 조건과 원본을 보존하고 단계별 계획 작성.
- [x] 왼손 동작/유한 제어/현재 기타 기준 목표/실제 접촉 로그 구현.
- [x] 문법 검사 및 독립 사전 검수, 실제16초2회 실행, 초기 상태·모델·속도·토크·Root/하체·금지 API·영상 경과 검증.
- [x] 원자료 접촉/이동 분석 및 이미지·영상 보관.
- 최종 독립 검수와 보존 봉인은 별도 review_final_v1.md/final_verification_v1.json에 남긴다. 완료 상태는 해당 원문으로 확인한다.

## 변경 파일의 절대 경로와 실제 줄 번호

- [계획V1](/home/ajou/yigyu/3/stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V1.md:1)
- [재현·보완 계획V2](/home/ajou/yigyu/3/stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V2.md:1)
- [동작·제어V2](/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v2.py:43)
- [실제16초 실행V2](/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v2.py:146)
- [V2 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_grip_release_cycle_v2.py:17)
- [반복 비교](/home/ajou/yigyu/3/stability_adapter_2/compare_left_grip_release_cycle_v1.py:8)
- [보존 검증](/home/ajou/yigyu/3/stability_adapter_2/verify_left_grip_release_cycle_v1.py:15)
- [V1 원본 제어](/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v1.py:43)
- [V1 원본 실행](/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v1.py:146)
- [V1 원본 분석](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_grip_release_cycle_v1.py:17)
- [초기 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/config_v1.json:1)
- [이미지·설명 정정본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/README_v2.md:1)
- [영상 모음 정정본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/INDEX_v2.md:1)
- [README.md 추가 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:2406)
- [PLAN.md 추가 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1318)
- [README.md 추가 기록](/home/ajou/yigyu/3/docs/2026-10-19/initial/README.md:31)
