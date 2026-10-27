# 위 볼록 외곽 진단 준비 V2 사전 검수

요약 판정: **재작업 필요 — V2 후보 native 실행 차단.** Critical 1 / Warning 1 / Suggestion 0. 새 물리 실행은 하지 않았다. 차단 사항은 root에게 즉시 전달했다.

V2는 V1 q81/G p·q를 보존하고 진단용 proximity6mm·팔꿈치 하강15mm로 수락한다. 나머지 source clear·capsule 양수0.05mm·지역/normal·고정관절·몸통/head·손 위치·모델/설계 범위 gate는 유지한다. 두 candidate의 q81/G p·q 및 contract q_ref exact를 확인했고 입력603개 SHA 불일치0개였다. 이 heuristic 수락은 actual contact/안정성 문턱이나 최종 자세 채택이 아니다.

## Critical

1. [prepare_upper_bout_axilla_v2.py:15](/home/ajou/yigyu/3/stability_adapter_2/prepare_upper_bout_axilla_v2.py:15): 생성 candidate에 `predicted_human_poses`가 없다. 실제 base.main이 호출하는 [run_om_body_geometry_trial_v2.py:102](/home/ajou/yigyu/3/stability_adapter_2/run_om_body_geometry_trial_v2.py:102)는 이 필드를 필수 조회하므로 초기화 검증에서 KeyError가 나며 정상 physics 루프를 시작할 수 없다. 소비된 V2를 보존하고 새 준비 버전에서 실제 q의 calibrated FK pose를 추가해야 한다. 임의 placeholder나 다른 초기 pose를 복사해서는 안 된다.

## Warning

1. 전체 상완 접촉 표본은 근위35%/지정 기타 볼록부 접촉 인증이 아니다. 접촉 위치를 별도 검증하기 전에는 이 공간 범위를 주장하지 않는다. 관련 [분석 집계](/home/ajou/yigyu/3/stability_adapter_2/analyze_upper_bout_axilla_v1.py:48)는 그대로다.

runner V2는 V1 대비 PLAN/search만 다르며 기존 두 점 제어·가드를 유지한다. 상대 CLI 정규화 보완도 유지된다. **V2 자체는 물리 실행 대상으로 사용하지 않는다.** 이후 보완본은 별도 사전 검수 기록을 남긴다.

검수 SHA256:

- 계획 V2: `6ec4cafcb4473c054cbb4aa0285a961e91b9b003ebcb06b9d5a43b76b887006d`
- prepare V2: `4528a9b2fafb5c8d94c4c2931a094199312802abb5fdb1098269874782e08276`
- runner V2: `b46f9b50e00caa7d9cb8a312e6fd29d66d1a25aad31ad26e07009026a8a9fc15`
- search V2: `66362d4bebca340d76246a4c552ac66eb880d7f98d3be883e5de68109a7956d1`

이 새 리뷰 외 기존 파일은 수정하지 않았다.
