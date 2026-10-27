# 위 볼록 외곽 FK 계약 보완 V3 사전 검수

요약 판정: **문제없음 — 두 진단 후보의 실행 차단 Critical 해소.** Critical 0 / Warning 1 / Suggestion 0. V2를 보존한 새 V3 코드/후보를 검토했으며 새 물리 실행은 하지 않았다.

[prepare V3](/home/ajou/yigyu/3/stability_adapter_2/prepare_upper_bout_axilla_v3.py:10)는 같은 원 natural native 초기값의 calibrated FK에 각 후보의 실제81 q를 넣어 `predicted_human_poses`를 추가한다. 두 후보의 기존 모든 키/q81/G p·q가 V2와 exact이고, native 진입점이 사용하는 FK66개 body의 이름·p/q가 존재한다. 직접 재계산한 최대 차이는 위치3.5e−16m 미만·회전1.1e−15rad 미만이었다. 새 contract q_ref도 exact이며 입력611개 SHA 불일치0개다. **사전 리뷰 V2의 필수 FK 필드 누락 Critical은 해소됐다.**

진단 수락은 V1 원해의 근위 gap5.669/5.029mm 및 하강17.057/17.896mm를 바꾸지 않은 proximity6mm/하강15mm heuristic이다. 고정57관절·기타 회전/위치·모델/설계 범위·source 양수/전체 겹침·볼록 영역·normal·body/head 오차 gate를 유지한다. 이는 실제 근위 접촉·무관통·자연스러움·유지 성공 인증이 아니다.

[runner V3](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v3.py:107)는 PLAN/search와 상완 configuration의 `source_segment_fraction_limit=.35` 기록만 바꾼다. legacy65 키의 실제 witness는35로 유지한다. 기존 전완+상완 human 토크 합산/한 번 actor 제출/모델 cap·other69 POSITION/effort0·owner·상태 불변·Jacobian 속도 gate는 그대로다. 기타 직접 외력·부착·pose overwrite가 없다. 점별30N은 측정 힘이나 합계30N 상한이 아니다. Python3.8 구문은 정상이다.

## Warning

1. [분석 집계](/home/ajou/yigyu/3/stability_adapter_2/analyze_upper_bout_axilla_v1.py:48)는 전체 R_Shoulder–G:body 접촉이다. 실제 겨드랑이 대리영역0~35%/상단 볼록부 접촉을 주장하려면 raw contact local→world 일치·캡슐 표면·구간·G 영역을 별도로 검증해야 한다. [계획 V3](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BOUT_AXILLA_PLAN_V3.md:10)는 이 한계를 명시한다. 그 후속 공간 분석을 이번 사전 검수에서 인증한 것은 아니다.

이전 V1 거절/V2 차단 원본을 보존하고 최대2개 native 시각 진단을 진행할 수 있다. 실제 초기 FK 일치·접촉·자세·기타 유지 결과는 실행 후 검수 대상이다.

검수 SHA256:

- 계획 V3: `377617f8530ce831c6567c0ceb87527897ddbd9a9a590d2182d12b5efc1d16c5`
- prepare V3: `68c328f4ff5ab5f962ee8c1d995fe834babab8cc4c7e418bfb8ef75f99560352`
- runner V3: `208b00078b572adf8d36413364d041efe37d9c3c8af5dd192c5d7d7c9cadc9e2`
- search V3: `0b6493a8222d3a1571851a55dea1e07ca3c5f04bb602379c0572fed0227f0663`

허용된 새 리뷰 파일만 작성했고 원본·다른 담당자의 소스/결과는 수정하지 않았다.
