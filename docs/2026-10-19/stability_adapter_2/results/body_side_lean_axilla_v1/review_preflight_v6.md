# 바디 쪽4° 동일 초기값 두 점 비교 V6 사전 검수

요약 판정: **문제없음 — 두 번째5초 native 비교에 실행용 코드 차단 없음.** Critical 0 / Warning 1 / Suggestion 0. runner/분석기 변경과 고정 입력을 검토했다. 새 물리 실행·학습은 하지 않았다. 상대 config 경로의 분석기 Warning은 물리 실행 gate와 별개다.

[runner V5](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v5.py:106)는 이미 검수한 두 점 runner에서 phase/PLAN/search5 및 candidate의 `body_side_lean_axilla` 키만 바꾼다. 확정 방향은 player-right=바디 쪽=정면 화면 왼쪽이며, 동일한 search5 config/candidate의81 q·기타 p/q를 사용한다. 새 초기 배치나 gain 변경은 없다. 상완 점은 초기 source surface 반대6mm의 고정 world human motor 목표로, 기타 고정 목표나 측정 접촉점이 아니다.

기존 전완 control은 계산·로그만 한다. [합산 제어](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v5.py:109)는 그 미clip 요청에 상완 `JᵀF` right12를 더하고 native 모델 effort cap으로 자른다. 실제 actor API는 `step_physics`의 한 번만 유지한다. gravity/posture를 중복 합산하지 않고 other69 effort0·새 POSITION 목표·owner window·상태 불변/readback·각 점0.01m/s Jacobian gate를 유지한다. 점별30N은 전체 요청의30N cap이나 실제 접촉력 N이 아니다. root/lower fixed·strapOFF·free 기타 조건이며 기타 직접 힘·부착·pose overwrite를 추가하지 않는다.

[분석기 V2](/home/ajou/yigyu/3/stability_adapter_2/analyze_body_side_lean_axilla_v2.py:34)는 기존 두 점 분석기를 복사해 phase만 바꾼다. candidate/config pin·초기81 q·손목 고정 마스크·mixed69 제출/state 검사·각 점/총 요청/clip/1200행 cadence 검증을 유지한다. 전체 중력보상/Jacobian 또는 지지력 기여의 인증은 아니다.

첫 native의 [analysis_v2 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v2/verification.json:29)는 root373.073mm·body BB중심48.051mm·SO3 52.174°, 상완968/전완1191/left0/Head0 of1200이다. `passed`는 명령·기록 검증이며 접촉만으로 기타 초기 자세 유지 성공을 뜻하지 않는다. 새 두 점 비교의 실제 초기 JSON 동일성과 성능은 실행 뒤 확인해야 한다. 기존 능동 전완 제어에 상완점 하나를 추가한 비교다. Python3.8 구문은 정상이다.

## Warning

1. [analyze_body_side_lean_axilla_v2.py:19](/home/ajou/yigyu/3/stability_adapter_2/analyze_body_side_lean_axilla_v2.py:19): `--config`를 resolve하지 않고24행에서 attempt의 절대 경로 키로 조회한다. 상대 경로를 전달하면 기존 실패처럼 KeyError가 발생한다. 미소비 분석기의 경로를 정규화하거나 실제 CLI의 case/config/out을 절대 경로로 한정해야 한다. native 제어 코드에는 영향이 없다. 실패한 analysis_v1은 보존한다.

검수 SHA256:

- 계획 V6: `4d302f2b092fe8a0b3cd460dc30885f0becbd6a189c11b4dfd9d580e79da2fd3`
- runner V5: `c7d656e1633ad77d3e8a58f4e2ceea6886d4d3afc1b46bce24e7abeb9efef384`
- 분석기 V2: `b59b4ebd72f2ec648bbc14b47659f5c9b276e265c5c07bceb88bff82c8ba3907`
- 고정 candidate: `0743ef3b743d8eeb90585d5858ae77286ce53713a942f5ffb3bbc847a3990b81`
- 고정 config: `9fd8fe76fa6f2d07349d0798f982fb6f9fd898c72db316fe282aa1b41680cc30`

이 새 리뷰 외 원본·기존 결과·이전 리뷰는 수정하지 않았다.
